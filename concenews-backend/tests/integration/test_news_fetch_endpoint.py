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
        Then: 응답 상태 코드는 200
        """
        response = client.get("/news")
        assert response.status_code == 200

    def test_get_news_response_structure(self, client):
        """응답 구조는 {news: [...], count: N}이다.

        Given: FastAPI test client
        When: GET /news 호출
        Then: 응답에 'news' 배열과 'count' 정수 필드 포함
        """
        response = client.get("/news")
        data = response.json()

        assert "news" in data, "응답에 'news' 필드 필요"
        assert "count" in data, "응답에 'count' 필드 필요"
        assert isinstance(data["news"], list), "'news'는 배열"
        assert isinstance(data["count"], int), "'count'는 정수"

    def test_get_news_count_matches_articles(self, client):
        """count는 실제 기사 수와 일치한다.

        Given: FastAPI test client
        When: GET /news 호출
        Then: count 값 == 기사 배열 길이
        """
        response = client.get("/news")
        data = response.json()

        assert data["count"] == len(data["news"]), "count는 articles 개수와 일치"

    def test_get_news_empty_when_no_articles(self, client):
        """저장된 뉴스가 없으면 빈 배열을 반환한다.

        Given: 초기 상태 (뉴스 없음)
        When: GET /news 호출
        Then: news는 빈 배열, count는 0
        """
        response = client.get("/news")
        data = response.json()

        assert data["news"] == [], "초기 상태에서 빈 배열 반환"
        assert data["count"] == 0, "count = 0"

    def test_get_news_article_fields(self, client):
        """각 기사는 필수 필드를 포함한다.

        Given: FastAPI test client
        When: GET /news 호출 후 기사 데이터가 존재하는 경우
        Then: 각 기사는 id, title, description, link, source, published_at, keywords, categories 필드 포함
        """
        response = client.get("/news")
        data = response.json()

        if data["news"]:  # 데이터가 있으면 검증
            article = data["news"][0]

            required_fields = {
                "id": str,
                "title": str,
                "description": str,
                "link": str,
                "source": str,
                "published_at": str,
                "keywords": str,
                "categories": list,
            }

            for field, expected_type in required_fields.items():
                assert field in article, f"필드 '{field}' 필요"
                assert isinstance(
                    article[field], expected_type
                ), f"'{field}'는 {expected_type.__name__} 타입"

    def test_get_news_max_50_articles(self, client):
        """최대 50개의 기사를 반환한다.

        Given: FastAPI test client
        When: GET /news?limit=50 호출
        Then: 반환되는 기사 개수는 50개 이하
        """
        response = client.get("/news?limit=50")
        data = response.json()

        assert len(data["news"]) <= 50, "최대 50개 제한"

    def test_get_news_limit_parameter(self, client):
        """limit 파라미터로 조회 개수를 제어할 수 있다.

        Given: FastAPI test client
        When: GET /news?limit={10, 5} 호출
        Then: count 값은 각각 10, 5 이하
        """
        # limit=10
        response = client.get("/news?limit=10")
        data = response.json()
        assert data["count"] <= 10, "limit=10 요청"

        # limit=5
        response = client.get("/news?limit=5")
        data = response.json()
        assert data["count"] <= 5, "limit=5 요청"

    def test_get_news_default_limit_50(self, client):
        """limit 파라미터 생략 시 기본값은 50이다.

        Given: FastAPI test client
        When: GET /news 호출 (limit 파라미터 없음)
        Then: count 값은 50 이하 (기본값 적용)
        """
        response = client.get("/news")
        data = response.json()

        assert data["count"] <= 50, "기본 limit=50"
