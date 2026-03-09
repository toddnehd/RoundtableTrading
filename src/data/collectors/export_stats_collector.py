"""관세청 수출입무역통계 API collector."""

import httpx
from loguru import logger

SECTOR_HS_CODES: dict[str, list[str]] = {
    "반도체": ["8542", "8541"],
    "자동차": ["8703", "8704"],
    "이차전지": ["8507"],
    "디스플레이": ["9013"],
    "조선": ["8901", "8902"],
    "철강": ["7206", "7207", "7208"],
    "화학": ["2901", "2902"],
    "바이오": ["3002", "3004"],
}


class ExportStatsCollector:
    """관세청 수출입무역통계 데이터 수집기.

    Note:
        관세청 공공 API (API 키 불필요).
        실패 시 None 반환 (graceful degradation).
    """

    BASE_URL = "https://unipass.customs.go.kr:38010/ext/rest/tradeStats"

    async def get_export_yoy(self, sector: str, year_month: str) -> float | None:
        """전년동월비 수출증가율 조회.

        Args:
            sector: 섹터명 (SECTOR_HS_CODES의 키)
            year_month: 조회 연월 (YYYYMM)

        Returns:
            전년동월비 수출증가율 (%) 또는 None
        """
        hs_codes = SECTOR_HS_CODES.get(sector)
        if not hs_codes:
            logger.warning(f"Unknown sector: {sector}")
            return None

        try:
            total_current = 0.0
            total_prev = 0.0
            prev_year_month = self._get_prev_year_month(year_month)

            async with httpx.AsyncClient(timeout=10.0) as client:
                for hs_code in hs_codes[:2]:
                    current = await self._fetch_export_amount(client, hs_code, year_month)
                    prev = await self._fetch_export_amount(client, hs_code, prev_year_month)
                    if current is not None:
                        total_current += current
                    if prev is not None:
                        total_prev += prev

            if total_prev > 0:
                return round((total_current - total_prev) / total_prev * 100, 2)
            return None

        except Exception as e:
            logger.error(f"Failed to get export stats for {sector}: {e}")
            return None

    async def _fetch_export_amount(
        self, client: httpx.AsyncClient, hs_code: str, year_month: str
    ) -> float | None:
        """단일 HS코드의 수출금액 조회."""
        try:
            params = {
                "customsCode": "00",
                "dateType": "MON",
                "startDate": year_month,
                "endDate": year_month,
                "hsCode": hs_code,
                "tradeType": "E",
            }
            response = await client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            items = data.get("tradeStats", {}).get("item", [])
            if items:
                return float(str(items[0].get("expDlr", "0")).replace(",", ""))
            return None
        except Exception:
            return None

    def _get_prev_year_month(self, year_month: str) -> str:
        """전년동월 계산 (YYYYMM -> 전년 YYYYMM)."""
        year = int(year_month[:4]) - 1
        month = year_month[4:]
        return f"{year}{month}"
