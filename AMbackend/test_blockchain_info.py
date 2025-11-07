"""Test Blockchain.info collector"""

import asyncio
import json
from app.services.data_collectors.blockchain_info import BlockchainInfoCollector


async def test_blockchain_info():
    print("Testing Blockchain.info API...")
    print("=" * 60)

    collector = BlockchainInfoCollector()

    print(f"Is configured: {collector.is_configured}")
    print()

    print("Collecting data...")
    data = await collector.collect()

    print("\nResults:")
    print(json.dumps(data, indent=2, default=str))

    print("\n" + "=" * 60)
    print("Test Summary:")
    if "error" in data:
        print(f"❌ Error: {data['error']}")
    else:
        print("✅ Successfully collected data")
        print(f"  - Active addresses (24h): {data.get('active_addresses_24h')}")

        tx_count = data.get('transaction_count_30d')
        if tx_count:
            print(f"  - Transaction count (30d avg): {tx_count.get('avg_30d')}")
        else:
            print(f"  - Transaction count (30d avg): N/A")

        market_cap = data.get('market_cap')
        if market_cap:
            print(f"  - Market cap: ${market_cap:,.0f}")
        else:
            print(f"  - Market cap: N/A")

        print(f"  - Network stats: {len(data.get('network_stats', {}))} fields")


if __name__ == "__main__":
    asyncio.run(test_blockchain_info())
