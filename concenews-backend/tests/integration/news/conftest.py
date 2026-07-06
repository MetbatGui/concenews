"""News integration fixture.

testing.md: 모듈 전용 fixture 는 tests/integration/{module}/conftest.py.
Fixture data (constants) 는 data.py 에 별도.
Dependency override 정리는 tests/conftest.py autouse fixture 가 담당.
"""
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.main import app
from src.modules.news.bootstrap import get_repository
from src.modules.news.infrastructure.repositories.in_memory import InMemoryNewsRepository
from src.shared_kernel.db.settings import get_database_url

from tests.integration.news.data import NEWS_MID, NEWS_NEW, NEWS_OLD


@pytest.fixture
def filled_repository() -> InMemoryNewsRepository:
    """3개 news 를 pre-populate 한 저장소 (Object Mother 상수).

    published_at 이 서로 다름 (정렬 검증용).

    Returns:
        InMemoryNewsRepository (NEWS_OLD, NEWS_MID, NEWS_NEW).
    """
    return InMemoryNewsRepository(initial=[NEWS_OLD, NEWS_MID, NEWS_NEW])


@pytest.fixture
def filled_client(filled_repository: InMemoryNewsRepository) -> TestClient:
    """filled_repository 를 DI 로 주입한 TestClient.

    Args:
        filled_repository: 3개 news 저장된 저장소.

    Returns:
        TestClient. dependency_overrides 정리는 autouse teardown 이 담당.
    """
    app.dependency_overrides[get_repository] = lambda: filled_repository
    return TestClient(app)


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
