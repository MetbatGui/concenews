"""Integration test 공통 fixture.

testing.md: 사용 범위별 위치. 여기는 integration 전체 공유.
Dependency override 정리는 tests/conftest.py autouse fixture 가 담당.
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.modules.news.bootstrap import get_repository
from src.modules.news.infrastructure.repositories.in_memory import InMemoryNewsRepository


@pytest.fixture
def empty_repository() -> InMemoryNewsRepository:
    """빈 InMemoryNewsRepository."""
    return InMemoryNewsRepository()


@pytest.fixture
def client(empty_repository: InMemoryNewsRepository) -> TestClient:
    """FastAPI TestClient — 기본 empty repository 주입.

    Args:
        empty_repository: 빈 저장소 fixture.

    Returns:
        TestClient. dependency_overrides 정리는 autouse teardown 이 담당.
    """
    app.dependency_overrides[get_repository] = lambda: empty_repository
    return TestClient(app)
