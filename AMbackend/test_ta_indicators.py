"""Test technical indicators in Research Workflow"""

import asyncio
import json
from app.workflows.research_workflow import research_workflow


async def test_ta_indicators():
    """Test that technical indicators are properly collected and displayed"""
    print("=" * 80)
    print("🧪 Testing Technical Indicators in Research Workflow")
    print("=" * 80)

    event_count = 0
    data_collected_event = None
    ta_agent_event = None

    async for event in research_workflow.process_question("现在适合买BTC吗？"):
        event_count += 1
        event_type = event.get("type")
        print(f"\n[Event {event_count}] Type: {event_type}")

        if event_type == "data_collected":
            data_collected_event = event
            data = event["data"]
            print(f"\n📊 Data Collected:")
            print(f"  BTC Price: ${data.get('btc_price', 'N/A'):,.2f}")
            print(f"  24h Change: {data.get('price_change_24h', 0):+.2f}%")

            # Check technical indicators
            tech_indicators = data.get("technical_indicators")
            if tech_indicators:
                print(f"\n  ✅ Technical Indicators Found:")

                # EMA
                ema = tech_indicators.get("ema", {})
                print(f"    - EMA 9: ${ema.get('period_9', 'N/A')}")
                print(f"    - EMA 20: ${ema.get('period_20', 'N/A')}")
                print(f"    - EMA 50: ${ema.get('period_50', 'N/A')}")
                print(f"    - EMA 200: ${ema.get('period_200', 'N/A')}")

                # RSI
                rsi = tech_indicators.get("rsi", {})
                print(f"    - RSI: {rsi.get('value', 'N/A')}")

                # MACD
                macd = tech_indicators.get("macd", {})
                print(f"    - MACD Histogram: {macd.get('histogram', 'N/A')}")

                # Bollinger Bands
                bb = tech_indicators.get("bollinger_bands", {})
                print(f"    - BB Upper: ${bb.get('upper', 'N/A')}")
                print(f"    - BB Lower: ${bb.get('lower', 'N/A')}")
            else:
                print(f"  ❌ No Technical Indicators in data_collected event")

        elif event_type == "agent_result":
            agent_name = event["data"].get("agent_name")
            print(f"\n🤖 Agent: {agent_name}")
            print(f"  Signal: {event['data'].get('signal')}")
            print(f"  Confidence: {event['data'].get('confidence'):.2%}")

            if agent_name == "ta_agent":
                ta_agent_event = event
                data = event["data"]

                # Check technical indicators in TAAgent result
                tech_indicators = data.get("technical_indicators")
                if tech_indicators:
                    print(f"\n  ✅ TAAgent Technical Indicators:")
                    print(f"    EMA: {tech_indicators.get('ema', {}).get('trend', 'N/A')}")
                    print(f"    RSI: {tech_indicators.get('rsi', {}).get('status', 'N/A')}")
                    print(f"    MACD: {tech_indicators.get('macd', {}).get('status', 'N/A')}")
                else:
                    print(f"  ❌ No Technical Indicators in TAAgent result")

                # Check support/resistance levels
                support_levels = data.get("support_levels", [])
                resistance_levels = data.get("resistance_levels", [])
                print(f"\n  Support Levels: {support_levels}")
                print(f"  Resistance Levels: {resistance_levels}")

                # Check key patterns
                key_patterns = data.get("key_patterns", [])
                if key_patterns:
                    print(f"\n  Key Patterns:")
                    for pattern in key_patterns:
                        print(f"    - {pattern}")

        elif event_type == "error":
            print(f"\n❌ Error: {event['data'].get('error')}")
            break

        elif event_type == "final_answer":
            print(f"\n✅ Final Answer Received")

    print("\n" + "=" * 80)
    print("📋 Test Summary")
    print("=" * 80)

    # Verify data_collected has technical indicators
    if data_collected_event:
        has_indicators = "technical_indicators" in data_collected_event["data"]
        print(f"✅ data_collected event has technical_indicators: {has_indicators}")
    else:
        print(f"❌ No data_collected event received")

    # Verify TAAgent result has detailed indicators
    if ta_agent_event:
        data = ta_agent_event["data"]
        has_tech_indicators = "technical_indicators" in data
        has_support_levels = "support_levels" in data
        has_resistance_levels = "resistance_levels" in data
        has_key_patterns = "key_patterns" in data

        print(f"✅ ta_agent result has technical_indicators: {has_tech_indicators}")
        print(f"✅ ta_agent result has support_levels: {has_support_levels}")
        print(f"✅ ta_agent result has resistance_levels: {has_resistance_levels}")
        print(f"✅ ta_agent result has key_patterns: {has_key_patterns}")
    else:
        print(f"⚠️  No ta_agent result received (might be network timeout)")

    print(f"\n✅ Total events: {event_count}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_ta_indicators())
