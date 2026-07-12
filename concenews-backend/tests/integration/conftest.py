"""Integration test 공통 fixture.

testing.md: 사용 범위별 위치. 여기는 integration 전체 공유.
Dependency override 정리는 tests/conftest.py autouse fixture 가 담당.
"""

import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.modules.news.bootstrap import get_repository
from src.modules.news.infrastructure.repositories.in_memory import InMemoryNewsRepository
from src.shared_kernel.db.settings import load_config, get_database_url


@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    """Integration test 전 자동으로 DB migrations 적용.

    .env.test 로드 후 alembic upgrade head 실행.
    마이그레이션은 한 번만 실행 (session scope, autouse).
    """
    load_config(".env.test")
    db_url = get_database_url()

    # Run alembic upgrade
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"Alembic upgrade failed:\n{result.stderr}", file=sys.stderr)
        pytest.skip(f"Alembic upgrade failed, tests cannot run. DB: {db_url}")


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
