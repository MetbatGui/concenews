"""News 모듈 조립 (Composition Root).

Repository / Service / Endpoint 조합을 여기서 결정.
Layer 안쪽 (application, domain) 는 이 파일을 몰라도 됨.
Router 는 provider 함수만 참조 — Infrastructure 직접 import 금지.
"""
import os
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from src.shared_kernel.db.engine import get_engine
from src.shared_kernel.db.session import get_session

from .application.ports import NewsRepositoryPort
from .application.services import NewsCollectorService, NewsService
from .infrastructure.cache import InMemoryCacheAdapter
from .infrastructure.repositories.postgres import PgNewsRepository
from .infrastructure.scheduler import AsyncioSchedulerAdapter
from .infrastructure.the_news_api_client import TheNewsAPIClient


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


async def setup_news_collector() -> tuple[AsyncioSchedulerAdapter, Session]:
    """News collector 및 scheduler 초기화 (lifespan startup 용).

    Returns:
        (scheduler, db_session) 튜플.

    Raises:
        ValueError: NEWS_API_KEY 환경 변수 미설정.
    """
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        raise ValueError("NEWS_API_KEY 환경 변수 미설정")

    # Create instances
    session = Session(get_engine())
    api_client = TheNewsAPIClient(api_key=api_key)
    cache = InMemoryCacheAdapter()
    repository = PgNewsRepository(session)
    collector = NewsCollectorService(
        news_source=api_client,
        cache=cache,
        repository=repository,
    )

    scheduler = AsyncioSchedulerAdapter()

    # Schedule collector job (15분 간격)
    async def run_collector() -> None:
        collector.run(keywords=["interest rate", "forex", "central bank"])

    scheduler.schedule(run_collector, interval_seconds=900)

    return scheduler, session
