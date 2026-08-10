"""News 모듈 조립(Composition Root)."""
import asyncio
import os
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from src.shared_kernel.db.engine import get_engine
from src.shared_kernel.db.session import get_session
from src.shared_kernel.scheduler import AsyncioSchedulerAdapter

from .application.ports import NewsRepositoryPort
from .application.services import NewsCollectorService, NewsService
from .infrastructure.cache import InMemoryCacheAdapter
from .infrastructure.repositories.postgres import PgNewsRepository
from .infrastructure.the_news_api_client import TheNewsAPIClient


def get_repository(
    session: Annotated[Session, Depends(get_session)],
) -> NewsRepositoryPort:
    """요청 범위 Session으로 뉴스 Repository를 조립한다."""
    return PgNewsRepository(session)


def get_service(
    repository: Annotated[NewsRepositoryPort, Depends(get_repository)],
) -> NewsService:
    """뉴스 조회 서비스를 조립한다."""
    return NewsService(repository=repository)


def register_news_collection_job(scheduler: AsyncioSchedulerAdapter) -> None:
    """뉴스 수집 작업을 공용 Scheduler에 등록한다.

    Args:
        scheduler: 뉴스 수집 작업을 등록할 공용 Scheduler.

    Raises:
        ValueError: TheNewsAPI 토큰이 설정되지 않은 경우.
    """
    api_key = os.getenv("THENEWSAPI_TOKEN")
    if not api_key:
        raise ValueError("THENEWSAPI_TOKEN 환경 변수가 설정되지 않았습니다.")

    api_client = TheNewsAPIClient(api_key=api_key)
    cache = InMemoryCacheAdapter()
    interval_seconds = int(os.getenv("NEWS_COLLECTOR_INTERVAL", 900))

    async def run_collector() -> None:
        """실행마다 새 Session을 생성해 뉴스 수집을 실행한다."""
        session = Session(get_engine())
        try:
            repository = PgNewsRepository(session)
            collector = NewsCollectorService(
                news_source=api_client,
                cache=cache,
                repository=repository,
            )
            await asyncio.to_thread(
                collector.run,
                keywords=["interest rate", "forex", "central bank"],
            )
        finally:
            session.close()

    scheduler.schedule(
        "news_collector", run_collector, interval_seconds=interval_seconds
    )
