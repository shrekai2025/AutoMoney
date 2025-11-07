"""add_strategy_execution_id_fk

Revision ID: 75222f346b27
Revises: efcaf925438a
Create Date: 2025-11-06 16:32:06.028415

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '75222f346b27'
down_revision: Union[str, Sequence[str], None] = 'efcaf925438a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add ForeignKey to strategy_execution_id."""
    # Add foreign key constraint to agent_executions.strategy_execution_id
    op.create_foreign_key(
        'fk_agent_executions_strategy_execution_id',
        'agent_executions',
        'strategy_executions',
        ['strategy_execution_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    """Downgrade schema - Remove ForeignKey from strategy_execution_id."""
    # Drop foreign key constraint
    op.drop_constraint(
        'fk_agent_executions_strategy_execution_id',
        'agent_executions',
        type_='foreignkey'
    )
