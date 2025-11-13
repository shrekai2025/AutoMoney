-- 重置 Paper Trading 测试组合
-- Portfolio ID: e0d275e1-9e22-479c-b905-de44d9b66519

BEGIN;

-- 1. 删除所有交易记录（最先删除，因为它引用了 strategy_executions）
DELETE FROM trades WHERE portfolio_id = 'e0d275e1-9e22-479c-b905-de44d9b66519';

-- 2. 删除 agent 执行记录（有外键指向 strategy_executions）
DELETE FROM agent_executions WHERE strategy_execution_id IN (
    SELECT id FROM strategy_executions WHERE user_id = (
        SELECT user_id FROM portfolios WHERE id = 'e0d275e1-9e22-479c-b905-de44d9b66519'
    )
);

-- 3. 删除所有策略执行记录（通过 user_id 关联）
DELETE FROM strategy_executions WHERE user_id = (
    SELECT user_id FROM portfolios WHERE id = 'e0d275e1-9e22-479c-b905-de44d9b66519'
);

-- 4. 删除所有持仓记录
DELETE FROM portfolio_holdings WHERE portfolio_id = 'e0d275e1-9e22-479c-b905-de44d9b66519';

-- 5. 删除所有快照记录
DELETE FROM portfolio_snapshots WHERE portfolio_id = 'e0d275e1-9e22-479c-b905-de44d9b66519';

-- 6. 重置 Portfolio 统计数据
UPDATE portfolios
SET
    current_balance = initial_balance,
    total_value = initial_balance,
    total_pnl = 0,
    total_pnl_percent = 0,
    total_trades = 0,
    winning_trades = 0,
    losing_trades = 0,
    win_rate = 0,
    max_drawdown = 0,
    sharpe_ratio = NULL,
    -- 重置连续信号状态
    consecutive_bullish_count = 0,
    consecutive_bullish_since = NULL,
    last_conviction_score = NULL,
    -- 重置基准对比参数
    initial_btc_amount = NULL,
    updated_at = NOW()
WHERE id = 'e0d275e1-9e22-479c-b905-de44d9b66519';

COMMIT;

-- 验证重置结果
SELECT
    name,
    initial_balance,
    current_balance,
    total_value,
    total_pnl,
    total_trades,
    winning_trades,
    losing_trades
FROM portfolios
WHERE id = 'e0d275e1-9e22-479c-b905-de44d9b66519';
