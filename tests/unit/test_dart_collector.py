from unittest.mock import AsyncMock, patch

import pytest

from src.data.collectors.dart_errors import (
    DartAPIError,
    DartNoDataError,
    DartRateLimitError,
)
from src.data.collectors.dart_parser import parse_corp_code_xml, parse_dart_response


class TestParseDartResponse:
    """Test parse_dart_response function."""

    def test_parse_dart_response_success(self) -> None:
        """Test successful DART API response parsing with status 000."""
        response = {
            "status": "000",
            "message": "정상",
            "list": [{"account_nm": "매출액", "thstrm_amount": "300000000000"}],
        }
        result = parse_dart_response(response)
        assert len(result) == 1
        assert result[0]["account_nm"] == "매출액"

    def test_parse_dart_response_no_data_raises_dart_no_data_error(self) -> None:
        """Test that status 013 raises DartNoDataError."""
        response = {"status": "013", "message": "데이터가 없습니다"}
        with pytest.raises(DartNoDataError) as exc_info:
            parse_dart_response(response)
        assert exc_info.value.status == "013"

    def test_parse_dart_response_rate_limit_raises(self) -> None:
        """Test that status 020 raises DartRateLimitError."""
        response = {"status": "020", "message": "일일 한도 초과"}
        with pytest.raises(DartRateLimitError):
            parse_dart_response(response)

    def test_parse_dart_response_unknown_error_raises(self) -> None:
        """Test that unknown status raises DartAPIError."""
        response = {"status": "100", "message": "파라미터 오류"}
        with pytest.raises(DartAPIError) as exc_info:
            parse_dart_response(response)
        assert exc_info.value.status == "100"


class TestParseCorporateCodeXml:
    """Test parse_corp_code_xml function."""

    def test_parse_corp_code_xml_returns_mapping(self) -> None:
        """Test XML parsing returns correct stock_code to corp_code mapping."""
        xml_str = """<?xml version="1.0" encoding="UTF-8"?>
<result>
  <list>
    <corp_code>00126380</corp_code>
    <corp_name>삼성전자</corp_name>
    <stock_code>005930</stock_code>
    <modify_date>20240101</modify_date>
  </list>
  <list>
    <corp_code>00164779</corp_code>
    <corp_name>비상장회사</corp_name>
    <stock_code> </stock_code>
    <modify_date>20240101</modify_date>
  </list>
</result>"""
        xml_bytes = xml_str.encode("utf-8")
        mapping = parse_corp_code_xml(xml_bytes)
        assert mapping["005930"] == "00126380"
        assert len(mapping) == 1

    def test_parse_corp_code_xml_excludes_unlisted_companies(self) -> None:
        """Test that unlisted companies (empty stock_code) are excluded."""
        xml_str = """<?xml version="1.0" encoding="UTF-8"?>
<result>
  <list>
    <corp_code>00126380</corp_code>
    <corp_name>삼성전자</corp_name>
    <stock_code>005930</stock_code>
  </list>
  <list>
    <corp_code>00164779</corp_code>
    <corp_name>비상장회사</corp_name>
    <stock_code></stock_code>
  </list>
</result>"""
        xml_bytes = xml_str.encode("utf-8")
        mapping = parse_corp_code_xml(xml_bytes)
        assert "00164779" not in mapping.values()
        assert len(mapping) == 1


class TestDartCorpCodeMapper:
    def test_corp_code_mapper_parse_xml_fixture(self) -> None:
        from src.data.collectors.dart_corp_code import DartCorpCodeMapper

        mapper = DartCorpCodeMapper()
        mapper._mapping = {"005930": "00126380", "000660": "00164742"}
        assert mapper.get_corp_code("005930") == "00126380"
        assert mapper.get_corp_code("000660") == "00164742"

    def test_corp_code_mapper_returns_none_for_unknown_stock(self) -> None:
        from src.data.collectors.dart_corp_code import DartCorpCodeMapper

        mapper = DartCorpCodeMapper()
        mapper._mapping = {"005930": "00126380"}
        assert mapper.get_corp_code("999999") is None


