"""뉴스 수집 end-to-end integration test.

Scheduler → API mock → DB 저장 흐름 검증.
"""

import pytest
import responses

from src.modules.news.application.services import NewsCollectorService
from src.modules.news.infrastructure.cache import InMemoryCacheAdapter
from src.modules.news.infrastructure.repositories.postgres import PgNewsRepository
from src.modules.news.infrastructure.scheduler import AsyncioSchedulerAdapter
from src.modules.news.infrastructure.the_news_api_client import TheNewsAPIClient


class TestNewsCollectionE2E:
    """Scheduler + API mock + DB 통합."""

    @pytest.mark.asyncio
    async def test_collector_saves_to_db(self, pg_session):
        """Given: API mock (3개 기사), PG DB, scheduler
        When: scheduler.trigger() 호출 (manual run)
        Then: API 호출 → DB 저장 (3개 row 확인)
        """
        # Setup
        api_key = "test-key"
        keywords = ["interest rate"]

        with responses.RequestsMock() as rsps:
            # Mock API 응답
            rsps.add(
                responses.GET,
                "https://api.thenewsapi.com/v1/news/top",
                json={
                    "data": [
                        {
                            "title": "Article 1",
                            "description": "Description 1",
                            "url": "https://example.com/1",
                            "source": "Source A",
                            "publishedAt": "2026-07-06T10:00:00Z",
                        },
                        {
                            "title": "Article 2",
                            "description": "Description 2",
                            "url": "https://example.com/2",
                            "source": "Source B",
                            "publishedAt": "2026-07-06T11:00:00Z",
                        },
                        {
                            "title": "Article 3",
                            "description": None,
                            "url": "https://example.com/3",
                            "source": "Source C",
                            "publishedAt": "2026-07-06T12:00:00Z",
                        },
                    ]
                },
                status=200,
            )

            # Setup 서비스
            api_client = TheNewsAPIClient(api_key=api_key)
            cache = InMemoryCacheAdapter()
            repository = PgNewsRepository(pg_session)
            collector = NewsCollectorService(
                news_source=api_client, cache=cache, repository=repository
            )

            # Collect
            collector.run(keywords=keywords)

            # Assert: DB에 3개 저장
            items = repository.find_all()
            assert len(items) == 3
            assert items[0].title == "Article 1"
            assert items[1].title == "Article 2"
            assert items[2].title == "Article 3"

    @pytest.mark.asyncio
    async def test_collector_dedup_on_second_run(self, pg_session):
        """Given: 첫 실행 후 3개 저장, 두 번째 실행 시 같은 기사
        When: collector.run() 2번 호출
        Then: 두 번째는 dedup (캐시), 저장 0개
        """
        api_key = "test-key"
        keywords = ["test"]

        articles_response = {
            "data": [
                {
                    "title": "News",
                    "description": None,
                    "url": "https://example.com/dup",
                    "source": "Source",
                    "publishedAt": "2026-07-06T10:00:00Z",
                }
            ]
        }

        with responses.RequestsMock() as rsps:
            # Mock: 2번 호출
            rsps.add(
                responses.GET,
                "https://api.thenewsapi.com/v1/news/top",
                json=articles_response,
                status=200,
            )
            rsps.add(
                responses.GET,
                "https://api.thenewsapi.com/v1/news/top",
                json=articles_response,
                status=200,
            )

            api_client = TheNewsAPIClient(api_key=api_key)
            cache = InMemoryCacheAdapter()
            repository = PgNewsRepository(pg_session)
            collector = NewsCollectorService(
                news_source=api_client, cache=cache, repository=repository
            )

            # 첫 번째 실행
            collector.run(keywords=keywords)
            items_after_first = repository.find_all()
            assert len(items_after_first) == 1

            # 두 번째 실행 (캐시됨)
            collector.run(keywords=keywords)
            items_after_second = repository.find_all()
            assert len(items_after_second) == 1  # 추가 저장 없음

    @pytest.mark.asyncio
    async def test_scheduler_runs_collector(self, pg_session):
        """Given: AsyncioScheduler + NewsCollectorService
        When: scheduler.start() → schedule(collector.run) → trigger
        Then: collector 실행 (DB 저장 확인)
        """
        api_key = "test-key"

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                "https://api.thenewsapi.com/v1/news/top",
                json={
                    "data": [
                        {
                            "title": "News",
                            "description": None,
                            "url": "https://example.com/news",
                            "source": "Source",
                            "publishedAt": "2026-07-06T10:00:00Z",
                        }
                    ]
                },
                status=200,
            )

            api_client = TheNewsAPIClient(api_key=api_key)
            cache = InMemoryCacheAdapter()
            repository = PgNewsRepository(pg_session)
            collector = NewsCollectorService(
                news_source=api_client, cache=cache, repository=repository
            )

            scheduler = AsyncioSchedulerAdapter()

            # Schedule job
            async def run_collector() -> None:
                collector.run(keywords=["test"])

            scheduler.schedule(run_collector, interval_seconds=900)

            # Start, trigger, stop
            await scheduler.start()
            await scheduler.trigger_all()  # Manual trigger for test
            await scheduler.stop()

            # Assert
            items = repository.find_all()
            assert len(items) == 1
            assert items[0].title == "News"
