"""Scheduler 스냅샷 작업의 commit 경계 회귀 테스트."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modules.market.bootstrap import register_market_snapshot_job
from src.modules.market.domain.models import (
    Classification,
    MarketClassification,
    MarketSnapshotPayload,
    Tag,
)
from src.modules.market.infrastructure.orm import MarketSnapshotRow
from src.modules.market.infrastructure.repositories import (
    PgMarketClassificationRepository,
)
from src.shared_kernel.scheduler import AsyncioSchedulerAdapter


class _Source:
    async def fetch_active_market_snapshots(self, limit, order, ascending):
        assert (limit, order, ascending) == (200, "volume24hr", False)
        return [
            MarketSnapshotPayload(
                market_id="m1",
                question="금리 유지?",
                outcomes=("예", "아니오"),
                outcome_prices=(0.6, 0.4),
                volume_24h=100.0,
                end_date=datetime.now(UTC) + timedelta(days=1),
                active=True,
                closed=False,
            )
        ]

    async def aclose(self):
        return None


class _Ids:
    def generate(self):
        return UUID("018f0d3d-5b5a-7a3d-8b54-8f3c11a20d01")


@pytest.mark.asyncio
async def test_scheduler_snapshot_job_commits_for_fresh_session(pg_engine):
    """Given: 별도 Scheduler Session과 유효한 MACRO 분류
    When: snapshot 작업을 실행하고 작업 Session을 닫음
    Then: 새 Session에서도 스냅샷 행이 남는다.
    """
    seed = Session(pg_engine)
    try:
        PgMarketClassificationRepository(seed).save_bulk(
            [
                MarketClassification(
                    condition_id="m1",
                    question="금리 유지?",
                    classification=Classification.MACRO,
                    tags=(Tag(id=159, label="Fed", slug="fed"),),
                    end_date=datetime.now(UTC) + timedelta(days=1),
                    classified_at=datetime.now(UTC),
                )
            ]
        )
        seed.commit()
    finally:
        seed.close()

    scheduler = AsyncioSchedulerAdapter()
    register_market_snapshot_job(
        scheduler,
        session_factory=lambda: Session(pg_engine),
        source_factory=_Source,
        id_generator_factory=_Ids,
    )
    await scheduler.trigger_all()

    verify = Session(pg_engine)
    try:
        assert verify.execute(select(MarketSnapshotRow.market_id)).scalars().all() == [
            "m1"
        ]
    finally:
        verify.close()
