"""Integration test for market_snapshot migration.

목적: market_snapshot 테이블이 올바르게 생성되었는지 검증.
로직 없는 schema 검증이므로 최소 테스트.
상세: docs/decisions/2026-07-12-polymarket-api-choice.md

주: 마이그레이션은 app startup 시 alembic upgrade head 로 자동 실행되어야 함.
이 테스트는 마이그레이션 후 schema 가 올바름을 smoke-test.
"""

import pytest
from sqlalchemy import create_engine, inspect

from src.shared_kernel.db.settings import get_database_url


@pytest.fixture(scope="module")
def engine():
    """Main DB engine (no transaction wrapping for DDL verification)."""
    eng = create_engine(get_database_url(), pool_pre_ping=True)
    yield eng
    eng.dispose()


class TestMarketSnapshotMigration:
    """market_snapshot 테이블 schema 검증."""

    def test_market_snapshot_table_created(self, engine):
        """market_snapshot 테이블이 생성됨.

        Given: DB migration 완료 (alembic upgrade head)
        When: 테이블 목록 조회
        Then: market_snapshot 존재
        """
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        assert 'market_snapshot' in tables

    def test_market_snapshot_table_columns(self, engine):
        """market_snapshot 테이블이 필수 컬럼 보유.

        Given: market_snapshot 테이블 생성됨
        When: 컬럼 목록 조회
        Then: 필수 컬럼 18개 존재
        """
        inspector = inspect(engine)
        columns = {col['name']: col for col in inspector.get_columns('market_snapshot')}

        expected_columns = {
            'id', 'market_id', 'question', 'outcomes', 'outcome_prices',
            'last_price', 'best_bid', 'best_ask', 'spread', 'liquidity',
            'volume_24h', 'volume_1w', 'volume_1m', 'end_date',
            'active', 'closed', 'timestamp', 'created_at'
        }

        actual_columns = set(columns.keys())
        assert expected_columns == actual_columns

    def test_market_snapshot_table_indexes(self, engine):
        """market_snapshot 테이블이 필수 인덱스 보유.

        Given: market_snapshot 테이블 생성됨
        When: 인덱스 목록 조회
        Then: 3개 인덱스 (market_id, timestamp, market_id+timestamp) 존재
        """
        inspector = inspect(engine)
        indexes = inspector.get_indexes('market_snapshot')
        index_names = {idx['name'] for idx in indexes}

        expected_indexes = {
            'ix_market_snapshot_market_id',
            'ix_market_snapshot_timestamp',
            'ix_market_snapshot_market_time'
        }

        assert expected_indexes.issubset(index_names)
