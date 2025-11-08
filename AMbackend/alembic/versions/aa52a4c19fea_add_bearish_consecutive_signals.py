"""add_bearish_consecutive_signals

Revision ID: aa52a4c19fea
Revises: 2554cdc8386c
Create Date: 2025-11-07 18:08:49.099791

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aa52a4c19fea'
down_revision: Union[str, Sequence[str], None] = '2554cdc8386c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add consecutive_bearish_count and consecutive_bearish_since fields
    op.add_column('portfolios', sa.Column('consecutive_bearish_count', sa.Integer(), server_default='0', nullable=False))
    op.add_column('portfolios', sa.Column('consecutive_bearish_since', sa.TIMESTAMP(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove consecutive bearish fields
    op.drop_column('portfolios', 'consecutive_bearish_since')
    op.drop_column('portfolios', 'consecutive_bearish_count')
