"""프로젝트 전역 test 설정.

Autouse fixture 로 module-level singleton + FastAPI dependency_overrides 자동 정리.
상세: docs/decisions/2026-07-05-test-isolation-cache-clear.md
"""
import pytest

from src.main import app
from src.modules.news.bootstrap import get_repository


@pytest.fixture(autouse=True)
def _clear_test_state():
    """매 test 후 module-level singleton + dependency_overrides 자동 정리.

    - lru_cache: 다음 test 가 stale 인스턴스 만나지 않도록 clear.
    - dependency_overrides: test 가 예외 발생해도 override 잔존 방지.
    """
    yield
    get_repository.cache_clear()
    app.dependency_overrides.clear()
