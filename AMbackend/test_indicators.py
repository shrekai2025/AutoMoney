"""Test script for technical indicators"""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal

from app.schemas.market_data import OHLCVData
from app.services.indicators import IndicatorCalculator


def generate_sample_data(num_candles: int = 200) -> list:
    """Generate sample OHLCV data for testing"""
    data = []
    base_price = 45000.0
    timestamp = datetime.utcnow() - timedelta(hours=num_candles)

    for i in range(num_candles):
        # Simulate price movement with some randomness
        price_change = (i % 10 - 5) * 50  # Simple oscillation
        close = base_price + price_change + (i * 10)  # Upward trend

        data.append(
            OHLCVData(
                timestamp=timestamp + timedelta(hours=i),
                open=Decimal(str(close - 20)),
                high=Decimal(str(close + 50)),
                low=Decimal(str(close - 50)),
                close=Decimal(str(close)),
                volume=Decimal(str(1000 + i * 10)),
            )
        )

    return data


def main():
    """Test technical indicators"""
    print("Testing Technical Indicators Calculator\n")
    print("=" * 60)

    # Generate sample data
    ohlcv_data = generate_sample_data(200)
    print(f"✓ Generated {len(ohlcv_data)} OHLCV candles")
    print(f"  Price range: {ohlcv_data[0].close} -> {ohlcv_data[-1].close}")

    # Test individual indicators
    print("\n1. Testing EMA (20-period)...")
    ema_20 = IndicatorCalculator.calculate_ema(ohlcv_data, period=20)
    latest_ema = next((v for v in reversed(ema_20) if v is not None), None)
    print(f"   ✓ EMA-20: ${latest_ema:.2f}")

    print("\n2. Testing RSI (14-period)...")
    rsi = IndicatorCalculator.calculate_rsi(ohlcv_data, period=14)
    latest_rsi = next((v for v in reversed(rsi) if v is not None), None)
    print(f"   ✓ RSI-14: {latest_rsi:.2f}")
    if latest_rsi > 70:
        print("   Signal: OVERBOUGHT")
    elif latest_rsi < 30:
        print("   Signal: OVERSOLD")
    else:
        print("   Signal: NEUTRAL")

    print("\n3. Testing MACD...")
    macd = IndicatorCalculator.calculate_macd(ohlcv_data)
    latest_macd = next((v for v in reversed(macd["macd"]) if v is not None), None)
    latest_signal = next((v for v in reversed(macd["signal"]) if v is not None), None)
    latest_hist = next((v for v in reversed(macd["histogram"]) if v is not None), None)
    print(f"   ✓ MACD: {latest_macd:.2f}")
    print(f"   ✓ Signal: {latest_signal:.2f}")
    print(f"   ✓ Histogram: {latest_hist:.2f}")
    if latest_hist > 0:
        print("   Signal: BULLISH")
    else:
        print("   Signal: BEARISH")

    print("\n4. Testing Bollinger Bands...")
    bb = IndicatorCalculator.calculate_bollinger_bands(ohlcv_data)
    latest_upper = next((v for v in reversed(bb["upper"]) if v is not None), None)
    latest_middle = next((v for v in reversed(bb["middle"]) if v is not None), None)
    latest_lower = next((v for v in reversed(bb["lower"]) if v is not None), None)
    current_price = float(ohlcv_data[-1].close)
    print(f"   ✓ Upper: ${latest_upper:.2f}")
    print(f"   ✓ Middle: ${latest_middle:.2f}")
    print(f"   ✓ Lower: ${latest_lower:.2f}")
    print(f"   Current Price: ${current_price:.2f}")

    print("\n5. Testing calculate_all()...")
    all_indicators = IndicatorCalculator.calculate_all(ohlcv_data)
    print(f"   ✓ Calculated {len(all_indicators['indicators'])} indicator groups")
    print(f"   ✓ Data points: {all_indicators['data_points']}")

    print("\n6. Testing trading signals...")
    signals = IndicatorCalculator.get_trading_signals(all_indicators)
    print("   Signals:")
    for indicator, signal in signals.items():
        print(f"     - {indicator}: {signal.upper()}")

    print("\n" + "=" * 60)
    print("✓ All indicator tests passed!")
    print("\nIndicator Summary:")
    print("-" * 60)
    ind = all_indicators["indicators"]
    print(f"EMA-9:    ${ind['ema']['period_9']:.2f}")
    print(f"EMA-20:   ${ind['ema']['period_20']:.2f}")
    print(f"EMA-50:   ${ind['ema']['period_50']:.2f}")
    print(f"EMA-200:  ${ind['ema']['period_200']:.2f}")
    print(f"RSI:      {ind['rsi']['value']:.2f}")
    print(f"MACD:     {ind['macd']['macd']:.2f}")
    print(f"BB Upper: ${ind['bollinger_bands']['upper']:.2f}")
    print(f"BB Lower: ${ind['bollinger_bands']['lower']:.2f}")
    print("-" * 60)


if __name__ == "__main__":
    main()
