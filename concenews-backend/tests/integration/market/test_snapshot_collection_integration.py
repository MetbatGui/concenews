"""마켓 스냅샷 수집 서비스 통합 테스트."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modules.market.application.services import MarketSnapshotService
from src.modules.market.domain.models import (
    Classification,
    MarketClassification,
    MarketSnapshotPayload,
    Tag,
)
from src.modules.market.infrastructure.orm import MarketSnapshotRow
from src.modules.market.infrastructure.repositories import (
    PgMarketClassificationRepository,
    PgMarketSnapshotRepository,
)


def _payload(index: int) -> MarketSnapshotPayload:
    return MarketSnapshotPayload(
        market_id=f"market-{index}",
        condition_id=f"0xcondition-{index}",
        question=f"질문 {index}",
        outcomes=("예", "아니오"),
        outcome_prices=(0.6, 0.4),
        volume_24h=float(200 - index),
        end_date=datetime(2026, 9, 1, tzinfo=UTC),
        active=True,
        closed=False,
    )


class _FakeSource:
    def __init__(self, candidates: list[MarketSnapshotPayload]) -> None:
        self._candidates = candidates

    async def fetch_active_market_snapshots(
        self, limit: int, order: str, ascending: bool
    ) -> list[MarketSnapshotPayload]:
        assert (limit, order, ascending) == (200, "volume24hr", False)
        return list(self._candidates)


class _FakeIdGenerator:
    def __init__(self) -> None:
        self._next = 1

    def generate(self) -> UUID:
        generated = UUID(int=self._next)
        self._next += 1
        return generated


class TestMarketSnapshotCollectionIntegration:
    """Fake Gamma와 실제 PostgreSQL 조합의 수집 경로."""

    @pytest.mark.asyncio
    async def test_saves_only_first_fifty_active_macro_candidates(
        self, pg_session: Session
    ):
        """Given: 거래량 순 후보 60개와 유효한 MACRO 분류 55개
        When: 스냅샷 수집 서비스 실행
        Then: 실제 DB에 MACRO 상위 50개만 저장된다.
        """
        candidates = [_payload(index) for index in range(60)]
        classifications = [
            MarketClassification(
                condition_id=f"market-{index}",
                question=f"질문 {index}",
                classification=Classification.MACRO,
                tags=(Tag(id=159, label="Fed", slug="fed"),),
                end_date=datetime.now(UTC) + timedelta(days=1),
                classified_at=datetime.now(UTC),
            )
            for index in range(55)
        ]
        classification_repository = PgMarketClassificationRepository(pg_session)
        classification_repository.save_bulk(classifications)
        service = MarketSnapshotService(
            source=_FakeSource(candidates),
            classification_repository=classification_repository,
            snapshot_repository=PgMarketSnapshotRepository(pg_session),
            id_generator=_FakeIdGenerator(),
        )

        await service.run()

        rows = (
            pg_session.execute(select(MarketSnapshotRow).order_by(MarketSnapshotRow.id))
            .scalars()
            .all()
        )
        assert len(rows) == 50
        assert {row.market_id for row in rows} == {
            f"market-{index}" for index in range(50)
        }
        assert {row.condition_id for row in rows} == {
            f"0xcondition-{index}" for index in range(50)
        }
