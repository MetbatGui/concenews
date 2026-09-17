"""Integration test — Kalshi 마켓 소스 Walking Skeleton.

KalshiMarketSourcePort(fetch_active_markets → fetch_categories_bulk)와
classify_by_category()가 끊기지 않고 이어지는지 검증한다. 저장(Repository)
연결은 이 Slice 범위 밖 — 분류 결과 확인까지가 끝이다.

기존 Polymarket 흐름(test_classifier_integration.py)과는 완전히 별개이며,
이 파일 추가가 그 흐름에 영향을 주지 않는다.
"""
from datetime import UTC, datetime, timedelta

import pytest

from src.modules.market.domain.classifier import classify_by_category
from src.modules.market.domain.models import KalshiMarketMetadata


class _FakeKalshiSource:
    """KalshiMarketSourcePort 테스트용 구현 (하드코딩 응답)."""

    def __init__(
        self,
        markets: list[KalshiMarketMetadata],
        category_map: dict[str, str],
    ) -> None:
        self._markets = markets
        self._category_map = category_map
        self.fetch_active_markets_calls: list[int] = []
        self.fetch_categories_bulk_calls: list[list[str]] = []

    async def fetch_active_markets(self, limit: int) -> list[KalshiMarketMetadata]:
        self.fetch_active_markets_calls.append(limit)
        return list(self._markets)

    async def fetch_categories_bulk(self, series_ids: list[str]) -> dict[str, str]:
        self.fetch_categories_bulk_calls.append(list(series_ids))
        return {
            series_id: self._category_map[series_id]
            for series_id in series_ids
            if series_id in self._category_map
        }


class TestKalshiMarketSourceWalkingSkeleton:
    """Fake source → fetch_categories_bulk → classify_by_category 흐름."""

    @pytest.mark.asyncio
    async def test_flow_reaches_classify_by_category_without_breaking(self):
        """Given: Fake Kalshi source (마켓 1개 + 카테고리 매핑)
        When: fetch_active_markets → fetch_categories_bulk → classify_by_category
        Then: 흐름이 끊기지 않고 Classification 결과(placeholder라 None)까지 도달한다.
        """
        future = datetime.now(UTC) + timedelta(days=30)
        market = KalshiMarketMetadata(
            market_id="KXFEDDECISION-26",
            series_id="KXFEDDECISION",
            question="Will the Fed cut rates?",
            end_date=future,
        )
        source = _FakeKalshiSource(
            markets=[market],
            category_map={"KXFEDDECISION": "Economics"},
        )

        markets = await source.fetch_active_markets(limit=500)
        category_map = await source.fetch_categories_bulk(
            [m.series_id for m in markets]
        )
        result = classify_by_category({category_map[market.series_id]})

        assert source.fetch_active_markets_calls == [500]
        assert source.fetch_categories_bulk_calls == [["KXFEDDECISION"]]
        assert category_map == {"KXFEDDECISION": "Economics"}
        # placeholder 상수(빈 집합)라 현재는 항상 None — 실제 매핑은 별도 Task.
        assert result is None

    @pytest.mark.asyncio
    async def test_missing_category_mapping_is_skipped_not_errored(self):
        """Given: series_id에 대응하는 카테고리가 없는 마켓
        When: fetch_categories_bulk
        Then: 매핑 없는 series_id는 결과 dict에서 빠지고 예외가 나지 않는다.
        """
        source = _FakeKalshiSource(markets=[], category_map={})

        result = await source.fetch_categories_bulk(["KXUNKNOWN"])

        assert result == {}
