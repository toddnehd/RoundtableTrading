"""Expanded DART collector validation tests (T13).

Tests for multi-name account extraction, growth rate calculation,
14-field derived metrics, and indicator API fallback behavior.
"""

from unittest.mock import AsyncMock, patch

from src.data.collectors.dart_collector import (
    OPERATING_INCOME_NAMES,
    REVENUE_NAMES,
    DartCollector,
)
from src.data.collectors.dart_errors import DartNoDataError
from src.data.models import FinancialData


class TestExtractAccountMultiName:
    """Verify _extract_account_any() matches REVENUE_NAMES in priority order."""

    def test_matches_first_name_revenue(self) -> None:
        """Case A: '매출액' present → returns its value."""
        accounts = [
            {"account_nm": "매출액", "thstrm_amount": "500000000000"},
            {"account_nm": "영업수익", "thstrm_amount": "999999999999"},
        ]
        collector = DartCollector(api_key="test_key")
        result = collector._extract_account_any(accounts, REVENUE_NAMES)
        assert result == 500000000000.0

    def test_fallback_to_operating_revenue_when_revenue_absent(self) -> None:
        """Case B: '매출액' absent, '영업수익' present → returns 영업수익 value."""
        accounts = [
            {"account_nm": "기타수익", "thstrm_amount": "1000"},
            {"account_nm": "영업수익", "thstrm_amount": "200000000000"},
        ]
        collector = DartCollector(api_key="test_key")
        result = collector._extract_account_any(accounts, REVENUE_NAMES)
        assert result == 200000000000.0

    def test_returns_none_when_no_name_matches(self) -> None:
        """Case C: None of REVENUE_NAMES present → returns None."""
        accounts = [
            {"account_nm": "수수료수익", "thstrm_amount": "3000000000"},
            {"account_nm": "유가증권평가이익", "thstrm_amount": "1000000000"},
        ]
        collector = DartCollector(api_key="test_key")
        result = collector._extract_account_any(accounts, REVENUE_NAMES)
        assert result is None

    def test_operating_income_names_fallback(self) -> None:
        """OPERATING_INCOME_NAMES fallback: '영업이익' absent → '영업이익(손실)' matches."""
        accounts = [
            {"account_nm": "영업이익(손실)", "thstrm_amount": "30000000000"},
        ]
        collector = DartCollector(api_key="test_key")
        result = collector._extract_account_any(accounts, OPERATING_INCOME_NAMES)
        assert result == 30000000000.0


class TestGrowthRateCalculation:
    """Verify _calculate_derived_metrics() growth rate logic."""

    def _make_accounts(
        self,
        revenue: str,
        prev_revenue: str,
        op_income: str = "0",
        prev_op_income: str = "0",
    ) -> list[dict]:
        """Build mock account list with current and prior term amounts."""
        return [
            {
                "account_nm": "매출액",
                "thstrm_amount": revenue,
                "frmtrm_amount": prev_revenue,
            },
            {
                "account_nm": "영업이익",
                "thstrm_amount": op_income,
                "frmtrm_amount": prev_op_income,
            },
            {
                "account_nm": "당기순이익",
                "thstrm_amount": "0",
                "frmtrm_amount": "0",
            },
        ]

    def test_positive_growth_rate(self) -> None:
        """revenue=1200, prev=1000 → revenue_growth=20.0%."""
        accounts = self._make_accounts(
            revenue="1200000000000",
            prev_revenue="1000000000000",
            op_income="120000000000",
            prev_op_income="100000000000",
        )
        collector = DartCollector(api_key="test_key")
        derived = collector._calculate_derived_metrics(accounts, {}, None)

        assert derived["revenue_growth"] == 20.0
        assert derived["operating_income_growth"] == 20.0

    def test_negative_growth_rate(self) -> None:
        """revenue=800, prev=1000 → revenue_growth=-20.0%."""
        accounts = self._make_accounts(
            revenue="800000000000",
            prev_revenue="1000000000000",
        )
        collector = DartCollector(api_key="test_key")
        derived = collector._calculate_derived_metrics(accounts, {}, None)

        assert derived["revenue_growth"] == -20.0

    def test_zero_prev_returns_none(self) -> None:
        """prev=0 → growth_rate=None (division by zero guard)."""
        accounts = self._make_accounts(
            revenue="1200000000000",
            prev_revenue="0",
        )
        collector = DartCollector(api_key="test_key")
        derived = collector._calculate_derived_metrics(accounts, {}, None)

        assert derived["revenue_growth"] is None


