"""Debug SSE streaming issue - simulate the exact user scenario"""

import asyncio
import sys

# Add the backend to path
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from app.workflows.research_workflow import research_workflow


async def debug_sse_streaming():
    """Simulate the exact user question and see where it breaks"""

    user_question = "结合链上数据，说说现在能不能买BTC"

    print("=" * 80)
    print(f"🔍 Debugging SSE Stream for: {user_question}")
    print("=" * 80)

    event_count = 0
    last_event_type = None

    try:
        async for event in research_workflow.process_question(user_question):
            event_count += 1
            event_type = event.get('type')
            last_event_type = event_type

            print(f"\n[Event #{event_count}] Type: {event_type}")
            print("-" * 80)

            if event_type == 'status':
                print(f"  Stage: {event['data'].get('stage')}")
                print(f"  Message: {event['data'].get('message')}")

            elif event_type == 'planning_result':
                analysis_phase = event['data']['task_breakdown']['analysis_phase']
                print(f"  Analysis Phase Agents: {len(analysis_phase)}")
                for agent in analysis_phase:
                    print(f"    - {agent['agent']} (Priority: {agent['priority']})")

            elif event_type == 'agent_result':
                agent_name = event['data'].get('agent_name')
                signal = event['data'].get('signal')
                confidence = event['data'].get('confidence')
                print(f"  Agent: {agent_name}")
                print(f"  Signal: {signal}")
                print(f"  Confidence: {confidence}")

                if agent_name == 'onchain_agent':
                    print(f"  ✅ OnChainAgent executed successfully!")

            elif event_type == 'final_answer':
                answer = event['data'].get('answer', '')
                print(f"  Answer length: {len(answer)} chars")
                print(f"  Answer preview: {answer[:200]}...")

            elif event_type == 'error':
                error_msg = event['data'].get('error')
                print(f"  ❌ ERROR: {error_msg}")

        print("\n" + "=" * 80)
        print(f"✅ Stream completed successfully!")
        print(f"   Total events: {event_count}")
        print(f"   Last event: {last_event_type}")
        print("=" * 80)

    except Exception as e:
        print("\n" + "=" * 80)
        print(f"❌ Stream interrupted!")
        print(f"   Total events before crash: {event_count}")
        print(f"   Last successful event: {last_event_type}")
        print(f"   Error: {e}")
        print("=" * 80)

        import traceback
        print("\nFull traceback:")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_sse_streaming())
