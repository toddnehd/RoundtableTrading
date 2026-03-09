from datetime import date as date_type
from datetime import datetime, timedelta

import httpx
from loguru import logger

from src.config import settings
from src.data.models import InvestorFlow

_REAL_BASE = "https://openapi.koreainvestment.com:9443"
_VIRTUAL_BASE = "https://openapivts.koreainvestment.com:29443"

_INVESTOR_TR_ID = "FHKST01010900"
_INDEX_TR_ID = "FHKST03010100"
_KOSPI_CODE = "0001"
_KOSDAQ_CODE = "0002"


class KisCollector:
    """한국투자증권 KIS Developers API 기반 시장 데이터 수집.

    투자자별 매매동향과 KOSPI/KOSDAQ 지수 OHLCV를 제공.
    KRX 직접 스크래핑 차단(2026년~) 이후 공식 대체 수단.
    """

    def __init__(self) -> None:
        self._base = _VIRTUAL_BASE if settings.kis_is_virtual else _REAL_BASE
        self._token: str | None = None
        self._token_expires_at: datetime | None = None

    def _is_configured(self) -> bool:
        return bool(settings.kis_app_key and settings.kis_app_secret)

    async def _fetch_token(self, client: httpx.AsyncClient) -> str:
        resp = await client.post(
            f"{self._base}/oauth2/tokenP",
            json={
                "grant_type": "client_credentials",
                "appkey": settings.kis_app_key,
                "appsecret": settings.kis_app_secret,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        token: str = data["access_token"]
        self._token = token
        self._token_expires_at = datetime.now() + timedelta(hours=23, minutes=55)
        logger.info("KIS access token issued")
        return token

    async def _get_token(self, client: httpx.AsyncClient) -> str:
        if self._token and self._token_expires_at and datetime.now() < self._token_expires_at:
            return self._token
        return await self._fetch_token(client)

    def _auth_headers(self, token: str, tr_id: str) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "authorization": f"Bearer {token}",
            "appkey": settings.kis_app_key,
            "appsecret": settings.kis_app_secret,
            "tr_id": tr_id,
            "custtype": "P",
        }

    async def get_investor_trading(
        self, stock_code: str, start_date: str, end_date: str
    ) -> list[InvestorFlow]:
        """KIS API로 투자자별 일별 순매수 조회.

        TR_ID FHKST01010900 — 최근 30 거래일 데이터 반환.
        start_date/end_date 범위로 필터링.
        """
        if not self._is_configured():
            logger.warning("KIS API key not configured — skipping investor trading")
            return []

        start_dt = datetime.strptime(start_date, "%Y%m%d").date()
        end_dt = datetime.strptime(end_date, "%Y%m%d").date()

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                token = await self._get_token(client)
                resp = await client.get(
                    f"{self._base}/uapi/domestic-stock/v1/quotations/inquire-investor",
                    headers=self._auth_headers(token, _INVESTOR_TR_ID),
                    params={
                        "FID_COND_MRKT_DIV_CODE": "J",
                        "FID_INPUT_ISCD": stock_code,
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            if data.get("rt_cd") != "0":
                logger.error(f"KIS investor API error [{stock_code}]: {data.get('msg1')}")
                return []

            flows: list[InvestorFlow] = []
            for item in data.get("output", []):
                date_val = datetime.strptime(item["stck_bsop_date"], "%Y%m%d").date()
                if date_val < start_dt or date_val > end_dt:
                    continue
                flows.append(
                    InvestorFlow(
                        stock_code=stock_code,
                        date=date_val,
                        foreign_net=int(item.get("frgn_ntby_qty") or 0),
                        institution_net=int(item.get("orgn_ntby_qty") or 0),
                        retail_net=int(item.get("prsn_ntby_qty") or 0),
                    )
                )

            flows.sort(key=lambda f: f.date)
            logger.info(f"Retrieved {len(flows)} investor trading records for {stock_code}")
            return flows

        except httpx.HTTPStatusError as e:
            logger.error(f"KIS investor API HTTP error [{stock_code}]: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to get investor trading [{stock_code}]: {e}")
            return []

    async def get_market_index(
        self, start_date: str, end_date: str
    ) -> list[tuple[date_type, float, float]]:
        """KIS API로 KOSPI/KOSDAQ 일별 지수 종가 조회.

        TR_ID FHKST03010100 — 최대 100건/회.
        """
        if not self._is_configured():
            logger.warning("KIS API key not configured — skipping market index")
            return []

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                token = await self._get_token(client)
                kospi_map = await self._fetch_index(
                    client, token, _KOSPI_CODE, start_date, end_date
                )
                kosdaq_map = await self._fetch_index(
                    client, token, _KOSDAQ_CODE, start_date, end_date
                )

            result: list[tuple[date_type, float, float]] = [
                (d, kospi_map[d], kosdaq_map.get(d, 0.0)) for d in sorted(kospi_map)
            ]
            logger.info(f"Retrieved {len(result)} market index records")
            return result

        except httpx.HTTPStatusError as e:
            logger.error(f"KIS index API HTTP error: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to get market index: {e}")
            return []

    async def _fetch_index(
        self,
        client: httpx.AsyncClient,
        token: str,
        index_code: str,
        start_date: str,
        end_date: str,
    ) -> dict[date_type, float]:
        resp = await client.get(
            f"{self._base}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",
            headers=self._auth_headers(token, _INDEX_TR_ID),
            params={
                "FID_COND_MRKT_DIV_CODE": "U",
                "FID_INPUT_ISCD": index_code,
                "FID_INPUT_DATE_1": start_date,
                "FID_INPUT_DATE_2": end_date,
                "FID_PERIOD_DIV_CODE": "D",
                "FID_ORG_ADJ_PRC": "0",
            },
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("rt_cd") != "0":
            logger.error(f"KIS index API error [{index_code}]: {data.get('msg1')}")
            return {}

        index_map: dict[date_type, float] = {}
        for item in data.get("output2", []):
            raw_date = item.get("stck_bsop_date") or item.get("bsop_date", "")
            raw_close = item.get("stck_clpr") or item.get("bstp_nmix_prpr", "")
            if not raw_date or not raw_close:
                continue
            try:
                date_val = datetime.strptime(raw_date, "%Y%m%d").date()
                index_map[date_val] = float(raw_close.replace(",", ""))
            except (ValueError, AttributeError):
                continue

        return index_map
