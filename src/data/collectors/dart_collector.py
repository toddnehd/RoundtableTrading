"""DART API financial data collector."""

import asyncio
import time

import httpx
from loguru import logger

from src.data.collectors.dart_errors import DartAPIError, DartNoDataError
from src.data.collectors.dart_parser import parse_dart_response
from src.data.models import FinancialData

DART_BASE_URL = "https://opendart.fss.or.kr/api"

REPRT_CODE_TO_QUARTER = {
    "11013": "Q1",
    "11012": "Q2",
    "11014": "Q3",
    "11011": "Q4",
}


class DartCollector:
    """DART API 재무 데이터 수집기."""

    def __init__(self, api_key: str, rate_limit_per_minute: int = 60) -> None:
        self._api_key = api_key
        self._min_interval = 60.0 / rate_limit_per_minute
        self._last_call_time: float = 0.0

    async def get_financial_data(
        self,
        corp_code: str,
        stock_code: str,
        bsns_year: str,
        reprt_code: str,
        current_price: int | None = None,
    ) -> FinancialData | None:
        """Fetch financial data for a company.

        Tries CFS (consolidated) first, falls back to OFS (individual) if no data.
        Returns None for financial sector companies.

        Args:
            corp_code: DART 8-digit company code
            stock_code: KRX 6-digit stock code
            bsns_year: Business year (e.g., "2024")
            reprt_code: Report code (11011=Q4, 11012=Q2, 11013=Q1, 11014=Q3)
            current_price: Current stock price for PER/PBR calculation

        Returns:
            FinancialData or None if financial sector or no data
        """
        accounts: list[dict] = []
        used_fs_div = "CFS"
        for fs_div in ("CFS", "OFS"):
            try:
                accounts = await self._get_main_accounts(corp_code, bsns_year, reprt_code, fs_div)
                used_fs_div = fs_div
                break
            except DartNoDataError:
                if fs_div == "OFS":
                    logger.warning(f"No data for {stock_code} ({bsns_year} {reprt_code})")
                    return None
                logger.info(f"CFS not found for {stock_code}, trying OFS")
                continue

        if self._is_financial_sector(accounts):
            logger.warning(f"Financial sector detected for {stock_code}, skipping")
            return None

        indicators: dict = {}
        try:
            indicators = await self._get_financial_indicators(corp_code, bsns_year, reprt_code)
        except (DartNoDataError, DartAPIError) as e:
            logger.warning(f"Could not fetch indicators for {stock_code}: {e}")

        quarter_suffix = REPRT_CODE_TO_QUARTER.get(reprt_code, "Q4")
        quarter = f"{bsns_year}{quarter_suffix}"

        revenue = self._extract_account(accounts, "매출액")
        operating_income = self._extract_account(accounts, "영업이익")
        net_income = self._extract_account(accounts, "당기순이익")

        roe = indicators.get("roe")
        debt_ratio = indicators.get("debt_ratio")

        eps = self._extract_account_exact(accounts, "기본주당이익")
        bps = self._calculate_bps(accounts)

        per: float | None = None
        pbr: float | None = None
        if current_price and eps and eps > 0:
            per = round(current_price / eps, 2)
        if current_price and bps and bps > 0:
            pbr = round(current_price / bps, 2)

        return FinancialData(
            stock_code=stock_code,
            quarter=quarter,
            revenue=revenue,
            operating_income=operating_income,
            net_income=net_income,
            per=per,
            pbr=pbr,
            roe=roe,
            debt_ratio=debt_ratio,
            eps=eps,
            bps=bps,
            fs_div=used_fs_div,
        )

    async def _get_main_accounts(
        self, corp_code: str, bsns_year: str, reprt_code: str, fs_div: str
    ) -> list[dict]:
        """Fetch main accounts from /fnlttSinglAcntAll.

        Args:
            corp_code: DART company code
            bsns_year: Business year
            reprt_code: Report code
            fs_div: Financial statement division (CFS or OFS)

        Returns:
            list[dict]: Account data list
        """
        return await self._call_api(
            "fnlttSinglAcntAll.json",
            {
                "corp_code": corp_code,
                "bsns_year": bsns_year,
                "reprt_code": reprt_code,
                "fs_div": fs_div,
            },
        )

    async def _get_financial_indicators(
        self, corp_code: str, bsns_year: str, reprt_code: str
    ) -> dict:
        """Fetch financial indicators from /fnlttSinglIndx.

        Args:
            corp_code: DART company code
            bsns_year: Business year
            reprt_code: Report code

        Returns:
            dict with keys: roe, debt_ratio, eps, bps
        """
        result: dict = {}
        for idx_cl_code in ("M210000", "M220000"):
            try:
                items = await self._call_api(
                    "fnlttSinglIndx.json",
                    {
                        "corp_code": corp_code,
                        "bsns_year": bsns_year,
                        "reprt_code": reprt_code,
                        "idx_cl_code": idx_cl_code,
                    },
                )
                for item in items:
                    idx_nm = item.get("idx_nm", "")
                    idx_val = item.get("idx_val", "")
                    try:
                        val = float(str(idx_val).replace(",", ""))
                    except (ValueError, TypeError):
                        continue
                    if idx_nm == "ROE" or idx_nm == "자기자본이익률":
                        result["roe"] = val
                    elif idx_nm == "부채비율":
                        result["debt_ratio"] = val
            except (DartNoDataError, DartAPIError):
                pass
        return result

    async def _call_api(self, endpoint: str, params: dict) -> list[dict]:
        """Call DART API with rate limiting.

        Args:
            endpoint: API endpoint (e.g., "fnlttSinglAcntAll.json")
            params: Query parameters (without crtfc_key)

        Returns:
            list[dict]: Response data list

        Raises:
            DartNoDataError: If no data (status 013)
            DartRateLimitError: If rate limit exceeded (status 020)
            DartAPIError: For other errors
        """
        now = time.monotonic()
        elapsed = now - self._last_call_time
        if elapsed < self._min_interval:
            await asyncio.sleep(self._min_interval - elapsed)
        self._last_call_time = time.monotonic()

        url = f"{DART_BASE_URL}/{endpoint}"
        all_params = {"crtfc_key": self._api_key, **params}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=all_params)
            response.raise_for_status()

        return parse_dart_response(response.json())

    def _is_financial_sector(self, accounts: list[dict]) -> bool:
        """Detect if company is in financial sector.

        Financial sector companies don't have '매출액' account.

        Args:
            accounts: List of account dicts from DART API

        Returns:
            True if financial sector (no revenue account found)
        """
        account_names = [item.get("account_nm", "") for item in accounts]
        return not any("매출액" in name for name in account_names)

    def _extract_account(self, accounts: list[dict], account_name: str) -> float | None:
        """Extract account value by name.

        Args:
            accounts: List of account dicts
            account_name: Account name to search for

        Returns:
            Account value as float or None
        """
        for item in accounts:
            if account_name in item.get("account_nm", ""):
                val_str = item.get("thstrm_amount", "")
                try:
                    return float(str(val_str).replace(",", ""))
                except (ValueError, TypeError):
                    return None
        return None

    def _extract_account_exact(self, accounts: list[dict], account_name: str) -> float | None:
        """Extract account value by exact name match.

        Args:
            accounts: List of account dicts
            account_name: Exact account name to match

        Returns:
            Account value as float or None
        """
        for item in accounts:
            if item.get("account_nm", "") == account_name:
                val_str = item.get("thstrm_amount", "")
                try:
                    return float(str(val_str).replace(",", ""))
                except (ValueError, TypeError):
                    return None
        return None

    def _calculate_bps(self, accounts: list[dict]) -> float | None:
        """Calculate BPS from equity total and shares outstanding.

        BPS = 자본총계 / 발행주식수
        발행주식수 = 당기순이익 / 기본주당이익(EPS)

        Args:
            accounts: List of account dicts from DART API

        Returns:
            BPS as float or None if calculation not possible
        """
        equity = self._extract_account_exact(accounts, "자본총계")
        eps = self._extract_account_exact(accounts, "기본주당이익")
        net_income = self._extract_account(accounts, "당기순이익")

        if equity and eps and net_income and eps > 0 and net_income > 0:
            shares = net_income / eps
            if shares > 0:
                return round(equity / shares, 0)
        return None
