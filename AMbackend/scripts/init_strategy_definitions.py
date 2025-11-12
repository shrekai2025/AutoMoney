"""初始化策略模板

创建初始的策略模板: Multi-Agent BTC Strategy
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models import StrategyDefinition


async def init_strategy_definitions():
    """初始化策略模板"""
    print("📋 开始初始化策略模板...")
    
    async with AsyncSessionLocal() as db:
        try:
            # 检查是否已存在
            result = await db.execute(
                select(StrategyDefinition).where(StrategyDefinition.name == "multi_agent_btc_v1")
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                print("⚠️  策略模板 'multi_agent_btc_v1' 已存在，跳过创建")
                return
            
            # 创建Multi-Agent BTC Strategy模板
            definition = StrategyDefinition(
                name="multi_agent_btc_v1",
                display_name="Multi-Agent BTC Strategy",
                description="使用宏观、链上、技术分析三个Agent的BTC现货策略。通过多维度分析市场，生成高信念分数的交易信号。",
                
                # 决策引擎配置
                decision_agent_module="app.decision_agents.multi_agent_conviction",
                decision_agent_class="MultiAgentConvictionDecision",
                
                # 业务Agent列表
                business_agents=["macro", "ta", "onchain"],
                
                # 交易配置
                trade_channel="binance_spot",
                trade_symbol="BTC",
                rebalance_period_minutes=10,
                
                # 默认参数配置
                default_params={
                    # Agent权重
                    "agent_weights": {
                        "macro": 0.40,
                        "onchain": 0.40,
                        "ta": 0.20
                    },
                    
                    # 交易阈值
                    "buy_threshold": 50,  # Conviction Score >= 50 买入
                    "partial_sell_threshold": 50,  # 45-50之间部分减仓
                    "full_sell_threshold": 45,  # < 45全部清仓
                    
                    # 连续信号机制
                    "consecutive_signal_threshold": 30,  # 连续30次触发加速
                    "acceleration_multiplier_min": 1.1,  # 最小乘数
                    "acceleration_multiplier_max": 2.0,  # 最大乘数
                    
                    # 熔断机制
                    "fg_circuit_breaker_threshold": 20,  # Fear & Greed < 20 暂停交易
                    "fg_position_adjust_threshold": 30,  # Fear & Greed < 30 减少仓位
                },
                
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            
            db.add(definition)
            await db.commit()
            await db.refresh(definition)
            
            print(f"\n✅ 策略模板创建成功!")
            print(f"   ID: {definition.id}")
            print(f"   名称: {definition.display_name}")
            print(f"   标识: {definition.name}")
            print(f"   业务Agent: {', '.join(definition.business_agents)}")
            print(f"   交易渠道: {definition.trade_channel}")
            print(f"   交易币种: {definition.trade_symbol}")
            
        except Exception as e:
            print(f"\n❌ 创建失败: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    print("=" * 60)
    print("初始化策略模板")
    print("=" * 60)
    print()
    
    asyncio.run(init_strategy_definitions())

