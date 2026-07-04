"""Acceptance test for GET /news endpoint (walking skeleton).

TDD RED phase — endpoint 미구현.

Walking skeleton 원칙:
- 1개 acceptance test 로 end-to-end 연결만 증명
- Detail behavior (필드/정렬/limit/빈배열 등) 검증은 wire-up PR 에서
  fixture (filled_repository, empty_repository) 로 상태 통제 후 추가

이전 시도 (feature/news-fetch-endpoint-mock) 에서 9개 통합 테스트가
서로 상반된 상태를 암묵적으로 가정 → 같은 endpoint 로 동시 GREEN 불가.
결정 이력: master merge commit 72158c6 참고.
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.modules.news.public import GetNewsResponse


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


class TestGetNewsEndpoint:
    """GET /news endpoint acceptance test."""

    def test_get_news_returns_valid_response(self, client):
        """GET /news 는 유효한 응답을 반환한다.

        Given: FastAPI test client
        When: GET /news 호출
        Then: 200 OK + GetNewsResponse schema 유효
        """
        response = client.get("/news")
        assert response.status_code == 200
        GetNewsResponse.model_validate(response.json())
