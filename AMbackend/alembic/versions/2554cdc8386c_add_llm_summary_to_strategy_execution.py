"""add_llm_summary_to_strategy_execution

Revision ID: 2554cdc8386c
Revises: b2c3d4e5f6a7
Create Date: 2025-11-07 17:57:51.312369

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2554cdc8386c'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add llm_summary field to strategy_executions table
    op.add_column('strategy_executions', sa.Column('llm_summary', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove llm_summary field
    op.drop_column('strategy_executions', 'llm_summary')
