"""add_last_execution_time_to_portfolio

Revision ID: 344b4ede5d08
Revises: 44b097e75c19
Create Date: 2025-11-07 00:46:45.562506

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '344b4ede5d08'
down_revision: Union[str, Sequence[str], None] = '44b097e75c19'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add last_execution_time column to portfolios table
    op.add_column('portfolios', sa.Column('last_execution_time', sa.TIMESTAMP(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove last_execution_time column from portfolios table
    op.drop_column('portfolios', 'last_execution_time')