class TestFinancialDataHas14Fields:
    """Verify get_financial_data() returns FinancialData with 14 extended fields."""

    async def test_all_derived_fields_populated(self) -> None:
        """All 14 extended fields should be non-None when sufficient data exists."""
        mock_accounts = [
            {
                "account_nm": "매출액",
                "thstrm_amount": "1200000000000",
                "frmtrm_amount": "1000000000000",
            },
            {
                "account_nm": "영업이익",
                "thstrm_amount": "120000000000",
                "frmtrm_amount": "100000000000",
            },
            {
                "account_nm": "당기순이익",
                "thstrm_amount": "80000000000",
                "frmtrm_amount": "70000000000",
            },
            {"account_nm": "기본주당이익", "thstrm_amount": "8000"},
            {"account_nm": "자산총계", "thstrm_amount": "2000000000000"},
            {"account_nm": "자본총계", "thstrm_amount": "1000000000000"},
            {"account_nm": "감가상각비", "thstrm_amount": "30000000000"},
            {"account_nm": "유동자산", "thstrm_amount": "600000000000"},
            {"account_nm": "유동부채", "thstrm_amount": "300000000000"},
            {"account_nm": "재고자산", "thstrm_amount": "50000000000"},
            {"account_nm": "이자비용", "thstrm_amount": "10000000000"},
            {"account_nm": "자본금", "thstrm_amount": "100000000000"},
            {"account_nm": "이익잉여금", "thstrm_amount": "500000000000"},
        ]

        mock_indicators = {
            "roe": 8.0,
            "debt_ratio": 100.0,
            "dps": 500.0,
            "dividend_yield": 0.67,
        }

        collector = DartCollector(api_key="test_key")
        with patch.object(
            collector, "_get_main_accounts", new=AsyncMock(return_value=mock_accounts)
        ):
            with patch.object(
                collector,
                "_get_financial_indicators",
                new=AsyncMock(return_value=mock_indicators),
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

        assert result.operating_margin is not None
        assert result.net_margin is not None
        assert result.roa is not None
        assert result.ebitda is not None
        assert result.current_ratio is not None
        assert result.quick_ratio is not None
        assert result.interest_coverage is not None
        assert result.capital_retention_ratio is not None
        assert result.ev_ebitda is not None
        assert result.dps is not None
        assert result.dividend_yield is not None
        assert result.revenue_growth is not None
        assert result.operating_income_growth is not None
        assert result.net_income_growth is not None

    async def test_derived_field_values_correct(self) -> None:
        """Spot-check derived metric calculations."""
        mock_accounts = [
            {
                "account_nm": "매출액",
                "thstrm_amount": "1000000000000",
                "frmtrm_amount": "800000000000",
            },
            {
                "account_nm": "영업이익",
                "thstrm_amount": "200000000000",
                "frmtrm_amount": "150000000000",
            },
            {
                "account_nm": "당기순이익",
                "thstrm_amount": "100000000000",
                "frmtrm_amount": "80000000000",
            },
            {"account_nm": "기본주당이익", "thstrm_amount": "10000"},
            {"account_nm": "자산총계", "thstrm_amount": "2000000000000"},
            {"account_nm": "자본총계", "thstrm_amount": "1000000000000"},
            {"account_nm": "감가상각비", "thstrm_amount": "50000000000"},
            {"account_nm": "유동자산", "thstrm_amount": "500000000000"},
            {"account_nm": "유동부채", "thstrm_amount": "250000000000"},
            {"account_nm": "자본금", "thstrm_amount": "100000000000"},
            {"account_nm": "이익잉여금", "thstrm_amount": "400000000000"},
        ]

        collector = DartCollector(api_key="test_key")
        with patch.object(
            collector, "_get_main_accounts", new=AsyncMock(return_value=mock_accounts)
        ):
            with patch.object(
                collector,
                "_get_financial_indicators",
                new=AsyncMock(return_value={}),
            ):
                result = await collector.get_financial_data(
                    corp_code="00126380",
                    stock_code="005930",
                    bsns_year="2024",
                    reprt_code="11011",
                )

        assert result is not None
        # operating_margin = operating_income / revenue * 100 = 200/1000 * 100 = 20.0
        assert result.operating_margin == 20.0
        # net_margin = net_income / revenue * 100 = 100/1000 * 100 = 10.0
        assert result.net_margin == 10.0
        # roa = net_income / total_assets * 100 = 100/2000 * 100 = 5.0
        assert result.roa == 5.0
        # revenue_growth = (1000 - 800) / 800 * 100 = 25.0
        assert result.revenue_growth == 25.0


class TestFallbackWithoutIndicatorAPI:
    """Verify get_financial_data() works when fnlttSinglIndx API fails."""

    async def test_basic_data_returned_despite_indicator_failure(self) -> None:
        """DartNoDataError from _get_financial_indicators → still returns data."""
        mock_accounts = [
            {
                "account_nm": "매출액",
                "thstrm_amount": "300000000000",
                "frmtrm_amount": "250000000000",
            },
            {
                "account_nm": "영업이익",
                "thstrm_amount": "50000000000",
                "frmtrm_amount": "40000000000",
            },
            {
                "account_nm": "당기순이익",
                "thstrm_amount": "40000000000",
                "frmtrm_amount": "35000000000",
            },
        ]

        collector = DartCollector(api_key="test_key")
        with patch.object(
            collector, "_get_main_accounts", new=AsyncMock(return_value=mock_accounts)
        ):
            with patch.object(
                collector,
                "_get_financial_indicators",
                new=AsyncMock(side_effect=DartNoDataError("No indicator data", status="013")),
            ):
                result = await collector.get_financial_data(
                    corp_code="00126380",
                    stock_code="005930",
                    bsns_year="2024",
                    reprt_code="11011",
                )

        assert result is not None
        assert isinstance(result, FinancialData)
        assert result.revenue == 300000000000.0
        assert result.operating_income == 50000000000.0
        assert result.net_income == 40000000000.0
        assert result.roe is None
        assert result.debt_ratio is None

    async def test_indicator_api_error_also_handled(self) -> None:
        """DartAPIError (not just DartNoDataError) also handled gracefully."""
        from src.data.collectors.dart_errors import DartAPIError

        mock_accounts = [
            {"account_nm": "매출액", "thstrm_amount": "100000000000"},
            {"account_nm": "영업이익", "thstrm_amount": "20000000000"},
            {"account_nm": "당기순이익", "thstrm_amount": "15000000000"},
        ]

        collector = DartCollector(api_key="test_key")
        with patch.object(
            collector, "_get_main_accounts", new=AsyncMock(return_value=mock_accounts)
        ):
            with patch.object(
                collector,
                "_get_financial_indicators",
                new=AsyncMock(side_effect=DartAPIError("Server error", status="800")),
            ):
                result = await collector.get_financial_data(
                    corp_code="00164742",
                    stock_code="000660",
                    bsns_year="2024",
                    reprt_code="11013",
                )

        assert result is not None
        assert result.stock_code == "000660"
        assert result.quarter == "2024Q1"
        assert result.revenue == 100000000000.0
