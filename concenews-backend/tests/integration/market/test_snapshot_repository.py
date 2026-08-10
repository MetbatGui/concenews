"""PgMarketSnapshotRepository 통합 테스트."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modules.market.domain.models import MarketSnapshot
from src.modules.market.infrastructure.orm import MarketSnapshotRow
from src.modules.market.infrastructure.repositories import PgMarketSnapshotRepository


def _make_snapshot(snapshot_id: UUID, timestamp: datetime) -> MarketSnapshot:
    """테스트용 MarketSnapshot을 만든다."""
    return MarketSnapshot(
        id=snapshot_id,
        market_id="market-1",
        condition_id="0xcondition",
        question="금리가 유지될까?",
        outcomes=("예", "아니오"),
        outcome_prices=(0.62, 0.38),
        last_price=0.62,
        best_bid=0.61,
        best_ask=0.63,
        spread=0.02,
        liquidity=12_000.0,
        volume_24h=8_000.0,
        volume_1w=40_000.0,
        volume_1m=120_000.0,
        end_date=datetime(2026, 9, 1, tzinfo=UTC),
        active=True,
        closed=False,
        timestamp=timestamp,
    )


class TestPgMarketSnapshotRepository:
    """실제 PostgreSQL market_snapshot 저장 계약."""

    def test_save_bulk_persists_two_times_for_same_market(self, pg_session: Session):
        """Given: 수집 시각이 다른 같은 마켓 스냅샷 두 건
        When: save_bulk
        Then: 두 행의 배열·숫자·시각이 모두 보존된다.
        """
        first_time = datetime(2026, 8, 10, 5, 0, tzinfo=UTC)
        second_time = first_time + timedelta(minutes=5)
        repository = PgMarketSnapshotRepository(pg_session)

        repository.save_bulk(
            [
                _make_snapshot(
                    UUID("018f0d3d-5b5a-7a3d-8b54-8f3c11a20d01"), first_time
                ),
                _make_snapshot(
                    UUID("018f0d3d-5b5b-7a3d-8b54-8f3c11a20d02"), second_time
                ),
            ]
        )

        rows = (
            pg_session.execute(
                select(MarketSnapshotRow).order_by(MarketSnapshotRow.timestamp)
            )
            .scalars()
            .all()
        )

        assert [row.market_id for row in rows] == ["market-1", "market-1"]
        assert [row.condition_id for row in rows] == ["0xcondition", "0xcondition"]
        assert [row.timestamp for row in rows] == [first_time, second_time]
        assert rows[0].outcomes == ["예", "아니오"]
        assert rows[0].outcome_prices == [0.62, 0.38]
        assert rows[0].volume_24h == 8_000.0

    def test_save_bulk_empty_list_is_noop(self, pg_session: Session):
        """Given: 빈 스냅샷 목록
        When: save_bulk
        Then: 행을 만들지 않고 정상 종료한다.
        """
        repository = PgMarketSnapshotRepository(pg_session)

        repository.save_bulk([])

        rows = pg_session.execute(select(MarketSnapshotRow)).scalars().all()
        assert rows == []
