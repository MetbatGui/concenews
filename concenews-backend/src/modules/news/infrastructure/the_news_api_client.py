"""TheNewsAPI HTTP adapter.

뉴스 외부 소스 (TheNewsAPI) 에서 기사 가져오기 및 NewsItem 변환.
"""
from datetime import datetime, timedelta, timezone

import requests

from src.modules.news.domain.models import NewsItem
from src.modules.news.infrastructure.id_generator import UuidV7Generator


class TheNewsAPIClient:
    """TheNewsAPI HTTP client.

    외부 뉴스 API 에서 기사를 가져와 도메인 NewsItem 으로 변환.
    UTC published_at 을 KST 로 정규화.
    """

    def __init__(self, api_key: str) -> None:
        """Initialize client.

        Args:
            api_key: TheNewsAPI 인증 키.
        """
        self.api_key = api_key
        self.base_url = "https://api.thenewsapi.com/v1/news/top"
        self._id_generator = UuidV7Generator()

    def fetch(self, keywords: list[str]) -> list[NewsItem]:
        """뉴스 기사 조회.

        Args:
            keywords: 검색 키워드 (AND 조건, 최대 5개).

        Returns:
            NewsItem 리스트.

        Raises:
            requests.RequestException: HTTP 요청 실패.
        """
        # 키워드를 쿼리 문자열로 변환 (AND 연결)
        query = " ".join(keywords) if keywords else ""

        params = {
            "api_token": self.api_key,
            "search": query,
            "limit": 100,
        }

        response = requests.get(self.base_url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        articles = data.get("data", [])

        return [self._convert_to_news_item(article) for article in articles]

    def _convert_to_news_item(self, raw_article: dict) -> NewsItem:
        """Raw API 응답을 NewsItem 으로 변환.

        UTC published_at 을 KST 로 정규화.

        Args:
            raw_article: API 응답 기사 dict.

        Returns:
            NewsItem 인스턴스.
        """
        # published_at: ISO8601 UTC 파싱 (publishedAt 또는 published_at)
        published_at_str = raw_article.get("publishedAt") or raw_article.get("published_at", "")
        if not published_at_str:
            raise ValueError("publishedAt/published_at 필드 없음")
        published_at_utc = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))

        # UTC → KST (UTC+9)
        kst_offset = timezone(timedelta(hours=9))
        published_at_kst = published_at_utc.astimezone(kst_offset)

        # source 필드는 dict 또는 string
        source_field = raw_article.get("source", "")
        if isinstance(source_field, dict):
            source_name = source_field.get("name", "")
        else:
            source_name = source_field

        return NewsItem(
            id=self._id_generator.generate(),
            title=raw_article["title"],
            description=raw_article.get("description"),
            link=raw_article.get("url") or raw_article.get("link", ""),
            source=source_name,
            published_at=published_at_kst,
            keywords="",
            categories=(),
        )
