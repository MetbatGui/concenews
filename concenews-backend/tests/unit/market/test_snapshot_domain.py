"""마켓 스냅샷 Domain 모델 테스트."""

from datetime import UTC, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from src.modules.market.domain.models import MarketSnapshot


def _make_snapshot(**overrides: object) -> MarketSnapshot:
    """유효한 MarketSnapshot 테스트 데이터를 만든다."""
    values: dict[str, object] = {
        "id": UUID("018f0d3d-5b5a-7a3d-8b54-8f3c11a20d01"),
        "market_id": "market-1",
        "condition_id": "0xcondition",
        "question": "금리가 유지될까?",
        "outcomes": ["예", "아니오"],
        "outcome_prices": [0.62, 0.38],
        "last_price": 0.62,
        "best_bid": 0.61,
        "best_ask": 0.63,
        "spread": 0.02,
        "liquidity": 12_000.0,
        "volume_24h": 8_000.0,
        "volume_1w": 40_000.0,
        "volume_1m": 120_000.0,
        "end_date": datetime(2026, 9, 1, tzinfo=UTC),
        "active": True,
        "closed": False,
        "timestamp": datetime(2026, 8, 10, 5, 0, tzinfo=UTC),
    }
    values.update(overrides)
    return MarketSnapshot(**values)


class TestMarketSnapshot:
    """MarketSnapshot 불변성 및 입력 계약."""

    def test_collections_are_stored_as_tuples(self):
        """Given: list 형태의 결과 이름과 확률
        When: MarketSnapshot 생성
        Then: immutable tuple로 변환된다.
        """
        snapshot = _make_snapshot()

        assert snapshot.outcomes == ("예", "아니오")
        assert snapshot.outcome_prices == (0.62, 0.38)
        assert isinstance(snapshot.outcomes, tuple)
        assert isinstance(snapshot.outcome_prices, tuple)

    def test_rejects_attribute_reassignment(self):
        """Given: 생성된 스냅샷
        When: market_id를 재할당
        Then: frozen Domain 모델이 ValidationError를 낸다.
        """
        snapshot = _make_snapshot()

        with pytest.raises(ValidationError):
            snapshot.market_id = "other-market"  # type: ignore[misc]

    def test_rejects_naive_timestamp(self):
        """Given: timezone 정보가 없는 수집 시각
        When: MarketSnapshot 생성
        Then: UTC 인지 시각 계약 위반으로 ValidationError를 낸다.
        """
        with pytest.raises(ValidationError):
            _make_snapshot(timestamp=datetime(2026, 8, 10, 5, 0))

    def test_rejects_mismatched_outcomes_and_prices(self):
        """Given: 결과 이름과 확률의 개수가 다른 입력
        When: MarketSnapshot 생성
        Then: 결과별 확률 대응 계약 위반으로 ValidationError를 낸다.
        """
        with pytest.raises(ValidationError):
            _make_snapshot(outcome_prices=[0.62])

    @pytest.mark.parametrize("price", [-0.01, 1.01])
    def test_rejects_probability_outside_zero_to_one(self, price: float):
        """Given: 0~1 범위를 벗어난 결과별 확률
        When: MarketSnapshot 생성
        Then: 확률 범위 계약 위반으로 ValidationError를 낸다.
        """
        with pytest.raises(ValidationError):
            _make_snapshot(outcome_prices=[price, 0.38])

    def test_rejects_empty_outcomes(self):
        """Given: 결과와 확률이 모두 비어 있는 입력
        When: MarketSnapshot 생성
        Then: 최소 한 결과가 필요하므로 ValidationError를 낸다.
        """
        with pytest.raises(ValidationError):
            _make_snapshot(outcomes=[], outcome_prices=[])
