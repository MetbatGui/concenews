"""Market 모듈 조립 (Composition Root, Walking Skeleton).

후속 PR 에서 FastAPI lifespan 통합 + Scheduler 등록 완성.
현재: DI 뼈대만.
"""
from sqlalchemy.orm import Session

from src.modules.market.application.services import MarketClassifierService
from src.modules.market.infrastructure.polymarket_client import PolymarketGammaClient
from src.modules.market.infrastructure.repositories import (
    PgMarketClassificationRepository,
)


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
