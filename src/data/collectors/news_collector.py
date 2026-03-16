import re
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

import httpx
from loguru import logger

from src.data.models import NewsItem

_NAVER_NEWS_URL = "https://openapi.naver.com/v1/search/news.json"


class NewsCollector:
    """네이버 검색 API 기반 뉴스 수집.

    API 키 미설정 시 빈 리스트 즉시 반환.
    """

    def __init__(self, client_id: str, client_secret: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret

    def _is_configured(self) -> bool:
        return bool(self._client_id and self._client_secret)

    def _strip_html(self, text: str) -> str:
        return re.sub(r"<[^>]+>", "", text)

    def _parse_pub_date(self, pub_date: str) -> str:
        """RFC 2822 날짜 문자열을 ISO 형식으로 변환."""
        try:
            dt = parsedate_to_datetime(pub_date)
            return dt.isoformat()
        except Exception:
            return pub_date

    def _extract_domain(self, url: str) -> str:
        """URL에서 도메인 추출."""
        try:
            parsed = urlparse(url)
            return parsed.netloc or ""
        except Exception:
            return ""

    async def get_news(self, query: str, display: int = 5) -> list[NewsItem]:
        """뉴스 검색.

        Args:
            query: 검색 키워드
            display: 반환할 뉴스 수 (기본 5)

        Returns:
            NewsItem 리스트. API 키 없거나 실패 시 빈 리스트.
        """
        if not self._is_configured():
            logger.warning("Naver API key not configured — skipping news search")
            return []

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    _NAVER_NEWS_URL,
                    headers={
                        "X-Naver-Client-Id": self._client_id,
                        "X-Naver-Client-Secret": self._client_secret,
                    },
                    params={
                        "query": query,
                        "display": display,
                        "sort": "date",
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            items: list[NewsItem] = []
            for item in data.get("items", []):
                title = self._strip_html(item.get("title", ""))
                pub_date = self._parse_pub_date(item.get("pubDate", ""))
                url = item.get("link", "")
                original_link = item.get("originallink", "")
                source = self._extract_domain(original_link) or self._extract_domain(url)
                items.append(
                    NewsItem(
                        title=title,
                        published_at=pub_date,
                        url=url,
                        source=source,
                    )
                )

            logger.info(f"Naver news: {len(items)} items for query='{query}'")
            return items

        except httpx.HTTPStatusError as e:
            logger.error(f"Naver news API HTTP error [query={query}]: {e}")
            return []
        except Exception as e:
            logger.error(f"Naver news fetch error [query={query}]: {e}")
            return []
