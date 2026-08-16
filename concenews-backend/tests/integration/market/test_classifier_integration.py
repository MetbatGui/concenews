"""Integration test — 매크로 마켓 분류 슬라이스.

Walking Skeleton 검증: Fake source → Service → PG Repository → DB 저장 흐름.
각 후속 PR (Domain, Repository, Adapter, Service, Scheduler)는 이 테스트를 계속 GREEN 유지.
"""
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modules.market.bootstrap import register_market_classifier_job
from src.modules.market.application.services import MarketClassifierService
from src.modules.market.domain.models import MarketMetadata, Tag
from src.modules.market.infrastructure.orm import MarketClassificationRow
from src.modules.market.infrastructure.repositories import (
    PgMarketClassificationRepository,
)
from src.shared_kernel.scheduler import AsyncioSchedulerAdapter


class _FakeSource:
    """MarketSourcePort 테스트용 구현 (하드코딩 응답)."""

    def __init__(
        self,
        markets: list[MarketMetadata],
        tag_map: dict[str, list[Tag]],
    ) -> None:
        self._markets = markets
        self._tag_map = tag_map
        self.closed = False
        self.fetch_active_markets_calls: list[dict] = []
        self.fetch_tags_bulk_calls: list[list[str]] = []

    async def fetch_active_markets(
        self, limit: int, order: str, ascending: bool
    ) -> list[MarketMetadata]:
        self.fetch_active_markets_calls.append(
            {"limit": limit, "order": order, "ascending": ascending}
        )
        return list(self._markets)

    async def fetch_tags_bulk(
        self, condition_ids: list[str]
    ) -> dict[str, list[Tag]]:
        self.fetch_tags_bulk_calls.append(list(condition_ids))
        return {cid: self._tag_map.get(cid, []) for cid in condition_ids}

    async def aclose(self) -> None:
        """Scheduler가 외부 경계 자원을 정리했는지 기록한다."""
        self.closed = True


def _make_macro_market(index: int, end_date):
    """태그 rate limit 배치 테스트용 MACRO 마켓 하나를 만든다."""
    condition_id = f"0xmarket{index:04d}"
    market = MarketMetadata(
        condition_id=condition_id, question=f"Market {index}?", end_date=end_date
    )
    tag = Tag(id=159, label="Fed", slug="fed")
    return market, tag


class TestClassifierIntegration:
    """Walking Skeleton Integration: Fake source → PG repository → DB 저장."""

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

    @pytest.mark.asyncio
    async def test_fetches_top_500_market_list(self, pg_session: Session):
        """Given: Fake source
        When: run()
        Then: 마켓 목록 조회는 상위 500개를 요청한다 (AC2).
        """
        source = _FakeSource(markets=[], tag_map={})
        repository = PgMarketClassificationRepository(pg_session)
        service = MarketClassifierService(source=source, repository=repository)

        await service.run()

        assert source.fetch_active_markets_calls == [
            {"limit": 500, "order": "volume24hr", "ascending": False}
        ]

    @pytest.mark.asyncio
    async def test_caps_new_markets_processed_per_run(self, pg_session: Session):
        """Given: rate limit 안전 배치 크기(100)를 초과하는 신규 마켓 150개
        When: run() 을 두 번 호출 (콜드스타트 후 다음 주기 시뮬레이션)
        Then: 첫 run() 은 최대 100개만 태그 조회·저장하고, 두 번째 run() 이
            나머지를 처리해 두 번 합쳐 150개 전부 저장된다.
        """
        future = datetime.now(UTC) + timedelta(days=30)
        markets_and_tags = [_make_macro_market(i, future) for i in range(150)]
        markets = [m for m, _ in markets_and_tags]
        tag_map = {m.condition_id: [t] for m, t in markets_and_tags}
        source = _FakeSource(markets=markets, tag_map=tag_map)
        repository = PgMarketClassificationRepository(pg_session)
        service = MarketClassifierService(source=source, repository=repository)

        await service.run()

        rows_after_first = (
            pg_session.execute(select(MarketClassificationRow)).scalars().all()
        )
        assert len(rows_after_first) == 100
        assert len(source.fetch_tags_bulk_calls[0]) == 100

        await service.run()

        rows_after_second = (
            pg_session.execute(select(MarketClassificationRow)).scalars().all()
        )
        assert len(rows_after_second) == 150
        assert len(source.fetch_tags_bulk_calls[1]) == 50

    @pytest.mark.asyncio
    async def test_registered_job_uses_own_session_and_closes_external_source(
        self, pg_session: Session
    ):
        """등록된 작업은 실제 DB에 저장하고 매 실행 자원을 정리한다."""
        future = datetime.now(UTC) + timedelta(days=30)
        source = _FakeSource(
            markets=[
                MarketMetadata(
                    condition_id="0xjob",
                    question="Will Fed cut rates in 2026?",
                    end_date=future,
                )
            ],
            tag_map={"0xjob": [Tag(id=159, label="Fed", slug="fed")]},
        )
        scheduler = AsyncioSchedulerAdapter()
        created_sessions: list[Session] = []

        class TrackingSession(Session):
            """작업 전용 Session 종료 여부를 관찰한다."""

            def __init__(self, **kwargs) -> None:
                super().__init__(**kwargs)
                self.closed_by_job = False

            def close(self) -> None:
                self.closed_by_job = True
                super().close()

        def create_session() -> Session:
            session = TrackingSession(bind=pg_session.connection())
            created_sessions.append(session)
            return session

        register_market_classifier_job(
            scheduler,
            session_factory=create_session,
            source_factory=lambda: source,
        )

        await scheduler.trigger_all()

        rows = pg_session.execute(select(MarketClassificationRow)).scalars().all()
        assert {row.condition_id for row in rows} == {"0xjob"}
        assert len(created_sessions) == 1
        assert source.closed
        assert created_sessions[0].closed_by_job


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
