"""Technical Indicators Calculator

Implements common technical analysis indicators:
- EMA (Exponential Moving Average)
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime

from app.schemas.market_data import OHLCVData


class IndicatorCalculator:
    """Calculate technical indicators from OHLCV data"""

    @staticmethod
    def _to_dataframe(ohlcv_data: List[OHLCVData]) -> pd.DataFrame:
        """Convert OHLCV data to pandas DataFrame"""
        data = {
            "timestamp": [d.timestamp for d in ohlcv_data],
            "open": [float(d.open) for d in ohlcv_data],
            "high": [float(d.high) for d in ohlcv_data],
            "low": [float(d.low) for d in ohlcv_data],
            "close": [float(d.close) for d in ohlcv_data],
            "volume": [float(d.volume) for d in ohlcv_data],
        }
        df = pd.DataFrame(data)
        df.sort_values("timestamp", inplace=True)
        return df

    @staticmethod
    def calculate_ema(
        ohlcv_data: List[OHLCVData], period: int = 20, price_key: str = "close"
    ) -> List[Optional[float]]:
        """
        Calculate Exponential Moving Average

        Args:
            ohlcv_data: List of OHLCV data points
            period: EMA period (default: 20)
            price_key: Price to use (close, open, high, low)

        Returns:
            List of EMA values (None for insufficient data)
        """
        if len(ohlcv_data) < period:
            return [None] * len(ohlcv_data)

        df = IndicatorCalculator._to_dataframe(ohlcv_data)
        ema = df[price_key].ewm(span=period, adjust=False).mean()

        # Return list, with None for initial values before we have enough data
        result = [None] * (period - 1) + ema.iloc[period - 1 :].tolist()
        return result

    @staticmethod
    def calculate_rsi(ohlcv_data: List[OHLCVData], period: int = 14) -> List[Optional[float]]:
        """
        Calculate Relative Strength Index

        Args:
            ohlcv_data: List of OHLCV data points
            period: RSI period (default: 14)

        Returns:
            List of RSI values (0-100, None for insufficient data)
        """
        if len(ohlcv_data) <= period:
            return [None] * len(ohlcv_data)

        df = IndicatorCalculator._to_dataframe(ohlcv_data)
        close = df["close"]

        # Calculate price changes
        delta = close.diff()

        # Separate gains and losses
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # Calculate average gain and loss using EMA
        avg_gain = gain.ewm(span=period, adjust=False).mean()
        avg_loss = loss.ewm(span=period, adjust=False).mean()

        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        # Return list, with None for initial values
        result = [None] * period + rsi.iloc[period:].tolist()
        return result

    @staticmethod
    def calculate_macd(
        ohlcv_data: List[OHLCVData],
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> Dict[str, List[Optional[float]]]:
        """
        Calculate MACD (Moving Average Convergence Divergence)

        Args:
            ohlcv_data: List of OHLCV data points
            fast_period: Fast EMA period (default: 12)
            slow_period: Slow EMA period (default: 26)
            signal_period: Signal line EMA period (default: 9)

        Returns:
            Dict with 'macd', 'signal', and 'histogram' lists
        """
        if len(ohlcv_data) < slow_period + signal_period:
            null_list = [None] * len(ohlcv_data)
            return {"macd": null_list, "signal": null_list, "histogram": null_list}

        df = IndicatorCalculator._to_dataframe(ohlcv_data)
        close = df["close"]

        # Calculate fast and slow EMAs
        ema_fast = close.ewm(span=fast_period, adjust=False).mean()
        ema_slow = close.ewm(span=slow_period, adjust=False).mean()

        # Calculate MACD line
        macd_line = ema_fast - ema_slow

        # Calculate signal line
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()

        # Calculate histogram
        histogram = macd_line - signal_line

        # Prepare results with None for initial values
        min_period = slow_period + signal_period - 1

        macd_result = [None] * (slow_period - 1) + macd_line.iloc[slow_period - 1 :].tolist()
        signal_result = [None] * min_period + signal_line.iloc[min_period:].tolist()
        histogram_result = [None] * min_period + histogram.iloc[min_period:].tolist()

        return {
            "macd": macd_result,
            "signal": signal_result,
            "histogram": histogram_result,
        }

    @staticmethod
    def calculate_bollinger_bands(
        ohlcv_data: List[OHLCVData], period: int = 20, num_std: float = 2.0
    ) -> Dict[str, List[Optional[float]]]:
        """
        Calculate Bollinger Bands

        Args:
            ohlcv_data: List of OHLCV data points
            period: Moving average period (default: 20)
            num_std: Number of standard deviations (default: 2.0)

        Returns:
            Dict with 'upper', 'middle', and 'lower' band lists
        """
        if len(ohlcv_data) < period:
            null_list = [None] * len(ohlcv_data)
            return {"upper": null_list, "middle": null_list, "lower": null_list}

        df = IndicatorCalculator._to_dataframe(ohlcv_data)
        close = df["close"]

        # Calculate middle band (SMA)
        middle = close.rolling(window=period).mean()

        # Calculate standard deviation
        std = close.rolling(window=period).std()

        # Calculate upper and lower bands
        upper = middle + (std * num_std)
        lower = middle - (std * num_std)

        # Prepare results with None for initial values
        upper_result = [None] * (period - 1) + upper.iloc[period - 1 :].tolist()
        middle_result = [None] * (period - 1) + middle.iloc[period - 1 :].tolist()
        lower_result = [None] * (period - 1) + lower.iloc[period - 1 :].tolist()

        return {
            "upper": upper_result,
            "middle": middle_result,
            "lower": lower_result,
        }

    @staticmethod
    def calculate_all(
        ohlcv_data: List[OHLCVData],
        ema_periods: List[int] = None,
        rsi_period: int = 14,
        macd_params: Dict[str, int] = None,
        bb_params: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Calculate all technical indicators at once

        Args:
            ohlcv_data: List of OHLCV data points
            ema_periods: List of EMA periods to calculate (default: [9, 20, 50, 200])
            rsi_period: RSI period (default: 14)
            macd_params: MACD parameters (default: {fast: 12, slow: 26, signal: 9})
            bb_params: Bollinger Bands parameters (default: {period: 20, num_std: 2.0})

        Returns:
            Dict containing all calculated indicators
        """
        if ema_periods is None:
            ema_periods = [9, 20, 50, 200]

        if macd_params is None:
            macd_params = {"fast_period": 12, "slow_period": 26, "signal_period": 9}

        if bb_params is None:
            bb_params = {"period": 20, "num_std": 2.0}

        # Calculate EMAs
        emas = {}
        for period in ema_periods:
            emas[f"ema_{period}"] = IndicatorCalculator.calculate_ema(ohlcv_data, period)

        # Calculate RSI
        rsi = IndicatorCalculator.calculate_rsi(ohlcv_data, rsi_period)

        # Calculate MACD
        macd = IndicatorCalculator.calculate_macd(ohlcv_data, **macd_params)

        # Calculate Bollinger Bands
        bb = IndicatorCalculator.calculate_bollinger_bands(ohlcv_data, **bb_params)

        # Get latest values (non-None)
        def get_latest(values: List[Optional[float]]) -> Optional[float]:
            """Get the latest non-None value"""
            for val in reversed(values):
                if val is not None:
                    return val
            return None

        # Compile results
        result = {
            "timestamp": datetime.utcnow(),
            "data_points": len(ohlcv_data),
            "indicators": {
                "ema": {f"period_{p}": get_latest(emas[f"ema_{p}"]) for p in ema_periods},
                "rsi": {"value": get_latest(rsi), "period": rsi_period},
                "macd": {
                    "macd": get_latest(macd["macd"]),
                    "signal": get_latest(macd["signal"]),
                    "histogram": get_latest(macd["histogram"]),
                },
                "bollinger_bands": {
                    "upper": get_latest(bb["upper"]),
                    "middle": get_latest(bb["middle"]),
                    "lower": get_latest(bb["lower"]),
                },
            },
            # Also include full series for charting
            "series": {
                "ema": emas,
                "rsi": rsi,
                "macd": macd,
                "bollinger_bands": bb,
            },
        }

        return result

    @staticmethod
    def get_trading_signals(indicators: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate trading signals from calculated indicators

        Args:
            indicators: Result from calculate_all()

        Returns:
            Dict with signal for each indicator type
        """
        signals = {}
        ind = indicators.get("indicators", {})

        # RSI signals
        rsi_value = ind.get("rsi", {}).get("value")
        if rsi_value is not None:
            if rsi_value > 70:
                signals["rsi"] = "overbought"
            elif rsi_value < 30:
                signals["rsi"] = "oversold"
            else:
                signals["rsi"] = "neutral"

        # MACD signals
        macd_hist = ind.get("macd", {}).get("histogram")
        if macd_hist is not None:
            if macd_hist > 0:
                signals["macd"] = "bullish"
            elif macd_hist < 0:
                signals["macd"] = "bearish"
            else:
                signals["macd"] = "neutral"

        # EMA trend signals (compare short vs long EMAs)
        ema_data = ind.get("ema", {})
        ema_9 = ema_data.get("period_9")
        ema_20 = ema_data.get("period_20")
        ema_50 = ema_data.get("period_50")

        if ema_9 is not None and ema_20 is not None:
            if ema_9 > ema_20:
                signals["ema_short"] = "bullish"
            else:
                signals["ema_short"] = "bearish"

        if ema_20 is not None and ema_50 is not None:
            if ema_20 > ema_50:
                signals["ema_long"] = "bullish"
            else:
                signals["ema_long"] = "bearish"

        # Overall signal (simple majority)
        bullish_count = sum(
            1 for s in signals.values() if s in ["bullish", "oversold"]
        )
        bearish_count = sum(
            1 for s in signals.values() if s in ["bearish", "overbought"]
        )

        if bullish_count > bearish_count:
            signals["overall"] = "bullish"
        elif bearish_count > bullish_count:
            signals["overall"] = "bearish"
        else:
            signals["overall"] = "neutral"

        return signals
