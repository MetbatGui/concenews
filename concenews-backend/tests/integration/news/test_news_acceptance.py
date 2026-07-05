"""Acceptance test for GET /news endpoint.

Walking skeleton + behavior 시나리오 (endpoint 단위 응집).
자세한 test 구조 규칙: docs/conventions/testing.md
"""

from src.modules.news.public import GetNewsResponse

from tests.integration.news.data import NEWS_MID, NEWS_NEW, NEWS_OLD


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


class TestGetNewsBehavior:
    """세부 behavior (empty/filled/sorted/limit/fields)."""

    def test_returns_empty_when_no_articles(self, client):
        """저장된 뉴스가 없으면 빈 배열을 반환한다.

        Given: empty repository
        When: GET /news
        Then: news == [], count == 0
        """
        data = GetNewsResponse.model_validate(client.get("/news").json())
        assert data.news == []
        assert data.count == 0

    def test_count_matches_returned_news_length(self, filled_client):
        """count 는 실제 news 배열 길이와 일치한다.

        Given: filled_repository (3 items: NEWS_OLD/MID/NEW)
        When: GET /news
        Then: count == 3
        """
        data = GetNewsResponse.model_validate(filled_client.get("/news").json())
        assert data.count == 3
        assert len(data.news) == 3

    def test_returns_sorted_by_published_at_desc(self, filled_client):
        """뉴스는 published_at 내림차순으로 반환된다.

        Given: filled_repository (NEWS_OLD/MID/NEW)
        When: GET /news
        Then: id 순서가 [NEWS_NEW, NEWS_MID, NEWS_OLD]
        """
        data = GetNewsResponse.model_validate(filled_client.get("/news").json())
        assert [item.id for item in data.news] == [NEWS_NEW.id, NEWS_MID.id, NEWS_OLD.id]

    def test_respects_limit_parameter(self, filled_client):
        """limit 쿼리 파라미터는 반환 개수를 제한한다.

        Given: filled_repository (3 items)
        When: GET /news?limit=2
        Then: 최신 2개 반환 (NEWS_NEW, NEWS_MID)
        """
        data = GetNewsResponse.model_validate(filled_client.get("/news?limit=2").json())
        assert data.count == 2
        assert [item.id for item in data.news] == [NEWS_NEW.id, NEWS_MID.id]

    def test_rejects_limit_out_of_range(self, client):
        """limit 이 1-100 범위 밖이면 422 반환.

        Given: FastAPI test client
        When: GET /news?limit=101 (or 0)
        Then: 422 Unprocessable Entity
        """
        assert client.get("/news?limit=101").status_code == 422
        assert client.get("/news?limit=0").status_code == 422

    def test_article_fields_match_source(self, filled_client):
        """반환 아이템의 필드 값이 원본 상수와 일치한다.

        Given: filled_repository (NEWS_NEW 등)
        When: GET /news
        Then: 첫 번째 아이템 (NEWS_NEW) 의 title/link/source/published_at 원본과 동일
        """
        data = GetNewsResponse.model_validate(filled_client.get("/news").json())
        latest = data.news[0]
        assert latest.id == NEWS_NEW.id
        assert latest.title == NEWS_NEW.title
        assert str(latest.link) == NEWS_NEW.link
        assert latest.source == NEWS_NEW.source
        assert latest.published_at == NEWS_NEW.published_at
