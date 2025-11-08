"""add_consecutive_signal_fields

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2025-11-07 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TIMESTAMP


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add consecutive signal tracking fields
    op.add_column('portfolios', sa.Column('consecutive_bullish_count', sa.Integer(), server_default='0', nullable=False))
    op.add_column('portfolios', sa.Column('consecutive_bullish_since', TIMESTAMP(), nullable=True))
    op.add_column('portfolios', sa.Column('last_conviction_score', sa.Float(), nullable=True))

    # Add consecutive signal configuration fields
    op.add_column('portfolios', sa.Column('consecutive_signal_threshold', sa.Integer(), server_default='30', nullable=False))
    op.add_column('portfolios', sa.Column('acceleration_multiplier_min', sa.Float(), server_default='1.1', nullable=False))
    op.add_column('portfolios', sa.Column('acceleration_multiplier_max', sa.Float(), server_default='2.0', nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove consecutive signal fields
    op.drop_column('portfolios', 'acceleration_multiplier_max')
    op.drop_column('portfolios', 'acceleration_multiplier_min')
    op.drop_column('portfolios', 'consecutive_signal_threshold')
    op.drop_column('portfolios', 'last_conviction_score')
    op.drop_column('portfolios', 'consecutive_bullish_since')
    op.drop_column('portfolios', 'consecutive_bullish_count')
