"""Market 모듈 조립 (Composition Root)."""
import os
from collections.abc import Callable

from sqlalchemy.orm import Session

from src.modules.market.application.ports import MarketSourcePort, SnapshotIdGeneratorPort
from src.modules.market.application.services import MarketClassifierService, MarketSnapshotService
from src.modules.market.infrastructure.polymarket_client import PolymarketGammaClient
from src.modules.market.infrastructure.repositories import (
    PgMarketClassificationRepository,
    PgMarketSnapshotRepository,
)
from src.modules.market.infrastructure.snapshot_id_generator import UuidV7SnapshotIdGenerator
from src.shared_kernel.db.engine import get_engine
from src.shared_kernel.scheduler import AsyncioSchedulerAdapter


def build_classifier_service(
    session: Session,
    source: MarketSourcePort | None = None,
) -> MarketClassifierService:
    """MarketClassifierService 조립.

    Args:
        session: SQLAlchemy Session.

    Returns:
        DI 조립된 서비스.
    """
    repository = PgMarketClassificationRepository(session)
    return MarketClassifierService(
        source=source or PolymarketGammaClient(),
        repository=repository,
    )


def register_market_classifier_job(
    scheduler: AsyncioSchedulerAdapter,
    *,
    session_factory: Callable[[], Session] | None = None,
    source_factory: Callable[[], MarketSourcePort] | None = None,
) -> None:
    """마켓 분류 작업을 공용 Scheduler에 등록한다.

    Args:
        scheduler: 마켓 분류 작업을 등록할 공용 Scheduler.
    """
    interval_seconds = int(os.getenv("MARKET_CLASSIFIER_INTERVAL", "300"))

    async def run_classifier() -> None:
        """매 실행마다 새 Session으로 마켓 분류를 실행한다."""
        session = (
            session_factory() if session_factory else Session(get_engine())
        )
        source = source_factory() if source_factory else PolymarketGammaClient()
        try:
            service = build_classifier_service(session, source=source)
            await service.run()
        finally:
            close = getattr(source, "aclose", None)
            if close is not None:
                await close()
            session.close()

    scheduler.schedule(
        "market_classifier", run_classifier, interval_seconds=interval_seconds
    )


def build_snapshot_service(
    session: Session,
    source: MarketSourcePort | None = None,
    id_generator: SnapshotIdGeneratorPort | None = None,
) -> MarketSnapshotService:
    """마켓 스냅샷 수집 서비스를 조립한다."""
    return MarketSnapshotService(
        source=source or PolymarketGammaClient(),
        classification_repository=PgMarketClassificationRepository(session),
        snapshot_repository=PgMarketSnapshotRepository(session),
        id_generator=id_generator or UuidV7SnapshotIdGenerator(),
    )


def register_market_snapshot_job(
    scheduler: AsyncioSchedulerAdapter,
    *,
    session_factory: Callable[[], Session] | None = None,
    source_factory: Callable[[], MarketSourcePort] | None = None,
    id_generator_factory: Callable[[], SnapshotIdGeneratorPort] | None = None,
) -> None:
    """마켓 스냅샷 수집 작업을 공용 Scheduler에 등록한다."""
    interval_seconds = int(os.getenv("MARKET_SNAPSHOT_INTERVAL", "300"))

    async def run_snapshot() -> None:
        session = session_factory() if session_factory else Session(get_engine())
        source = source_factory() if source_factory else PolymarketGammaClient()
        id_generator = id_generator_factory() if id_generator_factory else UuidV7SnapshotIdGenerator()
        try:
            await build_snapshot_service(session, source, id_generator).run()
        finally:
            close = getattr(source, "aclose", None)
            if close is not None:
                await close()
            session.close()

    scheduler.schedule("market_snapshot", run_snapshot, interval_seconds=interval_seconds)
