"""E2E acceptance test — 매크로 마켓 분류 슬라이스.

Walking Skeleton 검증: Fake source → Service → PG Repository → DB 저장 흐름.
각 후속 PR (Domain, Repository, Adapter, Service, Scheduler)는 이 테스트를 계속 GREEN 유지.
"""
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modules.market.application.services import MarketClassifierService
from src.modules.market.domain.models import MarketMetadata, Tag
from src.modules.market.infrastructure.orm import MarketClassificationRow
from src.modules.market.infrastructure.repositories import (
    PgMarketClassificationRepository,
)


class _FakeSource:
    """MarketSourcePort 테스트용 구현 (하드코딩 응답)."""

    def __init__(
        self,
        markets: list[MarketMetadata],
        tag_map: dict[str, list[Tag]],
    ) -> None:
        self._markets = markets
        self._tag_map = tag_map

    async def fetch_active_markets(
        self, limit: int, order: str, ascending: bool
    ) -> list[MarketMetadata]:
        del limit, order, ascending
        return list(self._markets)

    async def fetch_tags_bulk(
        self, condition_ids: list[str]
    ) -> dict[str, list[Tag]]:
        return {cid: self._tag_map.get(cid, []) for cid in condition_ids}


class TestClassifierE2E:
    """Walking Skeleton E2E: Fake source → PG repository → DB 저장."""

    @pytest.mark.asyncio
    async def test_run_saves_classified_markets_to_db(self, pg_session: Session):
        """Given: Fake source (2개 마켓 + 태그)
        When: MarketClassifierService.run()
        Then: DB에 2개 market_classification 저장.
        """
        future = datetime.now(UTC) + timedelta(days=30)
        markets = [
            MarketMetadata(
                condition_id="0xaaa",
                question="Will Fed cut rates in 2026?",
                end_date=future,
            ),
            MarketMetadata(
                condition_id="0xbbb",
                question="Will Bitcoin hit $150k?",
                end_date=future,
            ),
        ]
        tag_map = {
            "0xaaa": [Tag(id=159, label="Fed", slug="fed")],
            "0xbbb": [Tag(id=235, label="Bitcoin", slug="bitcoin")],
        }
        source = _FakeSource(markets=markets, tag_map=tag_map)
        repository = PgMarketClassificationRepository(pg_session)
        service = MarketClassifierService(source=source, repository=repository)

        await service.run()

        rows = pg_session.execute(select(MarketClassificationRow)).scalars().all()
        saved_ids = {r.condition_id for r in rows}
        assert saved_ids == {"0xaaa", "0xbbb"}
        assert all(r.classification == "MACRO" for r in rows)

    @pytest.mark.asyncio
    async def test_run_skips_cached_markets(self, pg_session: Session):
        """Given: 이미 캐시된 마켓 1개 + 신규 1개
        When: run()
        Then: 신규만 태그 조회/저장, 캐시된 것은 스킵.
        """
        future = datetime.now(UTC) + timedelta(days=30)
        markets = [
            MarketMetadata(
                condition_id="0xcached",
                question="Cached market",
                end_date=future,
            ),
            MarketMetadata(
                condition_id="0xnew",
                question="New market",
                end_date=future,
            ),
        ]
        tag_map = {
            "0xcached": [Tag(id=159, label="Fed", slug="fed")],
            "0xnew": [Tag(id=235, label="Bitcoin", slug="bitcoin")],
        }
        # Pre-populate cache
        pre_repo = PgMarketClassificationRepository(pg_session)
        pre_repo.save_bulk(
            [
                _make_classification(
                    condition_id="0xcached",
                    question="Cached market",
                    end_date=future,
                    tags=(Tag(id=159, label="Fed", slug="fed"),),
                )
            ]
        )

        source = _FakeSource(markets=markets, tag_map=tag_map)
        repository = PgMarketClassificationRepository(pg_session)
        service = MarketClassifierService(source=source, repository=repository)

        await service.run()

        rows = pg_session.execute(select(MarketClassificationRow)).scalars().all()
        saved_ids = {r.condition_id for r in rows}
        assert saved_ids == {"0xcached", "0xnew"}


def _make_classification(condition_id, question, end_date, tags):
    from src.modules.market.domain.models import Classification, MarketClassification

    return MarketClassification(
        condition_id=condition_id,
        question=question,
        classification=Classification.MACRO,
        tags=tags,
        end_date=end_date,
        classified_at=datetime.now(UTC),
    )
