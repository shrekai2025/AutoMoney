"""Test Research Chat agents"""

import asyncio
from app.agents.super_agent import super_agent
from app.agents.planning_agent import planning_agent


async def test_super_agent():
    """Test SuperAgent routing with GPT-5"""
    print("\n" + "=" * 60)
    print("Testing SuperAgent (GPT-5)")
    print("=" * 60 + "\n")

    test_cases = [
        {
            "question": "什么是比特币?",
            "expected": "DIRECT_ANSWER",
            "description": "Simple knowledge question",
        },
        {
            "question": "现在适合买BTC吗?",
            "expected": "ROUTE_TO_PLANNING",
            "description": "Investment decision question",
        },
        {
            "question": "What is MACD indicator?",
            "expected": "DIRECT_ANSWER",
            "description": "Technical concept explanation",
        },
        {
            "question": "分析当前BTC市场趋势",
            "expected": "ROUTE_TO_PLANNING",
            "description": "Market analysis request",
        },
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"Test Case {i}: {test['description']}")
        print(f"Question: '{test['question']}'")
        print(f"Expected: {test['expected']}")

        try:
            result = await super_agent.route(test["question"])

            print(f"✓ Decision: {result.decision.value}")
            print(f"  Confidence: {result.confidence:.2f}")
            print(f"  Reasoning: {result.reasoning[:100]}...")

            if result.direct_answer:
                print(f"  Direct Answer: {result.direct_answer[:150]}...")

            # Check if matches expected
            if result.decision.value == test["expected"]:
                print("  ✅ PASS\n")
            else:
                print(f"  ⚠️  UNEXPECTED (expected {test['expected']})\n")

        except Exception as e:
            print(f"  ❌ ERROR: {e}\n")
            import traceback

            traceback.print_exc()

    print("=" * 60)
    print("SuperAgent Test Completed")
    print("=" * 60)


async def test_planning_agent():
    """Test PlanningAgent with Claude"""
    print("\n" + "=" * 60)
    print("Testing PlanningAgent (Claude Thinking)")
    print("=" * 60 + "\n")

    test_question = "现在适合买BTC吗？请给我投资建议。"
    print(f"Question: '{test_question}'\n")

    try:
        result = await planning_agent.plan(test_question)

        print("✓ Planning completed successfully!\n")
        print("Task Breakdown:")
        print(f"  Analysis Phase: {len(result.task_breakdown.analysis_phase)} agents")
        for plan in result.task_breakdown.analysis_phase:
            print(f"    - {plan.agent} (priority: {plan.priority})")
            print(f"      Reason: {plan.reason[:80]}...")
            print(f"      Data: {', '.join(plan.data_required[:3])}...")

        print(f"\n  Decision Phase:")
        print(f"    - {result.task_breakdown.decision_phase['agent']}")

        print(f"\nExecution Strategy:")
        print(f"  Parallel: {', '.join(result.execution_strategy.parallel_agents)}")
        print(f"  Sequential: {', '.join(result.execution_strategy.sequential_after)}")
        print(f"  Estimated Time: {result.execution_strategy.estimated_time}")

        print(f"\nReasoning: {result.reasoning[:200]}...")

        print("\n✅ PASS")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback

        traceback.print_exc()

    print("\n" + "=" * 60)
    print("PlanningAgent Test Completed")
    print("=" * 60)


async def main():
    """Run all tests"""
    print("\n🧪 Testing Research Chat Agents\n")

    # Test SuperAgent
    await test_super_agent()

    # Test PlanningAgent
    await test_planning_agent()

    print("\n✨ All tests completed!\n")


if __name__ == "__main__":
    asyncio.run(main())
