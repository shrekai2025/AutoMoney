"""完整注册动量策略的Agent、Tool和API

将动量策略相关的所有组件注册到数据库:
1. Agents (agent_registry)
2. Tools (tool_registry)
3. APIs (api_config) - 如果需要
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.db.session import AsyncSessionLocal
from app.models.agent_registry import AgentRegistry
from app.models.tool_registry import ToolRegistry
from sqlalchemy import select


async def register_tools():
    """注册动量策略使用的Tools"""
    
    tools_to_register = [
        # RegimeFilterAgent使用的Tools
        {
            "tool_name": "collect_macro_data",
            "display_name": "Collect Macro Data",
            "description": "采集宏观经济数据,包括美元指数(DXY)、联邦基金利率、M2货币供应增速等",
            "tool_module": "app.services.data_collectors.fred",
            "tool_function": "FREDCollector.get_macro_data",
            "required_apis": ["fred_api"],
        },
        {
            "tool_name": "collect_sentiment_data",
            "display_name": "Collect Sentiment Data",
            "description": "采集市场情绪数据,包括Fear & Greed Index",
            "tool_module": "app.services.data_collectors.alternative_me",
            "tool_function": "AlternativeMeCollector.get_fear_greed_index",
            "required_apis": ["alternative_me_api"],
        },
        {
            "tool_name": "collect_futures_data",
            "display_name": "Collect Futures Data",
            "description": "采集期货衍生品数据,包括资金费率、持仓量、期货溢价",
            "tool_module": "app.services.data_collectors.binance_futures",
            "tool_function": "BinanceFuturesCollector.collect",
            "required_apis": ["binance_api"],
        },
        {
            "tool_name": "calculate_regime_score",
            "display_name": "Calculate Regime Score",
            "description": "计算Regime Score (0-100),综合评估市场环境健康度",
            "tool_module": "app.agents.regime_filter_agent",
            "tool_function": "RegimeFilterAgent._calculate_base_score",
            "required_apis": [],
        },
        
        # TAMomentumAgent使用的Tools
        {
            "tool_name": "collect_ohlcv_data",
            "display_name": "Collect OHLCV Data",
            "description": "采集K线数据(OHLCV),支持多时间框架(15m/60m)和多币种(BTC/ETH/SOL)",
            "tool_module": "app.services.data_collectors.binance",
            "tool_function": "BinanceCollector.get_klines",
            "required_apis": ["binance_api"],
        },
        {
            "tool_name": "calculate_ema",
            "display_name": "Calculate EMA",
            "description": "计算指数移动平均线(EMA),支持多周期(12/26/50/200)",
            "tool_module": "app.services.indicators.calculator",
            "tool_function": "IndicatorCalculator.calculate_ema",
            "required_apis": [],
        },
        {
            "tool_name": "calculate_rsi",
            "display_name": "Calculate RSI",
            "description": "计算相对强弱指标(RSI),默认14周期",
            "tool_module": "app.services.indicators.calculator",
            "tool_function": "IndicatorCalculator.calculate_rsi",
            "required_apis": [],
        },
        {
            "tool_name": "calculate_macd",
            "display_name": "Calculate MACD",
            "description": "计算MACD指标(12/26/9),包括DIF、DEA、MACD柱",
            "tool_module": "app.services.indicators.calculator",
            "tool_function": "IndicatorCalculator.calculate_macd",
            "required_apis": [],
        },
        {
            "tool_name": "calculate_bollinger_bands",
            "display_name": "Calculate Bollinger Bands",
            "description": "计算布林带指标,包括上轨、中轨、下轨",
            "tool_module": "app.services.indicators.calculator",
            "tool_function": "IndicatorCalculator.calculate_bollinger_bands",
            "required_apis": [],
        },
        {
            "tool_name": "calculate_atr",
            "display_name": "Calculate ATR",
            "description": "计算平均真实波动幅度(ATR),用于止损距离计算",
            "tool_module": "app.services.indicators.calculator",
            "tool_function": "IndicatorCalculator.calculate_atr",
            "required_apis": [],
        },
        {
            "tool_name": "identify_trend",
            "display_name": "Identify Trend",
            "description": "识别趋势方向,基于EMA排列和MACD状态",
            "tool_module": "app.agents.ta_momentum_agent",
            "tool_function": "TAMomentumAgent._identify_trend",
            "required_apis": [],
        },
        {
            "tool_name": "generate_trading_signal",
            "display_name": "Generate Trading Signal",
            "description": "生成交易信号(LONG/SHORT/HOLD)和信号强度(0-1)",
            "tool_module": "app.agents.ta_momentum_agent",
            "tool_function": "TAMomentumAgent._generate_signal",
            "required_apis": [],
        },
    ]
    
    async with AsyncSessionLocal() as db:
        print("\n" + "=" * 60)
        print("注册Tools...")
        print("=" * 60)
        
        registered_count = 0
        updated_count = 0
        
        for tool_data in tools_to_register:
            result = await db.execute(
                select(ToolRegistry).where(ToolRegistry.tool_name == tool_data["tool_name"])
            )
            tool = result.scalar_one_or_none()
            
            if tool:
                # 更新已存在的Tool
                tool.display_name = tool_data["display_name"]
                tool.description = tool_data["description"]
                tool.tool_module = tool_data["tool_module"]
                tool.tool_function = tool_data["tool_function"]
                tool.required_apis = tool_data["required_apis"]
                tool.is_active = True
                updated_count += 1
                print(f"  🔄 更新: {tool_data['tool_name']}")
            else:
                # 创建新Tool
                tool = ToolRegistry(**tool_data)
                db.add(tool)
                registered_count += 1
                print(f"  ✅ 创建: {tool_data['tool_name']}")
        
        await db.commit()
        
        print(f"\n📊 Tool注册完成: 新增 {registered_count}, 更新 {updated_count}")


async def register_agents():
    """注册动量策略的Agents"""
    
    agents_to_register = [
        {
            "agent_name": "regime_filter",
            "display_name": "Regime Filter Agent",
            "description": (
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
            "agent_module": "app.agents.regime_filter_agent",
            "agent_class": "RegimeFilterAgent",
            "available_tools": [
                "collect_macro_data",
                "collect_sentiment_data",
                "collect_futures_data",
                "calculate_regime_score"
            ],
        },
        {
            "agent_name": "ta_momentum",
            "display_name": "TA Momentum Agent",
            "description": (
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
            "agent_module": "app.agents.ta_momentum_agent",
            "agent_class": "TAMomentumAgent",
            "available_tools": [
                "collect_ohlcv_data",
                "calculate_ema",
                "calculate_rsi",
                "calculate_macd",
                "calculate_bollinger_bands",
                "calculate_atr",
                "identify_trend",
                "generate_trading_signal"
            ],
        },
    ]
    
    async with AsyncSessionLocal() as db:
        print("\n" + "=" * 60)
        print("注册Agents...")
        print("=" * 60)
        
        registered_count = 0
        updated_count = 0
        
        for agent_data in agents_to_register:
            result = await db.execute(
                select(AgentRegistry).where(AgentRegistry.agent_name == agent_data["agent_name"])
            )
            agent = result.scalar_one_or_none()
            
            if agent:
                # 更新已存在的Agent
                agent.display_name = agent_data["display_name"]
                agent.description = agent_data["description"]
                agent.agent_module = agent_data["agent_module"]
                agent.agent_class = agent_data["agent_class"]
                agent.available_tools = agent_data["available_tools"]
                agent.is_active = True
                updated_count += 1
                print(f"  🔄 更新: {agent_data['agent_name']}")
            else:
                # 创建新Agent
                agent = AgentRegistry(**agent_data)
                db.add(agent)
                registered_count += 1
                print(f"  ✅ 创建: {agent_data['agent_name']}")
        
        await db.commit()
        
        print(f"\n📊 Agent注册完成: 新增 {registered_count}, 更新 {updated_count}")


async def verify_registration():
    """验证注册结果"""
    
    async with AsyncSessionLocal() as db:
        print("\n" + "=" * 60)
        print("验证注册结果")
        print("=" * 60)
        
        # 验证Agents
        print("\n📋 Agents:")
        result = await db.execute(
            select(AgentRegistry).where(
                AgentRegistry.agent_name.in_(["regime_filter", "ta_momentum"])
            )
        )
        agents = result.scalars().all()
        
        for agent in agents:
            print(f"\n  {agent.display_name}")
            print(f"    - Name: {agent.agent_name}")
            print(f"    - Module: {agent.agent_module}")
            print(f"    - Class: {agent.agent_class}")
            print(f"    - Tools: {len(agent.available_tools or [])} ({', '.join((agent.available_tools or [])[:3])}...)")
            print(f"    - Active: {'✅' if agent.is_active else '❌'}")
        
        # 验证Tools
        print("\n🔧 Tools:")
        result = await db.execute(
            select(ToolRegistry).where(
                ToolRegistry.tool_name.in_([
                    "collect_macro_data",
                    "collect_sentiment_data",
                    "collect_futures_data",
                    "calculate_regime_score",
                    "collect_ohlcv_data",
                    "calculate_ema",
                    "calculate_rsi",
                    "calculate_macd",
                    "calculate_bollinger_bands",
                    "calculate_atr",
                    "identify_trend",
                    "generate_trading_signal"
                ])
            )
        )
        tools = result.scalars().all()
        
        print(f"  注册的Tools数量: {len(tools)}")
        for tool in tools[:5]:  # 只显示前5个
            apis = ", ".join(tool.required_apis) if tool.required_apis else "无"
            print(f"    - {tool.display_name} (APIs: {apis})")
        if len(tools) > 5:
            print(f"    ... 还有 {len(tools) - 5} 个Tools")


async def main():
    """主函数"""
    print("=" * 60)
    print("动量策略完整注册脚本")
    print("=" * 60)
    
    try:
        # 1. 注册Tools
        await register_tools()
        
        # 2. 注册Agents
        await register_agents()
        
        # 3. 验证
        await verify_registration()
        
        print("\n" + "=" * 60)
        print("✅ 所有组件注册完成!")
        print("=" * 60)
        print("\n💡 提示:")
        print("  1. 在Admin页面可以查看Agent List和Tool List")
        print("  2. RegimeFilterAgent和TAMomentumAgent现在可见")
        print("  3. 动量策略会自动调用这两个Agent")
        print("  4. Tools列表展示了Agent使用的所有工具")
        
    except Exception as e:
        print(f"\n❌ 注册失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

