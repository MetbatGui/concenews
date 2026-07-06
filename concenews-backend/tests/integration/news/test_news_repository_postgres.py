"""PgNewsRepository integration tests (실 PG + transaction rollback).

testing.md: DB 관용 (transaction rollback) 으로 test 격리.
상세: docs/decisions/2026-07-06-repository-strategy.md
"""
from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.modules.news.infrastructure.repositories.postgres import PgNewsRepository
from src.shared_kernel.db.settings import get_database_url

from tests.integration.news.data import NEWS_MID, NEWS_NEW, NEWS_OLD


@pytest.fixture(scope="module")
def pg_engine():
    """Test PG engine (5433). Alembic upgrade 사전 필요."""
    engine = create_engine(get_database_url(), pool_pre_ping=True)
    yield engine
    engine.dispose()


@pytest.fixture
def pg_session(pg_engine) -> Iterator[Session]:
    """Transaction rollback 으로 test 간 격리.

    각 test 는 자체 transaction 안에서 실행 → 종료 시 rollback.
    """
    connection = pg_engine.connect()
    trans = connection.begin()
    session = Session(bind=connection)
    try:
        yield session
    finally:
        session.close()
        trans.rollback()
        connection.close()


class TestPgNewsRepository:
    """PgNewsRepository 실 PG state-based 검증."""

    def test_save_and_find_all_persists_item(self, pg_session):
        """save 후 find_all 에 아이템 나타남.

        Given: 빈 news 테이블
        When: NEWS_NEW save
        Then: find_all 이 NEWS_NEW 반환
        """
        repo = PgNewsRepository(session=pg_session)

        repo.save(NEWS_NEW)

        result = repo.find_all()
        assert len(result) == 1
        assert result[0].id == NEWS_NEW.id
        assert result[0].title == NEWS_NEW.title
        assert result[0].link == NEWS_NEW.link

    def test_save_multiple_items(self, pg_session):
        """여러 items 저장 시 모두 반환.

        Given: 빈 테이블
        When: NEWS_OLD, MID, NEW 저장
        Then: find_all 이 3개 반환
        """
        repo = PgNewsRepository(session=pg_session)

        for item in [NEWS_OLD, NEWS_MID, NEWS_NEW]:
            repo.save(item)

        result = repo.find_all()
        assert len(result) == 3
        assert {r.id for r in result} == {NEWS_OLD.id, NEWS_MID.id, NEWS_NEW.id}

    def test_save_same_id_updates(self, pg_session):
        """같은 id 로 save 시 update.

        Given: NEWS_NEW 저장
        When: 같은 id, 다른 title 로 재저장
        Then: find_all 은 1개, title 은 새 값
        """
        repo = PgNewsRepository(session=pg_session)
        original = NEWS_NEW
        updated = NEWS_NEW.model_copy(update={"title": "갱신된 제목"})

        repo.save(original)
        repo.save(updated)

        result = repo.find_all()
        assert len(result) == 1
        assert result[0].title == "갱신된 제목"

    def test_find_all_empty_returns_empty_list(self, pg_session):
        """빈 테이블 → 빈 리스트.

        Given: 빈 news 테이블
        When: find_all
        Then: []
        """
        repo = PgNewsRepository(session=pg_session)

        assert repo.find_all() == []

    def test_categories_roundtrip_as_tuple(self, pg_session):
        """Domain tuple → PG ARRAY → Domain tuple 변환.

        Given: NEWS_NEW 저장 (categories 는 tuple, 지금 빈 tuple)
        When: find_all 후 categories 접근
        Then: tuple 타입 유지 (list 아님)
        """
        repo = PgNewsRepository(session=pg_session)

        repo.save(NEWS_NEW)

        [result_item] = repo.find_all()
        assert isinstance(result_item.categories, tuple)
