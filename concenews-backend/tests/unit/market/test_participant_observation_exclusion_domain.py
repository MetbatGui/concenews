"""참여자 관측 제외 Domain 계약 테스트."""

from datetime import UTC, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from src.modules.market.domain.models import (
    MarketParticipantObservationExclusion,
    ObservationExclusionReviewStatus,
)


def _make_exclusion(**overrides: object) -> MarketParticipantObservationExclusion:
    """유효한 관측 제외 항목을 만든다."""
    values: dict[str, object] = {
        "id": UUID("018f0d3d-5b5a-7a3d-8b54-8f3c11a20d10"),
        "wallet_address": "0xA5EF39C3D3E10D0B270233AF41CAC69796B12966",
        "reason": "거래 참여자로 귀속할 수 없음",
        "evidence_url": "https://example.com/evidence",
        "registered_at": datetime(2026, 8, 15, tzinfo=UTC),
        "review_status": ObservationExclusionReviewStatus.REVIEWED,
        "active": True,
    }
    values.update(overrides)
    return MarketParticipantObservationExclusion(**values)


class TestMarketParticipantObservationExclusion:
    """관측 제외 항목의 불변 조건."""

    def test_normalizes_wallet_address_to_lowercase(self):
        """Given: 대문자를 포함한 유효 지갑 주소
        When: 관측 제외 항목 생성
        Then: 비교 가능한 소문자 주소로 정규화한다.
        """
        exclusion = _make_exclusion()

        assert exclusion.wallet_address == "0xa5ef39c3d3e10d0b270233af41cac69796b12966"

    @pytest.mark.parametrize("wallet_address", ["0xwallet", "a5ef39c3d3e10d0b270233af41cac69796b12966"])
    def test_rejects_invalid_wallet_address(self, wallet_address: str):
        """Given: Ethereum 지갑 형식이 아닌 주소
        When: 관측 제외 항목 생성
        Then: 계약 위반으로 거부한다.
        """
        with pytest.raises(ValidationError):
            _make_exclusion(wallet_address=wallet_address)

    def test_rejects_active_item_before_review(self):
        """Given: 검토 대기 상태의 활성 제외 항목
        When: 관측 제외 항목 생성
        Then: 사람 검토 전에는 활성화할 수 없어 거부한다.
        """
        with pytest.raises(ValidationError):
            _make_exclusion(
                review_status=ObservationExclusionReviewStatus.PENDING,
                active=True,
            )
