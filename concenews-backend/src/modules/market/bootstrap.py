"""Market 모듈 조립 (Composition Root)."""
import os

from sqlalchemy.orm import Session

from src.modules.market.application.services import MarketClassifierService
from src.modules.market.infrastructure.polymarket_client import PolymarketGammaClient
from src.modules.market.infrastructure.repositories import (
    PgMarketClassificationRepository,
)
from src.shared_kernel.db.engine import get_engine
from src.shared_kernel.scheduler import AsyncioSchedulerAdapter


def build_classifier_service(session: Session) -> MarketClassifierService:
    """MarketClassifierService 조립.

    Args:
        session: SQLAlchemy Session.

    Returns:
        DI 조립된 서비스.
    """
    client = PolymarketGammaClient()
    repository = PgMarketClassificationRepository(session)
    return MarketClassifierService(source=client, repository=repository)


def register_market_classifier_job(scheduler: AsyncioSchedulerAdapter) -> None:
    """마켓 분류 작업을 공용 Scheduler에 등록한다.

    Args:
        scheduler: 마켓 분류 작업을 등록할 공용 Scheduler.
    """
    interval_seconds = int(os.getenv("MARKET_CLASSIFIER_INTERVAL", "300"))

    async def run_classifier() -> None:
        """매 실행마다 새 Session으로 마켓 분류를 실행한다."""
        session = Session(get_engine())
        try:
            service = build_classifier_service(session)
            await service.run()
        finally:
            session.close()

    scheduler.schedule(
        "market_classifier", run_classifier, interval_seconds=interval_seconds
    )