class TestDartCollector:
    def test_dart_collector_instantiation(self) -> None:
        from src.data.collectors.dart_collector import DartCollector

        collector = DartCollector(api_key="test_key", rate_limit_per_minute=60)
        assert collector is not None

    async def test_get_financial_data_success(self) -> None:
        from src.data.collectors.dart_collector import DartCollector
        from src.data.models import FinancialData

        mock_accounts = [
            {"account_nm": "매출액", "thstrm_amount": "300000000000"},
            {"account_nm": "영업이익", "thstrm_amount": "50000000000"},
            {"account_nm": "당기순이익", "thstrm_amount": "40000000000"},
        ]

        collector = DartCollector(api_key="test_key")
        with patch.object(
            collector, "_get_main_accounts", new=AsyncMock(return_value=mock_accounts)
        ):
            with patch.object(
                collector,
                "_get_financial_indicators",
                new=AsyncMock(return_value={"roe": 15.5, "eps": 5000.0}),
            ):
                result = await collector.get_financial_data(
                    corp_code="00126380",
                    stock_code="005930",
                    bsns_year="2024",
                    reprt_code="11011",
                    current_price=75000,
                )

        assert result is not None
        assert isinstance(result, FinancialData)
        assert result.stock_code == "005930"
        assert result.quarter == "2024Q4"
        assert result.revenue == 300000000000.0
        assert result.roe == 15.5

    async def test_get_financial_data_cfs_fallback_to_ofs(self) -> None:
        from src.data.collectors.dart_collector import DartCollector

        mock_accounts = [{"account_nm": "매출액", "thstrm_amount": "100000000000"}]
        call_count = 0

        async def mock_get_accounts(
            corp_code: str, bsns_year: str, reprt_code: str, fs_div: str
        ) -> list[dict]:
            nonlocal call_count
            call_count += 1
            if fs_div == "CFS":
                raise DartNoDataError("No CFS data", status="013")
            return mock_accounts

        collector = DartCollector(api_key="test_key")
        with patch.object(collector, "_get_main_accounts", side_effect=mock_get_accounts):
            with patch.object(
                collector, "_get_financial_indicators", new=AsyncMock(return_value={})
            ):
                result = await collector.get_financial_data(
                    corp_code="00164742",
                    stock_code="000660",
                    bsns_year="2024",
                    reprt_code="11011",
                )

        assert result is not None
        assert call_count == 2

    async def test_get_financial_data_financial_sector_returns_none(self) -> None:
        from src.data.collectors.dart_collector import DartCollector

        mock_accounts = [
            {"account_nm": "이자수익", "thstrm_amount": "5000000000"},
            {"account_nm": "수수료수익", "thstrm_amount": "1000000000"},
        ]

        collector = DartCollector(api_key="test_key")
        with patch.object(
            collector, "_get_main_accounts", new=AsyncMock(return_value=mock_accounts)
        ):
            result = await collector.get_financial_data(
                corp_code="00000001",
                stock_code="105560",
                bsns_year="2024",
                reprt_code="11011",
            )

        assert result is None

    async def test_get_financial_data_calculates_per_pbr(self) -> None:
        from src.data.collectors.dart_collector import DartCollector

        mock_accounts = [
            {"account_nm": "매출액", "thstrm_amount": "100000000000"},
            {"account_nm": "당기순이익", "thstrm_amount": "50000000000"},
            {"account_nm": "기본주당이익", "thstrm_amount": "5000"},
            {"account_nm": "자본총계", "thstrm_amount": "500000000000"},
        ]
        mock_indicators: dict = {}

        collector = DartCollector(api_key="test_key")
        with patch.object(
            collector, "_get_main_accounts", new=AsyncMock(return_value=mock_accounts)
        ):
            with patch.object(
                collector, "_get_financial_indicators", new=AsyncMock(return_value=mock_indicators)
            ):
                result = await collector.get_financial_data(
                    corp_code="00126380",
                    stock_code="005930",
                    bsns_year="2024",
                    reprt_code="11011",
                    current_price=75000,
                )

        assert result is not None
        assert result.eps == 5000.0
        assert result.bps == 50000.0
        assert result.per == 15.0
        assert result.pbr == 1.5
