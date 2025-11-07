"""Test complete Research Chat workflow end-to-end"""

import asyncio
from app.workflows.research_workflow import research_workflow


async def test_complete_workflow():
    """Test complete workflow with a real question"""
    print("\n" + "=" * 80)
    print("Testing Complete Research Chat Workflow")
    print("=" * 80 + "\n")

    test_questions = [
        "什么是比特币？",  # Should trigger DIRECT_ANSWER
        "现在适合买BTC吗？",  # Should trigger full workflow
    ]

    for question in test_questions:
        print(f"\n{'=' * 80}")
        print(f"Question: '{question}'")
        print("=" * 80 + "\n")

        try:
            event_count = 0
            async for event in research_workflow.process_question(question):
                event_count += 1
                event_type = event.get("type")

                print(f"[Event {event_count}] Type: {event_type}")

                if event_type == "status":
                    print(f"  Status: {event['data']['message']}")

                elif event_type == "super_agent_decision":
                    print(f"  Decision: {event['data']['decision']}")
                    print(f"  Confidence: {event['data']['confidence']:.2f}")
                    print(f"  Reasoning: {event['data']['reasoning'][:100]}...")

                elif event_type == "planning_result":
                    analysis_phase = event['data']['task_breakdown']['analysis_phase']
                    print(f"  Analysis Phase: {len(analysis_phase)} agents")
                    for agent in analysis_phase:
                        print(f"    - {agent['agent']} (priority: {agent['priority']})")

                elif event_type == "data_collected":
                    print(f"  BTC Price: ${event['data'].get('btc_price', 'N/A')}")
                    print(f"  24h Change: {event['data'].get('price_change_24h', 'N/A')}%")

                elif event_type == "agent_result":
                    print(f"  Agent: {event['data']['agent_name']}")
                    print(f"  Signal: {event['data']['signal']}")
                    print(f"  Confidence: {event['data']['confidence']:.2f}")

                elif event_type == "final_answer":
                    answer = event['data'].get('answer', event['data'])
                    if isinstance(answer, str):
                        print(f"  Answer: {answer[:200]}...")
                    else:
                        print(f"  Answer length: {len(str(answer))} chars")

                    if 'key_insights' in event['data']:
                        print(f"  Key Insights: {len(event['data']['key_insights'])} items")

                elif event_type == "error":
                    print(f"  ❌ Error: {event['data']['error']}")

                print()  # Empty line between events

            print(f"✅ Workflow completed successfully! Total events: {event_count}\n")

        except Exception as e:
            print(f"\n❌ Error during workflow: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 80)
    print("All tests completed")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_complete_workflow())
