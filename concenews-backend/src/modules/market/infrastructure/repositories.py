"""PostgreSQL Repository — market_classification 저장/조회.

Walking Skeleton 단계에서 이미 실제 SQL 구현 (E2E 검증에 필요).
"""

from datetime import datetime

from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src.modules.market.domain.models import (
    MarketClassification,
    MarketParticipantObservationExclusion,
    MarketParticipantSnapshot,
    MarketSnapshot,
    ObservationExclusionReviewStatus,
    TrackedMarket,
)
from src.modules.market.infrastructure.orm import (
    MarketClassificationRow,
    MarketParticipantObservationExclusionRow,
    MarketParticipantSnapshotRow,
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

    def find_active_macro_condition_ids(self, now: datetime) -> set[str]:
        """유효 기간이 남은 MACRO 분류의 시장 식별자만 조회한다."""
        stmt = select(MarketClassificationRow.condition_id).where(
            MarketClassificationRow.end_date > now,
            MarketClassificationRow.classification == "MACRO",
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
                "condition_id": snapshot.condition_id,
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

    def find_latest_tracked_markets(self, limit: int) -> list[TrackedMarket]:
        """condition ID가 있는 최신 수집 시점의 마켓을 최대 개수만큼 조회한다."""
        latest_timestamp = select(
            func.max(MarketSnapshotRow.timestamp)
        ).scalar_subquery()
        stmt = (
            select(MarketSnapshotRow.market_id, MarketSnapshotRow.condition_id)
            .where(
                MarketSnapshotRow.timestamp == latest_timestamp,
                MarketSnapshotRow.condition_id.is_not(None),
            )
            .order_by(MarketSnapshotRow.market_id)
            .limit(limit)
        )
        return [
            TrackedMarket(market_id=market_id, condition_id=condition_id)
            for market_id, condition_id in self._session.execute(stmt)
        ]


class PgMarketParticipantObservationExclusionRepository:
    """market_participant_observation_exclusion PostgreSQL 저장소 어댑터."""

    def __init__(self, session: Session) -> None:
        """SQLAlchemy Session을 받는다."""
        self._session = session

    def register_if_absent(
        self, exclusions: list[MarketParticipantObservationExclusion]
    ) -> None:
        """같은 지갑의 활성 항목이 이미 있으면 저장하지 않는다."""
        if not exclusions:
            return

        rows = [
            {
                "id": exclusion.id,
                "wallet_address": exclusion.wallet_address,
                "reason": exclusion.reason,
                "evidence_url": exclusion.evidence_url,
                "registered_at": exclusion.registered_at,
                "review_status": exclusion.review_status.value,
                "active": exclusion.active,
            }
            for exclusion in exclusions
        ]
        stmt = insert(MarketParticipantObservationExclusionRow).values(rows)
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["wallet_address"],
            index_where=text("active"),
        )
        self._session.execute(stmt)
        self._session.flush()

    def find_active_wallet_addresses(self) -> set[str]:
        """활성·검토 완료 제외 지갑 주소만 조회한다."""
        stmt = select(MarketParticipantObservationExclusionRow.wallet_address).where(
            MarketParticipantObservationExclusionRow.active.is_(True),
            MarketParticipantObservationExclusionRow.review_status
            == ObservationExclusionReviewStatus.REVIEWED.value,
        )
        return set(self._session.execute(stmt).scalars().all())


class PgMarketParticipantSnapshotRepository:
    """market_participant_snapshot PostgreSQL 저장소 어댑터."""

    def __init__(self, session: Session) -> None:
        """SQLAlchemy Session을 받는다."""
        self._session = session

    def save_bulk(self, snapshots: list[MarketParticipantSnapshot]) -> None:
        """보유 포지션 관측값을 한 번에 저장한다."""
        if not snapshots:
            return

        rows = [
            {
                "id": snapshot.id,
                "market_id": snapshot.market_id,
                "condition_id": snapshot.condition_id,
                "wallet_address": snapshot.wallet_address,
                "outcome_index": snapshot.outcome_index,
                "position_amount": snapshot.position_amount,
                "timestamp": snapshot.timestamp,
            }
            for snapshot in snapshots
        ]
        self._session.execute(insert(MarketParticipantSnapshotRow).values(rows))
        self._session.flush()

    def find_latest_snapshots(self) -> list[MarketParticipantSnapshot]:
        """가장 최근 수집 배치(timestamp 최댓값)의 원본 스냅샷을 조회한다."""
        latest_timestamp = select(
            func.max(MarketParticipantSnapshotRow.timestamp)
        ).scalar_subquery()
        stmt = select(MarketParticipantSnapshotRow).where(
            MarketParticipantSnapshotRow.timestamp == latest_timestamp
        )
        rows = self._session.execute(stmt).scalars().all()
        return [
            MarketParticipantSnapshot(
                id=row.id,
                market_id=row.market_id,
                condition_id=row.condition_id,
                wallet_address=row.wallet_address,
                outcome_index=row.outcome_index,
                position_amount=float(row.position_amount),
                timestamp=row.timestamp,
            )
            for row in rows
        ]
