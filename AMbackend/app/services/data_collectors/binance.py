"""Binance price data collector"""

from typing import Dict, Any, List
from datetime import datetime

from app.services.data_collectors.base import DataCollector
from app.schemas.market_data import PriceData, OHLCVData


class BinanceCollector(DataCollector):
    """
    Binance API data collector for cryptocurrency prices

    Documentation: https://binance-docs.github.io/apidocs/spot/en/
    """

    def __init__(self, api_key: str = "", api_secret: str = ""):
        """
        Initialize Binance collector

        Args:
            api_key: Binance API key
            api_secret: Binance API secret
        """
        super().__init__(api_key=api_key, base_url="https://api.binance.com")
        self.api_secret = api_secret

    async def collect(self) -> Dict[str, Any]:
        """
        Collect price data from Binance

        Returns:
            Dictionary with BTC and ETH price data

        Raises:
            Exception: If API fetch fails (no mock data fallback)

        API Endpoint: GET /api/v3/ticker/24hr
        """
        # Check cache first (1 minute cache)
        cached = await self.get_cached_data("price_data", max_age_seconds=60)
        if cached:
            return cached

        # Call real API for BTC and ETH (no fallback)
        btc_data = await self._get_real_price_data("BTCUSDT")
        eth_data = await self._get_real_price_data("ETHUSDT")

        result = {
            "btc": btc_data,
            "eth": eth_data,
        }

        self.set_cache("price_data", result)
        self.last_fetch_time = datetime.utcnow()

        return result

    async def get_ohlcv(
        self, symbol: str = "BTCUSDT", interval: str = "1h", limit: int = 100
    ) -> List[OHLCVData]:
        """
        Get OHLCV (candlestick) data

        Args:
            symbol: Trading pair symbol
            interval: Candle interval (1m, 5m, 15m, 1h, 4h, 1d, etc.)
            limit: Number of candles to fetch

        Returns:
            List of OHLCV data

        Raises:
            Exception: If API fetch fails (no mock data fallback)

        API Endpoint: GET /api/v3/klines?symbol=BTCUSDT&interval=1h&limit=100
        """
        cache_key = f"ohlcv_{symbol}_{interval}_{limit}"
        cached = await self.get_cached_data(cache_key, max_age_seconds=300)
        if cached:
            return cached

        # Call real Binance Klines API (no fallback)
        response = await self.get(
            "/api/v3/klines",
            params={"symbol": symbol, "interval": interval, "limit": limit}
        )

        ohlcv_data = []
        for kline in response:
            # Binance kline format:
            # [timestamp, open, high, low, close, volume, close_time, ...]
            ohlcv_data.append(
                OHLCVData(
                    timestamp=datetime.fromtimestamp(kline[0] / 1000),
                    open=float(kline[1]),
                    high=float(kline[2]),
                    low=float(kline[3]),
                    close=float(kline[4]),
                    volume=float(kline[5]),
                )
            )

        self.set_cache(cache_key, ohlcv_data)
        return ohlcv_data

    async def _get_real_price_data(self, symbol: str) -> PriceData:
        """
        Get real price data from Binance 24hr ticker API

        Args:
            symbol: Binance symbol (e.g., 'BTCUSDT')

        Returns:
            PriceData object with current price information
        """
        response = await self.get("/api/v3/ticker/24hr", params={"symbol": symbol})

        # Convert symbol format (BTCUSDT -> BTC/USDT)
        formatted_symbol = f"{symbol[:-4]}/{symbol[-4:]}"

        return PriceData(
            symbol=formatted_symbol,
            price=float(response["lastPrice"]),
            volume_24h=float(response["volume"]),
            price_change_24h=float(response["priceChangePercent"]),
            timestamp=datetime.fromtimestamp(response["closeTime"] / 1000),
        )

    @property
    def is_configured(self) -> bool:
        """Check if Binance collector is configured"""
        # Public API endpoints don't require authentication
        return True
