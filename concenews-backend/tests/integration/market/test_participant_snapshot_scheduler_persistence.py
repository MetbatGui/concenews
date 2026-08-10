"""참여자 스냅샷 Scheduler의 commit 경계 테스트."""

from datetime import UTC, datetime
from uuid import UUID

import pytest
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from src.modules.market.bootstrap import register_market_participant_snapshot_job
from src.modules.market.domain.models import (
    MarketSnapshot,
    ParticipantPositionPayload,
)
from src.modules.market.infrastructure.orm import (
    MarketParticipantSnapshotRow,
    MarketSnapshotRow,
)
from src.modules.market.infrastructure.repositories import PgMarketSnapshotRepository
from src.shared_kernel.scheduler import AsyncioSchedulerAdapter


class _Source:
    async def fetch_top_holder_positions(self, condition_id: str, limit: int):
        assert (condition_id, limit) == ("0xcondition", 20)
        return [
            ParticipantPositionPayload(
                wallet_address="0xwallet", outcome_index=0, position_amount=10.0
            )
        ]

    async def aclose(self):
        return None


class _Ids:
    def generate(self):
        return UUID("018f0d3d-5b5a-7a3d-8b54-8f3c11a20d08")


@pytest.mark.asyncio
async def test_scheduler_participant_job_commits_for_fresh_session(pg_engine):
    """Given: condition ID가 있는 최신 마켓 스냅샷
    When: 참여자 Scheduler 작업을 실행하고 Session을 닫음
    Then: 새 Session에서 보유 포지션을 읽을 수 있다.
    """
    observed_at = datetime(2026, 8, 10, 5, 0, tzinfo=UTC)
    market_snapshot_id = UUID("018f0d3d-5b5a-7a3d-8b54-8f3c11a20d09")
    participant_snapshot_id = UUID("018f0d3d-5b5a-7a3d-8b54-8f3c11a20d08")
    try:
        seed = Session(pg_engine)
        try:
            PgMarketSnapshotRepository(seed).save_bulk(
                [
                    MarketSnapshot(
                        id=market_snapshot_id,
                        market_id="m1",
                        condition_id="0xcondition",
                        question="질문",
                        outcomes=("Yes", "No"),
                        outcome_prices=(0.6, 0.4),
                        end_date=datetime(2026, 9, 1, tzinfo=UTC),
                        active=True,
                        closed=False,
                        timestamp=observed_at,
                    )
                ]
            )
            seed.commit()
        finally:
            seed.close()

        scheduler = AsyncioSchedulerAdapter()
        register_market_participant_snapshot_job(
            scheduler,
            session_factory=lambda: Session(pg_engine),
            source_factory=_Source,
            id_generator_factory=_Ids,
        )
        await scheduler.trigger_all()

        verify = Session(pg_engine)
        try:
            assert verify.execute(
                select(MarketParticipantSnapshotRow.wallet_address)
            ).scalars().all() == ["0xwallet"]
        finally:
            verify.close()
    finally:
        cleanup = Session(pg_engine)
        try:
            cleanup.execute(
                delete(MarketParticipantSnapshotRow).where(
                    MarketParticipantSnapshotRow.id == participant_snapshot_id
                )
            )
            cleanup.execute(
                delete(MarketSnapshotRow).where(
                    MarketSnapshotRow.id == market_snapshot_id
                )
            )
            cleanup.commit()
        finally:
            cleanup.close()
