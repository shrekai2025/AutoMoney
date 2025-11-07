"""集成测试：ResearchWorkflow + AgentExecutionRecorder

测试完整的 Research Chat 流程，验证 Agent 执行记录是否正确保存到数据库
"""

import asyncio
import sys
import os
import uuid

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select, desc
from datetime import datetime

from app.models.agent_execution import AgentExecution
from app.workflows.research_workflow import research_workflow
from app.core.config import settings


# Create test database session
test_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def test_workflow_with_recording():
    """测试完整的 ResearchWorkflow 流程并验证数据库记录"""

    print("=" * 80)
    print("集成测试：ResearchWorkflow + AgentExecutionRecorder")
    print("=" * 80)
    print()

    # Create database session
    async with TestSessionLocal() as db:
        try:
            # Test question
            user_message = "BTC现在的市场情况如何？应该买入还是观望？"
            conversation_id = str(uuid.uuid4())  # Generate valid UUID
            user_id = None  # Test without user authentication

            print(f"📝 测试问题: {user_message}")
            print(f"🆔 对话ID: {conversation_id}")
            print()

            # Count executions before workflow
            result_before = await db.execute(
                select(AgentExecution).where(
                    AgentExecution.caller_id == conversation_id
                )
            )
            count_before = len(result_before.scalars().all())
            print(f"✅ 执行前数据库记录数: {count_before}")
            print()

            # Execute workflow
            print("🚀 开始执行 ResearchWorkflow...")
            print("-" * 80)
            print()

            event_count = 0
            agent_results_received = []

            async for event in research_workflow.process_question(
                user_message=user_message,
                chat_history=[],
                db=db,
                user_id=user_id,
                conversation_id=conversation_id,
            ):
                event_count += 1
                event_type = event.get("type")

                if event_type == "status":
                    stage = event["data"].get("stage")
                    message = event["data"].get("message")
                    print(f"  📊 阶段: {stage} - {message}")

                elif event_type == "agent_result":
                    agent_name = event["data"].get("agent_name")
                    signal = event["data"].get("signal")
                    confidence = event["data"].get("confidence")
                    agent_results_received.append(agent_name)
                    print(f"  🤖 Agent结果: {agent_name} - {signal} (置信度: {confidence})")

                elif event_type == "final_answer":
                    answer = event["data"].get("answer", "")
                    summary = event["data"].get("summary", "")
                    print(f"\n  ✅ 最终答案:")
                    print(f"     摘要: {summary}")
                    if answer:
                        print(f"     详情: {answer[:200]}...")

            print()
            print("-" * 80)
            print(f"✅ Workflow 完成，共收到 {event_count} 个事件")
            print(f"✅ 收到 {len(agent_results_received)} 个 Agent 结果: {agent_results_received}")
            print()

            # Verify database records
            print("🔍 验证数据库记录...")
            print()

            result_after = await db.execute(
                select(AgentExecution)
                .where(AgentExecution.caller_id == conversation_id)
                .order_by(desc(AgentExecution.executed_at))
            )
            executions = result_after.scalars().all()
            count_after = len(executions)

            print(f"✅ 执行后数据库记录数: {count_after}")
            print(f"✅ 新增记录数: {count_after - count_before}")
            print()

            # Verify each execution
            if executions:
                print("📋 执行记录详情:")
                print()
                for i, execution in enumerate(executions, 1):
                    print(f"  {i}. Agent: {execution.agent_display_name} ({execution.agent_name})")
                    print(f"     - ID: {execution.id}")
                    print(f"     - 信号: {execution.signal}")
                    print(f"     - 置信度: {execution.confidence}")
                    print(f"     - 状态: {execution.status}")
                    print(f"     - 执行时间: {execution.executed_at}")
                    print(f"     - 耗时: {execution.execution_duration_ms}ms")
                    print(f"     - 调用方: {execution.caller_type}")
                    print(f"     - 调用方ID: {execution.caller_id}")
                    print(f"     - 用户ID: {execution.user_id}")
                    print(f"     - LLM Provider: {execution.llm_provider}")
                    print(f"     - LLM Model: {execution.llm_model}")
                    print()

            # Assertions
            print("🧪 运行断言...")
            print()

            assert count_after > count_before, "❌ 数据库记录数应该增加"
            print("  ✅ 断言1: 数据库记录数已增加")

            expected_agents = {"macro_agent", "ta_agent", "onchain_agent"}
            recorded_agents = {ex.agent_name for ex in executions}
            assert expected_agents.issubset(recorded_agents), f"❌ 期望记录的Agent: {expected_agents}, 实际: {recorded_agents}"
            print(f"  ✅ 断言2: 所有业务Agent已记录 ({expected_agents})")

            for execution in executions:
                assert execution.caller_type == "research_chat", f"❌ caller_type应为 'research_chat', 实际: {execution.caller_type}"
                assert str(execution.caller_id) == conversation_id, f"❌ caller_id应为 '{conversation_id}', 实际: {execution.caller_id}"
                assert execution.status == "success", f"❌ status应为 'success', 实际: {execution.status}"
                assert execution.signal in ["BULLISH", "BEARISH", "NEUTRAL"], f"❌ signal无效: {execution.signal}"
                assert 0 <= execution.confidence <= 1, f"❌ confidence超出范围: {execution.confidence}"
                assert execution.executed_at is not None, "❌ executed_at不应为空"
                assert execution.reasoning, "❌ reasoning不应为空"

            print("  ✅ 断言3: 所有执行记录字段验证通过")
            print()

            print("=" * 80)
            print("🎉 所有测试通过！")
            print("=" * 80)
            print()
            print("📋 测试总结:")
            print(f"  - 测试问题: {user_message}")
            print(f"  - 对话ID: {conversation_id}")
            print(f"  - Workflow事件数: {event_count}")
            print(f"  - Agent结果数: {len(agent_results_received)}")
            print(f"  - 数据库新增记录: {count_after - count_before}")
            print(f"  - 记录的Agent: {', '.join(recorded_agents)}")
            print()
            print("✅ ResearchWorkflow + AgentExecutionRecorder 集成成功！")

        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            raise


async def main():
    """运行测试"""
    try:
        await test_workflow_with_recording()
    finally:
        # Close database connections
        await test_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
