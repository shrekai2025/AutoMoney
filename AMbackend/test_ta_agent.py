"""Test TAAgent"""

import asyncio
from datetime import datetime, timedelta
from app.agents.ta_agent import ta_agent
from app.services.indicators.calculator import IndicatorCalculator
from app.schemas.market_data import OHLCVData


def generate_sample_ohlcv_data(num_candles=200):
    """Generate sample OHLCV data for testing"""
    ohlcv_data = []
    base_price = 95000.0
    timestamp = datetime.utcnow() - timedelta(days=num_candles)

    for i in range(num_candles):
        # Simulate price movement with slight trend and volatility
        price_change = (i - num_candles / 2) * 10 + (i % 20 - 10) * 50
        current_price = base_price + price_change

        # Generate OHLC with some variance
        open_price = current_price + (i % 5 - 2) * 20
        high_price = max(open_price, current_price) + abs(i % 7) * 10
        low_price = min(open_price, current_price) - abs(i % 7) * 10
        close_price = current_price
        volume = 1000 + (i % 50) * 100

        ohlcv_data.append(
            OHLCVData(
                timestamp=timestamp + timedelta(days=i),
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=volume,
            )
        )

    return ohlcv_data


async def test_ta_agent():
    """Test TAAgent with sample data"""
    print("=" * 80)
    print("🧪 Testing TAAgent")
    print("=" * 80)

    # Generate sample OHLCV data
    print("\n📊 Generating sample OHLCV data...")
    ohlcv_data = generate_sample_ohlcv_data(200)
    print(f"✅ Generated {len(ohlcv_data)} candles")

    # Calculate technical indicators
    print("\n📈 Calculating technical indicators...")
    indicators = IndicatorCalculator.calculate_all(ohlcv_data)
    print(f"✅ Calculated indicators")
    print(f"   - EMAs: {list(indicators['indicators']['ema'].keys())}")
    print(f"   - RSI: {indicators['indicators']['rsi']['value']:.2f}")
    print(
        f"   - MACD Histogram: {indicators['indicators']['macd']['histogram']:.2f}"
    )
    print(
        f"   - Bollinger Bands: Upper={indicators['indicators']['bollinger_bands']['upper']:.2f}, Lower={indicators['indicators']['bollinger_bands']['lower']:.2f}"
    )

    # Prepare market data
    current_price = float(ohlcv_data[-1].close)
    previous_price = float(ohlcv_data[-2].close)
    price_change_24h = ((current_price - previous_price) / previous_price) * 100

    market_data = {
        "btc_price": current_price,
        "price_change_24h": price_change_24h,
        "indicators": indicators,
    }

    print(f"\n💰 Current BTC Price: ${current_price:,.2f}")
    print(f"📊 24h Change: {price_change_24h:+.2f}%")

    # Test TAAgent
    print("\n🤖 Running TAAgent analysis...")
    try:
        result = await ta_agent.analyze(market_data)

        print("\n" + "=" * 80)
        print("✅ TAAgent Analysis Result")
        print("=" * 80)

        print(f"\n🎯 Signal: {result.signal.value}")
        print(f"💪 Confidence: {result.confidence_percentage}% ({result.confidence_level.value})")
        print(f"\n📝 Reasoning:\n{result.reasoning}")

        print(f"\n📊 Technical Indicators Analysis:")
        if "ema" in result.technical_indicators:
            ema = result.technical_indicators["ema"]
            print(f"   EMA Trend: {ema.get('trend', 'N/A')}")

        if "rsi" in result.technical_indicators:
            rsi = result.technical_indicators["rsi"]
            print(f"   RSI Status: {rsi.get('status', 'N/A')} (Value: {rsi.get('value', 'N/A')})")

        if "macd" in result.technical_indicators:
            macd = result.technical_indicators["macd"]
            print(f"   MACD Status: {macd.get('status', 'N/A')}")

        print(f"\n🛡️ Support Levels: {result.support_levels}")
        print(f"🚧 Resistance Levels: {result.resistance_levels}")

        print(f"\n📈 Trend Analysis:\n{result.trend_analysis}")

        if result.key_patterns:
            print(f"\n🔍 Key Patterns:")
            for pattern in result.key_patterns:
                print(f"   - {pattern}")

        # Show full conversation
        print(f"\n" + "=" * 80)
        print("💬 Full Conversation (for debugging)")
        print("=" * 80)
        print(f"\n📤 Prompt Sent (first 500 chars):\n{result.prompt_sent[:500]}...")
        print(f"\n📥 LLM Response (first 800 chars):\n{result.llm_response[:800]}...")

        return result

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return None


async def test_with_real_indicators():
    """Test TAAgent with pre-calculated indicators (simpler test)"""
    print("\n" + "=" * 80)
    print("🧪 Testing TAAgent with Pre-calculated Indicators")
    print("=" * 80)

    # Mock pre-calculated indicators
    current_price = 96234.5
    indicators = {
        "timestamp": datetime.utcnow(),
        "data_points": 200,
        "indicators": {
            "ema": {
                "period_9": 96100.0,
                "period_20": 95800.0,
                "period_50": 94500.0,
                "period_200": 88000.0,
            },
            "rsi": {"value": 58.3, "period": 14},
            "macd": {
                "macd": 1234.5,
                "signal": 1100.2,
                "histogram": 134.3,
            },
            "bollinger_bands": {
                "upper": 98000.0,
                "middle": 95000.0,
                "lower": 92000.0,
            },
        },
    }

    market_data = {
        "btc_price": current_price,
        "price_change_24h": 2.3,
        "indicators": indicators,
    }

    print(f"\n💰 BTC Price: ${current_price:,.2f}")
    print(f"📊 24h Change: +2.3%")

    print("\n🤖 Running TAAgent analysis...")
    try:
        result = await ta_agent.analyze(market_data)

        print("\n" + "=" * 80)
        print("✅ TAAgent Analysis Result")
        print("=" * 80)

        print(f"\n🎯 Signal: {result.signal.value}")
        print(f"💪 Confidence: {result.confidence_percentage}%")
        print(f"\n📝 Reasoning (first 500 chars):\n{result.reasoning[:500]}...")

        return result

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("🚀 Starting TAAgent Tests\n")

    # Test 1: Full test with generated OHLCV data
    asyncio.run(test_ta_agent())

    print("\n" + "=" * 80)
    print("\n")

    # Test 2: Quick test with pre-calculated indicators
    asyncio.run(test_with_real_indicators())

    print("\n" + "=" * 80)
    print("✅ All tests completed!")
    print("=" * 80)
