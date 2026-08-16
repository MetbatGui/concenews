"""마켓 참여자 관측 자격 조회 서비스 통합 테스트."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modules.market.application.services import (
    MarketParticipantObservationService,
)
from src.modules.market.domain.models import (
    MarketParticipantObservationExclusion,
    MarketParticipantSnapshot,
    ObservationExclusionReviewStatus,
)
from src.modules.market.infrastructure.orm import MarketParticipantSnapshotRow
from src.modules.market.infrastructure.repositories import (
    PgMarketParticipantObservationExclusionRepository,
    PgMarketParticipantSnapshotRepository,
)

WHALE_WALLET = "0x" + "a" * 40
ORDINARY_WALLET = "0x" + "b" * 40


def _position(
    snapshot_id: str,
    wallet_address: str,
    timestamp: datetime,
    *,
    market_id: str = "3438892",
    condition_id: str = "0xcondition",
) -> MarketParticipantSnapshot:
    """원본 보유 포지션 스냅샷을 만든다."""
    return MarketParticipantSnapshot(
        id=UUID(snapshot_id),
        market_id=market_id,
        condition_id=condition_id,
        wallet_address=wallet_address,
        outcome_index=1,
        position_amount=125.5,
        timestamp=timestamp,
    )


def _exclusion(
    exclusion_id: str,
    wallet_address: str,
    *,
    review_status: ObservationExclusionReviewStatus = (
        ObservationExclusionReviewStatus.REVIEWED
    ),
    active: bool = True,
) -> MarketParticipantObservationExclusion:
    """제외 목록 항목을 만든다."""
    return MarketParticipantObservationExclusion(
        id=UUID(exclusion_id),
        wallet_address=wallet_address,
        reason="거래 참여자로 귀속할 수 없음",
        evidence_url="https://example.com/evidence",
        registered_at=datetime(2026, 8, 15, tzinfo=UTC),
        review_status=review_status,
        active=active,
    )


class TestMarketParticipantObservationService:
    """원본 보존과 관측 자격 필터를 함께 검증한다."""

    def test_returns_same_result_when_exclusion_list_is_empty(
        self, pg_session: Session
    ):
        """Given: 제외 목록이 비어 있고 원본 포지션만 있음
        When: 관측 자격 조회
        Then: 원본과 동일한 결과를 반환한다.
        """
        observed_at = datetime(2026, 8, 10, 5, 0, tzinfo=UTC)
        snapshot_repository = PgMarketParticipantSnapshotRepository(pg_session)
        snapshot_repository.save_bulk(
            [
                _position(
                    "018f0d3d-5b5a-7a3d-8b54-8f3c11a20f01",
                    ORDINARY_WALLET,
                    observed_at,
                )
            ]
        )
        exclusion_repository = PgMarketParticipantObservationExclusionRepository(
            pg_session
        )
        service = MarketParticipantObservationService(
            snapshot_repository=snapshot_repository,
            exclusion_repository=exclusion_repository,
        )

        result = service.list_observable_positions()

        assert [p.wallet_address for p in result] == [ORDINARY_WALLET]

    def test_excludes_only_active_reviewed_wallet_and_preserves_raw_row(
        self, pg_session: Session
    ):
        """Given: 활성·검토 완료 제외 지갑과 일반 지갑의 원본 포지션
        When: 관측 자격 조회
        Then: 제외 지갑만 결과에서 빠지고, 원본 행과 나머지 필드는 그대로다.
        """
        observed_at = datetime(2026, 8, 10, 5, 0, tzinfo=UTC)
        snapshot_repository = PgMarketParticipantSnapshotRepository(pg_session)
        snapshot_repository.save_bulk(
            [
                _position(
                    "018f0d3d-5b5a-7a3d-8b54-8f3c11a20f02",
                    WHALE_WALLET,
                    observed_at,
                ),
                _position(
                    "018f0d3d-5b5a-7a3d-8b54-8f3c11a20f03",
                    ORDINARY_WALLET,
                    observed_at,
                ),
            ]
        )
        exclusion_repository = PgMarketParticipantObservationExclusionRepository(
            pg_session
        )
        exclusion_repository.register_if_absent(
            [_exclusion("018f0d3d-5b5a-7a3d-8b54-8f3c11a20f10", WHALE_WALLET)]
        )
        service = MarketParticipantObservationService(
            snapshot_repository=snapshot_repository,
            exclusion_repository=exclusion_repository,
        )

        result = service.list_observable_positions()

        assert [p.wallet_address for p in result] == [ORDINARY_WALLET]
        remaining = result[0]
        assert remaining.market_id == "3438892"
        assert remaining.condition_id == "0xcondition"
        assert remaining.outcome_index == 1
        assert remaining.position_amount == 125.5
        assert remaining.timestamp == observed_at

        raw_rows = (
            pg_session.execute(select(MarketParticipantSnapshotRow))
            .scalars()
            .all()
        )
        assert {row.wallet_address for row in raw_rows} == {
            WHALE_WALLET,
            ORDINARY_WALLET,
        }

    def test_does_not_exclude_pending_or_inactive_wallets(
        self, pg_session: Session
    ):
        """Given: 검토 대기 후보 지갑과 비활성 제외 지갑의 원본 포지션
        When: 관측 자격 조회
        Then: 둘 다 결과에서 제거되지 않는다.
        """
        observed_at = datetime(2026, 8, 10, 5, 0, tzinfo=UTC)
        pending_wallet = "0x" + "c" * 40
        inactive_wallet = "0x" + "d" * 40
        snapshot_repository = PgMarketParticipantSnapshotRepository(pg_session)
        snapshot_repository.save_bulk(
            [
                _position(
                    "018f0d3d-5b5a-7a3d-8b54-8f3c11a20f04",
                    pending_wallet,
                    observed_at,
                ),
                _position(
                    "018f0d3d-5b5a-7a3d-8b54-8f3c11a20f05",
                    inactive_wallet,
                    observed_at,
                ),
            ]
        )
        exclusion_repository = PgMarketParticipantObservationExclusionRepository(
            pg_session
        )
        exclusion_repository.register_if_absent(
            [
                _exclusion(
                    "018f0d3d-5b5a-7a3d-8b54-8f3c11a20f11",
                    pending_wallet,
                    review_status=ObservationExclusionReviewStatus.PENDING,
                    active=False,
                ),
                _exclusion(
                    "018f0d3d-5b5a-7a3d-8b54-8f3c11a20f12",
                    inactive_wallet,
                    active=False,
                ),
            ]
        )
        service = MarketParticipantObservationService(
            snapshot_repository=snapshot_repository,
            exclusion_repository=exclusion_repository,
        )

        result = service.list_observable_positions()

        assert {p.wallet_address for p in result} == {
            pending_wallet,
            inactive_wallet,
        }

    def test_only_returns_latest_batch(self, pg_session: Session):
        """Given: 서로 다른 시각에 저장된 두 배치의 포지션
        When: 관측 자격 조회
        Then: 가장 최근 배치만 반환한다.
        """
        older = datetime(2026, 8, 10, 5, 0, tzinfo=UTC)
        latest = older + timedelta(minutes=5)
        snapshot_repository = PgMarketParticipantSnapshotRepository(pg_session)
        snapshot_repository.save_bulk(
            [
                _position(
                    "018f0d3d-5b5a-7a3d-8b54-8f3c11a20f06", ORDINARY_WALLET, older
                ),
                _position(
                    "018f0d3d-5b5a-7a3d-8b54-8f3c11a20f07", WHALE_WALLET, latest
                ),
            ]
        )
        exclusion_repository = PgMarketParticipantObservationExclusionRepository(
            pg_session
        )
        service = MarketParticipantObservationService(
            snapshot_repository=snapshot_repository,
            exclusion_repository=exclusion_repository,
        )

        result = service.list_observable_positions()

        assert [p.wallet_address for p in result] == [WHALE_WALLET]

    def test_includes_all_markets_from_the_same_batch(self, pg_session: Session):
        """Given: 서로 다른 두 마켓이 같은 실행에서 같은 timestamp 로 저장됨
        When: 관측 자격 조회
        Then: 두 마켓의 포지션이 모두 최신 배치로 반환된다.
        """
        observed_at = datetime(2026, 8, 10, 5, 0, tzinfo=UTC)
        snapshot_repository = PgMarketParticipantSnapshotRepository(pg_session)
        snapshot_repository.save_bulk(
            [
                _position(
                    "018f0d3d-5b5a-7a3d-8b54-8f3c11a20f08",
                    ORDINARY_WALLET,
                    observed_at,
                    market_id="3438892",
                    condition_id="0xcondition",
                ),
                _position(
                    "018f0d3d-5b5a-7a3d-8b54-8f3c11a20f09",
                    WHALE_WALLET,
                    observed_at,
                    market_id="9999999",
                    condition_id="0xothercondition",
                ),
            ]
        )
        exclusion_repository = PgMarketParticipantObservationExclusionRepository(
            pg_session
        )
        service = MarketParticipantObservationService(
            snapshot_repository=snapshot_repository,
            exclusion_repository=exclusion_repository,
        )

        result = service.list_observable_positions()

        assert {(p.market_id, p.wallet_address) for p in result} == {
            ("3438892", ORDINARY_WALLET),
            ("9999999", WHALE_WALLET),
        }
