"""Test PlanningAgent to verify OnChainAgent is being planned"""

import asyncio
from app.agents.planning_agent import planning_agent
from app.agents.registry import agent_registry


async def test_planning_with_onchain():
    """Test PlanningAgent to see if it includes OnChainAgent"""

    print("=" * 80)
    print("🧪 Testing PlanningAgent - OnChainAgent Integration")
    print("=" * 80)

    # Step 1: Check Agent Registry
    print("\n[1] Checking Agent Registry...")
    print("-" * 80)

    available_agents = agent_registry.get_available_agents()
    print(f"✅ Available agents: {len(available_agents)}")
    for agent in available_agents:
        print(f"  - {agent.name} ({agent.display_name}) - Priority: {agent.priority_hint}")

    available_names = agent_registry.get_available_agent_names()
    print(f"\n📋 Available agent names: {available_names}")

    # Check if onchain_agent is available
    is_onchain_available = agent_registry.is_agent_available("onchain_agent")
    print(f"\n🔍 Is onchain_agent available? {is_onchain_available}")

    if is_onchain_available:
        onchain_info = agent_registry.get_agent_info("onchain_agent")
        print(f"   - Display Name: {onchain_info.display_name}")
        print(f"   - Description: {onchain_info.description}")
        print(f"   - Priority: {onchain_info.priority_hint}")
        print(f"   - Is Available: {onchain_info.is_available}")

    # Step 2: Get LLM Description
    print("\n[2] Getting LLM-formatted agent descriptions...")
    print("-" * 80)

    llm_desc = agent_registry.get_agent_descriptions_for_llm()
    print("Agent descriptions for LLM:")
    print(llm_desc)

    # Step 3: Test Planning with investment question
    print("\n[3] Testing PlanningAgent with investment question...")
    print("-" * 80)

    test_questions = [
        "现在适合买BTC吗？",
        "分析当前BTC市场情况",
        "比特币网络是否健康？",
    ]

    for question in test_questions:
        print(f"\n❓ Question: {question}")
        print("-" * 40)

        try:
            plan = await planning_agent.plan(question)

            print(f"✅ Plan created successfully")
            print(f"\n📊 Analysis Phase Agents ({len(plan.task_breakdown.analysis_phase)}):")
            for agent_plan in plan.task_breakdown.analysis_phase:
                print(f"  - {agent_plan.agent} (Priority: {agent_plan.priority})")
                print(f"    Reason: {agent_plan.reason[:100]}...")

            print(f"\n⚙️  Execution Strategy:")
            print(f"  - Parallel: {plan.execution_strategy.parallel_agents}")
            print(f"  - Sequential: {plan.execution_strategy.sequential_after}")
            print(f"  - Estimated Time: {plan.execution_strategy.estimated_time}")

            print(f"\n💭 Reasoning: {plan.reasoning[:200]}...")

            # Check if onchain_agent is in the plan
            onchain_in_plan = any(
                agent_plan.agent == "onchain_agent"
                for agent_plan in plan.task_breakdown.analysis_phase
            )

            if onchain_in_plan:
                print(f"\n✅ ✅ ✅ OnChainAgent IS in the plan!")
            else:
                print(f"\n❌ ❌ ❌ OnChainAgent NOT in the plan!")
                print(f"   Only these agents were selected: {[ap.agent for ap in plan.task_breakdown.analysis_phase]}")

        except Exception as e:
            print(f"❌ Error creating plan: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 80)
    print("🎉 Test completed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_planning_with_onchain())
