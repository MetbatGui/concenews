"""Acceptance test for GET /news endpoint.

Walking skeleton + behavior 시나리오 (endpoint 단위 응집).
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

        Given: filled_repository (3 items)
        When: GET /news
        Then: count == len(news)
        """
        data = GetNewsResponse.model_validate(filled_client.get("/news").json())
        assert data.count == len(data.news)

    def test_returns_sorted_by_published_at_desc(self, filled_client):
        """뉴스는 published_at 내림차순으로 반환된다.

        Given: filled_repository (오래된/중간/최신 3개)
        When: GET /news
        Then: published_at 이 내림차순 (최신 first)
        """
        data = GetNewsResponse.model_validate(filled_client.get("/news").json())
        assert data.news[0].title == "최신 뉴스"
        assert data.news[-1].title == "오래된 뉴스"

    def test_respects_limit_parameter(self, filled_client):
        """limit 쿼리 파라미터는 반환 개수를 제한한다.

        Given: filled_repository (3 items)
        When: GET /news?limit=2
        Then: 2개만 반환 (최신 2개)
        """
        data = GetNewsResponse.model_validate(filled_client.get("/news?limit=2").json())
        assert data.count == 2

    def test_rejects_limit_out_of_range(self, client):
        """limit 이 1-100 범위 밖이면 422 반환.

        Given: FastAPI test client
        When: GET /news?limit=101 (or 0)
        Then: 422 Unprocessable Entity
        """
        assert client.get("/news?limit=101").status_code == 422
        assert client.get("/news?limit=0").status_code == 422

    def test_article_fields_are_present(self, filled_client):
        """각 news 아이템은 필수 필드를 포함한다.

        Given: filled_repository
        When: GET /news
        Then: 각 아이템에 id/title/link/source/published_at 존재
        """
        data = GetNewsResponse.model_validate(filled_client.get("/news").json())
        for item in data.news:
            assert item.id
            assert item.title
            assert item.link
            assert item.source
            assert item.published_at
