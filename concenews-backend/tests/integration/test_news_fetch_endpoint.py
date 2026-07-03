"""Integration tests for GET /news endpoint.

TDD: RED phase
- 모든 테스트 실패 (구현 전)
- Mock Service로 스켈레톤만 작동
- 경계: Endpoint ↔ Service

구현 순서:
1. Mock Service 반환 (RED → GREEN)
2. Domain 추가
3. Repository 추가
4. Service 실제 로직 추가
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


class TestGetNewsEndpoint:
    """GET /news endpoint integration tests."""

    def test_get_news_returns_200(self, client):
        """GET /news returns 200 OK."""
        response = client.get("/news")
        assert response.status_code == 200

    def test_get_news_response_structure(self, client):
        """응답 구조: {news: [...], count: N}."""
        response = client.get("/news")
        data = response.json()

        assert "news" in data, "응답에 'news' 필드 필요"
        assert "count" in data, "응답에 'count' 필드 필요"
        assert isinstance(data["news"], list), "'news'는 배열"
        assert isinstance(data["count"], int), "'count'는 정수"

    def test_get_news_count_matches_articles(self, client):
        """count는 실제 기사 수와 일치."""
        response = client.get("/news")
        data = response.json()

        assert data["count"] == len(data["news"]), "count는 articles 개수와 일치"

    def test_get_news_empty_when_no_articles(self, client):
        """저장된 뉴스가 없으면 빈 배열."""
        response = client.get("/news")
        data = response.json()

        # 초기 상태: 뉴스 없음
        assert data["news"] == [], "초기 상태에서 빈 배열 반환"
        assert data["count"] == 0, "count = 0"

    def test_get_news_article_fields(self, client):
        """각 기사 필드: id, title, description, link, source, published_at, keywords, categories."""
        # 이 테스트는 나중에 실제 데이터가 있을 때 작동
        # 현재는 스킵 가능 (or fixture로 데이터 추가)
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
        """최대 50개 기사 반환."""
        response = client.get("/news?limit=50")
        data = response.json()

        assert len(data["news"]) <= 50, "최대 50개 제한"

    def test_get_news_limit_parameter(self, client):
        """limit 파라미터 처리."""
        # limit=10
        response = client.get("/news?limit=10")
        data = response.json()
        assert data["count"] <= 10, "limit=10 요청"

        # limit=5
        response = client.get("/news?limit=5")
        data = response.json()
        assert data["count"] <= 5, "limit=5 요청"

    def test_get_news_default_limit_50(self, client):
        """기본 limit=50."""
        response = client.get("/news")
        data = response.json()

        # 기본값 50이므로 50 이하
        assert data["count"] <= 50, "기본 limit=50"
