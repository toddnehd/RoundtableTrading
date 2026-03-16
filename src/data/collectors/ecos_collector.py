import asyncio
from datetime import date, datetime

import httpx
from loguru import logger

from src.data.models import MacroSnapshot

_BASE_RATE_STAT = "722Y001"
_BASE_RATE_ITEM = "0101000"
_USD_KRW_STAT = "731Y001"
_USD_KRW_ITEM = "0000001"
_CPI_STAT = "901Y009"
_CPI_ITEM = "0"


class EcosCollector:
    """한국은행 ECOS API 기반 거시경제 데이터 수집.

    기준금리, 원달러 환율, CPI 전년비를 제공.
    API 키 미설정 시 빈 리스트/None 즉시 반환.
    """

    BASE_URL = "https://ecos.bok.or.kr/api/StatisticSearch"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def _is_configured(self) -> bool:
        return bool(self._api_key)

    def _build_url(
        self, stat_code: str, item_code: str, start_date: str, end_date: str, period: str = "D"
    ) -> str:
        """ECOS API URL 생성."""
        return (
            f"{self.BASE_URL}/{self._api_key}/json/kr/1/100"
            f"/{stat_code}/{period}/{start_date}/{end_date}/{item_code}"
        )

    async def _fetch_series(
        self,
        client: httpx.AsyncClient,
        stat_code: str,
        item_code: str,
        start_date: str,
        end_date: str,
        period: str = "D",
    ) -> list[tuple[date, float]]:
        """ECOS API에서 시계열 데이터 조회."""
        url = self._build_url(stat_code, item_code, start_date, end_date, period)
        try:
            resp = await client.get(url, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            rows = data.get("StatisticSearch", {}).get("row", [])
            if not rows:
                logger.debug(f"ECOS: no rows for stat_code={stat_code}, item_code={item_code}")
                return []

            result: list[tuple[date, float]] = []
            for row in rows:
                time_str = row.get("TIME", "")
                value_str = row.get("DATA_VALUE", "")
                if not time_str or not value_str:
                    continue
                try:
                    # YYYYMMDD 또는 YYYYMM 형식 처리
                    if len(time_str) == 6:
                        time_str = time_str + "01"
                    date_val = datetime.strptime(time_str, "%Y%m%d").date()
                    value = float(value_str)
                    result.append((date_val, value))
                except (ValueError, TypeError):
                    continue

            return result

        except httpx.HTTPStatusError as e:
            logger.error(f"ECOS HTTP error [stat={stat_code}]: {e}")
            return []
        except Exception as e:
            logger.error(f"ECOS fetch error [stat={stat_code}]: {e}")
            return []

    async def get_base_rate(self, start_date: str, end_date: str) -> list[tuple[date, float]]:
        """기준금리 일별 조회.

        Args:
            start_date: 조회 시작일 (YYYYMMDD)
            end_date: 조회 종료일 (YYYYMMDD)

        Returns:
            (날짜, 기준금리%) 튜플 리스트. 실패 시 빈 리스트.
        """
        if not self._is_configured():
            logger.warning("ECOS API key not configured — skipping base rate")
            return []

        async with httpx.AsyncClient() as client:
            result = await self._fetch_series(
                client, _BASE_RATE_STAT, _BASE_RATE_ITEM, start_date, end_date, "D"
            )

        logger.info(f"ECOS base rate: {len(result)} records ({start_date}~{end_date})")
        return result

    async def get_usd_krw(self, start_date: str, end_date: str) -> list[tuple[date, float]]:
        """원달러 환율 일별 조회.

        Args:
            start_date: 조회 시작일 (YYYYMMDD)
            end_date: 조회 종료일 (YYYYMMDD)

        Returns:
            (날짜, 환율) 튜플 리스트. 실패 시 빈 리스트.
        """
        if not self._is_configured():
            logger.warning("ECOS API key not configured — skipping USD/KRW")
            return []

        async with httpx.AsyncClient() as client:
            result = await self._fetch_series(
                client, _USD_KRW_STAT, _USD_KRW_ITEM, start_date, end_date, "D"
            )

        logger.info(f"ECOS USD/KRW: {len(result)} records ({start_date}~{end_date})")
        return result

    async def get_cpi(self, start_date: str, end_date: str) -> list[tuple[date, float]]:
        """CPI 전년비 월별 조회.

        Args:
            start_date: 조회 시작월 (YYYYMMDD 또는 YYYYMM)
            end_date: 조회 종료월 (YYYYMMDD 또는 YYYYMM)

        Returns:
            (날짜, CPI전년비%) 튜플 리스트. 실패 시 빈 리스트.
        """
        if not self._is_configured():
            logger.warning("ECOS API key not configured — skipping CPI")
            return []

        async with httpx.AsyncClient() as client:
            result = await self._fetch_series(
                client, _CPI_STAT, _CPI_ITEM, start_date, end_date, "M"
            )

        logger.info(f"ECOS CPI: {len(result)} records ({start_date}~{end_date})")
        return result

    async def get_macro_snapshot(self, target_date: date) -> MacroSnapshot | None:
        """특정 날짜 기준 거시경제 스냅샷 조회.

        3개 API(기준금리, 환율, CPI)를 병렬 호출하여 가장 가까운 이전 값 사용.
        거시지표는 일별로 없을 수 있으므로 가장 최근 이전 값을 사용.

        Args:
            target_date: 기준 날짜

        Returns:
            MacroSnapshot 객체. 실패 시 None.
        """
        if not self._is_configured():
            logger.warning("ECOS API key not configured — skipping macro snapshot")
            return None

        # 조회 범위: target_date 기준 90일 이전 ~ target_date
        end_str = target_date.strftime("%Y%m%d")
        start_date = date(target_date.year - 1, target_date.month, target_date.day)
        start_str = start_date.strftime("%Y%m%d")

        try:
            base_rate_data, usd_krw_data, cpi_data = await asyncio.gather(
                self.get_base_rate(start_str, end_str),
                self.get_usd_krw(start_str, end_str),
                self.get_cpi(start_str, end_str),
            )
        except Exception as e:
            logger.error(f"ECOS macro snapshot gather error: {e}")
            return None

        def latest_value(series: list[tuple[date, float]]) -> float | None:
            """target_date 이하 가장 최근 값 반환."""
            candidates = [(d, v) for d, v in series if d <= target_date]
            if not candidates:
                return None
            return max(candidates, key=lambda x: x[0])[1]

        return MacroSnapshot(
            date=target_date,
            base_rate=latest_value(base_rate_data),
            usd_krw=latest_value(usd_krw_data),
            cpi_yoy=latest_value(cpi_data),
        )
