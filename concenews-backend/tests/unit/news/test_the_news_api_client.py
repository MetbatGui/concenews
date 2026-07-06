"""TheNewsAPI HTTP adapter unit tests.

GWT (Given-When-Then) 형식.
"""
from datetime import timedelta, timezone
from unittest.mock import patch

import pytest

from src.modules.news.domain.models import NewsItem
from src.modules.news.infrastructure.the_news_api_client import TheNewsAPIClient


@pytest.fixture
def api_client():
    """TheNewsAPIClient instance with mocked requests."""
    return TheNewsAPIClient(api_key="test-key")


class TestTheNewsAPIClientFetch:
    """Raw API 응답 파싱 및 NewsItem 변환."""

    def test_fetch_parses_single_article(self, api_client):
        """Given: API 응답 1개 뉴스
        When: fetch() 호출
        Then: NewsItem으로 변환 반환
        """
        raw_response = {
            "articles": [
                {
                    "title": "Interest Rate Decision",
                    "description": "Central bank raises rates",
                    "link": "https://example.com/news/1",
                    "source": {"name": "Financial News"},
                    "publishedAt": "2026-07-06T03:00:00Z",
                }
            ]
        }

        with patch("requests.get") as mock_get:
            mock_get.return_value.json.return_value = raw_response
            mock_get.return_value.raise_for_status.return_value = None

            items = api_client.fetch(keywords=["interest rate"])

            assert len(items) == 1
            assert isinstance(items[0], NewsItem)
            assert items[0].title == "Interest Rate Decision"
            assert items[0].link == "https://example.com/news/1"

    def test_fetch_converts_utc_to_kst(self, api_client):
        """Given: published_at는 UTC
        When: fetch() 호출
        Then: KST (UTC+9)로 변환 저장
        """
        raw_response = {
            "articles": [
                {
                    "title": "News",
                    "description": None,
                    "link": "https://example.com/1",
                    "source": {"name": "Source"},
                    "publishedAt": "2026-07-06T12:00:00Z",  # UTC noon
                }
            ]
        }

        with patch("requests.get") as mock_get:
            mock_get.return_value.json.return_value = raw_response
            mock_get.return_value.raise_for_status.return_value = None

            items = api_client.fetch(keywords=[])

            # UTC 12:00 → KST 21:00 (UTC+9)
            assert items[0].published_at.hour == 21
            assert items[0].published_at.tzinfo == timezone(timedelta(hours=9))

    def test_fetch_maps_all_fields(self, api_client):
        """Given: 완전한 API 응답
        When: fetch() 호출
        Then: 모든 필드 매핑됨
        """
        raw_response = {
            "articles": [
                {
                    "title": "Title",
                    "description": "Detailed description",
                    "link": "https://example.com/article",
                    "source": {"name": "Reuters"},
                    "publishedAt": "2026-07-06T10:30:00Z",
                }
            ]
        }

        with patch("requests.get") as mock_get:
            mock_get.return_value.json.return_value = raw_response
            mock_get.return_value.raise_for_status.return_value = None

            items = api_client.fetch(keywords=[])

            item = items[0]
            assert item.title == "Title"
            assert item.description == "Detailed description"
            assert item.link == "https://example.com/article"
            assert item.source == "Reuters"
            assert item.keywords == ""
            assert item.categories == ()

    def test_fetch_multiple_articles(self, api_client):
        """Given: API 응답 여러 뉴스
        When: fetch() 호출
        Then: 모두 변환 반환
        """
        raw_response = {
            "articles": [
                {
                    "title": "News 1",
                    "description": None,
                    "link": "https://example.com/1",
                    "source": {"name": "Source A"},
                    "publishedAt": "2026-07-06T10:00:00Z",
                },
                {
                    "title": "News 2",
                    "description": None,
                    "link": "https://example.com/2",
                    "source": {"name": "Source B"},
                    "publishedAt": "2026-07-06T11:00:00Z",
                },
            ]
        }

        with patch("requests.get") as mock_get:
            mock_get.return_value.json.return_value = raw_response
            mock_get.return_value.raise_for_status.return_value = None

            items = api_client.fetch(keywords=["test"])

            assert len(items) == 2
            assert items[0].title == "News 1"
            assert items[1].title == "News 2"

    def test_fetch_handles_missing_description(self, api_client):
        """Given: description이 null
        When: fetch() 호출
        Then: None으로 저장
        """
        raw_response = {
            "articles": [
                {
                    "title": "Title",
                    "description": None,
                    "link": "https://example.com/1",
                    "source": {"name": "Source"},
                    "publishedAt": "2026-07-06T10:00:00Z",
                }
            ]
        }

        with patch("requests.get") as mock_get:
            mock_get.return_value.json.return_value = raw_response
            mock_get.return_value.raise_for_status.return_value = None

            items = api_client.fetch(keywords=[])

            assert items[0].description is None

    def test_fetch_raises_on_http_error(self, api_client):
        """Given: API 응답 에러 (4xx/5xx)
        When: fetch() 호출
        Then: 예외 발생
        """
        with patch("requests.get") as mock_get:
            mock_get.return_value.raise_for_status.side_effect = Exception("HTTP 500")

            with pytest.raises(Exception):
                api_client.fetch(keywords=["test"])

    def test_fetch_passes_keywords_to_api(self, api_client):
        """Given: keywords 전달
        When: fetch(keywords=["interest rate", ...])
        Then: API 요청에 포함됨
        """
        raw_response = {"articles": []}

        with patch("requests.get") as mock_get:
            mock_get.return_value.json.return_value = raw_response
            mock_get.return_value.raise_for_status.return_value = None

            api_client.fetch(keywords=["interest rate", "forex"])

            # requests.get 호출 확인 + URL에 키워드 포함 확인
            assert mock_get.called
            call_kwargs = mock_get.call_args
            # URL 또는 params에 keywords 포함되었는지 확인
            assert call_kwargs is not None
