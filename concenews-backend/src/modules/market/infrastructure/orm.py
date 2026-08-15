"""SQLAlchemy ORM 정의 — market_classification 테이블."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import ARRAY, Boolean, DateTime, Float, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID
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


class MarketSnapshotRow(Base):
    """market_snapshot 테이블 ORM."""

    __tablename__ = "market_snapshot"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    market_id: Mapped[str] = mapped_column(String, nullable=False)
    condition_id: Mapped[str | None] = mapped_column(String, nullable=True)
    question: Mapped[str] = mapped_column(String, nullable=False)
    outcomes: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    outcome_prices: Mapped[list[float]] = mapped_column(ARRAY(Float), nullable=False)
    last_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    best_bid: Mapped[float | None] = mapped_column(Float, nullable=True)
    best_ask: Mapped[float | None] = mapped_column(Float, nullable=True)
    spread: Mapped[float | None] = mapped_column(Float, nullable=True)
    liquidity: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume_24h: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume_1w: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume_1m: Mapped[float | None] = mapped_column(Float, nullable=True)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    closed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MarketParticipantObservationExclusionRow(Base):
    """market_participant_observation_exclusion 테이블 ORM."""

    __tablename__ = "market_participant_observation_exclusion"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    wallet_address: Mapped[str] = mapped_column(String, nullable=False)
    reason: Mapped[str] = mapped_column(String, nullable=False)
    evidence_url: Mapped[str] = mapped_column(String, nullable=False)
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    review_status: Mapped[str] = mapped_column(String, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False)


class MarketParticipantSnapshotRow(Base):
    """market_participant_snapshot 테이블 ORM."""

    __tablename__ = "market_participant_snapshot"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    market_id: Mapped[str] = mapped_column(String, nullable=False)
    condition_id: Mapped[str] = mapped_column(String, nullable=False)
    wallet_address: Mapped[str] = mapped_column(String, nullable=False)
    outcome_index: Mapped[int] = mapped_column(Integer, nullable=False)
    position_amount: Mapped[float] = mapped_column(Numeric, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
