"""初始化注册表

初始化Agent、Tool、API注册表
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models import AgentRegistry, ToolRegistry, APIConfig


async def init_agent_registry(db):
    """初始化业务Agent注册表"""
    print("\n📦 初始化业务Agent注册表...")
    
    agents = [
        {
            "agent_name": "macro",
            "display_name": "The Oracle - 宏观分析Agent",
            "description": "分析宏观经济指标（联邦基金利率、M2货币供应、美元指数、恐惧贪婪指数等）对BTC的影响",
            "agent_module": "app.agents.macro_agent",
            "agent_class": "MacroAgent",
            "available_tools": ["fetch_macro_data", "fetch_fear_greed"],
        },
        {
            "agent_name": "ta",
            "display_name": "Momentum Scout - 技术分析Agent",
            "description": "使用技术指标（RSI、MACD、布林带、移动平均等）分析价格走势和动量",
            "agent_module": "app.agents.ta_agent",
            "agent_class": "TAAgent",
            "available_tools": ["calculate_indicators"],
        },
        {
            "agent_name": "onchain",
            "display_name": "Data Warden - 链上分析Agent",
            "description": "分析链上数据（交易量、活跃地址、难度调整、mempool状态等）",
            "agent_module": "app.agents.onchain_agent",
            "agent_class": "OnChainAgent",
            "available_tools": ["fetch_onchain_data"],
        },
    ]
    
    for agent_data in agents:
        result = await db.execute(
            select(AgentRegistry).where(AgentRegistry.agent_name == agent_data["agent_name"])
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"   ⚠️  Agent '{agent_data['agent_name']}' 已存在，跳过")
            continue
        
        agent = AgentRegistry(
            **agent_data,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(agent)
        print(f"   ✓ 创建 Agent: {agent_data['display_name']}")
    
    await db.commit()
    print("✅ Agent注册表初始化完成")


async def init_tool_registry(db):
    """初始化Tool注册表"""
    print("\n🔧 初始化Tool注册表...")
    
    tools = [
        {
            "tool_name": "fetch_macro_data",
            "display_name": "获取宏观经济数据",
            "description": "从FRED API获取宏观经济指标（DFF, M2, DXY, DGS10等）",
            "tool_module": "app.services.data_collectors.fred",
            "tool_function": "FREDCollector.collect",
            "required_apis": ["fred_api"],
        },
        {
            "tool_name": "fetch_fear_greed",
            "display_name": "获取恐惧贪婪指数",
            "description": "从Alternative.me API获取比特币恐惧贪婪指数",
            "tool_module": "app.services.data_collectors.alternative_me",
            "tool_function": "AlternativeMeCollector.collect",
            "required_apis": ["alternative_me_api"],
        },
        {
            "tool_name": "calculate_indicators",
            "display_name": "计算技术指标",
            "description": "计算技术指标（RSI, MACD, 布林带, MA等）",
            "tool_module": "app.services.indicators.calculator",
            "tool_function": "IndicatorCalculator.calculate_all",
            "required_apis": ["binance_api"],
        },
        {
            "tool_name": "fetch_onchain_data",
            "display_name": "获取链上数据",
            "description": "从Blockchain.info和Mempool.space获取链上指标",
            "tool_module": "app.services.data_collectors.manager",
            "tool_function": "DataManager.collect_for_onchain_agent",
            "required_apis": ["blockchain_info_api", "mempool_space_api"],
        },
    ]
    
    for tool_data in tools:
        result = await db.execute(
            select(ToolRegistry).where(ToolRegistry.tool_name == tool_data["tool_name"])
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"   ⚠️  Tool '{tool_data['tool_name']}' 已存在，跳过")
            continue
        
        tool = ToolRegistry(
            **tool_data,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(tool)
        print(f"   ✓ 创建 Tool: {tool_data['display_name']}")
    
    await db.commit()
    print("✅ Tool注册表初始化完成")


async def init_api_config(db):
    """初始化API配置表"""
    print("\n🌐 初始化API配置表...")
    
    apis = [
        {
            "api_name": "binance_api",
            "display_name": "Binance API",
            "description": "币安交易所API，用于获取市场数据和执行交易",
            "base_url": "https://api.binance.com",
            "rate_limit": 1200,
        },
        {
            "api_name": "fred_api",
            "display_name": "FRED API",
            "description": "美联储经济数据API，提供宏观经济指标",
            "base_url": "https://api.stlouisfed.org/fred",
            "rate_limit": 120,
        },
        {
            "api_name": "alternative_me_api",
            "display_name": "Alternative.me API",
            "description": "比特币恐惧贪婪指数API",
            "base_url": "https://api.alternative.me",
            "rate_limit": 60,
        },
        {
            "api_name": "blockchain_info_api",
            "display_name": "Blockchain.info API",
            "description": "比特币区块链数据API",
            "base_url": "https://blockchain.info",
            "rate_limit": 300,
        },
        {
            "api_name": "mempool_space_api",
            "display_name": "Mempool.space API",
            "description": "比特币内存池和链上数据API",
            "base_url": "https://mempool.space/api",
            "rate_limit": 600,
        },
        {
            "api_name": "glassnode_api",
            "display_name": "Glassnode API",
            "description": "链上数据和指标API（备用）",
            "base_url": "https://api.glassnode.com",
            "rate_limit": 100,
        },
    ]
    
    for api_data in apis:
        result = await db.execute(
            select(APIConfig).where(APIConfig.api_name == api_data["api_name"])
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"   ⚠️  API '{api_data['api_name']}' 已存在，跳过")
            continue
        
        api = APIConfig(
            **api_data,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(api)
        print(f"   ✓ 创建 API: {api_data['display_name']}")
    
    await db.commit()
    print("✅ API配置表初始化完成")


async def init_all_registries():
    """初始化所有注册表"""
    print("=" * 60)
    print("初始化注册表")
    print("=" * 60)
    
    async with AsyncSessionLocal() as db:
        try:
            await init_agent_registry(db)
            await init_tool_registry(db)
            await init_api_config(db)
            
            print("\n" + "=" * 60)
            print("✅ 所有注册表初始化完成!")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ 初始化失败: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(init_all_registries())

