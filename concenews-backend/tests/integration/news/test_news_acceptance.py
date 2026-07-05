"""Acceptance test for GET /news endpoint.

Walking skeleton + behavior 시나리오 통합 (endpoint 단위 응집).
자세한 test 구조 규칙: docs/conventions/testing.md
"""

from src.modules.news.public import GetNewsResponse


class TestGetNewsWalkingSkeleton:
    """Endpoint 최소 연결 증명."""

    def test_get_news_returns_valid_response(self, client):
        """GET /news 는 유효한 응답을 반환한다.

        Given: FastAPI test client (기본 empty repository)
        When: GET /news 호출
        Then: 200 OK + GetNewsResponse schema 유효
        """
        response = client.get("/news")
        assert response.status_code == 200
        GetNewsResponse.model_validate(response.json())
