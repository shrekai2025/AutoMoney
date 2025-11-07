"""add_rebalance_period_to_portfolio

Revision ID: 44b097e75c19
Revises: 45a7e756d0a8
Create Date: 2025-11-07 00:13:20.996653

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '44b097e75c19'
down_revision: Union[str, Sequence[str], None] = '45a7e756d0a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add rebalance_period_minutes column to portfolios table
    op.add_column('portfolios', sa.Column('rebalance_period_minutes', sa.Integer(), server_default='10', nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove rebalance_period_minutes column from portfolios table
    op.drop_column('portfolios', 'rebalance_period_minutes')
