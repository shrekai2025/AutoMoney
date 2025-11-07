"""Technical Indicators Schemas"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime
from decimal import Decimal


class EMAIndicators(BaseModel):
    """EMA (Exponential Moving Average) indicators"""

    period_9: Optional[float] = Field(None, description="9-period EMA")
    period_20: Optional[float] = Field(None, description="20-period EMA")
    period_50: Optional[float] = Field(None, description="50-period EMA")
    period_200: Optional[float] = Field(None, description="200-period EMA")


class RSIIndicator(BaseModel):
    """RSI (Relative Strength Index) indicator"""

    value: Optional[float] = Field(None, description="RSI value (0-100)", ge=0, le=100)
    period: int = Field(14, description="RSI calculation period")
    signal: Optional[str] = Field(None, description="oversold/neutral/overbought")


class MACDIndicator(BaseModel):
    """MACD (Moving Average Convergence Divergence) indicator"""

    macd: Optional[float] = Field(None, description="MACD line value")
    signal: Optional[float] = Field(None, description="Signal line value")
    histogram: Optional[float] = Field(None, description="MACD histogram")


class BollingerBands(BaseModel):
    """Bollinger Bands indicator"""

    upper: Optional[float] = Field(None, description="Upper band")
    middle: Optional[float] = Field(None, description="Middle band (SMA)")
    lower: Optional[float] = Field(None, description="Lower band")
    width: Optional[float] = Field(None, description="Band width %")


class TradingSignals(BaseModel):
    """Trading signals derived from indicators"""

    rsi: Optional[str] = Field(None, description="RSI signal")
    macd: Optional[str] = Field(None, description="MACD signal")
    ema_short: Optional[str] = Field(None, description="Short-term EMA trend")
    ema_long: Optional[str] = Field(None, description="Long-term EMA trend")
    overall: Optional[str] = Field(None, description="Overall signal")


class TechnicalIndicators(BaseModel):
    """Complete technical indicators analysis"""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    symbol: str = Field(..., description="Trading pair symbol")
    timeframe: str = Field(default="1h", description="Timeframe (e.g., 1h, 4h, 1d)")
    data_points: int = Field(..., description="Number of candles analyzed")

    # Indicators
    ema: EMAIndicators
    rsi: RSIIndicator
    macd: MACDIndicator
    bollinger_bands: BollingerBands

    # Signals
    signals: TradingSignals

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2024-01-01T00:00:00",
                "symbol": "BTC/USDT",
                "timeframe": "1h",
                "data_points": 200,
                "ema": {
                    "period_9": 45123.45,
                    "period_20": 45000.12,
                    "period_50": 44800.00,
                    "period_200": 44200.00,
                },
                "rsi": {"value": 65.5, "period": 14, "signal": "neutral"},
                "macd": {"macd": 123.45, "signal": 100.23, "histogram": 23.22},
                "bollinger_bands": {
                    "upper": 46000.0,
                    "middle": 45000.0,
                    "lower": 44000.0,
                    "width": 4.44,
                },
                "signals": {
                    "rsi": "neutral",
                    "macd": "bullish",
                    "ema_short": "bullish",
                    "ema_long": "bullish",
                    "overall": "bullish",
                },
            }
        }


class IndicatorSeries(BaseModel):
    """Time series data for charting indicators"""

    timestamps: List[datetime]
    ema: Dict[str, List[Optional[float]]] = Field(
        ..., description="EMA series for different periods"
    )
    rsi: List[Optional[float]] = Field(..., description="RSI series")
    macd: Dict[str, List[Optional[float]]] = Field(
        ..., description="MACD, signal, and histogram series"
    )
    bollinger_bands: Dict[str, List[Optional[float]]] = Field(
        ..., description="Upper, middle, lower band series"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "timestamps": ["2024-01-01T00:00:00", "2024-01-01T01:00:00"],
                "ema": {
                    "ema_9": [45000.0, 45100.0],
                    "ema_20": [44900.0, 45000.0],
                },
                "rsi": [65.0, 66.5],
                "macd": {
                    "macd": [100.0, 110.0],
                    "signal": [95.0, 105.0],
                    "histogram": [5.0, 5.0],
                },
                "bollinger_bands": {
                    "upper": [46000.0, 46100.0],
                    "middle": [45000.0, 45100.0],
                    "lower": [44000.0, 44100.0],
                },
            }
        }
