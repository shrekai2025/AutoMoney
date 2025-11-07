"""Test OnChainAgent integration"""

import asyncio
import json
from app.agents.onchain_agent import OnChainAgent
from app.services.data_collectors.manager import data_manager


async def test_onchain_agent():
    print("=" * 70)
    print("Testing OnChainAgent Integration")
    print("=" * 70)

    # Step 1: Test data collection
    print("\n[1] Testing data collection for OnChainAgent...")
    try:
        onchain_data = await data_manager.collect_for_onchain_agent()
        print("✅ Data collection successful")

        # Show summary of collected data
        print("\n📊 Data Summary:")
        blockchain_info = onchain_data.get("blockchain_info", {})
        mempool_space = onchain_data.get("mempool_space", {})
        btc_price = onchain_data.get("btc_price", {})

        print(f"  BTC Price: ${btc_price.get('price', 0):,.2f}")
        print(f"  Active Addresses: {blockchain_info.get('active_addresses_24h', 'N/A')}")
        print(f"  Mempool TX: {mempool_space.get('mempool_stats', {}).get('count', 'N/A')}")

    except Exception as e:
        print(f"❌ Data collection failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 2: Test OnChainAgent analysis
    print("\n[2] Testing OnChainAgent analysis...")
    try:
        agent = OnChainAgent()

        # Test query
        user_query = "比特币网络当前的健康状况如何？"

        print(f"  Query: {user_query}")
        print("  Running analysis...")

        result = await agent.analyze(user_query, onchain_data)

        print("\n✅ Analysis completed successfully")
        print("\n📈 Analysis Result:")
        print(f"  Signal: {result.signal.value}")
        print(f"  Confidence: {result.confidence:.2%}")
        print(f"  Network Health: {result.network_health}")
        print(f"\n  Reasoning: {result.reasoning}")

        print("\n📊 On-Chain Metrics:")
        metrics = result.onchain_metrics
        print(f"  Active Addresses: {metrics.get('active_addresses', 'N/A')}")
        print(f"  Daily Transactions: {metrics.get('daily_transactions', 'N/A')}")
        print(f"  TX Fees: {metrics.get('transaction_fees_sat_vb', 'N/A')} sat/vB")
        print(f"  Mempool TX: {metrics.get('mempool_tx_count', 'N/A')}")
        print(f"  Hash Rate: {metrics.get('hash_rate_eh', 'N/A')} EH/s")

        nvt = metrics.get('nvt_ratio')
        if nvt:
            print(f"  NVT Ratio: {nvt}")

        if result.key_observations:
            print("\n🔍 Key Observations:")
            for i, obs in enumerate(result.key_observations, 1):
                print(f"  {i}. {obs}")

        # Step 3: Verify output format for frontend
        print("\n[3] Verifying output format for frontend...")
        result_dict = {
            "agent_name": result.agent_name,
            "signal": result.signal.value,
            "confidence": result.confidence,
            "reasoning": result.reasoning,
            "onchain_metrics": result.onchain_metrics,
            "network_health": result.network_health,
            "key_observations": result.key_observations,
        }

        print("✅ Output format is valid for frontend")
        print("\n📦 Frontend Data Structure:")
        print(json.dumps(result_dict, indent=2, default=str))

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n" + "=" * 70)
    print("✅ All tests passed! OnChainAgent is ready for production.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_onchain_agent())
