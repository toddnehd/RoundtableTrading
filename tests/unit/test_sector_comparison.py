from unittest.mock import AsyncMock, MagicMock

from src.screener.pipeline import ScreeningPipeline


class FakeRecord:
    def __init__(self, data: dict) -> None:
        self._data = data

    def __getitem__(self, key: str):
        return self._data[key]


class TestScreeningPipelineSectorComparison:
    def _make_pool(self, fetchrow_return) -> tuple:
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=fetchrow_return)
        pool = MagicMock()
        pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
        pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        return pool, conn

    async def test_raises_when_not_connected(self):
        pipeline = ScreeningPipeline.__new__(ScreeningPipeline)
        pipeline._pool = None

        try:
            await pipeline.get_sector_comparison("005930", "반도체")
            assert False, "RuntimeError expected"
        except RuntimeError as e:
            assert "connect" in str(e).lower()

    async def test_returns_sector_averages(self):
        row = FakeRecord(
            {
                "sector_per_avg": 18.5,
                "sector_pbr_avg": 1.8,
                "sector_roe_avg": 12.0,
                "sector_op_margin_avg": 15.0,
                "peer_count": 12,
            }
        )
        pool, conn = self._make_pool(fetchrow_return=row)
        pipeline = ScreeningPipeline.__new__(ScreeningPipeline)
        pipeline._pool = pool

        result = await pipeline.get_sector_comparison("005930", "반도체")

        assert result["sector_per_avg"] == 18.5
        assert result["sector_pbr_avg"] == 1.8
        assert result["sector_roe_avg"] == 12.0
        assert result["sector_op_margin_avg"] == 15.0
        assert result["peer_count"] == 12.0

    async def test_returns_none_values_when_no_peers(self):
        row = FakeRecord(
            {
                "sector_per_avg": None,
                "sector_pbr_avg": None,
                "sector_roe_avg": None,
                "sector_op_margin_avg": None,
                "peer_count": 0,
            }
        )
        pool, conn = self._make_pool(fetchrow_return=row)
        pipeline = ScreeningPipeline.__new__(ScreeningPipeline)
        pipeline._pool = pool

        result = await pipeline.get_sector_comparison("005930", "반도체")

        assert result["sector_per_avg"] is None
        assert result["sector_roe_avg"] is None
        assert result["peer_count"] == 0.0

    async def test_returns_all_none_when_row_is_none(self):
        pool, conn = self._make_pool(fetchrow_return=None)
        pipeline = ScreeningPipeline.__new__(ScreeningPipeline)
        pipeline._pool = pool

        result = await pipeline.get_sector_comparison("005930", "반도체")

        assert all(v is None for v in result.values())
        assert set(result.keys()) == {
            "sector_per_avg",
            "sector_pbr_avg",
            "sector_roe_avg",
            "sector_op_margin_avg",
            "peer_count",
        }

    async def test_passes_correct_params_to_query(self):
        row = FakeRecord(
            {
                "sector_per_avg": 15.0,
                "sector_pbr_avg": 1.5,
                "sector_roe_avg": 10.0,
                "sector_op_margin_avg": 12.0,
                "peer_count": 5,
            }
        )
        pool, conn = self._make_pool(fetchrow_return=row)
        pipeline = ScreeningPipeline.__new__(ScreeningPipeline)
        pipeline._pool = pool

        await pipeline.get_sector_comparison("000660", "반도체")

        conn.fetchrow.assert_called_once()
        call_args = conn.fetchrow.call_args[0]
        assert "반도체" in call_args
        assert "000660" in call_args
