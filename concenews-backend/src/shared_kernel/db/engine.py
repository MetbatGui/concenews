"""SQLAlchemy engine (module-level singleton).

상세: docs/decisions/2026-07-06-db-library.md
"""
from functools import lru_cache

from sqlalchemy import Engine, create_engine

from src.shared_kernel.db.settings import get_database_url

CONNECT_TIMEOUT_SECONDS = 5


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """앱 수명 동안 하나의 Engine 인스턴스 공유.

    Returns:
        SQLAlchemy Engine (pool_pre_ping=True 로 stale connection 자동 감지).
        connect_timeout 을 지정해 DB 가 응답하지 않을 때 OS 기본 TCP
        타임아웃에 기대어 무제한 대기하지 않는다.
    """
    return create_engine(
        get_database_url(),
        pool_pre_ping=True,
        connect_args={"connect_timeout": CONNECT_TIMEOUT_SECONDS},
    )
