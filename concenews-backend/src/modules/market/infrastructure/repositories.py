"""PostgreSQL Repository — market_classification 저장/조회.

Walking Skeleton 단계에서 이미 실제 SQL 구현 (E2E 검증에 필요).
"""
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src.modules.market.domain.models import MarketClassification, MarketSnapshot
from src.modules.market.infrastructure.orm import (
    MarketClassificationRow,
    MarketSnapshotRow,
)


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
        self._session.flush()


class PgMarketSnapshotRepository:
    """market_snapshot용 PostgreSQL 저장소 어댑터."""

    def __init__(self, session: Session) -> None:
        """저장소에 사용할 SQLAlchemy Session을 받는다."""
        self._session = session

    def save_bulk(self, snapshots: list[MarketSnapshot]) -> None:
        """스냅샷을 한 번에 저장한다.

        Args:
            snapshots: 저장할 스냅샷 목록.
        """
        if not snapshots:
            return

        rows = [
            {
                "id": snapshot.id,
                "market_id": snapshot.market_id,
                "question": snapshot.question,
                "outcomes": list(snapshot.outcomes),
                "outcome_prices": list(snapshot.outcome_prices),
                "last_price": snapshot.last_price,
                "best_bid": snapshot.best_bid,
                "best_ask": snapshot.best_ask,
                "spread": snapshot.spread,
                "liquidity": snapshot.liquidity,
                "volume_24h": snapshot.volume_24h,
                "volume_1w": snapshot.volume_1w,
                "volume_1m": snapshot.volume_1m,
                "end_date": snapshot.end_date,
                "active": snapshot.active,
                "closed": snapshot.closed,
                "timestamp": snapshot.timestamp,
            }
            for snapshot in snapshots
        ]
        self._session.execute(insert(MarketSnapshotRow).values(rows))
        self._session.flush()


