"""Test complete workflow to see if OnChainAgent actually runs"""

import asyncio
from app.workflows.research_workflow import research_workflow


async def test_workflow():
    """Test complete Research Workflow"""

    print("=" * 80)
    print("🧪 Testing Complete Research Workflow with OnChainAgent")
    print("=" * 80)

    test_questions = [
        "分析当前BTC市场情况",
        "比特币网络是否健康？",
    ]

    for question in test_questions:
        print(f"\n{'='*80}")
        print(f"❓ Question: {question}")
        print("=" * 80)

        event_count = {}
        onchain_result_found = False

        try:
            async for event in research_workflow.process_question(question):
                event_type = event.get("type")
                event_count[event_type] = event_count.get(event_type, 0) + 1

                print(f"\n📨 Event #{sum(event_count.values())}: {event_type}")
                print("-" * 80)

                if event_type == "status":
                    print(f"   Stage: {event['data'].get('stage')}")
                    print(f"   Message: {event['data'].get('message')}")

                elif event_type == "planning_result":
                    analysis_phase = event['data']['task_breakdown']['analysis_phase']
                    print(f"   Agents Planned: {len(analysis_phase)}")
                    for agent_plan in analysis_phase:
                        print(f"     - {agent_plan['agent']} (Priority: {agent_plan['priority']})")

                    parallel_agents = event['data']['execution_strategy']['parallel_agents']
                    print(f"   Parallel Agents: {parallel_agents}")

                    if "onchain_agent" in parallel_agents:
                        print(f"   ✅ OnChainAgent IN parallel execution list")
                    else:
                        print(f"   ❌ OnChainAgent NOT in parallel execution list")

                elif event_type == "agent_result":
                    agent_name = event['data'].get('agent_name')
                    signal = event['data'].get('signal')
                    confidence = event['data'].get('confidence')

                    print(f"   Agent: {agent_name}")
                    print(f"   Signal: {signal}")
                    print(f"   Confidence: {confidence}")

                    if agent_name == "onchain_agent":
                        onchain_result_found = True
                        print(f"   ✅ ✅ ✅ OnChainAgent EXECUTED SUCCESSFULLY!")

                        # Show on-chain specific data
                        onchain_metrics = event['data'].get('onchain_metrics', {})
                        network_health = event['data'].get('network_health')
                        key_observations = event['data'].get('key_observations', [])

                        print(f"   Network Health: {network_health}")
                        print(f"   Metrics Keys: {list(onchain_metrics.keys())}")
                        print(f"   Observations: {len(key_observations)} items")

                elif event_type == "final_answer":
                    answer = event['data'].get('answer', '')
                    print(f"   Answer Preview: {answer[:200]}...")

                elif event_type == "error":
                    error_msg = event['data'].get('error')
                    print(f"   ❌ Error: {error_msg}")

            print(f"\n{'='*80}")
            print(f"📊 Event Summary for: {question}")
            print(f"{'='*80}")
            for event_type, count in event_count.items():
                print(f"  {event_type}: {count}")

            if onchain_result_found:
                print(f"\n✅ ✅ ✅ OnChainAgent WAS EXECUTED!")
            else:
                print(f"\n❌ ❌ ❌ OnChainAgent WAS NOT EXECUTED!")
                print(f"   Agent results received:")
                for event_type in event_count.keys():
                    if event_type == "agent_result":
                        print(f"     - agent_result events: {event_count[event_type]}")

        except Exception as e:
            print(f"\n❌ Workflow error: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 80)
    print("🎉 Workflow Test Completed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_workflow())
