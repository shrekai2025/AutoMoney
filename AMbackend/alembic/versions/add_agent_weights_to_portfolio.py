"""add_agent_weights_to_portfolio

Revision ID: 9f8e3a1b2c5d
Revises: 344b4ede5d08
Create Date: 2025-11-07 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = '9f8e3a1b2c5d'
down_revision: Union[str, Sequence[str], None] = '344b4ede5d08'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add agent_weights column to portfolios table
    # Default value: {"macro": 0.40, "onchain": 0.40, "ta": 0.20}
    op.add_column('portfolios', sa.Column('agent_weights', JSONB(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove agent_weights column from portfolios table
    op.drop_column('portfolios', 'agent_weights')
