"""프로젝트 전역 test 설정.

Autouse fixture 로 module-level singleton (lru_cache) 자동 clear.
상세: docs/decisions/2026-07-05-test-isolation-cache-clear.md
"""
import pytest

from src.modules.news.bootstrap import get_repository


@pytest.fixture(autouse=True)
def _clear_singleton_cache():
    """매 test 후 module-level lru_cache 자동 clear (test 간 상태 격리)."""
    yield
    get_repository.cache_clear()
