"""End-to-end test of OnChainAgent"""

import asyncio
from app.agents.onchain_agent import OnChainAgent
from app.services.data_collectors.manager import data_manager


async def test_onchain_agent():
    """Test OnChainAgent end-to-end"""

    print("=" * 80)
    print("🧪 Testing OnChainAgent End-to-End")
    print("=" * 80)

    # Step 1: Collect data
    print("\n[1] Collecting on-chain data...")
    print("-" * 80)

    try:
        market_data = await data_manager.collect_for_onchain_agent()
        print(f"✅ Data collected successfully")
        print(f"   Keys: {list(market_data.keys())}")

        if "blockchain_info" in market_data:
            blockchain_info = market_data["blockchain_info"]
            print(f"   Blockchain Info:")
            print(f"     - Active addresses: {blockchain_info.get('active_addresses_24h')}")
            print(f"     - Market cap: {blockchain_info.get('market_cap')}")

        if "mempool_space" in market_data:
            mempool_space = market_data["mempool_space"]
            print(f"   Mempool Space:")
            print(f"     - Fees: {mempool_space.get('recommended_fees')}")

    except Exception as e:
        print(f"❌ Data collection failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 2: Create OnChainAgent and analyze
    print("\n[2] Creating OnChainAgent and running analysis...")
    print("-" * 80)

    try:
        agent = OnChainAgent()
        print(f"✅ OnChainAgent created")
        print(f"   Name: {agent.name}")
        print(f"   Description: {agent.description}")

    except Exception as e:
        print(f"❌ OnChainAgent creation failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 3: Run analysis
    user_query = "结合链上数据，说说现在能不能买BTC"
    print(f"\n[3] Running analysis with query: '{user_query}'...")
    print("-" * 80)

    try:
        result = await agent.analyze(user_query, market_data)
        print(f"✅ Analysis completed successfully!")
        print(f"\n📊 Results:")
        print(f"   Agent: {result.agent_name}")
        print(f"   Signal: {result.signal}")
        print(f"   Confidence: {result.confidence}")
        print(f"   Confidence Level: {result.confidence_level}")
        print(f"   Network Health: {result.network_health}")
        print(f"   Reasoning: {result.reasoning[:200]}...")

        print(f"\n📈 On-Chain Metrics:")
        for key, value in result.onchain_metrics.items():
            print(f"     - {key}: {value}")

        print(f"\n🔍 Key Observations ({len(result.key_observations)}):")
        for i, obs in enumerate(result.key_observations, 1):
            print(f"     {i}. {obs}")

        print(f"\n✅ ✅ ✅ OnChainAgent is working correctly!")

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)
    print("🎉 Test completed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_onchain_agent())
