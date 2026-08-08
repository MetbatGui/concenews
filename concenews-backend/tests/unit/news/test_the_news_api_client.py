"""TheNewsAPI HTTP adapter 단위 테스트."""
from datetime import timedelta, timezone
from urllib.parse import parse_qs, urlparse

import pytest
import requests
import responses

from src.modules.news.domain.models import NewsItem
from src.modules.news.infrastructure.the_news_api_client import TheNewsAPIClient
from tests.fixtures.thenewsapi import ARTICLE_ONE, ARTICLE_TWO, top_news_response


@pytest.fixture
def api_client() -> TheNewsAPIClient:
    """테스트용 TheNewsAPIClient."""
    return TheNewsAPIClient(api_key="test-key")


class TestTheNewsAPIClientFetch:
    """TheNewsAPI 응답 계약을 NewsItem으로 변환한다."""

    @responses.activate
    def test_fetch_parses_single_article(self, api_client: TheNewsAPIClient) -> None:
        """TheNewsAPI 기사 한 건을 NewsItem으로 변환한다.

        Given: 실제 API 계약 형식의 기사 한 건
        When: fetch() 호출
        Then: NewsItem 한 건을 반환한다.
        """
        responses.add(responses.GET, api_client.base_url, json=top_news_response(ARTICLE_ONE), status=200)

        items = api_client.fetch(keywords=["interest rate"])

        assert len(items) == 1
        assert isinstance(items[0], NewsItem)
        assert items[0].title == ARTICLE_ONE["title"]
        assert items[0].link == ARTICLE_ONE["url"]

    @responses.activate
    def test_fetch_normalizes_utc_to_kst(self, api_client: TheNewsAPIClient) -> None:
        """UTC 발행 시각을 KST로 정규화한다.

        Given: UTC 정오에 발행된 기사
        When: fetch() 호출
        Then: KST 21시의 timezone-aware 시각으로 반환한다.
        """
        article = {**ARTICLE_ONE, "published_at": "2026-07-06T12:00:00Z"}
        responses.add(responses.GET, api_client.base_url, json=top_news_response(article), status=200)

        items = api_client.fetch(keywords=[])

        assert items[0].published_at.hour == 21
        assert items[0].published_at.tzinfo == timezone(timedelta(hours=9))

    @responses.activate
    def test_fetch_maps_optional_fields(self, api_client: TheNewsAPIClient) -> None:
        """선택 필드를 포함해 응답을 매핑한다.

        Given: description이 없는 실제 API 계약 형식의 기사
        When: fetch() 호출
        Then: 선택 필드가 도메인 모델에 보존된다.
        """
        responses.add(responses.GET, api_client.base_url, json=top_news_response(ARTICLE_TWO), status=200)

        items = api_client.fetch(keywords=[])

        item = items[0]
        assert item.description is None
        assert item.source == ARTICLE_TWO["source"]
        assert item.keywords == ""
        assert item.categories == ()

    @responses.activate
    def test_fetch_returns_all_articles(self, api_client: TheNewsAPIClient) -> None:
        """여러 기사를 빠짐없이 변환한다.

        Given: 실제 API 계약 형식의 기사 두 건
        When: fetch() 호출
        Then: 입력 순서대로 두 NewsItem을 반환한다.
        """
        responses.add(responses.GET, api_client.base_url, json=top_news_response(ARTICLE_ONE, ARTICLE_TWO), status=200)

        items = api_client.fetch(keywords=["interest rate"])

        assert [item.title for item in items] == [ARTICLE_ONE["title"], ARTICLE_TWO["title"]]

    @responses.activate
    def test_fetch_raises_for_http_error(self, api_client: TheNewsAPIClient) -> None:
        """HTTP 오류를 호출자에게 전달한다.

        Given: 500 응답
        When: fetch() 호출
        Then: HTTPError를 발생시킨다.
        """
        responses.add(responses.GET, api_client.base_url, status=500)

        with pytest.raises(requests.HTTPError):
            api_client.fetch(keywords=["interest rate"])

    @responses.activate
    def test_fetch_sends_api_contract_query(self, api_client: TheNewsAPIClient) -> None:
        """검색어와 인증 정보를 TheNewsAPI 계약대로 전달한다.

        Given: 키워드 두 개
        When: fetch() 호출
        Then: 요청 query에 인증 정보와 공백 결합 검색어가 포함된다.
        """
        responses.add(responses.GET, api_client.base_url, json=top_news_response(), status=200)

        api_client.fetch(keywords=["interest rate", "forex"])

        request_url = responses.calls[0].request.url
        query = parse_qs(urlparse(request_url).query)
        assert query == {
            "api_token": ["test-key"],
            "search": ["interest rate forex"],
            "limit": ["100"],
        }
