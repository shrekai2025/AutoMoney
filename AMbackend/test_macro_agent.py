"""Test MacroAgent with real data"""

import asyncio
import json
from app.agents.macro_agent import macro_agent
from app.services.data_collectors.manager import data_manager


async def test_macro_agent():
    """Test MacroAgent with real market data"""
    print("\n" + "=" * 60)
    print("Testing MacroAgent with Real Data")
    print("=" * 60 + "\n")

    try:
        # Step 1: Collect real market data
        print("📊 Collecting real market data...")
        market_data = await data_manager.collect_for_macro_agent()

        print("\n✅ Market data collected:")
        print(f"  BTC Price: ${market_data['btc_price']:,.2f}")
        print(f"  24h Change: {market_data['price_change_24h']:+.2f}%")

        if market_data.get("macro"):
            macro = market_data["macro"]
            print(f"\n  Macro Indicators:")
            print(f"    Fed Funds Rate: {macro.get('fed_rate_prob', 'N/A')}%")
            print(f"    M2 Growth: {macro.get('m2_growth', 'N/A')}%")
            print(f"    Dollar Index: {macro.get('dxy_index', 'N/A')}")
            if macro.get('metadata'):
                print(f"    10Y Treasury: {macro['metadata'].get('dgs10_rate', 'N/A')}%")

        if market_data.get("fear_greed"):
            fg = market_data["fear_greed"]
            # FearGreedIndex is a Pydantic model, not a dict
            if isinstance(fg, dict):
                print(f"\n  Fear & Greed Index: {fg.get('value', 'N/A')}/100")
                print(f"  Classification: {fg.get('classification', 'N/A')}")
            else:
                # It's already a Pydantic model
                print(f"\n  Fear & Greed Index: {fg.value}/100")
                print(f"  Classification: {fg.classification}")

        # Step 2: Run MacroAgent analysis
        print("\n\n🤖 Running MacroAgent analysis...")
        print("(This may take 10-30 seconds...)\n")

        analysis = await macro_agent.analyze(market_data)

        # Step 3: Display results
        print("\n" + "=" * 60)
        print("MacroAgent Analysis Results")
        print("=" * 60 + "\n")

        print(f"Signal: {analysis.signal.value}")
        print(f"Confidence: {analysis.confidence_percentage}% ({analysis.confidence_level.value})")
        print(f"\nReasoning:\n{analysis.reasoning}\n")

        print(f"Risk Assessment:\n{analysis.risk_assessment}\n")

        print("Key Factors:")
        for i, factor in enumerate(analysis.key_factors, 1):
            print(f"  {i}. {factor}")

        print("\n\nMacro Indicators Analysis:")
        print(json.dumps(analysis.macro_indicators, indent=2))

        # Step 4: Check if backend needs restart for changes to take effect
        print("\n" + "=" * 60)
        print("✅ MacroAgent Test Completed Successfully!")
        print("=" * 60)

        return analysis

    except Exception as e:
        print(f"\n❌ Error during MacroAgent test: {e}")
        import traceback

        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(test_macro_agent())
