"""SQLAlchemy Session provider (request-scoped via FastAPI Depends).

상세: docs/decisions/2026-07-06-db-library.md
"""
from collections.abc import Iterator

from sqlalchemy.orm import Session

from src.shared_kernel.db.engine import get_engine


def get_session() -> Iterator[Session]:
    """Session provider (request-scoped).

    FastAPI Depends 로 endpoint 에 주입.
    Context 종료 시 자동 rollback + close.

    Yields:
        SQLAlchemy Session.
    """
    with Session(get_engine()) as session:
        yield session
