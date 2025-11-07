"""Market data schemas"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class OHLCVData(BaseModel):
    """OHLCV (Open, High, Low, Close, Volume) candlestick data"""

    timestamp: datetime = Field(..., description="Candle timestamp")
    open: float = Field(..., description="Opening price")
    high: float = Field(..., description="Highest price")
    low: float = Field(..., description="Lowest price")
    close: float = Field(..., description="Closing price")
    volume: float = Field(..., description="Trading volume")


class PriceData(BaseModel):
    """Current price data"""

    symbol: str = Field(..., description="Trading pair symbol (e.g., BTC/USDT)")
    price: float = Field(..., description="Current price")
    volume_24h: float = Field(..., description="24-hour trading volume")
    price_change_24h: float = Field(..., description="24-hour price change percentage")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Data timestamp")


class OnChainMetrics(BaseModel):
    """On-chain metrics data"""

    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Data timestamp")

    # Valuation metrics
    mvrv_z_score: Optional[float] = Field(None, description="MVRV Z-Score")
    nvt_ratio: Optional[float] = Field(None, description="NVT Ratio")

    # Activity metrics
    active_addresses: Optional[int] = Field(None, description="Number of active addresses")
    transaction_count: Optional[int] = Field(None, description="Transaction count")

    # Accumulation metrics
    exchange_netflow: Optional[float] = Field(None, description="Net flow to/from exchanges (BTC)")
    whale_addresses: Optional[int] = Field(None, description="Number of whale addresses")

    # Long-term holder metrics
    lth_supply_change: Optional[float] = Field(None, description="Long-term holder supply change (%)")

    # Additional metrics
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metrics")


class MacroEconomicData(BaseModel):
    """Macroeconomic data"""

    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Data timestamp")

    # Bitcoin-specific macro data
    etf_flow: Optional[float] = Field(None, description="Bitcoin ETF net flow (USD)")
    futures_oi: Optional[float] = Field(None, description="Futures open interest")
    futures_long_ratio: Optional[float] = Field(None, description="Futures long/short ratio (%)")

    # Traditional macro
    fed_rate_prob: Optional[float] = Field(None, description="Fed rate cut probability (%)")
    m2_growth: Optional[float] = Field(None, description="M2 money supply growth (%)")
    dxy_index: Optional[float] = Field(None, description="US Dollar Index")
    gold_price: Optional[float] = Field(None, description="Gold price (USD)")

    # Additional data
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional data")


class FearGreedIndex(BaseModel):
    """Crypto Fear & Greed Index"""

    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Data timestamp")
    value: int = Field(..., description="Index value (0-100)")
    classification: str = Field(..., description="Classification (e.g., Extreme Fear, Fear, Neutral, Greed, Extreme Greed)")

    # Component values (if available)
    components: Optional[Dict[str, float]] = Field(None, description="Index components")


class MarketDataSnapshot(BaseModel):
    """Complete market data snapshot for analysis"""

    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Snapshot timestamp")

    # Price data
    btc_price: PriceData
    eth_price: Optional[PriceData] = None

    # Historical OHLCV (for technical analysis)
    btc_ohlcv: List[OHLCVData] = Field(default_factory=list, description="BTC price history")

    # On-chain metrics
    onchain: Optional[OnChainMetrics] = None

    # Macro data
    macro: Optional[MacroEconomicData] = None

    # Sentiment
    fear_greed: Optional[FearGreedIndex] = None
