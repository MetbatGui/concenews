"""System acceptance test: Collector → DB → GET /news.

뉴스 수집(ORM 적재) 후 HTTP GET으로 조회하는 전체 흐름 검증.
"""
from src.modules.news.public import GetNewsResponse


class TestGetNewsSystemAcceptance:
    """System acceptance: collector data → GET /news."""

    def test_get_news_returns_collected_data(self, pg_client_with_news_data):
        """Given: 3개 뉴스 ORM 적재 (Real API 응답 형태)
        When: GET /news 호출
        Then: 적재된 뉴스 조회 + 정렬 확인

        검증:
        - HTTP 200 OK
        - 3개 뉴스 반환
        - published_at 내림차순 정렬
        - 필드 무결성
        """
        response = pg_client_with_news_data.get("/news")
        assert response.status_code == 200

        # 응답 스키마 검증
        data = GetNewsResponse.model_validate(response.json())

        # 데이터 검증
        assert data.count == 3
        assert len(data.news) == 3

        # 정렬 검증 (최신순)
        published_times = [item.published_at for item in data.news]
        assert published_times == sorted(published_times, reverse=True)

        # 필드 검증
        for item in data.news:
            assert item.title
            assert item.link
            assert item.source
            assert item.published_at
            assert item.published_at.tzinfo is not None  # timezone aware

    def test_get_news_with_limit(self, pg_client_with_news_data):
        """Given: 3개 뉴스 적재
        When: GET /news?limit=2 호출
        Then: 최신 2개만 반환

        limit 파라미터 동작 검증.
        """
        response = pg_client_with_news_data.get("/news?limit=2")
        assert response.status_code == 200

        data = GetNewsResponse.model_validate(response.json())
        assert data.count == 2
        assert len(data.news) == 2

        # 최신 2개 정렬: newest 먼저
        titles = [item.title for item in data.news]
        assert titles[0] == "Interest Rate Policy Update"  # 12:00 (newest)
        assert titles[1] == "Forex Market Analysis"  # 11:00
        # "Central Bank Decision" (10:00, oldest) 제외
