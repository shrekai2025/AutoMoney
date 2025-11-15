"""create_system_errors_table

Revision ID: 71975ee8943c
Revises: 6b35b1d544f8
Create Date: 2025-11-14 10:03:00.617829

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '71975ee8943c'
down_revision: Union[str, Sequence[str], None] = '6b35b1d544f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'system_errors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('error_type', sa.String(length=100), nullable=False, comment='错误类型 (e.g., data_collection, agent_execution, strategy_execution)'),
        sa.Column('error_category', sa.String(length=50), nullable=False, comment='错误分类 (e.g., network, database, llm, logic)'),
        sa.Column('severity', sa.String(length=20), nullable=False, comment='严重程度 (critical, error, warning, info)'),
        sa.Column('component', sa.String(length=200), nullable=False, comment='发生错误的组件 (e.g., BinanceCollector, MacroAgent, Scheduler)'),
        sa.Column('error_message', sa.Text(), nullable=False, comment='错误摘要信息'),
        sa.Column('error_details', sa.Text(), nullable=True, comment='详细错误堆栈或上下文'),
        sa.Column('context', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='错误发生时的额外上下文数据 (JSON)'),
        sa.Column('user_id', sa.Integer(), nullable=True, comment='关联用户ID'),
        sa.Column('portfolio_id', sa.String(length=36), nullable=True, comment='关联Portfolio ID'),
        sa.Column('strategy_name', sa.String(length=100), nullable=True, comment='关联策略名称'),
        sa.Column('is_resolved', sa.Boolean(), nullable=False, server_default=sa.text('false'), comment='是否已解决'),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True, comment='解决时间'),
        sa.Column('resolution_note', sa.Text(), nullable=True, comment='解决备注'),
        sa.Column('occurrence_count', sa.Integer(), nullable=False, server_default=sa.text('1'), comment='错误发生次数'),
        sa.Column('first_occurred_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='首次发生时间'),
        sa.Column('last_occurred_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='最近发生时间'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_system_errors_error_type'), 'system_errors', ['error_type'], unique=False)
    op.create_index(op.f('ix_system_errors_error_category'), 'system_errors', ['error_category'], unique=False)
    op.create_index(op.f('ix_system_errors_severity'), 'system_errors', ['severity'], unique=False)
    op.create_index(op.f('ix_system_errors_is_resolved'), 'system_errors', ['is_resolved'], unique=False)
    op.create_index(op.f('ix_system_errors_user_id'), 'system_errors', ['user_id'], unique=False)
    op.create_index(op.f('ix_system_errors_portfolio_id'), 'system_errors', ['portfolio_id'], unique=False)
    op.create_index(op.f('ix_system_errors_strategy_name'), 'system_errors', ['strategy_name'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_system_errors_strategy_name'), table_name='system_errors')
    op.drop_index(op.f('ix_system_errors_portfolio_id'), table_name='system_errors')
    op.drop_index(op.f('ix_system_errors_user_id'), table_name='system_errors')
    op.drop_index(op.f('ix_system_errors_is_resolved'), table_name='system_errors')
    op.drop_index(op.f('ix_system_errors_severity'), table_name='system_errors')
    op.drop_index(op.f('ix_system_errors_error_category'), table_name='system_errors')
    op.drop_index(op.f('ix_system_errors_error_type'), table_name='system_errors')
    op.drop_table('system_errors')
