"""Test integration of data collection with technical indicators"""

import asyncio
from app.services.data_collectors.manager import data_manager


async def main():
    """Test complete technical analysis integration"""
    print("Testing Technical Analysis Integration")
    print("=" * 70)

    # Test 1: Collect data for TA Agent
    print("\n1. Testing collect_for_ta_agent()...")
    ta_data = await data_manager.collect_for_ta_agent()

    print(f"   ✓ Current BTC Price: ${ta_data['btc_price']:.2f}")
    print(f"   ✓ 24h Volume: ${ta_data['volume_24h']:,.0f}")
    print(f"   ✓ OHLCV Candles: {len(ta_data['ohlcv'])}")
    print(f"   ✓ Indicators Calculated: {ta_data['indicators']['data_points']} data points")

    # Display indicators
    print("\n2. Technical Indicators:")
    print("-" * 70)
    indicators = ta_data["indicators"]

    # EMA
    print("   EMA Indicators:")
    for period, value in indicators["ema"].items():
        if value:
            print(f"     • {period.upper()}: ${value:,.2f}")

    # RSI
    rsi = indicators["rsi"]
    print(f"\n   RSI ({rsi['period']}-period):")
    print(f"     • Value: {rsi['value']:.2f}")
    print(f"     • Signal: {rsi['signal'].upper()}")

    # MACD
    macd = indicators["macd"]
    print(f"\n   MACD:")
    print(f"     • MACD Line: {macd['macd']:.2f}")
    print(f"     • Signal Line: {macd['signal']:.2f}")
    print(f"     • Histogram: {macd['histogram']:.2f}")

    # Bollinger Bands
    bb = indicators["bollinger_bands"]
    print(f"\n   Bollinger Bands:")
    print(f"     • Upper: ${bb['upper']:,.2f}")
    print(f"     • Middle: ${bb['middle']:,.2f}")
    print(f"     • Lower: ${bb['lower']:,.2f}")
    band_width = ((bb["upper"] - bb["lower"]) / bb["middle"]) * 100
    print(f"     • Width: {band_width:.2f}%")

    # Trading Signals
    print("\n3. Trading Signals:")
    print("-" * 70)
    signals = indicators["signals"]
    for signal_name, signal_value in signals.items():
        icon = "🟢" if signal_value == "bullish" else "🔴" if signal_value == "bearish" else "🟡"
        print(f"   {icon} {signal_name.upper()}: {signal_value.upper()}")

    # Test 2: Direct technical analysis call
    print("\n4. Testing get_technical_analysis()...")
    tech_analysis = await data_manager.get_technical_analysis()
    print(f"   ✓ Symbol: {tech_analysis.symbol}")
    print(f"   ✓ Timeframe: {tech_analysis.timeframe}")
    print(f"   ✓ Timestamp: {tech_analysis.timestamp}")
    print(f"   ✓ Overall Signal: {tech_analysis.signals.overall.upper()}")

    # Test 3: Check series data for charting
    print("\n5. Checking series data for charts...")
    series = ta_data["raw_series"]
    print(f"   ✓ EMA series available: {list(series['ema'].keys())}")
    print(f"   ✓ RSI values: {sum(1 for x in series['rsi'] if x is not None)} points")
    print(f"   ✓ MACD values: {sum(1 for x in series['macd']['macd'] if x is not None)} points")
    print(
        f"   ✓ BB values: {sum(1 for x in series['bollinger_bands']['upper'] if x is not None)} points"
    )

    print("\n" + "=" * 70)
    print("✓ Technical Analysis Integration Test Complete!")
    print("\nSummary:")
    print(f"  • Current Price: ${ta_data['btc_price']:,.2f}")
    print(f"  • RSI: {rsi['value']:.2f} ({rsi['signal']})")
    print(f"  • MACD Histogram: {macd['histogram']:.2f}")
    print(f"  • Overall Signal: {signals['overall'].upper()}")


if __name__ == "__main__":
    asyncio.run(main())
