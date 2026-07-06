"""News ORM 모델 (SQLAlchemy).

Domain (NewsItem, Pydantic frozen) 와 분리.
매핑은 postgres.py 의 _to_domain / _to_orm 함수가 담당.
"""
from datetime import datetime
from uuid import UUID

from sqlalchemy import ARRAY, String, Text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from src.shared_kernel.db.base import Base


class NewsRow(Base):
    """news 테이블 ORM 모델."""

    __tablename__ = "news"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    link: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    source: Mapped[str] = mapped_column(String, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    keywords: Mapped[str] = mapped_column(String, nullable=False, default="")
    categories: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
