"""SQLAlchemy engine (module-level singleton).

상세: docs/decisions/2026-07-06-db-library.md
"""
from functools import lru_cache

from sqlalchemy import Engine, create_engine

from src.shared_kernel.db.settings import get_database_url


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """앱 수명 동안 하나의 Engine 인스턴스 공유.

    Returns:
        SQLAlchemy Engine (pool_pre_ping=True 로 stale connection 자동 감지).
    """
    return create_engine(get_database_url(), pool_pre_ping=True)
