"""add_initial_btc_amount_to_portfolio

Revision ID: a1b2c3d4e5f6
Revises: 9f8e3a1b2c5d
Create Date: 2025-11-07 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import NUMERIC


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '9f8e3a1b2c5d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add initial_btc_amount column to portfolios table
    # This stores the amount of BTC that could have been bought with initial_balance
    op.add_column('portfolios', sa.Column('initial_btc_amount', NUMERIC(20, 8), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove initial_btc_amount column from portfolios table
    op.drop_column('portfolios', 'initial_btc_amount')
