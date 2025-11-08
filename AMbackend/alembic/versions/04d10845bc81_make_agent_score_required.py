"""make_agent_score_required

Revision ID: 04d10845bc81
Revises: aa52a4c19fea
Create Date: 2025-11-08 00:55:11.087478

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '04d10845bc81'
down_revision: Union[str, Sequence[str], None] = 'aa52a4c19fea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Step 1: Update existing NULL values to 0.0
    op.execute("UPDATE agent_executions SET score = 0.0 WHERE score IS NULL")

    # Step 2: Drop existing constraint
    op.drop_constraint('chk_score', 'agent_executions', type_='check')

    # Step 3: Make score NOT NULL with new range
    op.alter_column('agent_executions', 'score',
                    existing_type=sa.NUMERIC(precision=3, scale=2),
                    type_=sa.NUMERIC(precision=5, scale=2),
                    nullable=False,
                    existing_nullable=True)

    # Step 4: Add new constraint for -100 to +100
    op.create_check_constraint(
        'chk_score',
        'agent_executions',
        'score >= -100 AND score <= 100'
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Step 1: Drop new constraint
    op.drop_constraint('chk_score', 'agent_executions', type_='check')

    # Step 2: Make score nullable again
    op.alter_column('agent_executions', 'score',
                    existing_type=sa.NUMERIC(precision=5, scale=2),
                    type_=sa.NUMERIC(precision=3, scale=2),
                    nullable=True,
                    existing_nullable=False)

    # Step 3: Restore old constraint
    op.create_check_constraint(
        'chk_score',
        'agent_executions',
        'score IS NULL OR (score >= -1 AND score <= 1)'
    )
