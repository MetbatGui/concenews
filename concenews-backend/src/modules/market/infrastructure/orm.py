"""SQLAlchemy ORM 정의 — market_classification 테이블."""
from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.shared_kernel.db.base import Base


class MarketClassificationRow(Base):
    """market_classification 테이블 ORM.

    Attributes:
        condition_id: Polymarket condition ID (Primary Key).
        question: 마켓 질문 텍스트.
        classification: 분류 결과 ('MACRO' 또는 'NON_MACRO').
        tags_json: 분류에 사용된 태그 리스트 (JSONB).
        end_date: 마켓 종료일. 캐시 만료 기준 (WHERE end_date > NOW()).
        classified_at: 분류 시각.
    """

    __tablename__ = "market_classification"

    condition_id: Mapped[str] = mapped_column(String, primary_key=True)
    question: Mapped[str] = mapped_column(String, nullable=False)
    classification: Mapped[str] = mapped_column(String, nullable=False)
    tags_json: Mapped[list] = mapped_column(JSONB, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    classified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
