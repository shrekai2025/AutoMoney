"""注册动量策略的业务Agent到agent_registry表

将RegimeFilterAgent和TAMomentumAgent注册到数据库,
使其在Admin页面的Agent List中可见
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.db.session import AsyncSessionLocal
from app.models.agent_registry import AgentRegistry
from sqlalchemy import select


async def register_momentum_agents():
    """注册动量策略的Agent"""
    
    async with AsyncSessionLocal() as db:
        print("=" * 60)
        print("注册动量策略业务Agent...")
        print("=" * 60)
        
        # 1. RegimeFilterAgent
        print("\n1. 检查 RegimeFilterAgent...")
        result = await db.execute(
            select(AgentRegistry).where(AgentRegistry.agent_name == "regime_filter")
        )
        regime_agent = result.scalar_one_or_none()
        
        if regime_agent:
            print(f"   ✅ RegimeFilterAgent已存在 (ID: {regime_agent.id})")
            # 更新信息
            regime_agent.display_name = "Regime Filter Agent"
            regime_agent.description = (
                "市场环境评估专家,综合分析宏观经济、市场情绪、衍生品指标和链上数据,"
                "输出Regime Score (0-100)来评估市场健康度,用于动量策略的制度确认层。"
            )
            regime_agent.agent_module = "app.agents.regime_filter_agent"
            regime_agent.agent_class = "RegimeFilterAgent"
            regime_agent.available_tools = [
                "analyze_macro_health",
                "analyze_sentiment",
                "analyze_derivatives",
                "calculate_regime_score"
            ]
            regime_agent.is_active = True
            print("   🔄 更新RegimeFilterAgent信息")
        else:
            # 创建新记录
            regime_agent = AgentRegistry(
                agent_name="regime_filter",
                display_name="Regime Filter Agent",
                description=(
                    "市场环境评估专家,综合分析宏观经济、市场情绪、衍生品指标和链上数据,"
                    "输出Regime Score (0-100)来评估市场健康度,用于动量策略的制度确认层。\n\n"
                    "**职责**:\n"
                    "- 评估宏观流动性 (35%): ETF流入、美元指数、降息预期\n"
                    "- 评估市场情绪 (20%): Fear & Greed Index\n"
                    "- 评估衍生品健康度 (40%): 资金费率、持仓量、期货溢价\n"
                    "- 评估链上信号 (5%): MVRV等指标\n\n"
                    "**输出**:\n"
                    "- Regime Score: 0-100分,分数越高市场越健康\n"
                    "- 推荐乘数: 0.3x-1.6x,用于调制仓位大小\n"
                    "- 详细reasoning和关键因素"
                ),
                agent_module="app.agents.regime_filter_agent",
                agent_class="RegimeFilterAgent",
                available_tools=[
                    "analyze_macro_health",
                    "analyze_sentiment",
                    "analyze_derivatives",
                    "calculate_regime_score"
                ],
                is_active=True
            )
            db.add(regime_agent)
            print("   ✅ 创建RegimeFilterAgent记录")
        
        # 2. TAMomentumAgent
        print("\n2. 检查 TAMomentumAgent...")
        result = await db.execute(
            select(AgentRegistry).where(AgentRegistry.agent_name == "ta_momentum")
        )
        ta_agent = result.scalar_one_or_none()
        
        if ta_agent:
            print(f"   ✅ TAMomentumAgent已存在 (ID: {ta_agent.id})")
            # 更新信息
            ta_agent.display_name = "TA Momentum Agent"
            ta_agent.description = (
                "技术动量分析专家,对BTC/ETH/SOL进行多时间框架(15m/60m)技术分析,"
                "识别最佳交易机会并提供止损止盈建议,用于动量策略的技术分析层。"
            )
            ta_agent.agent_module = "app.agents.ta_momentum_agent"
            ta_agent.agent_class = "TAMomentumAgent"
            ta_agent.available_tools = [
                "calculate_ema",
                "calculate_rsi",
                "calculate_macd",
                "calculate_bollinger_bands",
                "calculate_atr",
                "identify_trend",
                "generate_signal"
            ]
            ta_agent.is_active = True
            print("   🔄 更新TAMomentumAgent信息")
        else:
            # 创建新记录
            ta_agent = AgentRegistry(
                agent_name="ta_momentum",
                display_name="TA Momentum Agent",
                description=(
                    "技术动量分析专家,对BTC/ETH/SOL进行多时间框架(15m/60m)技术分析,"
                    "识别最佳交易机会并提供止损止盈建议,用于动量策略的技术分析层。\n\n"
                    "**职责**:\n"
                    "- 多币种分析: BTC, ETH, SOL\n"
                    "- 双时间框架: 15分钟(主导) + 60分钟(确认)\n"
                    "- 技术指标: EMA排列、RSI、MACD、布林带、ATR、成交量\n"
                    "- 趋势判断: STRONG_UPTREND/UPTREND/NEUTRAL/DOWNTREND/STRONG_DOWNTREND\n"
                    "- 信号生成: LONG/SHORT/HOLD + 信号强度(0-1)\n\n"
                    "**输出**:\n"
                    "- 每个币种的技术分析结果\n"
                    "- Best Opportunity: 信号最强的交易机会\n"
                    "- 止损止盈建议: ATR-based止损距离和风险回报比"
                ),
                agent_module="app.agents.ta_momentum_agent",
                agent_class="TAMomentumAgent",
                available_tools=[
                    "calculate_ema",
                    "calculate_rsi",
                    "calculate_macd",
                    "calculate_bollinger_bands",
                    "calculate_atr",
                    "identify_trend",
                    "generate_signal"
                ],
                is_active=True
            )
            db.add(ta_agent)
            print("   ✅ 创建TAMomentumAgent记录")
        
        # 提交到数据库
        await db.commit()
        
        print("\n" + "=" * 60)
        print("✅ 动量策略Agent注册完成!")
        print("=" * 60)
        
        # 验证
        print("\n验证结果:")
        result = await db.execute(
            select(AgentRegistry).where(
                AgentRegistry.agent_name.in_(["regime_filter", "ta_momentum"])
            )
        )
        agents = result.scalars().all()
        
        for agent in agents:
            print(f"\n  📋 {agent.display_name}")
            print(f"     - ID: {agent.id}")
            print(f"     - Name: {agent.agent_name}")
            print(f"     - Module: {agent.agent_module}")
            print(f"     - Class: {agent.agent_class}")
            print(f"     - Active: {agent.is_active}")
            print(f"     - Tools: {len(agent.available_tools or [])}")
        
        print("\n💡 现在可以在Admin页面的Agent List中看到这两个Agent了!")


if __name__ == "__main__":
    asyncio.run(register_momentum_agents())

