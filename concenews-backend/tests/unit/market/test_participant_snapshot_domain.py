"""참여자 보유 포지션 Domain 계약 테스트."""

from datetime import UTC, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from src.modules.market.domain.models import MarketParticipantSnapshot


def _make_snapshot(**overrides: object) -> MarketParticipantSnapshot:
    """유효한 참여자 포지션 스냅샷을 만든다."""
    values: dict[str, object] = {
        "id": UUID("018f0d3d-5b5a-7a3d-8b54-8f3c11a20d03"),
        "market_id": "3438892",
        "condition_id": "0xcondition",
        "wallet_address": "0xwallet",
        "outcome_index": 0,
        "position_amount": 125.5,
        "timestamp": datetime(2026, 8, 10, 5, 0, tzinfo=UTC),
    }
    values.update(overrides)
    return MarketParticipantSnapshot(**values)


class TestMarketParticipantSnapshot:
    """공개 보유 포지션의 최소 불변 조건."""

    def test_rejects_non_positive_raw_position_amount(self):
        """Given: 0 이하의 원시 보유량
        When: 포지션 스냅샷 생성
        Then: 관측값 계약 위반으로 거부한다.
        """
        with pytest.raises(ValidationError):
            _make_snapshot(position_amount=0)

    def test_rejects_negative_outcome_index(self):
        """Given: 음수 결과 인덱스
        When: 포지션 스냅샷 생성
        Then: 결과별 관측 계약 위반으로 거부한다.
        """
        with pytest.raises(ValidationError):
            _make_snapshot(outcome_index=-1)

    def test_rejects_attribute_reassignment(self):
        """Given: 생성된 참여자 포지션
        When: 원시 보유량 재할당
        Then: 불변 Domain 모델이 변경을 거부한다.
        """
        snapshot = _make_snapshot()

        with pytest.raises(ValidationError):
            snapshot.position_amount = 0.1  # type: ignore[misc]
