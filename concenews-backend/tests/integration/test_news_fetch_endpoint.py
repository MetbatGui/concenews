"""Integration tests for GET /news endpoint.

TDD: RED phase
- 모든 테스트 실패 (구현 전)
- 엔드포인트 구현 (GREEN)
- 점진적 refactor로 계층 분리

구현 순서:
1. Mock 데이터로 endpoint 반환 (RED → GREEN)
2. Refactor: Service 추출
3. Refactor: Domain 모델 추출
4. Refactor: Repository 추출
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.modules.news.public import GetNewsResponse, NewsItemResponse


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


class TestGetNewsEndpoint:
    """GET /news endpoint integration tests."""

    def test_get_news_returns_200(self, client):
        """GET /news 엔드포인트는 200 OK를 반환한다.

        Given: FastAPI test client
        When: GET /news 호출
        Then: 응답 상태 코드는 200, schema 검증 통과
        """
        response = client.get("/news")
        assert response.status_code == 200

        # Schema 검증 (계약 강제)
        GetNewsResponse.model_validate(response.json())

    def test_get_news_response_structure(self, client):
        """응답 구조는 {news: [...], count: N}이다.

        Given: FastAPI test client
        When: GET /news 호출
        Then: GetNewsResponse schema 검증 통과
        """
        response = client.get("/news")

        # Schema 검증 (구조, 타입, 필드 모두 확인)
        data = GetNewsResponse.model_validate(response.json())

        # 타입 검증 (schema로 자동 처리되지만 명시)
        assert isinstance(data.news, list)
        assert isinstance(data.count, int)

    def test_get_news_count_matches_articles(self, client):
        """count는 실제 기사 수와 일치한다.

        Given: FastAPI test client
        When: GET /news 호출
        Then: count == len(news)
        """
        response = client.get("/news")
        data = GetNewsResponse.model_validate(response.json())

        # 비즈니스 로직 검증
        assert data.count == len(data.news)

    def test_get_news_empty_when_no_articles(self, client):
        """저장된 뉴스가 없으면 빈 배열을 반환한다.

        Given: 초기 상태 (뉴스 없음)
        When: GET /news 호출
        Then: news == [], count == 0
        """
        response = client.get("/news")
        data = GetNewsResponse.model_validate(response.json())

        # 초기 상태 검증
        assert data.news == []
        assert data.count == 0

    def test_get_news_article_fields(self, client):
        """각 기사는 필수 필드를 포함한다.

        Given: FastAPI test client
        When: GET /news 호출 후 기사 데이터가 존재하는 경우
        Then: 각 NewsItemResponse schema 검증 통과
        """
        response = client.get("/news")
        data = GetNewsResponse.model_validate(response.json())

        # 기사가 있으면 각각 schema 검증
        for article in data.news:
            assert isinstance(article, NewsItemResponse)
            assert article.id
            assert article.title
            assert article.link
            assert article.source
            assert article.published_at

    def test_get_news_max_50_articles(self, client):
        """최대 50개의 기사를 반환한다.

        Given: FastAPI test client
        When: GET /news?limit=50 호출
        Then: len(news) <= 50
        """
        response = client.get("/news?limit=50")
        data = GetNewsResponse.model_validate(response.json())

        # 비즈니스 로직 검증
        assert len(data.news) <= 50

    def test_get_news_limit_parameter(self, client):
        """limit 파라미터로 조회 개수를 제어할 수 있다.

        Given: FastAPI test client
        When: GET /news?limit={10, 5} 호출
        Then: count <= limit 값
        """
        # limit=10
        response = client.get("/news?limit=10")
        data = GetNewsResponse.model_validate(response.json())
        assert data.count <= 10

        # limit=5
        response = client.get("/news?limit=5")
        data = GetNewsResponse.model_validate(response.json())
        assert data.count <= 5

    def test_get_news_default_limit_50(self, client):
        """limit 파라미터 생략 시 기본값은 50이다.

        Given: FastAPI test client
        When: GET /news 호출 (limit 파라미터 없음)
        Then: count <= 50 (기본값)
        """
        response = client.get("/news")
        data = GetNewsResponse.model_validate(response.json())

        # 기본 limit 검증
        assert data.count <= 50

    def test_get_news_sorted_by_published_at_desc(self, client):
        """뉴스는 published_at 기준 최근순으로 정렬된다.

        Given: FastAPI test client
        When: GET /news 호출 후 뉴스가 2개 이상 있는 경우
        Then: published_at이 내림차순(최근순)
        """
        response = client.get("/news")
        data = GetNewsResponse.model_validate(response.json())

        # 뉴스가 2개 이상일 때만 정렬 검증
        if len(data.news) >= 2:
            for i in range(len(data.news) - 1):
                current = data.news[i].published_at
                next_item = data.news[i + 1].published_at
                assert current >= next_item, f"{current} should be >= {next_item} (descending)"
