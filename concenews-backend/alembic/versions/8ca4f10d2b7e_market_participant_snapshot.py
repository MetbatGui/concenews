"""market_participant_snapshot

Revision ID: 8ca4f10d2b7e
Revises: 52f7d8a55ac1
Create Date: 2026-08-10 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8ca4f10d2b7e"
down_revision: Union[str, Sequence[str], None] = "52f7d8a55ac1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """참여자 스냅샷 테이블과 마켓 condition ID를 추가한다."""
    op.add_column(
        "market_snapshot", sa.Column("condition_id", sa.String(), nullable=True)
    )
    op.create_index(
        "ix_market_snapshot_condition_id",
        "market_snapshot",
        ["condition_id"],
        unique=False,
    )
    op.create_table(
        "market_participant_snapshot",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("market_id", sa.String(), nullable=False),
        sa.Column("condition_id", sa.String(), nullable=False),
        sa.Column("wallet_address", sa.String(), nullable=False),
        sa.Column("outcome_index", sa.Integer(), nullable=False),
        sa.Column("position_amount", sa.Numeric(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_market_participant_snapshot_market_time",
        "market_participant_snapshot",
        ["market_id", "timestamp"],
        unique=False,
    )
    op.create_index(
        "ix_market_participant_snapshot_wallet_time",
        "market_participant_snapshot",
        ["wallet_address", "timestamp"],
        unique=False,
    )


def downgrade() -> None:
    """참여자 스냅샷 스키마를 제거한다."""
    op.drop_index(
        "ix_market_participant_snapshot_wallet_time",
        table_name="market_participant_snapshot",
    )
    op.drop_index(
        "ix_market_participant_snapshot_market_time",
        table_name="market_participant_snapshot",
    )
    op.drop_table("market_participant_snapshot")
    op.drop_index("ix_market_snapshot_condition_id", table_name="market_snapshot")
    op.drop_column("market_snapshot", "condition_id")
