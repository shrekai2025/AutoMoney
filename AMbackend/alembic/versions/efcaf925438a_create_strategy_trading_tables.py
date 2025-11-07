"""create_strategy_trading_tables

Revision ID: efcaf925438a
Revises: 59d6bfb0a721
Create Date: 2025-11-06 16:14:40.926365

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP, NUMERIC


# revision identifiers, used by Alembic.
revision: str = 'efcaf925438a'
down_revision: Union[str, Sequence[str], None] = '59d6bfb0a721'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Create strategy and trading tables."""

    # 1. Create strategy_executions table
    op.create_table(
        'strategy_executions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('execution_time', TIMESTAMP, nullable=False),
        sa.Column('strategy_name', sa.String(100), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id'), nullable=False),

        # Market data
        sa.Column('market_snapshot', JSONB, nullable=False),
        # Note: agent_outputs field removed - use agent_executions table instead

        # Decision results
        sa.Column('conviction_score', sa.Float),
        sa.Column('signal', sa.String(10)),
        sa.Column('signal_strength', sa.Float),
        sa.Column('position_size', sa.Float),
        sa.Column('risk_level', sa.String(20)),

        # Execution info
        sa.Column('execution_duration_ms', sa.Integer),
        sa.Column('error_message', sa.Text),

        sa.Column('created_at', TIMESTAMP, server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', TIMESTAMP, server_default=sa.text('NOW()'), onupdate=sa.text('NOW()')),
    )

    # Indexes for strategy_executions
    op.create_index('idx_executions_user_time', 'strategy_executions', ['user_id', sa.text('execution_time DESC')])
    op.create_index('idx_executions_strategy', 'strategy_executions', ['strategy_name', sa.text('execution_time DESC')])
    op.create_index('idx_executions_status', 'strategy_executions', ['status'])

    # 2. Create portfolios table
    op.create_table(
        'portfolios',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),

        # Account balance
        sa.Column('initial_balance', NUMERIC(20, 8), nullable=False),
        sa.Column('current_balance', NUMERIC(20, 8), nullable=False),
        sa.Column('total_value', NUMERIC(20, 8), nullable=False),

        # PnL statistics
        sa.Column('total_pnl', NUMERIC(20, 8), server_default='0'),
        sa.Column('total_pnl_percent', sa.Float, server_default='0'),

        # Trading statistics
        sa.Column('total_trades', sa.Integer, server_default='0'),
        sa.Column('winning_trades', sa.Integer, server_default='0'),
        sa.Column('losing_trades', sa.Integer, server_default='0'),
        sa.Column('win_rate', sa.Float, server_default='0'),

        # Risk metrics
        sa.Column('max_drawdown', sa.Float, server_default='0'),
        sa.Column('sharpe_ratio', sa.Float),

        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('strategy_name', sa.String(100)),

        sa.Column('created_at', TIMESTAMP, server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', TIMESTAMP, server_default=sa.text('NOW()'), onupdate=sa.text('NOW()')),
    )

    # Indexes for portfolios
    op.create_index('idx_portfolios_user', 'portfolios', ['user_id'])
    op.create_index('idx_portfolios_active', 'portfolios', ['is_active', 'user_id'])

    # 3. Create portfolio_holdings table
    op.create_table(
        'portfolio_holdings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('portfolio_id', UUID(as_uuid=True), sa.ForeignKey('portfolios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('symbol', sa.String(20), nullable=False),

        sa.Column('amount', NUMERIC(20, 8), nullable=False),
        sa.Column('avg_buy_price', NUMERIC(20, 8), nullable=False),
        sa.Column('current_price', NUMERIC(20, 8), nullable=False),
        sa.Column('market_value', NUMERIC(20, 8), nullable=False),
        sa.Column('cost_basis', NUMERIC(20, 8), nullable=False),

        sa.Column('unrealized_pnl', NUMERIC(20, 8), server_default='0'),
        sa.Column('unrealized_pnl_percent', sa.Float, server_default='0'),

        sa.Column('first_buy_time', TIMESTAMP, nullable=False),
        sa.Column('last_updated', TIMESTAMP, server_default=sa.text('NOW()'), onupdate=sa.text('NOW()')),

        # Unique constraint: one holding per portfolio per symbol
        sa.UniqueConstraint('portfolio_id', 'symbol', name='uq_holdings_portfolio_symbol'),
    )

    # Indexes for portfolio_holdings
    op.create_index('idx_holdings_portfolio', 'portfolio_holdings', ['portfolio_id', 'symbol'])

    # 4. Create trades table
    op.create_table(
        'trades',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('portfolio_id', UUID(as_uuid=True), sa.ForeignKey('portfolios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('execution_id', UUID(as_uuid=True), sa.ForeignKey('strategy_executions.id')),

        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('trade_type', sa.String(10), nullable=False),

        sa.Column('amount', NUMERIC(20, 8), nullable=False),
        sa.Column('price', NUMERIC(20, 8), nullable=False),
        sa.Column('total_value', NUMERIC(20, 8), nullable=False),
        sa.Column('fee', NUMERIC(20, 8), server_default='0'),
        sa.Column('fee_percent', sa.Float, server_default='0'),

        # Before/after state
        sa.Column('balance_before', NUMERIC(20, 8)),
        sa.Column('balance_after', NUMERIC(20, 8)),
        sa.Column('holding_before', NUMERIC(20, 8)),
        sa.Column('holding_after', NUMERIC(20, 8)),

        # PnL (only for SELL trades)
        sa.Column('realized_pnl', NUMERIC(20, 8)),
        sa.Column('realized_pnl_percent', sa.Float),

        # Strategy decision info
        sa.Column('conviction_score', sa.Float),
        sa.Column('signal_strength', sa.Float),
        sa.Column('reason', sa.Text),

        sa.Column('executed_at', TIMESTAMP, nullable=False),
        sa.Column('created_at', TIMESTAMP, server_default=sa.text('NOW()'), nullable=False),
    )

    # Indexes for trades
    op.create_index('idx_trades_portfolio', 'trades', ['portfolio_id', sa.text('executed_at DESC')])
    op.create_index('idx_trades_execution', 'trades', ['execution_id'])
    op.create_index('idx_trades_symbol', 'trades', ['symbol', sa.text('executed_at DESC')])
    op.create_index('idx_trades_type', 'trades', ['trade_type', sa.text('executed_at DESC')])

    # 5. Create portfolio_snapshots table
    op.create_table(
        'portfolio_snapshots',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('portfolio_id', UUID(as_uuid=True), sa.ForeignKey('portfolios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('snapshot_time', TIMESTAMP, nullable=False),

        sa.Column('total_value', NUMERIC(20, 8), nullable=False),
        sa.Column('balance', NUMERIC(20, 8), nullable=False),
        sa.Column('holdings_value', NUMERIC(20, 8), nullable=False),

        sa.Column('total_pnl', NUMERIC(20, 8)),
        sa.Column('total_pnl_percent', sa.Float),
        sa.Column('daily_pnl', NUMERIC(20, 8)),
        sa.Column('daily_pnl_percent', sa.Float),

        sa.Column('btc_price', NUMERIC(20, 8)),
        sa.Column('eth_price', NUMERIC(20, 8)),
        sa.Column('holdings', JSONB),

        sa.Column('created_at', TIMESTAMP, server_default=sa.text('NOW()'), nullable=False),
    )

    # Indexes for portfolio_snapshots
    op.create_index('idx_snapshots_portfolio_time', 'portfolio_snapshots', ['portfolio_id', sa.text('snapshot_time DESC')])


def downgrade() -> None:
    """Downgrade schema - Drop all strategy and trading tables."""

    # Drop tables in reverse order (respecting foreign key constraints)
    op.drop_table('portfolio_snapshots')
    op.drop_table('trades')
    op.drop_table('portfolio_holdings')
    op.drop_table('portfolios')
    op.drop_table('strategy_executions')
