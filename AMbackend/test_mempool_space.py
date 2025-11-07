"""Test Mempool.space collector"""

import asyncio
import json
from app.services.data_collectors.mempool_space import MempoolSpaceCollector


async def test_mempool_space():
    print("Testing Mempool.space API...")
    print("=" * 60)

    collector = MempoolSpaceCollector()

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

        fees = data.get('recommended_fees')
        if fees:
            print(f"  - Recommended fees:")
            print(f"    - Fastest: {fees.get('fastestFee')} sat/vB")
            print(f"    - Half hour: {fees.get('halfHourFee')} sat/vB")
            print(f"    - Hour: {fees.get('hourFee')} sat/vB")

        mempool = data.get('mempool_stats')
        if mempool:
            print(f"  - Mempool stats:")
            print(f"    - TX count: {mempool.get('count', 0):,}")
            print(f"    - Size: {mempool.get('vsize', 0):,} vB")

        tip = data.get('tip_height')
        if tip:
            print(f"  - Block height: {tip:,}")

        diff = data.get('difficulty_adjustment')
        if diff:
            print(f"  - Difficulty adjustment:")
            print(f"    - Progress: {diff.get('progressPercent', 0):.2f}%")
            print(f"    - Estimated change: {diff.get('difficultyChange', 0):.2f}%")


if __name__ == "__main__":
    asyncio.run(test_mempool_space())
