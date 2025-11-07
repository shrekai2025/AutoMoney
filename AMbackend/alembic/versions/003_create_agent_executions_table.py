"""Create agent_executions table

Revision ID: 003
Revises: e4d4ba0325a3
Create Date: 2025-11-06

Agent Decoupling Architecture - Phase 1
业务Agent执行记录统一存储表
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision = '003'
down_revision = 'e4d4ba0325a3'
branch_labels = None
depends_on = None


def upgrade():
    """创建 agent_executions 表"""

    # 创建主表
    op.create_table(
        'agent_executions',
        # 主键
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),

        # Agent标识
        sa.Column('agent_name', sa.String(50), nullable=False),
        sa.Column('agent_display_name', sa.String(100)),

        # 执行信息
        sa.Column('executed_at', sa.TIMESTAMP, nullable=False),
        sa.Column('execution_duration_ms', sa.Integer),
        sa.Column('status', sa.String(20), server_default='success'),

        # 标准化输出
        sa.Column('signal', sa.String(20), nullable=False),
        sa.Column('confidence', sa.Numeric(3, 2), nullable=False),
        sa.Column('score', sa.Numeric(3, 2)),
        sa.Column('reasoning', sa.Text, nullable=False),

        # Agent专属数据（JSONB灵活存储）
        sa.Column('agent_specific_data', JSONB, nullable=False),
        sa.Column('market_data_snapshot', JSONB),

        # LLM调用追踪
        sa.Column('llm_provider', sa.String(50)),
        sa.Column('llm_model', sa.String(100)),
        sa.Column('llm_prompt', sa.Text),
        sa.Column('llm_response', sa.Text),
        sa.Column('tokens_used', sa.Integer),
        sa.Column('llm_cost', sa.Numeric(10, 6)),

        # 调用方关联（可选，实现解耦）
        sa.Column('caller_type', sa.String(50)),
        sa.Column('caller_id', UUID(as_uuid=True)),

        # 💡 策略系统专用关联（强类型外键）
        # Note: 外键约束在 migration 75222f346b27 中添加
        sa.Column('strategy_execution_id', UUID(as_uuid=True)),

        # ⚠️ user_id 是 Integer 类型 (与 user.id 保持一致)
        sa.Column('user_id', sa.Integer),

        # 审计字段
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('NOW()')),

        # 约束
        sa.CheckConstraint('confidence >= 0 AND confidence <= 1', name='chk_confidence'),
        sa.CheckConstraint('score IS NULL OR (score >= -1 AND score <= 1)', name='chk_score'),
        sa.CheckConstraint("signal IN ('BULLISH', 'BEARISH', 'NEUTRAL')", name='chk_signal'),
        sa.CheckConstraint("status IN ('success', 'failed', 'timeout')", name='chk_status'),
    )

    # 创建索引
    # 1. Mind Hub查询最新结果（最高频）
    op.create_index(
        'idx_agent_executions_latest',
        'agent_executions',
        ['agent_name', sa.text('executed_at DESC')],
        postgresql_where=sa.text("status = 'success'")
    )

    # 2. 按调用方查询
    op.create_index(
        'idx_agent_executions_caller',
        'agent_executions',
        ['caller_type', 'caller_id', sa.text('executed_at DESC')]
    )

    # 2.5 按策略执行查询 (策略系统专用)
    op.create_index(
        'idx_agent_executions_strategy',
        'agent_executions',
        ['strategy_execution_id', sa.text('executed_at')]
    )

    # 3. 按用户查询
    op.create_index(
        'idx_agent_executions_user',
        'agent_executions',
        ['user_id', sa.text('executed_at DESC')]
    )

    # 4. 按时间范围查询
    op.create_index(
        'idx_agent_executions_time',
        'agent_executions',
        [sa.text('executed_at DESC')]
    )

    # 5. LLM成本分析
    op.create_index(
        'idx_agent_executions_llm',
        'agent_executions',
        ['llm_provider', 'llm_model', sa.text('executed_at DESC')]
    )


def downgrade():
    """删除 agent_executions 表"""

    # 删除索引
    op.drop_index('idx_agent_executions_llm', table_name='agent_executions')
    op.drop_index('idx_agent_executions_time', table_name='agent_executions')
    op.drop_index('idx_agent_executions_user', table_name='agent_executions')
    op.drop_index('idx_agent_executions_strategy', table_name='agent_executions')
    op.drop_index('idx_agent_executions_caller', table_name='agent_executions')
    op.drop_index('idx_agent_executions_latest', table_name='agent_executions')

    # 删除表
    op.drop_table('agent_executions')
