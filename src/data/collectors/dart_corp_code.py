"""DART corp_code mapping module."""

import io
import zipfile

import httpx
from loguru import logger

from src.data.collectors.dart_parser import parse_corp_code_xml

DART_BASE_URL = "https://opendart.fss.or.kr/api"


class DartCorpCodeMapper:
    """DART corp_code 매핑 관리.

    corpCode.xml ZIP을 다운로드하고 파싱하여
    stock_code → corp_code 매핑을 제공한다.
    """

    def __init__(self) -> None:
        self._mapping: dict[str, str] = {}

    async def download_and_parse(self, api_key: str) -> dict[str, str]:
        """Download corpCode.xml ZIP and parse to mapping dict.

        Args:
            api_key: DART API key

        Returns:
            dict[str, str]: {stock_code: corp_code} mapping for listed companies
        """
        url = f"{DART_BASE_URL}/corpCode.xml"
        params = {"crtfc_key": api_key}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()

        zip_buffer = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_buffer) as zf:
            xml_bytes = zf.read("CORPCODE.xml")

        self._mapping = parse_corp_code_xml(xml_bytes)
        logger.info(f"Loaded {len(self._mapping)} corp codes")
        return self._mapping

    def get_corp_code(self, stock_code: str) -> str | None:
        """Get corp_code for a given stock_code.

        Args:
            stock_code: 6-digit KRX stock code

        Returns:
            corp_code (8-digit DART code) or None if not found
        """
        return self._mapping.get(stock_code)
