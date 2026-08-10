"""MarketParticipantSnapshotService 수집 규칙 테스트."""

from uuid import UUID

import pytest
import httpx

from src.modules.market.application.services import MarketParticipantSnapshotService
from src.modules.market.domain.models import (
    MarketParticipantSnapshot,
    ParticipantPositionPayload,
    TrackedMarket,
)


class _FakeMarketSnapshotRepository:
    def __init__(self, markets: list[TrackedMarket]) -> None:
        self.markets = markets

    def find_latest_tracked_markets(self, limit: int) -> list[TrackedMarket]:
        assert limit == 50
        return self.markets


class _FakeParticipantRepository:
    def __init__(self) -> None:
        self.saved: list[MarketParticipantSnapshot] = []

    def save_bulk(self, snapshots: list[MarketParticipantSnapshot]) -> None:
        self.saved.extend(snapshots)


class _FakeSource:
    async def fetch_top_holder_positions(
        self, condition_id: str, limit: int
    ) -> list[ParticipantPositionPayload]:
        assert limit == 20
        if condition_id == "0xfail":
            raise httpx.ConnectError("외부 API 실패")
        return [
            ParticipantPositionPayload(
                wallet_address="0xwallet", outcome_index=1, position_amount=12.5
            )
        ]


class _FakeIdGenerator:
    def __init__(self) -> None:
        self.value = 0

    def generate(self) -> UUID:
        self.value += 1
        return UUID(int=self.value)


class TestMarketParticipantSnapshotService:
    """대상별 수집과 외부 실패 격리 계약."""

    @pytest.mark.asyncio
    async def test_saves_positions_for_remaining_market_when_one_source_request_fails(
        self,
    ):
        """Given: 첫 마켓 요청 실패와 두 번째 마켓의 유효 포지션
        When: 참여자 수집 실행
        Then: 실패를 격리하고 두 번째 관측값을 저장한다.
        """
        market_repository = _FakeMarketSnapshotRepository(
            [
                TrackedMarket(market_id="m1", condition_id="0xfail"),
                TrackedMarket(market_id="m2", condition_id="0xok"),
            ]
        )
        participant_repository = _FakeParticipantRepository()
        service = MarketParticipantSnapshotService(
            source=_FakeSource(),
            market_snapshot_repository=market_repository,
            participant_snapshot_repository=participant_repository,
            id_generator=_FakeIdGenerator(),
        )

        await service.run()

        assert [
            (item.market_id, item.condition_id, item.position_amount)
            for item in participant_repository.saved
        ] == [("m2", "0xok", 12.5)]
