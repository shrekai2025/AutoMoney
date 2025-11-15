"""Mock data generator for fallback when real APIs fail"""

import random
from datetime import datetime, timedelta
from typing import Dict, Any, List
from app.schemas.market_data import PriceData, OHLCVData


def generate_mock_binance_data() -> Dict[str, Any]:
    """生成Mock Binance数据"""
    
    # 生成价格数据
    btc_price = 91000.0 + random.uniform(-2000, 2000)
    eth_price = 3100.0 + random.uniform(-100, 100)
    
    price_data = {
        "btc": PriceData(
            symbol="BTC/USDT",
            price=btc_price,
            price_change_24h=random.uniform(-5, 5),
            price_change_percent_24h=random.uniform(-5, 5),
            high_24h=btc_price * 1.03,
            low_24h=btc_price * 0.97,
            volume_24h=25000000000,
        ),
        "eth": PriceData(
            symbol="ETH/USDT",
            price=eth_price,
            price_change_24h=random.uniform(-3, 3),
            price_change_percent_24h=random.uniform(-4, 4),
            high_24h=eth_price * 1.02,
            low_24h=eth_price * 0.98,
            volume_24h=12000000000,
        ),
    }
    
    # 生成OHLCV数据 (168小时 = 7天)
    ohlcv = []
    base_price = btc_price
    now = datetime.utcnow()
    
    for i in range(168, 0, -1):
        timestamp = now - timedelta(hours=i)
        open_price = base_price + random.uniform(-500, 500)
        high_price = open_price + random.uniform(0, 300)
        low_price = open_price - random.uniform(0, 300)
        close_price = open_price + random.uniform(-200, 200)
        volume = random.uniform(500, 2000)
        
        ohlcv.append(
            OHLCVData(
                timestamp=timestamp,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=volume,
            )
        )
        
        base_price = close_price
    
    return {"price_data": price_data, "ohlcv": ohlcv}


def generate_mock_market_snapshot() -> Dict[str, Any]:
    """生成完整的Mock市场快照"""
    
    binance_data = generate_mock_binance_data()
    btc_price = binance_data["price_data"]["btc"].price
    
    return {
        "btc_price": btc_price,
        "btc_price_change_24h": random.uniform(-5, 5),
        "btc_volume_24h": 25000000000,
        "eth_price": 3100.0 + random.uniform(-100, 100),
        "eth_price_change_24h": random.uniform(-4, 4),
        "fear_greed": {
            "value": random.randint(20, 80),
            "classification": random.choice(["Fear", "Neutral", "Greed"]),
        },
        "macro": {
            "dxy_index": 103.0 + random.uniform(-2, 2),
            "fed_funds_rate": 5.5,
            "m2_growth": 2.5,
            "treasury_10y": 4.5,
            "vix": 15.0 + random.uniform(-3, 3),
        },
        "indicators": None,  # Will be calculated later
        "timestamp": datetime.utcnow().isoformat(),
        "last_updated": datetime.utcnow().isoformat(),
        "_is_mock": True,  # 标记这是Mock数据
    }

