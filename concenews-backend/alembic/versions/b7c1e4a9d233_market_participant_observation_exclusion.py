"""market_participant_observation_exclusion

Revision ID: b7c1e4a9d233
Revises: 8ca4f10d2b7e
Create Date: 2026-08-16 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7c1e4a9d233"
down_revision: Union[str, Sequence[str], None] = "8ca4f10d2b7e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """참여자 관측 제외 목록 테이블을 추가한다."""
    op.create_table(
        "market_participant_observation_exclusion",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("wallet_address", sa.String(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("evidence_url", sa.String(), nullable=False),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("review_status", sa.String(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_observation_exclusion_active_wallet",
        "market_participant_observation_exclusion",
        ["wallet_address"],
        unique=True,
        postgresql_where=sa.text("active"),
    )


def downgrade() -> None:
    """참여자 관측 제외 목록 스키마를 제거한다."""
    op.drop_index(
        "uq_observation_exclusion_active_wallet",
        table_name="market_participant_observation_exclusion",
    )
    op.drop_table("market_participant_observation_exclusion")
