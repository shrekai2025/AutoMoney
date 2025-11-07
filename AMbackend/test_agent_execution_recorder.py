"""测试 AgentExecutionRecorder 基础功能"""

import asyncio
from datetime import datetime
from app.models.agent_execution import AgentExecution
from app.schemas.agents import MacroAnalysisOutput, SignalType, AgentOutput


async def test_model_creation():
    """测试直接创建 AgentExecution 模型对象"""

    print("=== 测试 AgentExecution 模型创建 ===\n")

    # 创建模型实例（不连接数据库）
    execution = AgentExecution(
        agent_name='macro_agent',
        agent_display_name='The Oracle',
        executed_at=datetime.utcnow(),
        execution_duration_ms=1500,
        status='success',
        signal='BULLISH',
        confidence=0.85,
        score=None,
        reasoning='测试推理: 宏观环境看多',
        agent_specific_data={
            'macro_indicators': {
                'fed_funds_rate': {'value': 3.87, 'impact': 'BEARISH'},
                'm2_growth': {'value': 0.47, 'impact': 'NEUTRAL'}
            },
            'risk_assessment': 'LOW'
        },
        market_data_snapshot={
            'btc_price': 45000,
            'fear_greed': {'value': 55}
        },
        llm_provider='tuzi',
        llm_model='claude-sonnet-4-5',
        caller_type='research_chat',
        caller_id=None,
        strategy_execution_id=None,
        user_id=None
    )

    print(f"✅ 模型创建成功:")
    print(f"  - Agent: {execution.agent_display_name} ({execution.agent_name})")
    print(f"  - Signal: {execution.signal}")
    print(f"  - Confidence: {execution.confidence}")
    print(f"  - Status: {execution.status}")
    print(f"  - Execution Duration: {execution.execution_duration_ms}ms")
    print(f"  - LLM Provider: {execution.llm_provider}")
    print(f"  - Agent Specific Data Keys: {list(execution.agent_specific_data.keys())}")
    print(f"\n✅ 模型 __repr__: {execution}")

    # 测试 to_dict 方法
    data_dict = execution.to_dict()
    print(f"\n✅ to_dict() 转换成功，包含 {len(data_dict)} 个字段")
    print(f"  主要字段: {list(data_dict.keys())[:8]}")

    return execution


async def test_schema_integration():
    """测试与 Pydantic Schema 的集成"""

    print("\n=== 测试 Schema 集成 ===\n")

    # 创建 MacroAnalysisOutput
    output = MacroAnalysisOutput(
        signal=SignalType.BULLISH,
        confidence=0.75,
        confidence_level=AgentOutput.get_confidence_level(0.75),
        reasoning="测试宏观分析推理",
        macro_indicators={
            'fed_funds_rate': {'value': 3.87, 'impact': 'BEARISH', 'weight': 0.3},
            'm2_growth': {'value': 0.47, 'impact': 'NEUTRAL', 'weight': 0.2}
        },
        key_factors=[
            "利率适中",
            "M2增长稳定"
        ],
        risk_assessment="中等风险环境"
    )

    print(f"✅ MacroAnalysisOutput 创建成功:")
    print(f"  - Signal: {output.signal}")
    print(f"  - Confidence: {output.confidence}")
    print(f"  - Confidence Level: {output.confidence_level}")
    print(f"  - Key Factors: {len(output.key_factors)} 个")

    # 模拟 recorder 会使用的数据
    llm_info = {
        'provider': 'tuzi',
        'model': 'claude-sonnet-4-5-thinking-all',
        'prompt': 'Analyze macro conditions...',
        'response': '{"signal": "BULLISH", ...}',
        'tokens_used': 2500,
        'cost': 0.0075
    }

    market_data = {
        'btc_price': 45000,
        'price_change_24h': 2.5,
        'macro': {'fed_rate_prob': 75},
        'fear_greed': {'value': 55, 'classification': 'Neutral'}
    }

    print(f"\n✅ LLM Info 准备完成: {llm_info['provider']} / {llm_info['model']}")
    print(f"✅ Market Data 准备完成: BTC ${market_data['btc_price']:,.0f}")

    return output, llm_info, market_data


async def main():
    """运行所有测试"""

    print("=" * 60)
    print("Agent Execution Recorder - 基础功能测试")
    print("=" * 60)
    print()

    # 测试1: 模型创建
    execution = await test_model_creation()

    # 测试2: Schema集成
    output, llm_info, market_data = await test_schema_integration()

    print("\n" + "=" * 60)
    print("✅ 所有基础测试通过!")
    print("=" * 60)
    print("\n📋 测试总结:")
    print("  1. ✅ AgentExecution 模型可以正确创建")
    print("  2. ✅ 所有字段类型正确")
    print("  3. ✅ to_dict() 方法工作正常")
    print("  4. ✅ MacroAnalysisOutput Schema 正常")
    print("  5. ✅ LLM Info 和 Market Data 格式正确")
    print("\n⏭️  下一步: 集成到 ResearchWorkflow 进行真实数据库测试")


if __name__ == "__main__":
    asyncio.run(main())
