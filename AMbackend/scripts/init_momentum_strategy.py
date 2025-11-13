"""初始化动量策略定义

在数据库中创建Momentum Strategy的strategy_definition记录
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.strategy_definition import StrategyDefinition
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_momentum_strategy():
    """初始化动量策略定义"""
    
    async with AsyncSessionLocal() as db:
        # 检查是否已存在
        result = await db.execute(
            select(StrategyDefinition).where(
                StrategyDefinition.name == "momentum_regime_btc_v1"
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            logger.info("动量策略模板已存在,更新配置...")
            strategy = existing
        else:
            logger.info("创建新的动量策略模板...")
            strategy = StrategyDefinition(
                name="momentum_regime_btc_v1",
                display_name="H.I.M.E. 动量策略",
                is_active=True
            )
            db.add(strategy)
        
        # 设置策略属性
        strategy.description = (
            "Hybrid Intelligence Momentum Engine - 混合智能动量引擎\n\n"
            "这是一个技术分析主导的AI驱动动量策略,专注于捕捉加密货币市场的短中期趋势机会。\n\n"
            "**核心特点**:\n"
            "- 🎯 技术分析主导(80%权重):多时间框架EMA/RSI/MACD动量信号\n"
            "- 🌍 宏观环境确认(20%权重):Regime Score动态调制仓位\n"
            "- 🛡️ 强制风控:每笔交易必带止损止盈(OCO订单)\n"
            "- 🪙 多币种支持:BTC/ETH/SOL同时扫描,自动选择最佳机会\n"
            "- ⚡ 15分钟级别执行:快速响应市场动量变化\n\n"
            "**适合人群**:激进型投资者,追求高频捕捉趋势的短线交易者"
        )
        
        # 投资哲学
        strategy.philosophy = (
            "技术分析主导 + 宏观环境确认 + 强制风控\n\n"
            "我们相信市场的短期动量是可以被捕捉的,通过AI分析多维度技术指标,"
            "结合宏观环境过滤,并严格执行止损止盈,能够在波动市场中持续获利。"
        )
        
        # 决策引擎配置
        strategy.decision_agent_module = "app.decision_agents.momentum_regime_decision"
        strategy.decision_agent_class = "MomentumRegimeDecision"
        
        # 业务Agent配置
        strategy.business_agents = ["regime_filter", "ta_momentum"]
        
        # 交易配置
        strategy.trade_channel = "binance_spot"
        strategy.trade_symbol = "BTC"  # 主币种,实际会分析BTC/ETH/SOL
        
        # 执行周期
        strategy.rebalance_period_minutes = 15  # 15分钟执行一次
        
        # 默认配置
        strategy.default_params = {
            # 资金管理
            "base_risk_pct": 2.0,  # 单笔风险比例(账户的%)
            "base_leverage": 3.0,  # 基础杠杆
            "max_leverage": 5.0,   # 最大杠杆
            
            # 信号过滤
            "min_signal_strength": 0.6,  # 最低信号强度(0-1)
            "min_confidence": 0.5,       # 最低信心水平(0-1)
            
            # Regime过滤
            "regime_weight": 0.2,  # Regime影响权重
            "ta_weight": 0.8,      # TA影响权重
            "extreme_regime_threshold": 25.0,  # 极端Regime阈值
            
            # 止损止盈
            "default_sl_atr_multiplier": 2.0,  # 默认止损ATR倍数
            "default_tp_rr": 2.0,              # 默认止盈风险回报比
            "min_tp_rr": 1.5,                  # 最小风险回报比
            "max_sl_distance_pct": 10.0,       # 最大止损距离(%)
            "min_sl_distance_pct": 0.5,        # 最小止损距离(%)
            
            # 执行控制
            "max_concurrent_positions": 3,  # 最大并发持仓数
            "cooldown_minutes": 60,         # 同一币种交易冷却期(分钟)
        }
        
        # 可配置参数已经在default_params中,不需要单独的configurable_params字段
        # (该字段不在模型中定义)
        
        # 保存
        await db.commit()
        await db.refresh(strategy)
        
        logger.info("=" * 60)
        logger.info("✅ 动量策略模板初始化完成!")
        logger.info(f"   模板名称: {strategy.name}")
        logger.info(f"   显示名称: {strategy.display_name}")
        logger.info(f"   交易品种: {strategy.trade_symbol}")
        logger.info(f"   执行周期: {strategy.rebalance_period_minutes}分钟")
        logger.info(f"   决策引擎: {strategy.decision_agent_class}")
        logger.info(f"   业务Agent: {strategy.business_agents}")
        logger.info(f"   策略ID: {strategy.id}")
        logger.info("=" * 60)
        
        return strategy


if __name__ == "__main__":
    asyncio.run(init_momentum_strategy())

