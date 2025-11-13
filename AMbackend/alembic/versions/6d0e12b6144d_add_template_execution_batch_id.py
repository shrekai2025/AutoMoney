"""add_template_execution_batch_id

Revision ID: 6d0e12b6144d
Revises: c68e97bfef95
Create Date: 2025-11-13 11:54:37.489231

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6d0e12b6144d'
down_revision: Union[str, Sequence[str], None] = 'c68e97bfef95'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add template_execution_batch_id to agent_executions
    op.add_column(
        'agent_executions',
        sa.Column('template_execution_batch_id', sa.UUID(), nullable=True, comment='批量执行批次ID，用于关联同一批次的agent和strategy executions')
    )

    # Add template_execution_batch_id to strategy_executions
    op.add_column(
        'strategy_executions',
        sa.Column('template_execution_batch_id', sa.UUID(), nullable=True, comment='批量执行批次ID，用于关联同一批次的agent和strategy executions')
    )

    # Create indexes for better query performance
    op.create_index(
        'idx_agent_executions_batch_id',
        'agent_executions',
        ['template_execution_batch_id'],
        unique=False
    )

    op.create_index(
        'idx_strategy_executions_batch_id',
        'strategy_executions',
        ['template_execution_batch_id'],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index('idx_strategy_executions_batch_id', table_name='strategy_executions')
    op.drop_index('idx_agent_executions_batch_id', table_name='agent_executions')

    # Drop columns
    op.drop_column('strategy_executions', 'template_execution_batch_id')
    op.drop_column('agent_executions', 'template_execution_batch_id')
