"""PostgreSQL Repository — market_classification 저장/조회.

Walking Skeleton 단계에서 이미 실제 SQL 구현 (E2E 검증에 필요).
"""
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src.modules.market.domain.models import MarketClassification
from src.modules.market.infrastructure.orm import MarketClassificationRow


class PgMarketClassificationRepository:
    """PostgreSQL adapter for market_classification.

    Attributes:
        _session: SQLAlchemy Session.
    """

    def __init__(self, session: Session) -> None:
        """Initialize.

        Args:
            session: SQLAlchemy Session.
        """
        self._session = session

    def find_active_condition_ids(self, now: datetime) -> set[str]:
        """유효 캐시의 condition_id 조회 (end_date > now).

        Args:
            now: 현재 시각.

        Returns:
            유효한 분류 캐시 condition_id 집합.
        """
        stmt = select(MarketClassificationRow.condition_id).where(
            MarketClassificationRow.end_date > now
        )
        rows = self._session.execute(stmt).scalars().all()
        return set(rows)

    def save_bulk(self, classifications: list[MarketClassification]) -> None:
        """분류 결과 일괄 저장 (upsert).

        Args:
            classifications: 저장할 분류 결과 리스트.
        """
        if not classifications:
            return

        rows = [
            {
                "condition_id": c.condition_id,
                "question": c.question,
                "classification": c.classification.value,
                "tags_json": [t.model_dump() for t in c.tags],
                "end_date": c.end_date,
                "classified_at": c.classified_at,
            }
            for c in classifications
        ]
        stmt = insert(MarketClassificationRow).values(rows)
        stmt = stmt.on_conflict_do_nothing(index_elements=["condition_id"])
        self._session.execute(stmt)
        self._session.commit()


