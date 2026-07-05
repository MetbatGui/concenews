"""SQLAlchemy ORM base.

모든 ORM 모델은 이 Base 를 상속.
Alembic autogenerate 는 Base.metadata 를 참조.
상세: docs/decisions/2026-07-06-db-library.md
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for ORM models."""
