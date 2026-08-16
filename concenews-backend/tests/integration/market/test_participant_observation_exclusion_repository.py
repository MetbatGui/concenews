"""참여자 관측 제외 목록 저장소 통합 테스트."""

from datetime import UTC, datetime
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.modules.market.bootstrap import register_initial_observation_exclusions
from src.modules.market.domain.models import (
    MarketParticipantObservationExclusion,
    ObservationExclusionReviewStatus,
)
from src.modules.market.infrastructure.orm import (
    MarketParticipantObservationExclusionRow,
)
from src.modules.market.infrastructure.repositories import (
    PgMarketParticipantObservationExclusionRepository,
)

INITIAL_WALLET = "0xa5ef39c3d3e10d0b270233af41cac69796b12966"


def _exclusion(
    exclusion_id: str,
    wallet_address: str,
    *,
    review_status: ObservationExclusionReviewStatus = (
        ObservationExclusionReviewStatus.REVIEWED
    ),
    active: bool = True,
) -> MarketParticipantObservationExclusion:
    """저장 계약 검증용 관측 제외 항목을 만든다."""
    return MarketParticipantObservationExclusion(
        id=UUID(exclusion_id),
        wallet_address=wallet_address,
        reason="거래 참여자로 귀속할 수 없음",
        evidence_url="https://example.com/evidence",
        registered_at=datetime(2026, 8, 15, tzinfo=UTC),
        review_status=review_status,
        active=active,
    )


class TestPgMarketParticipantObservationExclusionRepository:
    """실제 PostgreSQL 제외 목록 저장 계약."""

    def test_bootstrap_registers_initial_wallet_once(self, pg_session: Session):
        """Given: 초기 제외 지갑 bootstrap
        When: 같은 Session에서 두 번 실행
        Then: 근거와 검토 상태를 가진 행이 한 번만 저장된다.
        """
        register_initial_observation_exclusions(pg_session)
        register_initial_observation_exclusions(pg_session)

        rows = (
            pg_session.execute(select(MarketParticipantObservationExclusionRow))
            .scalars()
            .all()
        )

        assert len(rows) == 1
        assert rows[0].wallet_address == INITIAL_WALLET
        assert rows[0].review_status == "REVIEWED"
        assert rows[0].active is True
        assert rows[0].evidence_url.endswith(
            "docs/research/polymarket-system-wallet-eligibility.md"
        )

    def test_finds_only_active_reviewed_wallets(self, pg_session: Session):
        """Given: 활성 제외 지갑과 검토 대기 후보, 비활성 항목
        When: 활성 제외 지갑 조회
        Then: 활성·검토 완료 지갑만 반환한다.
        """
        repository = PgMarketParticipantObservationExclusionRepository(pg_session)
        repository.register_if_absent(
            [
                _exclusion(
                    "018f0d3d-5b5a-7a3d-8b54-8f3c11a20d20", "0x" + "a" * 40
                ),
                _exclusion(
                    "018f0d3d-5b5a-7a3d-8b54-8f3c11a20d21",
                    "0x" + "b" * 40,
                    review_status=ObservationExclusionReviewStatus.PENDING,
                    active=False,
                ),
                _exclusion(
                    "018f0d3d-5b5a-7a3d-8b54-8f3c11a20d22",
                    "0x" + "c" * 40,
                    active=False,
                ),
            ]
        )

        assert repository.find_active_wallet_addresses() == {"0x" + "a" * 40}

    def test_rejects_second_active_item_for_same_wallet(self, pg_session: Session):
        """Given: 이미 활성 제외된 지갑
        When: 같은 지갑의 다른 활성 항목을 직접 저장
        Then: DB 제약이 중복 활성 항목을 거부한다.
        """
        repository = PgMarketParticipantObservationExclusionRepository(pg_session)
        repository.register_if_absent(
            [_exclusion("018f0d3d-5b5a-7a3d-8b54-8f3c11a20d23", "0x" + "d" * 40)]
        )

        with pytest.raises(IntegrityError):
            pg_session.execute(
                MarketParticipantObservationExclusionRow.__table__.insert().values(
                    id=UUID("018f0d3d-5b5a-7a3d-8b54-8f3c11a20d24"),
                    wallet_address="0x" + "d" * 40,
                    reason="거래 참여자로 귀속할 수 없음",
                    evidence_url="https://example.com/evidence",
                    registered_at=datetime(2026, 8, 15, tzinfo=UTC),
                    review_status="REVIEWED",
                    active=True,
                )
            )
