"""Unit tests for KisCollector using mock HTTP responses."""

from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.data.collectors.kis_collector import KisCollector
from src.data.models import InvestorFlow


class TestKisCollectorNotConfigured:
    """Tests for KisCollector behavior when API keys are not set."""

    async def test_get_investor_trading_returns_empty_when_not_configured(self):
        """get_investor_trading should return [] when KIS keys are missing."""
        with patch("src.data.collectors.kis_collector.settings") as mock_settings:
            mock_settings.kis_app_key = ""
            mock_settings.kis_app_secret = ""
            mock_settings.kis_is_virtual = False
            collector = KisCollector.__new__(KisCollector)
            collector._token = None
            collector._token_expires_at = None
            collector._base = "https://openapi.koreainvestment.com:9443"

            result = await collector.get_investor_trading("005930", "20260301", "20260307")

        assert result == []

    async def test_get_market_index_returns_empty_when_not_configured(self):
        """get_market_index should return [] when KIS keys are missing."""
        with patch("src.data.collectors.kis_collector.settings") as mock_settings:
            mock_settings.kis_app_key = ""
            mock_settings.kis_app_secret = ""
            mock_settings.kis_is_virtual = False
            collector = KisCollector.__new__(KisCollector)
            collector._token = None
            collector._token_expires_at = None
            collector._base = "https://openapi.koreainvestment.com:9443"

            result = await collector.get_market_index("20260301", "20260307")

        assert result == []


class TestKisCollectorInvestorTradingParsing:
    """Tests for KisCollector.get_investor_trading parsing logic."""

    def _make_collector(self, mock_settings: MagicMock) -> KisCollector:
        mock_settings.kis_app_key = "test_key"
        mock_settings.kis_app_secret = "test_secret"
        mock_settings.kis_is_virtual = False
        collector = KisCollector.__new__(KisCollector)
        collector._token = "cached_token"
        collector._token_expires_at = datetime.now() + timedelta(hours=1)
        collector._base = "https://openapi.koreainvestment.com:9443"
        return collector

    async def test_get_investor_trading_parses_response_correctly(self):
        """get_investor_trading should parse API JSON and return InvestorFlow list."""
        fake_response_data = {
            "rt_cd": "0",
            "output": [
                {
                    "stck_bsop_date": "20260307",
                    "frgn_ntby_qty": "1000000",
                    "orgn_ntby_qty": "-500000",
                    "prsn_ntby_qty": "-500000",
                },
                {
                    "stck_bsop_date": "20260306",
                    "frgn_ntby_qty": "200000",
                    "orgn_ntby_qty": "100000",
                    "prsn_ntby_qty": "-300000",
                },
            ],
        }

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json = MagicMock(return_value=fake_response_data)

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("src.data.collectors.kis_collector.settings") as mock_settings:
            collector = self._make_collector(mock_settings)
            with patch(
                "src.data.collectors.kis_collector.httpx.AsyncClient", return_value=mock_client
            ):
                result = await collector.get_investor_trading("005930", "20260301", "20260307")

        assert len(result) == 2
        assert all(isinstance(flow, InvestorFlow) for flow in result)
        first = result[0]
        assert first.stock_code == "005930"
        assert first.date == date(2026, 3, 6)
        assert first.foreign_net == 200000

    async def test_get_investor_trading_filters_by_date_range(self):
        """get_investor_trading should exclude records outside the date range."""
        fake_response_data = {
            "rt_cd": "0",
            "output": [
                {
                    "stck_bsop_date": "20260307",
                    "frgn_ntby_qty": "1000000",
                    "orgn_ntby_qty": "0",
                    "prsn_ntby_qty": "0",
                },
                {
                    "stck_bsop_date": "20260215",
                    "frgn_ntby_qty": "999999",
                    "orgn_ntby_qty": "0",
                    "prsn_ntby_qty": "0",
                },
            ],
        }

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json = MagicMock(return_value=fake_response_data)

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("src.data.collectors.kis_collector.settings") as mock_settings:
            collector = self._make_collector(mock_settings)
            with patch(
                "src.data.collectors.kis_collector.httpx.AsyncClient", return_value=mock_client
            ):
                result = await collector.get_investor_trading("005930", "20260301", "20260307")

        assert len(result) == 1
        assert result[0].date == date(2026, 3, 7)
        assert result[0].foreign_net == 1000000

    async def test_get_investor_trading_returns_empty_on_api_error_code(self):
        """get_investor_trading should return [] when rt_cd != '0'."""
        fake_response_data = {"rt_cd": "1", "msg1": "ErrMsg"}

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json = MagicMock(return_value=fake_response_data)

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("src.data.collectors.kis_collector.settings") as mock_settings:
            collector = self._make_collector(mock_settings)
            with patch(
                "src.data.collectors.kis_collector.httpx.AsyncClient", return_value=mock_client
            ):
                result = await collector.get_investor_trading("005930", "20260301", "20260307")

        assert result == []

    async def test_get_investor_trading_returns_empty_on_http_error(self):
        """get_investor_trading should return [] gracefully on HTTP error."""
        import httpx

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "500 Internal Server Error",
                request=MagicMock(),
                response=MagicMock(),
            )
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("src.data.collectors.kis_collector.settings") as mock_settings:
            collector = self._make_collector(mock_settings)
            with patch(
                "src.data.collectors.kis_collector.httpx.AsyncClient", return_value=mock_client
            ):
                result = await collector.get_investor_trading("005930", "20260301", "20260307")

        assert result == []

    async def test_get_investor_trading_returns_sorted_by_date(self):
        """get_investor_trading should return records sorted by date ascending."""
        fake_response_data = {
            "rt_cd": "0",
            "output": [
                {
                    "stck_bsop_date": "20260307",
                    "frgn_ntby_qty": "300",
                    "orgn_ntby_qty": "0",
                    "prsn_ntby_qty": "0",
                },
                {
                    "stck_bsop_date": "20260305",
                    "frgn_ntby_qty": "100",
                    "orgn_ntby_qty": "0",
                    "prsn_ntby_qty": "0",
                },
                {
                    "stck_bsop_date": "20260306",
                    "frgn_ntby_qty": "200",
                    "orgn_ntby_qty": "0",
                    "prsn_ntby_qty": "0",
                },
            ],
        }

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json = MagicMock(return_value=fake_response_data)

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("src.data.collectors.kis_collector.settings") as mock_settings:
            collector = self._make_collector(mock_settings)
            with patch(
                "src.data.collectors.kis_collector.httpx.AsyncClient", return_value=mock_client
            ):
                result = await collector.get_investor_trading("005930", "20260301", "20260310")

        assert result[0].foreign_net == 100
        assert result[1].foreign_net == 200
        assert result[2].foreign_net == 300


