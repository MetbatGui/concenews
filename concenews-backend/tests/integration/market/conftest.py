"""Market integration test fixtures."""
from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.shared_kernel.db.settings import get_database_url


@pytest.fixture(scope="module")
def pg_engine():
    """Test PG engine. Alembic upgrade 사전 필요."""
    engine = create_engine(get_database_url(), pool_pre_ping=True)
    yield engine
    engine.dispose()


@pytest.fixture
def pg_session(pg_engine) -> Iterator[Session]:
    """Transaction rollback 으로 test 간 격리."""
    connection = pg_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()
