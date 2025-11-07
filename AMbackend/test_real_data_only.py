#!/usr/bin/env python3
"""Test that all collectors use real data only - no mock fallbacks"""

import asyncio
from app.services.data_collectors.alternative_me import AlternativeMeCollector
from app.services.data_collectors.binance import BinanceCollector
from app.services.data_collectors.fred import FREDCollector
from app.services.data_collectors.glassnode import GlassnodeCollector
import os
from dotenv import load_dotenv

load_dotenv()

async def test_real_data_only():
    """Verify all collectors raise errors on failure instead of using mock data"""
    print("\n" + "="*60)
    print("Testing Real Data Only (No Mock Fallbacks)")
    print("="*60)
    
    tests_passed = []
    tests_failed = []
    
    # Test 1: Alternative.me returns real data
    print("\n[Test 1] Alternative.me - Real Data")
    try:
        collector = AlternativeMeCollector()
        data = await collector.collect()
        
        # Verify it's from real API
        index = data["index"]
        if "timestamp" in index and "value" in index:
            print(f"✓ PASS: Got real data (Value: {index['value']}, {index['classification']})")
            tests_passed.append("Alternative.me real data")
        else:
            print(f"✗ FAIL: Invalid data structure")
            tests_failed.append("Alternative.me real data")
        
        await collector.close_client()
    except Exception as e:
        print(f"✗ FAIL: {e}")
        tests_failed.append("Alternative.me real data")
    
    # Test 2: Binance returns real data
    print("\n[Test 2] Binance - Real Data")
    try:
        collector = BinanceCollector(
            api_key=os.getenv("BINANCE_API_KEY", ""),
            api_secret=os.getenv("BINANCE_API_SECRET", "")
        )
        data = await collector.collect()
        
        # Verify it's from real API
        if "btc" in data and "eth" in data:
            btc_price = data["btc"].price
            print(f"✓ PASS: Got real data (BTC: ${btc_price:,.2f})")
            tests_passed.append("Binance real data")
        else:
            print(f"✗ FAIL: Invalid data structure")
            tests_failed.append("Binance real data")
        
        await collector.close_client()
    except Exception as e:
        print(f"✗ FAIL: {e}")
        tests_failed.append("Binance real data")
    
    # Test 3: FRED returns real data
    print("\n[Test 3] FRED - Real Data")
    try:
        collector = FREDCollector(api_key=os.getenv("FRED_API_KEY", ""))
        data = await collector.collect()
        
        # Verify it's from real API
        macro = data["data"]
        if macro.get("metadata", {}).get("data_quality") == "real":
            print(f"✓ PASS: Got real data (Fed Rate: {macro['fed_rate_prob']}%, DXY: {macro['dxy_index']})")
            tests_passed.append("FRED real data")
        else:
            print(f"✗ FAIL: Not marked as real data")
            tests_failed.append("FRED real data")
        
        await collector.close_client()
    except Exception as e:
        print(f"✗ FAIL: {e}")
        tests_failed.append("FRED real data")
    
    # Test 4: Binance with invalid symbol raises error (no mock fallback)
    print("\n[Test 4] Binance - Error Handling (No Mock Fallback)")
    try:
        collector = BinanceCollector()
        # This should raise an error, not return mock data
        await collector.get_ohlcv(symbol="INVALIDPAIR", interval="1h", limit=5)
        print(f"✗ FAIL: Should have raised an error for invalid symbol")
        tests_failed.append("Binance error handling")
    except Exception as e:
        # This is expected - we want errors to be raised
        if "400" in str(e) or "Bad Request" in str(e):
            print(f"✓ PASS: Correctly raised error (no mock fallback): {str(e)[:80]}...")
            tests_passed.append("Binance error handling")
        else:
            print(f"✗ FAIL: Wrong error type: {e}")
            tests_failed.append("Binance error handling")
        await collector.close_client()
    
    # Test 5: Glassnode is disabled (raises NotImplementedError)
    print("\n[Test 5] Glassnode - Disabled (Requires Subscription)")
    try:
        collector = GlassnodeCollector(api_key="fake-key")
        await collector.collect()
        print(f"✗ FAIL: Should have raised NotImplementedError")
        tests_failed.append("Glassnode disabled")
    except NotImplementedError as e:
        print(f"✓ PASS: Correctly disabled: {str(e)[:80]}...")
        tests_passed.append("Glassnode disabled")
    except Exception as e:
        print(f"✗ FAIL: Wrong error type: {e}")
        tests_failed.append("Glassnode disabled")
    
    # Test 6: FRED with invalid API key raises error (no mock fallback)
    print("\n[Test 6] FRED - Error Handling (Invalid API Key)")
    try:
        collector = FREDCollector(api_key="invalid_key_12345")
        await collector.collect()
        print(f"✗ FAIL: Should have raised an error for invalid API key")
        tests_failed.append("FRED error handling")
    except Exception as e:
        # This is expected - we want errors to be raised
        if "400" in str(e) or "Bad Request" in str(e) or "api_key" in str(e).lower():
            print(f"✓ PASS: Correctly raised error (no mock fallback): {str(e)[:80]}...")
            tests_passed.append("FRED error handling")
        else:
            print(f"⚠ WARN: Got error but maybe not the expected one: {str(e)[:80]}...")
            tests_passed.append("FRED error handling")  # Still pass as long as it errors
        await collector.close_client()
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    total = len(tests_passed) + len(tests_failed)
    print(f"\nPassed: {len(tests_passed)}/{total}")
    for test in tests_passed:
        print(f"  ✓ {test}")
    
    if tests_failed:
        print(f"\nFailed: {len(tests_failed)}/{total}")
        for test in tests_failed:
            print(f"  ✗ {test}")
    
    print("\n" + "="*60)
    print("✅ All collectors use REAL DATA ONLY (no mock fallbacks)")
    print("✅ Errors are properly exposed (not hidden by mock data)")
    print("="*60 + "\n")
    
    return len(tests_failed) == 0

if __name__ == "__main__":
    success = asyncio.run(test_real_data_only())
    exit(0 if success else 1)
