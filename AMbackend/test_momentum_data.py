#!/usr/bin/env python3
"""
测试动量策略数据采集功能

运行方式:
cd AMbackend
venv/bin/python test_momentum_data.py
"""

import asyncio
import json
from app.services.data_collectors.momentum_data_service import momentum_data_service


async def test_momentum_data_collection():
    """测试动量策略数据采集"""
    
    print("=" * 80)
    print("开始测试动量策略数据采集...")
    print("=" * 80)
    
    try:
        # 采集数据 (BTC, ETH, SOL)
        data = await momentum_data_service.collect_for_momentum_strategy(
            assets=["BTC", "ETH", "SOL"]
        )
        
        print("\n✅ 数据采集成功!\n")
        
        # 打印数据概览
        print("📊 数据概览:")
        print(f"  时间戳: {data['timestamp']}")
        print(f"\n  币种数量: {len(data['assets'])}")
        
        # 检查每个币种的数据
        for asset, asset_data in data['assets'].items():
            print(f"\n  {asset}:")
            if 'error' in asset_data:
                print(f"    ❌ 错误: {asset_data['error']}")
                continue
            
            print(f"    价格: ${asset_data.get('price', 0):,.2f}")
            print(f"    24h变化: {asset_data.get('price_change_24h', 0):+.2f}%")
            print(f"    24h成交量: ${asset_data.get('volume_24h', 0):,.0f}")
            print(f"    15分钟K线: {len(asset_data.get('ohlcv_15m', []))} 根")
            print(f"    60分钟K线: {len(asset_data.get('ohlcv_60m', []))} 根")
            print(f"    资金费率: {asset_data.get('funding_rate', 0):.6f}")
            print(f"    持仓量变化(24h): {asset_data.get('open_interest_change_24h', 0):+.2f}%")
            print(f"    期货溢价: {asset_data.get('futures_premium', 0):+.4f}%")
        
        # 宏观数据
        macro = data.get('macro', {})
        print(f"\n  宏观数据:")
        print(f"    美元指数(DXY): {macro.get('dxy', 'N/A')}")
        print(f"    联邦基金利率: {macro.get('fed_rate', 'N/A')}%")
        print(f"    M2增长: {macro.get('m2_growth', 'N/A')}%")
        print(f"    10年期国债: {macro.get('treasury_10y', 'N/A')}%")
        
        # 市场情绪
        sentiment = data.get('sentiment', {})
        print(f"\n  市场情绪:")
        print(f"    Fear & Greed: {sentiment.get('fear_greed_value', 'N/A')} ({sentiment.get('fear_greed_classification', 'N/A')})")
        
        # 链上数据
        onchain = data.get('onchain', {})
        print(f"\n  链上数据:")
        print(f"    MVRV Z-Score: {onchain.get('btc_mvrv_zscore', 'N/A')}")
        
        print("\n" + "=" * 80)
        print("✅ 所有数据采集测试通过!")
        print("=" * 80)
        
        # 保存完整数据到文件(可选)
        # with open("momentum_data_sample.json", "w") as f:
        #     json.dump(data, f, indent=2, ensure_ascii=False)
        # print("\n💾 完整数据已保存到 momentum_data_sample.json")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_momentum_data_collection())
    exit(0 if success else 1)

