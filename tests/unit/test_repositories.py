from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.data.freshness import calc_collection_range, get_collectible_end_date
from src.data.storage.financial_repository import FinancialRepository
from src.data.storage.price_repository import PriceRepository
from src.data.storage.stock_repository import StockRepository


class FakeRecord(dict):
    """Simple dict subclass to mimic asyncpg.Record behavior."""

    pass


# ============================================================================
# Tests for freshness.py functions
# ============================================================================


class TestGetCollectibleEndDate:
    """Tests for get_collectible_end_date() function."""

    def test_after_18_returns_today(self):
        """After 18:00 KST on weekday should return today."""
        # Mock datetime.now to return 18:00 on a Friday (weekday=4)
        mock_time = datetime(2026, 3, 6, 18, 0, 0)  # Friday 18:00
        with patch("src.data.freshness.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_time
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            result = get_collectible_end_date()
            assert result == date(2026, 3, 6)

    def test_before_18_returns_yesterday(self):
        """Before 18:00 KST on weekday should return yesterday."""
        # Mock datetime.now to return 17:59 on a Friday (weekday=4)
        mock_time = datetime(2026, 3, 6, 17, 59, 0)  # Friday 17:59
        with patch("src.data.freshness.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_time
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            result = get_collectible_end_date()
            assert result == date(2026, 3, 5)  # Thursday

    def test_saturday_rolls_back_to_friday(self):
        """Saturday should roll back to Friday."""
        # Mock datetime.now to return Saturday 20:00
        mock_time = datetime(2026, 3, 7, 20, 0, 0)  # Saturday 20:00
        with patch("src.data.freshness.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_time
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            result = get_collectible_end_date()
            assert result == date(2026, 3, 6)  # Friday

    def test_sunday_rolls_back_to_friday(self):
        """Sunday should roll back to Friday."""
        # Mock datetime.now to return Sunday 10:00
        mock_time = datetime(2026, 3, 8, 10, 0, 0)  # Sunday 10:00
        with patch("src.data.freshness.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_time
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            result = get_collectible_end_date()
            assert result == date(2026, 3, 6)  # Friday


class TestCalcCollectionRange:
    """Tests for calc_collection_range() function."""

    def test_none_returns_90_day_range(self):
        """When db_latest_date is None, return 90-day range."""
        collectible_end = date(2026, 3, 7)
        result = calc_collection_range(None, collectible_end)
        assert result is not None
        start, end = result
        assert end == collectible_end
        assert (end - start).days == 90

    def test_up_to_date_returns_none(self):
        """When db_latest >= collectible_end, return None."""
        collectible_end = date(2026, 3, 7)
        db_latest = "20260307"
        result = calc_collection_range(db_latest, collectible_end)
        assert result is None

    def test_future_date_returns_none(self):
        """When db_latest > collectible_end, return None."""
        collectible_end = date(2026, 3, 7)
        db_latest = "20260308"
        result = calc_collection_range(db_latest, collectible_end)
        assert result is None

    def test_needs_update_returns_range(self):
        """When db_latest < collectible_end, return range."""
        collectible_end = date(2026, 3, 7)
        db_latest = "20260305"
        result = calc_collection_range(db_latest, collectible_end)
        assert result is not None
        start, end = result
        assert start == date(2026, 3, 6)  # latest + 1 day
        assert end == collectible_end


# ============================================================================
# Tests for PriceRepository
# ============================================================================


class TestPriceRepository:
    """Tests for PriceRepository class."""

    def make_mock_pool(self, fetchrow_return=None, fetch_return=None):
        """Helper to create a mock asyncpg pool."""
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=fetchrow_return)
        conn.fetch = AsyncMock(return_value=fetch_return or [])

        pool = MagicMock()
        pool.acquire = MagicMock()
        pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
        pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        return pool, conn

    async def test_get_recent_returns_prices(self):
        """get_recent should return list of DailyPrice objects."""
        row = FakeRecord(
            {
                "stock_code": "005930",
                "date": date(2026, 3, 7),
                "open_price": 70000,
                "high_price": 71000,
                "low_price": 69000,
                "close_price": 70500,
                "volume": 1000000,
                "trading_value": None,
                "market_cap": None,
            }
        )
        pool, conn = self.make_mock_pool(fetch_return=[row])

        repo = PriceRepository(pool)
        with patch.object(repo, "ensure_fresh", new_callable=AsyncMock):
            result = await repo.get_recent("005930", days=60)

        assert len(result) == 1
        assert result[0].stock_code == "005930"
        assert result[0].close_price == 70500
        assert result[0].volume == 1000000

    async def test_ensure_fresh_no_collector_is_noop(self):
        """ensure_fresh with collector=None should do nothing."""
        pool, _ = self.make_mock_pool()
        repo = PriceRepository(pool, collector=None)

        # Should not raise and should not call pool
        await repo.ensure_fresh("005930")
        pool.acquire.assert_not_called()

    async def test_get_latest_date_returns_none_when_no_data(self):
        """_get_latest_date_str should return None when no data exists."""
        pool, conn = self.make_mock_pool(fetchrow_return=None)
        repo = PriceRepository(pool)

        result = await repo._get_latest_date_str("005930")
        assert result is None

    async def test_get_latest_date_returns_string(self):
        """_get_latest_date_str should return date string when data exists."""
        row = FakeRecord({"latest": date(2026, 3, 7)})
        pool, conn = self.make_mock_pool(fetchrow_return=row)
        repo = PriceRepository(pool)

        result = await repo._get_latest_date_str("005930")
        assert result == "20260307"

    async def test_get_range_returns_prices(self):
        """get_range should return prices in date order."""
        row1 = FakeRecord(
            {
                "stock_code": "005930",
                "date": date(2026, 3, 5),
                "open_price": 70000,
                "high_price": 71000,
                "low_price": 69000,
                "close_price": 70500,
                "volume": 1000000,
                "trading_value": None,
                "market_cap": None,
            }
        )
        row2 = FakeRecord(
            {
                "stock_code": "005930",
                "date": date(2026, 3, 6),
                "open_price": 70500,
                "high_price": 71500,
                "low_price": 69500,
                "close_price": 71000,
                "volume": 1100000,
                "trading_value": None,
                "market_cap": None,
            }
        )
        pool, conn = self.make_mock_pool(fetch_return=[row1, row2])

        repo = PriceRepository(pool)
        with patch.object(repo, "ensure_fresh", new_callable=AsyncMock):
            result = await repo.get_range("005930", date(2026, 3, 5), date(2026, 3, 6))

        assert len(result) == 2
        assert result[0].date == date(2026, 3, 5)
        assert result[1].date == date(2026, 3, 6)

    async def test_get_bulk_returns_dict_by_stock_code(self):
        """get_bulk should return dict grouped by stock_code."""
        row1 = FakeRecord(
            {
                "stock_code": "005930",
                "date": date(2026, 3, 7),
                "open_price": 70000,
                "high_price": 71000,
                "low_price": 69000,
                "close_price": 70500,
                "volume": 1000000,
                "trading_value": None,
                "market_cap": None,
            }
        )
        row2 = FakeRecord(
            {
                "stock_code": "000660",
                "date": date(2026, 3, 7),
                "open_price": 100000,
                "high_price": 101000,
                "low_price": 99000,
                "close_price": 100500,
                "volume": 500000,
                "trading_value": None,
                "market_cap": None,
            }
        )
        pool, conn = self.make_mock_pool(fetch_return=[row1, row2])

        repo = PriceRepository(pool)
        result = await repo.get_bulk(["005930", "000660"], date(2026, 3, 7), date(2026, 3, 7))

        assert "005930" in result
        assert "000660" in result
        assert len(result["005930"]) == 1
        assert len(result["000660"]) == 1


# ============================================================================
# Tests for StockRepository
# ============================================================================


class TestStockRepository:
    """Tests for StockRepository class."""

    def make_mock_pool(self, fetchrow_return=None):
        """Helper to create a mock asyncpg pool."""
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=fetchrow_return)

        pool = MagicMock()
        pool.acquire = MagicMock()
        pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
        pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        return pool, conn

    async def test_get_returns_stock(self):
        """get should return Stock object when found."""
        row = FakeRecord(
            {
                "stock_code": "005930",
                "stock_name": "삼성전자",
                "market": "KOSPI",
                "sector": "전자",
                "industry": "반도체",
            }
        )
        pool, conn = self.make_mock_pool(fetchrow_return=row)

        repo = StockRepository(pool)
        result = await repo.get("005930")

        assert result is not None
        assert result.stock_code == "005930"
        assert result.stock_name == "삼성전자"
        assert result.market == "KOSPI"
        assert result.sector == "전자"
        assert result.industry == "반도체"

    async def test_get_returns_none_when_not_found(self):
        """get should return None when stock not found."""
        pool, conn = self.make_mock_pool(fetchrow_return=None)

        repo = StockRepository(pool)
        result = await repo.get("999999")

        assert result is None

    async def test_exists_returns_true(self):
        """exists should return True when stock found."""
        row = FakeRecord({"1": 1})
        pool, conn = self.make_mock_pool(fetchrow_return=row)

        repo = StockRepository(pool)
        result = await repo.exists("005930")

        assert result is True

    async def test_exists_returns_false(self):
        """exists should return False when stock not found."""
        pool, conn = self.make_mock_pool(fetchrow_return=None)

        repo = StockRepository(pool)
        result = await repo.exists("999999")

        assert result is False

    async def test_get_with_none_sector_industry(self):
        """get should handle None sector and industry."""
        row = FakeRecord(
            {
                "stock_code": "005930",
                "stock_name": "삼성전자",
                "market": "KOSPI",
                "sector": None,
                "industry": None,
            }
        )
        pool, conn = self.make_mock_pool(fetchrow_return=row)

        repo = StockRepository(pool)
        result = await repo.get("005930")

        assert result is not None
        assert result.sector is None
        assert result.industry is None


# ============================================================================
# Tests for FinancialRepository
# ============================================================================


class TestFinancialRepository:
    """Tests for FinancialRepository class."""

    def make_mock_pool(self, fetch_return=None):
        """Helper to create a mock asyncpg pool."""
        conn = AsyncMock()
        conn.fetch = AsyncMock(return_value=fetch_return or [])

        pool = MagicMock()
        pool.acquire = MagicMock()
        pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
        pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        return pool, conn

    async def test_get_recent_returns_financials(self):
        """get_recent should return list of FinancialData objects."""
        row = FakeRecord(
            {
                "stock_code": "005930",
                "quarter": "2025Q3",
                "revenue": 1000000.0,
                "operating_income": 200000.0,
                "net_income": 150000.0,
                "per": 10.5,
                "pbr": 1.2,
                "roe": 15.0,
                "debt_ratio": 30.0,
                "eps": 1000.0,
                "bps": 8000.0,
                "fs_div": "CFS",
            }
        )
        pool, conn = self.make_mock_pool(fetch_return=[row])

        repo = FinancialRepository(pool)
        result = await repo.get_recent("005930", limit=8)

        assert len(result) == 1
        assert result[0].stock_code == "005930"
        assert result[0].quarter == "2025Q3"
        assert result[0].revenue == 1000000.0
        assert result[0].per == 10.5

    async def test_get_recent_with_none_values(self):
        """get_recent should handle None financial values."""
        row = FakeRecord(
            {
                "stock_code": "005930",
                "quarter": "2025Q3",
                "revenue": None,
                "operating_income": None,
                "net_income": None,
                "per": None,
                "pbr": None,
                "roe": None,
                "debt_ratio": None,
                "eps": None,
                "bps": None,
                "fs_div": None,
            }
        )
        pool, conn = self.make_mock_pool(fetch_return=[row])

        repo = FinancialRepository(pool)
        result = await repo.get_recent("005930", limit=8)

        assert len(result) == 1
        assert result[0].revenue is None
        assert result[0].per is None
        assert result[0].fs_div is None

    async def test_get_recent_returns_empty_list(self):
        """get_recent should return empty list when no data."""
        pool, conn = self.make_mock_pool(fetch_return=[])

        repo = FinancialRepository(pool)
        result = await repo.get_recent("999999", limit=8)

        assert result == []

    async def test_get_recent_multiple_quarters(self):
        """get_recent should return multiple quarters in order."""
        row1 = FakeRecord(
            {
                "stock_code": "005930",
                "quarter": "2025Q3",
                "revenue": 1000000.0,
                "operating_income": 200000.0,
                "net_income": 150000.0,
                "per": 10.5,
                "pbr": 1.2,
                "roe": 15.0,
                "debt_ratio": 30.0,
                "eps": 1000.0,
                "bps": 8000.0,
                "fs_div": "CFS",
            }
        )
        row2 = FakeRecord(
            {
                "stock_code": "005930",
                "quarter": "2025Q2",
                "revenue": 950000.0,
                "operating_income": 190000.0,
                "net_income": 140000.0,
                "per": 10.8,
                "pbr": 1.25,
                "roe": 14.5,
                "debt_ratio": 32.0,
                "eps": 950.0,
                "bps": 7800.0,
                "fs_div": "CFS",
            }
        )
        pool, conn = self.make_mock_pool(fetch_return=[row1, row2])

        repo = FinancialRepository(pool)
        result = await repo.get_recent("005930", limit=8)

        assert len(result) == 2
        assert result[0].quarter == "2025Q3"
        assert result[1].quarter == "2025Q2"
