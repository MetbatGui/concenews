"""MarketSnapshotService 선정 규칙 테스트."""
from datetime import UTC, datetime
from uuid import UUID

import pytest

from src.modules.market.application.services import MarketSnapshotService
from src.modules.market.domain.models import MarketSnapshot, MarketSnapshotPayload


def _payload(market_id: str, volume_24h: float) -> MarketSnapshotPayload:
    return MarketSnapshotPayload(
        market_id=market_id,
        question=f"질문 {market_id}",
        outcomes=("예", "아니오"),
        outcome_prices=(0.6, 0.4),
        volume_24h=volume_24h,
        end_date=datetime(2026, 9, 1, tzinfo=UTC),
        active=True,
        closed=False,
    )


class _FakeSource:
    def __init__(self, candidates: list[MarketSnapshotPayload]) -> None:
        self.candidates = candidates
        self.requests: list[tuple[int, str, bool]] = []

    async def fetch_active_market_snapshots(
        self, limit: int, order: str, ascending: bool
    ) -> list[MarketSnapshotPayload]:
        self.requests.append((limit, order, ascending))
        return list(self.candidates)


class _FakeClassificationRepository:
    def __init__(self, macro_ids: set[str]) -> None:
        self.macro_ids = macro_ids

    def find_active_macro_condition_ids(self, now: datetime) -> set[str]:
        del now
        return set(self.macro_ids)


class _FakeSnapshotRepository:
    def __init__(self) -> None:
        self.saved: list[MarketSnapshot] = []

    def save_bulk(self, snapshots: list[MarketSnapshot]) -> None:
        self.saved.extend(snapshots)


class _FakeIdGenerator:
    def __init__(self) -> None:
        self._next = 1

    def generate(self) -> UUID:
        value = UUID(int=self._next)
        self._next += 1
        return value


class TestMarketSnapshotService:
    """거래량 순서 보존과 MACRO 교집합 선정 규칙."""

    @pytest.mark.asyncio
    async def test_saves_first_fifty_macro_candidates_in_source_order(self):
        """Given: 거래량 내림차순 후보 60개와 그중 MACRO 55개
        When: run
        Then: MACRO 후보의 앞 50개만 원래 순서로 저장한다.
        """
        candidates = [_payload(f"m{index}", float(200 - index)) for index in range(60)]
        macro_ids = {f"m{index}" for index in range(55)}
        source = _FakeSource(candidates)
        repository = _FakeSnapshotRepository()
        service = MarketSnapshotService(
            source=source,
            classification_repository=_FakeClassificationRepository(macro_ids),
            snapshot_repository=repository,
            id_generator=_FakeIdGenerator(),
        )

        await service.run()

        assert source.requests == [(200, "volume24hr", False)]
        assert [snapshot.market_id for snapshot in repository.saved] == [
            f"m{index}" for index in range(50)
        ]

    @pytest.mark.asyncio
    async def test_does_not_fetch_when_no_active_macro_market_exists(self):
        """Given: 유효한 MACRO 분류가 없는 상태
        When: run
        Then: Gamma API를 호출하거나 빈 저장을 하지 않는다.
        """
        source = _FakeSource([_payload("m1", 100.0)])
        repository = _FakeSnapshotRepository()
        service = MarketSnapshotService(
            source=source,
            classification_repository=_FakeClassificationRepository(set()),
            snapshot_repository=repository,
            id_generator=_FakeIdGenerator(),
        )

        await service.run()

        assert source.requests == []
        assert repository.saved == []
