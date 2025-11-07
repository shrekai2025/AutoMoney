#!/usr/bin/env python3
"""Test all integrated APIs with real data"""

import asyncio
from app.services.data_collectors.alternative_me import AlternativeMeCollector
from app.services.data_collectors.binance import BinanceCollector
from app.services.data_collectors.fred import FREDCollector
import os
from dotenv import load_dotenv

load_dotenv()

async def test_alternative_me():
    """Test Alternative.me Fear & Greed Index"""
    print("\n" + "="*60)
    print("Testing Alternative.me API (Fear & Greed Index)")
    print("="*60)
    
    collector = AlternativeMeCollector()
    data = await collector.collect()
    
    index = data["index"]
    print(f"✓ Fear & Greed Index: {index['value']}")
    print(f"  Classification: {index['classification']}")
    print(f"  Timestamp: {index['timestamp']}")
    print(f"  Data Quality: Real API")
    
    await collector.close_client()
    return True

async def test_binance():
    """Test Binance API"""
    print("\n" + "="*60)
    print("Testing Binance API (Market Data)")
    print("="*60)
    
    api_key = os.getenv("BINANCE_API_KEY", "")
    api_secret = os.getenv("BINANCE_API_SECRET", "")
    
    collector = BinanceCollector(api_key=api_key, api_secret=api_secret)
    
    # Test price data
    data = await collector.collect()
    btc = data["btc"]
    eth = data["eth"]
    
    print(f"\n✓ BTC/USDT:")
    print(f"  Price: ${btc.price:,.2f}")
    print(f"  24h Change: {btc.price_change_24h:+.2f}%")
    print(f"  24h Volume: {btc.volume_24h:,.2f} BTC")
    
    print(f"\n✓ ETH/USDT:")
    print(f"  Price: ${eth.price:,.2f}")
    print(f"  24h Change: {eth.price_change_24h:+.2f}%")
    print(f"  24h Volume: {eth.volume_24h:,.2f} ETH")
    
    # Test OHLCV data
    ohlcv = await collector.get_ohlcv("BTCUSDT", "1h", 5)
    print(f"\n✓ OHLCV Data (last 5 hourly candles):")
    for candle in ohlcv[-3:]:
        print(f"  {candle.timestamp}: O=${candle.open:,.0f} H=${candle.high:,.0f} L=${candle.low:,.0f} C=${candle.close:,.0f}")
    
    await collector.close_client()
    return True

async def test_fred():
    """Test FRED API"""
    print("\n" + "="*60)
    print("Testing FRED API (Macroeconomic Data)")
    print("="*60)
    
    api_key = os.getenv("FRED_API_KEY", "")
    
    if not api_key:
        print("✗ FRED_API_KEY not found in .env")
        return False
    
    collector = FREDCollector(api_key=api_key)
    data = await collector.collect()
    
    macro = data["data"]
    metadata = macro.get("metadata", {})
    
    print(f"\n✓ Federal Funds Rate (DFF): {macro['fed_rate_prob']:.2f}%")
    print(f"✓ M2 Money Supply Growth: {macro['m2_growth']:+.2f}%")
    print(f"✓ US Dollar Index (DXY): {macro['dxy_index']:.4f}")
    print(f"✓ 10-Year Treasury Rate: {metadata.get('dgs10_rate', 0):.2f}%")
    print(f"\n  Data Quality: {metadata.get('data_quality', 'unknown')}")
    print(f"  Source: {metadata.get('source', 'unknown')}")
    
    await collector.close_client()
    return True

async def main():
    """Run all API tests"""
    print("\n" + "="*60)
    print("AutoMoney Data API Integration Test")
    print("="*60)
    
    results = {}
    
    try:
        results["alternative_me"] = await test_alternative_me()
    except Exception as e:
        print(f"✗ Alternative.me test failed: {e}")
        results["alternative_me"] = False
    
    try:
        results["binance"] = await test_binance()
    except Exception as e:
        print(f"✗ Binance test failed: {e}")
        results["binance"] = False
    
    try:
        results["fred"] = await test_fred()
    except Exception as e:
        print(f"✗ FRED test failed: {e}")
        results["fred"] = False
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    passed = sum(results.values())
    total = len(results)
    
    for name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{name:20s}: {status}")
    
    print(f"\nTotal: {passed}/{total} APIs working")
    print("="*60 + "\n")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
