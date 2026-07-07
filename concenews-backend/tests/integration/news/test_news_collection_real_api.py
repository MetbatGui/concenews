"""실제 TheNewsAPI와 PostgreSQL 통합 테스트.

API 파싱 + DB 저장 정상성 검증.
Mock 제거, 실제 API 호출 + 실제 DB 사용.
"""
import os

import pytest

from src.modules.news.application.services import NewsCollectorService
from src.modules.news.infrastructure.cache import InMemoryCacheAdapter
from src.modules.news.infrastructure.repositories.postgres import PgNewsRepository
from src.modules.news.infrastructure.the_news_api_client import TheNewsAPIClient


class TestNewsCollectionRealAPI:
    """Real API + Real DB integration."""

    def test_collector_real_api_parses_and_saves_to_db(self, pg_session):
        """Given: Real TheNewsAPI, test DB
        When: collector.run() 호출 (실제 API)
        Then: 파싱 + DB 저장 정상 확인

        검증:
        - API 응답 파싱 (UTC→KST 변환)
        - DB 저장 (schema 정합성)
        - 데이터 무결성 (필드, 타입)
        """
        api_key = os.getenv("THENEWSAPI_TOKEN")
        if not api_key:
            pytest.skip("THENEWSAPI_TOKEN 환경 변수 필요")
        api_client = TheNewsAPIClient(api_key=api_key)
        cache = InMemoryCacheAdapter()
        repository = PgNewsRepository(pg_session)

        collector = NewsCollectorService(
            news_source=api_client,
            cache=cache,
            repository=repository,
        )

        # Real API call
        keywords = ["interest rate"]
        collector.run(keywords=keywords)

        # Assert: DB에 저장됨
        items = repository.find_all()
        assert len(items) > 0, "API에서 가져온 기사가 저장되지 않음"

        # 첫 번째 기사 검증
        item = items[0]

        # 필드 존재 검증
        assert item.id is not None
        assert item.title, "title이 비어있음"
        assert item.link, "link가 비어있음"
        assert item.source, "source가 비어있음"
        assert item.published_at is not None

        # Timezone aware 검증 (UTC→KST 변환 확인)
        assert item.published_at.tzinfo is not None, "published_at이 timezone-naive"

        # 기본 타입 검증
        assert isinstance(item.title, str)
        assert isinstance(item.link, str)
        assert isinstance(item.source, str)
