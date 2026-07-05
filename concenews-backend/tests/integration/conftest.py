"""Integration test 공통 fixture.

testing.md: 사용 범위별 위치. 여기는 integration 전체 공유.
Sub-fixture (모듈 별) 는 tests/integration/{module}/conftest.py 에 위치.
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.modules.news.bootstrap import get_repository
from src.modules.news.infrastructure.repositories import InMemoryNewsRepository


@pytest.fixture
def empty_repository() -> InMemoryNewsRepository:
    """빈 InMemoryNewsRepository."""
    return InMemoryNewsRepository()


@pytest.fixture
def client(empty_repository: InMemoryNewsRepository) -> TestClient:
    """FastAPI TestClient — 기본 empty repository 주입.

    Args:
        empty_repository: 빈 저장소 fixture.

    Yields:
        TestClient. 종료 시 dependency override 정리.
    """
    app.dependency_overrides[get_repository] = lambda: empty_repository
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