class TestKisCollectorMarketIndexParsing:
    """Tests for KisCollector.get_market_index parsing logic."""

    def _make_collector(self, mock_settings: MagicMock) -> KisCollector:
        mock_settings.kis_app_key = "test_key"
        mock_settings.kis_app_secret = "test_secret"
        mock_settings.kis_is_virtual = False
        collector = KisCollector.__new__(KisCollector)
        collector._token = "cached_token"
        collector._token_expires_at = datetime.now() + timedelta(hours=1)
        collector._base = "https://openapi.koreainvestment.com:9443"
        return collector

    async def test_get_market_index_parses_response_correctly(self):
        """get_market_index should return list of (date, kospi, kosdaq) tuples."""
        kospi_data = {
            "rt_cd": "0",
            "output2": [
                {"stck_bsop_date": "20260307", "bstp_nmix_prpr": "2700.00"},
                {"stck_bsop_date": "20260306", "bstp_nmix_prpr": "2680.50"},
            ],
        }
        kosdaq_data = {
            "rt_cd": "0",
            "output2": [
                {"stck_bsop_date": "20260307", "bstp_nmix_prpr": "900.00"},
                {"stck_bsop_date": "20260306", "bstp_nmix_prpr": "895.30"},
            ],
        }

        call_count = 0

        async def mock_get(*args: object, **kwargs: object) -> MagicMock:
            nonlocal call_count
            call_count += 1
            mock_resp = MagicMock()
            mock_resp.raise_for_status = MagicMock()
            mock_resp.json = MagicMock(return_value=kospi_data if call_count == 1 else kosdaq_data)
            return mock_resp

        mock_client = AsyncMock()
        mock_client.get = mock_get
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("src.data.collectors.kis_collector.settings") as mock_settings:
            collector = self._make_collector(mock_settings)
            with patch(
                "src.data.collectors.kis_collector.httpx.AsyncClient", return_value=mock_client
            ):
                result = await collector.get_market_index("20260301", "20260307")

        assert len(result) == 2
        assert all(len(row) == 3 for row in result)
        assert result[0][0] == date(2026, 3, 6)
        assert result[0][1] == 2680.50
        assert result[0][2] == 895.30
        assert result[1][0] == date(2026, 3, 7)
        assert result[1][1] == 2700.00
        assert result[1][2] == 900.00

    async def test_get_market_index_returns_empty_on_http_error(self):
        """get_market_index should return [] gracefully on HTTP error."""
        import httpx

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "503 Service Unavailable",
                request=MagicMock(),
                response=MagicMock(),
            )
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("src.data.collectors.kis_collector.settings") as mock_settings:
            collector = self._make_collector(mock_settings)
            with patch(
                "src.data.collectors.kis_collector.httpx.AsyncClient", return_value=mock_client
            ):
                result = await collector.get_market_index("20260301", "20260307")

        assert result == []


class TestKisCollectorIsConfigured:
    """Tests for KisCollector._is_configured method."""

    def test_is_configured_true_when_keys_set(self):
        """_is_configured should return True when both keys are non-empty."""
        with patch("src.data.collectors.kis_collector.settings") as mock_settings:
            mock_settings.kis_app_key = "abc123"
            mock_settings.kis_app_secret = "xyz789"
            mock_settings.kis_is_virtual = False
            collector = KisCollector.__new__(KisCollector)
            collector._token = None
            collector._token_expires_at = None
            collector._base = "https://openapi.koreainvestment.com:9443"
            assert collector._is_configured() is True

    def test_is_configured_false_when_keys_empty(self):
        """_is_configured should return False when keys are empty strings."""
        with patch("src.data.collectors.kis_collector.settings") as mock_settings:
            mock_settings.kis_app_key = ""
            mock_settings.kis_app_secret = ""
            mock_settings.kis_is_virtual = False
            collector = KisCollector.__new__(KisCollector)
            collector._token = None
            collector._token_expires_at = None
            collector._base = "https://openapi.koreainvestment.com:9443"
            assert collector._is_configured() is False
