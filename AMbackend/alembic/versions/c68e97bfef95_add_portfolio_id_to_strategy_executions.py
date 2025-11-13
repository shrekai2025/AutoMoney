"""add_portfolio_id_to_strategy_executions

Revision ID: c68e97bfef95
Revises: c52c75ab840f
Create Date: 2025-11-13 11:12:06.086348

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c68e97bfef95'
down_revision: Union[str, Sequence[str], None] = 'c52c75ab840f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add portfolio_id column to strategy_executions table
    op.add_column(
        'strategy_executions',
        sa.Column('portfolio_id', sa.UUID(), nullable=True)
    )

    # Add foreign key constraint
    op.create_foreign_key(
        'strategy_executions_portfolio_id_fkey',
        'strategy_executions',
        'portfolios',
        ['portfolio_id'],
        ['id']
    )

    # Create index for better query performance
    op.create_index(
        'idx_executions_portfolio_time',
        'strategy_executions',
        ['portfolio_id', 'execution_time'],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop index
    op.drop_index('idx_executions_portfolio_time', table_name='strategy_executions')

    # Drop foreign key
    op.drop_constraint('strategy_executions_portfolio_id_fkey', 'strategy_executions', type_='foreignkey')

    # Drop column
    op.drop_column('strategy_executions', 'portfolio_id')
