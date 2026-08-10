"""News 모듈 조립 (Composition Root).

Repository / Service / Endpoint 조합을 여기서 결정.
Layer 안쪽 (application, domain) 는 이 파일을 몰라도 됨.
Router 는 provider 함수만 참조 — Infrastructure 직접 import 금지.
"""
import asyncio
import logging
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

logger = logging.getLogger(__name__)


def get_repository(
    session: Annotated[Session, Depends(get_session)],
) -> NewsRepositoryPort:
    """Repository provider (Session 주입).

    Production: PgNewsRepository (PostgreSQL adapter).
    Test: app.dependency_overrides 로 교체.

    Args:
        session: SQLAlchemy Session (request-scoped).

    Returns:
        NewsRepositoryPort 구현체 (PgNewsRepository).
    """
    return PgNewsRepository(session)


def get_service(
    repository: Annotated[NewsRepositoryPort, Depends(get_repository)],
) -> NewsService:
    """NewsService provider (Repository 주입).

    Args:
        repository: 저장소 (Depends 주입).

    Returns:
        NewsService 인스턴스.
    """
    return NewsService(repository=repository)


async def setup_news_collector() -> AsyncioSchedulerAdapter:
    """News collector 및 scheduler 초기화 (lifespan startup 용).

    매 실행마다 새 session 생성 (격리 + lifecycle 단순화).

    Returns:
        AsyncioSchedulerAdapter 스케줄러.

    Raises:
        ValueError: NEWS_API_KEY 환경 변수 미설정.
    """
    scheduler = AsyncioSchedulerAdapter()
    register_news_collection_job(scheduler)
    return scheduler


def register_news_collection_job(scheduler: AsyncioSchedulerAdapter) -> None:
    """뉴스 수집 작업을 공용 Scheduler에 등록한다.

    Args:
        scheduler: 뉴스 수집 작업을 등록할 공용 Scheduler.

    Raises:
        ValueError: TheNewsAPI 토큰이 설정되지 않은 경우.
    """
    api_key = os.getenv("THENEWSAPI_TOKEN")
    if not api_key:
        raise ValueError("THENEWSAPI_TOKEN 환경 변수 미설정")

    api_client = TheNewsAPIClient(api_key=api_key)
    cache = InMemoryCacheAdapter()

    # Schedule collector job (환경변수로 설정 가능, 기본 15분)
    interval_seconds = int(os.getenv("NEWS_COLLECTOR_INTERVAL", 900))

    async def run_collector() -> None:
        """매 실행마다 새 session 생성 후 실행."""
        session = Session(get_engine())
        try:
            repository = PgNewsRepository(session)
            collector = NewsCollectorService(
                news_source=api_client,
                cache=cache,
                repository=repository,
            )
            # Blocking call을 executor에서 실행 (non-blocking)
            await asyncio.to_thread(
                collector.run,
                keywords=["interest rate", "forex", "central bank"],
            )
        finally:
            session.close()

    scheduler.schedule(
        "news_collector", run_collector, interval_seconds=interval_seconds
    )
