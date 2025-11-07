"""Test OnChain data collection specifically"""

import asyncio
from app.services.data_collectors.manager import data_manager


async def test_onchain_collection():
    """Test if OnChain data collection works"""

    print("=" * 80)
    print("🧪 Testing OnChain Data Collection")
    print("=" * 80)

    try:
        print("\n[1] Testing blockchain_info collector...")
        print("-" * 80)
        blockchain_data = await data_manager.blockchain_info.collect()
        print(f"✅ Blockchain.info data collected")
        print(f"   Keys: {list(blockchain_data.keys())}")
        print(f"   Active addresses: {blockchain_data.get('active_addresses_24h')}")
        print(f"   Source: {blockchain_data.get('source')}")

    except Exception as e:
        print(f"❌ Blockchain.info failed: {e}")
        import traceback
        traceback.print_exc()

    try:
        print("\n[2] Testing mempool_space collector...")
        print("-" * 80)
        mempool_data = await data_manager.mempool_space.collect()
        print(f"✅ Mempool.space data collected")
        print(f"   Keys: {list(mempool_data.keys())}")
        print(f"   Recommended fees: {mempool_data.get('recommended_fees')}")
        print(f"   Source: {mempool_data.get('source')}")

    except Exception as e:
        print(f"❌ Mempool.space failed: {e}")
        import traceback
        traceback.print_exc()

    try:
        print("\n[3] Testing collect_for_onchain_agent()...")
        print("-" * 80)
        onchain_data = await data_manager.collect_for_onchain_agent()
        print(f"✅ OnChain agent data collected")
        print(f"   Keys: {list(onchain_data.keys())}")

        if "blockchain_info" in onchain_data:
            print(f"   ✅ blockchain_info present")
            print(f"      - active_addresses_24h: {onchain_data['blockchain_info'].get('active_addresses_24h')}")
        else:
            print(f"   ❌ blockchain_info MISSING")

        if "mempool_space" in onchain_data:
            print(f"   ✅ mempool_space present")
            print(f"      - recommended_fees: {onchain_data['mempool_space'].get('recommended_fees')}")
        else:
            print(f"   ❌ mempool_space MISSING")

        if "btc_price" in onchain_data:
            print(f"   ✅ btc_price present: {onchain_data['btc_price']}")
        else:
            print(f"   ❌ btc_price MISSING")

    except Exception as e:
        print(f"❌ collect_for_onchain_agent() failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)
    print("🎉 Test completed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_onchain_collection())
