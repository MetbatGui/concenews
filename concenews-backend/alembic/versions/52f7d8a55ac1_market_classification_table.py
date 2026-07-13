"""market_classification_table

Revision ID: 52f7d8a55ac1
Revises: 3e9fcf0f6d4e
Create Date: 2026-07-14 03:28:15.020001

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '52f7d8a55ac1'
down_revision: Union[str, Sequence[str], None] = '3e9fcf0f6d4e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'market_classification',
        sa.Column('condition_id', sa.String(), nullable=False),
        sa.Column('question', sa.String(), nullable=False),
        sa.Column('classification', sa.String(), nullable=False),
        sa.Column('tags_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('classified_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('condition_id'),
    )
    op.create_index('ix_market_classification_end_date', 'market_classification', ['end_date'], unique=False)
    op.create_index('ix_market_classification_type', 'market_classification', ['classification'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_market_classification_type', table_name='market_classification')
    op.drop_index('ix_market_classification_end_date', table_name='market_classification')
    op.drop_table('market_classification')
