"""PgMarketParticipantSnapshotRepository 통합 테스트."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modules.market.domain.models import MarketParticipantSnapshot, MarketSnapshot
from src.modules.market.infrastructure.orm import MarketParticipantSnapshotRow
from src.modules.market.infrastructure.repositories import (
    PgMarketParticipantSnapshotRepository,
    PgMarketSnapshotRepository,
)


def _market_snapshot(
    snapshot_id: UUID, timestamp: datetime, condition_id: str | None
) -> MarketSnapshot:
    """추적 대상 조회용 마켓 스냅샷을 만든다."""
    return MarketSnapshot(
        id=snapshot_id,
        market_id="3438892",
        condition_id=condition_id,
        question="질문",
        outcomes=("Yes", "No"),
        outcome_prices=(0.6, 0.4),
        end_date=datetime(2026, 9, 1, tzinfo=UTC),
        active=True,
        closed=False,
        timestamp=timestamp,
    )


class TestPgMarketParticipantSnapshotRepository:
    """실제 PostgreSQL 참여자 포지션 저장 계약."""

    def test_saves_raw_position_and_reads_latest_tracked_market(
        self, pg_session: Session
    ):
        """Given: condition ID가 있는 최신 마켓과 보유 포지션
        When: 각각 저장하고 최신 추적 대상을 조회
        Then: 원시 보유량과 두 식별자가 보존된다.
        """
        older = datetime(2026, 8, 10, 5, 0, tzinfo=UTC)
        latest = older + timedelta(minutes=5)
        market_repository = PgMarketSnapshotRepository(pg_session)
        market_repository.save_bulk(
            [
                _market_snapshot(
                    UUID("018f0d3d-5b5a-7a3d-8b54-8f3c11a20d04"), older, None
                ),
                _market_snapshot(
                    UUID("018f0d3d-5b5a-7a3d-8b54-8f3c11a20d05"), latest, "0xcondition"
                ),
            ]
        )
        participant_repository = PgMarketParticipantSnapshotRepository(pg_session)
        participant_repository.save_bulk(
            [
                MarketParticipantSnapshot(
                    id=UUID("018f0d3d-5b5a-7a3d-8b54-8f3c11a20d06"),
                    market_id="3438892",
                    condition_id="0xcondition",
                    wallet_address="0xwallet",
                    outcome_index=1,
                    position_amount=125.5,
                    timestamp=latest,
                )
            ]
        )

        tracked = market_repository.find_latest_tracked_markets(limit=50)
        row = pg_session.execute(select(MarketParticipantSnapshotRow)).scalar_one()

        assert tracked[0].market_id == "3438892"
        assert tracked[0].condition_id == "0xcondition"
        assert float(row.position_amount) == 125.5
        assert row.outcome_index == 1
