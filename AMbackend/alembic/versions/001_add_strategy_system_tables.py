"""add strategy system tables

Revision ID: 001_add_strategy_system
Revises: fddbafdebc9e
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_add_strategy_system'
down_revision = 'fddbafdebc9e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建 strategy_definitions 表
    op.create_table('strategy_definitions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False, comment='唯一标识，如 multi_agent_btc_v1'),
        sa.Column('display_name', sa.String(length=200), nullable=False, comment='显示名称，如 Multi-Agent BTC Strategy'),
        sa.Column('description', sa.Text(), nullable=True, comment='策略描述'),
        sa.Column('decision_agent_module', sa.String(length=200), nullable=False, comment='决策Agent模块路径'),
        sa.Column('decision_agent_class', sa.String(length=100), nullable=False, comment='决策Agent类名'),
        sa.Column('business_agents', postgresql.JSONB(astext_type=sa.Text()), nullable=False, comment='业务Agent列表'),
        sa.Column('trade_channel', sa.String(length=50), nullable=False, comment='交易渠道'),
        sa.Column('trade_symbol', sa.String(length=20), nullable=False, comment='交易币种'),
        sa.Column('rebalance_period_minutes', sa.Integer(), nullable=False, server_default='10', comment='策略执行周期（分钟）'),
        sa.Column('default_params', postgresql.JSONB(astext_type=sa.Text()), nullable=False, comment='默认参数配置'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='模板开关'),
        sa.Column('created_at', postgresql.TIMESTAMP(), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_strategy_definitions_id', 'strategy_definitions', ['id'], unique=False)
    op.create_index('ix_strategy_definitions_name', 'strategy_definitions', ['name'], unique=True)
    op.create_index('ix_strategy_definitions_is_active', 'strategy_definitions', ['is_active'], unique=False)

    # 创建 agent_registry 表
    op.create_table('agent_registry',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_name', sa.String(length=50), nullable=False, comment='Agent唯一标识'),
        sa.Column('display_name', sa.String(length=100), nullable=False, comment='显示名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='Agent功能描述'),
        sa.Column('agent_module', sa.String(length=200), nullable=False, comment='Agent模块路径'),
        sa.Column('agent_class', sa.String(length=100), nullable=False, comment='Agent类名'),
        sa.Column('available_tools', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', comment='Agent可用的Tool列表'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='Agent状态'),
        sa.Column('created_at', postgresql.TIMESTAMP(), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_agent_registry_id', 'agent_registry', ['id'], unique=False)
    op.create_index('ix_agent_registry_agent_name', 'agent_registry', ['agent_name'], unique=True)
    op.create_index('ix_agent_registry_is_active', 'agent_registry', ['is_active'], unique=False)

    # 创建 tool_registry 表
    op.create_table('tool_registry',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tool_name', sa.String(length=100), nullable=False, comment='Tool唯一标识'),
        sa.Column('display_name', sa.String(length=200), nullable=False, comment='显示名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='Tool功能描述'),
        sa.Column('tool_module', sa.String(length=200), nullable=False, comment='Tool模块路径'),
        sa.Column('tool_function', sa.String(length=100), nullable=False, comment='Tool函数名'),
        sa.Column('required_apis', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', comment='Tool依赖的API列表'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='Tool状态'),
        sa.Column('created_at', postgresql.TIMESTAMP(), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tool_registry_id', 'tool_registry', ['id'], unique=False)
    op.create_index('ix_tool_registry_tool_name', 'tool_registry', ['tool_name'], unique=True)
    op.create_index('ix_tool_registry_is_active', 'tool_registry', ['is_active'], unique=False)

    # 创建 api_config 表
    op.create_table('api_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('api_name', sa.String(length=100), nullable=False, comment='API唯一标识'),
        sa.Column('display_name', sa.String(length=200), nullable=False, comment='显示名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='API描述'),
        sa.Column('base_url', sa.String(length=500), nullable=True, comment='API基础URL'),
        sa.Column('api_key_encrypted', sa.Text(), nullable=True, comment='加密存储的API密钥'),
        sa.Column('api_secret_encrypted', sa.Text(), nullable=True, comment='加密存储的API密钥Secret'),
        sa.Column('rate_limit', sa.Integer(), nullable=True, comment='每分钟请求数限制'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='API状态'),
        sa.Column('created_at', postgresql.TIMESTAMP(), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_api_config_id', 'api_config', ['id'], unique=False)
    op.create_index('ix_api_config_api_name', 'api_config', ['api_name'], unique=True)
    op.create_index('ix_api_config_is_active', 'api_config', ['is_active'], unique=False)

    # 修改 portfolios 表
    # 添加新字段
    op.add_column('portfolios', sa.Column('strategy_definition_id', sa.Integer(), nullable=True, comment='关联的策略模板ID'))
    op.add_column('portfolios', sa.Column('instance_name', sa.String(length=200), nullable=True, comment='实例名称'))
    op.add_column('portfolios', sa.Column('instance_description', sa.Text(), nullable=True, comment='实例描述'))
    op.add_column('portfolios', sa.Column('instance_params', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='实例参数'))
    
    # 创建外键
    op.create_foreign_key('fk_portfolios_strategy_definition', 'portfolios', 'strategy_definitions', ['strategy_definition_id'], ['id'])
    op.create_index('idx_portfolios_definition', 'portfolios', ['strategy_definition_id'], unique=False)
    
    # 删除不再需要的字段（注意：这些字段的数据将丢失）
    # strategy_name - 从模板获取
    # rebalance_period_minutes - 从模板获取
    # agent_weights - 移入instance_params
    # 各种阈值配置 - 移入instance_params
    op.drop_column('portfolios', 'strategy_name')
    op.drop_column('portfolios', 'rebalance_period_minutes')
    op.drop_column('portfolios', 'agent_weights')
    op.drop_column('portfolios', 'consecutive_signal_threshold')
    op.drop_column('portfolios', 'acceleration_multiplier_min')
    op.drop_column('portfolios', 'acceleration_multiplier_max')
    op.drop_column('portfolios', 'fg_circuit_breaker_threshold')
    op.drop_column('portfolios', 'fg_position_adjust_threshold')
    op.drop_column('portfolios', 'buy_threshold')
    op.drop_column('portfolios', 'partial_sell_threshold')
    op.drop_column('portfolios', 'full_sell_threshold')


def downgrade() -> None:
    # 恢复 portfolios 表的字段
    op.add_column('portfolios', sa.Column('full_sell_threshold', sa.Float(), server_default='45', nullable=False))
    op.add_column('portfolios', sa.Column('partial_sell_threshold', sa.Float(), server_default='50', nullable=False))
    op.add_column('portfolios', sa.Column('buy_threshold', sa.Float(), server_default='50', nullable=False))
    op.add_column('portfolios', sa.Column('fg_position_adjust_threshold', sa.Integer(), server_default='30', nullable=False))
    op.add_column('portfolios', sa.Column('fg_circuit_breaker_threshold', sa.Integer(), server_default='20', nullable=False))
    op.add_column('portfolios', sa.Column('acceleration_multiplier_max', sa.Float(), server_default='2.0', nullable=False))
    op.add_column('portfolios', sa.Column('acceleration_multiplier_min', sa.Float(), server_default='1.1', nullable=False))
    op.add_column('portfolios', sa.Column('consecutive_signal_threshold', sa.Integer(), server_default='30', nullable=False))
    op.add_column('portfolios', sa.Column('agent_weights', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('portfolios', sa.Column('rebalance_period_minutes', sa.Integer(), server_default='10', nullable=False))
    op.add_column('portfolios', sa.Column('strategy_name', sa.String(length=100), nullable=True))
    
    # 删除新字段和外键
    op.drop_index('idx_portfolios_definition', table_name='portfolios')
    op.drop_constraint('fk_portfolios_strategy_definition', 'portfolios', type_='foreignkey')
    op.drop_column('portfolios', 'instance_params')
    op.drop_column('portfolios', 'instance_description')
    op.drop_column('portfolios', 'instance_name')
    op.drop_column('portfolios', 'strategy_definition_id')

    # 删除新表
    op.drop_index('ix_api_config_is_active', table_name='api_config')
    op.drop_index('ix_api_config_api_name', table_name='api_config')
    op.drop_index('ix_api_config_id', table_name='api_config')
    op.drop_table('api_config')
    
    op.drop_index('ix_tool_registry_is_active', table_name='tool_registry')
    op.drop_index('ix_tool_registry_tool_name', table_name='tool_registry')
    op.drop_index('ix_tool_registry_id', table_name='tool_registry')
    op.drop_table('tool_registry')
    
    op.drop_index('ix_agent_registry_is_active', table_name='agent_registry')
    op.drop_index('ix_agent_registry_agent_name', table_name='agent_registry')
    op.drop_index('ix_agent_registry_id', table_name='agent_registry')
    op.drop_table('agent_registry')
    
    op.drop_index('ix_strategy_definitions_is_active', table_name='strategy_definitions')
    op.drop_index('ix_strategy_definitions_name', table_name='strategy_definitions')
    op.drop_index('ix_strategy_definitions_id', table_name='strategy_definitions')
    op.drop_table('strategy_definitions')

