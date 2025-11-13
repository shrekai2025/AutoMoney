"""add_philosophy_tags_risk_level_fields

Revision ID: c52c75ab840f
Revises: 001_add_strategy_system
Create Date: 2025-11-13 09:52:49.956544

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c52c75ab840f'
down_revision: Union[str, Sequence[str], None] = '001_add_strategy_system'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. 为 strategy_definitions 表添加 philosophy 字段
    op.add_column(
        'strategy_definitions',
        sa.Column('philosophy', sa.Text, nullable=True, comment='策略哲学/说明（长文本）')
    )

    # 2. 为 portfolios 表添加 tags 字段（JSONB数组）
    op.add_column(
        'portfolios',
        sa.Column('tags', sa.dialects.postgresql.JSONB, nullable=True, server_default='[]', comment='策略标签（如 Macro-Driven, Low-Medium Risk）')
    )

    # 3. 为 portfolios 表添加 risk_level 字段
    op.add_column(
        'portfolios',
        sa.Column('risk_level', sa.String(20), nullable=True, server_default='medium', comment='风险程度: low, medium, high')
    )


def downgrade() -> None:
    """Downgrade schema."""
    # 回滚：删除添加的字段
    op.drop_column('portfolios', 'risk_level')
    op.drop_column('portfolios', 'tags')
    op.drop_column('strategy_definitions', 'philosophy')
