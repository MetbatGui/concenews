"""Integration test — PgMarketClassificationRepository.

E2E 에서 이미 흐름 검증. 여기서는 Repository 단위 엣지 케이스.
"""
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from src.modules.market.domain.models import (
    Classification,
    MarketClassification,
    Tag,
)
from src.modules.market.infrastructure.repositories import (
    PgMarketClassificationRepository,
)


def _make_classification(
    condition_id: str,
    end_date: datetime,
    classification: Classification = Classification.MACRO,
) -> MarketClassification:
    """테스트용 MarketClassification 생성."""
    return MarketClassification(
        condition_id=condition_id,
        question=f"question for {condition_id}",
        classification=classification,
        tags=(Tag(id=159, label="Fed", slug="fed"),),
        end_date=end_date,
        classified_at=datetime.now(UTC),
    )


class TestFindActiveConditionIds:
    """find_active_condition_ids: end_date 기반 유효 캐시 조회."""

    def test_returns_empty_when_no_data(self, pg_session: Session):
        """Given: 빈 테이블
        When: find_active_condition_ids
        Then: 빈 set 반환.
        """
        repo = PgMarketClassificationRepository(pg_session)
        result = repo.find_active_condition_ids(datetime.now(UTC))
        assert result == set()

    def test_returns_only_unexpired_markets(self, pg_session: Session):
        """Given: 만료(과거) 1개 + 활성(미래) 2개
        When: now 기준 조회
        Then: 활성 2개만 반환.
        """
        now = datetime.now(UTC)
        past = now - timedelta(days=1)
        future = now + timedelta(days=30)

        repo = PgMarketClassificationRepository(pg_session)
        repo.save_bulk(
            [
                _make_classification("0xexpired", past),
                _make_classification("0xactive1", future),
                _make_classification("0xactive2", future),
            ]
        )

        result = repo.find_active_condition_ids(now)
        assert result == {"0xactive1", "0xactive2"}

    def test_end_date_equal_to_now_is_expired(self, pg_session: Session):
        """Given: end_date == now (경계)
        When: find_active_condition_ids
        Then: 만료 처리 (> 조건이므로 포함 안 됨).
        """
        now = datetime.now(UTC)
        repo = PgMarketClassificationRepository(pg_session)
        repo.save_bulk([_make_classification("0xboundary", now)])

        result = repo.find_active_condition_ids(now)
        assert result == set()


class TestSaveBulk:
    """save_bulk: upsert 저장."""

    def test_empty_list_is_noop(self, pg_session: Session):
        """Given: 빈 리스트
        When: save_bulk
        Then: 예외 없이 통과, DB 변경 없음.
        """
        repo = PgMarketClassificationRepository(pg_session)
        repo.save_bulk([])
        assert repo.find_active_condition_ids(datetime.now(UTC)) == set()

    def test_saves_multiple_classifications(self, pg_session: Session):
        """Given: 3개 분류 결과
        When: save_bulk
        Then: 3개 모두 저장됨.
        """
        future = datetime.now(UTC) + timedelta(days=30)
        repo = PgMarketClassificationRepository(pg_session)
        repo.save_bulk(
            [
                _make_classification("0xaaa", future),
                _make_classification("0xbbb", future),
                _make_classification("0xccc", future, Classification.NON_MACRO),
            ]
        )

        result = repo.find_active_condition_ids(datetime.now(UTC))
        assert result == {"0xaaa", "0xbbb", "0xccc"}

    def test_duplicate_condition_id_is_ignored(self, pg_session: Session):
        """Given: 이미 저장된 condition_id 재저장 시도
        When: save_bulk
        Then: ON CONFLICT DO NOTHING → 기존 데이터 유지, 예외 없음.
        """
        future = datetime.now(UTC) + timedelta(days=30)
        repo = PgMarketClassificationRepository(pg_session)
        repo.save_bulk([_make_classification("0xdup", future)])

        # Re-save with same condition_id
        repo.save_bulk([_make_classification("0xdup", future)])

        result = repo.find_active_condition_ids(datetime.now(UTC))
        assert result == {"0xdup"}
