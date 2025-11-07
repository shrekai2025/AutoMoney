"""Data collection manager to coordinate all data sources"""

from typing import Optional
from datetime import datetime

from app.core.config import settings
from app.services.data_collectors.binance import BinanceCollector
from app.services.data_collectors.glassnode import GlassnodeCollector
from app.services.data_collectors.fred import FREDCollector
from app.services.data_collectors.alternative_me import AlternativeMeCollector
from app.services.data_collectors.blockchain_info import BlockchainInfoCollector
from app.services.data_collectors.mempool_space import MempoolSpaceCollector
from app.services.indicators import IndicatorCalculator
from app.schemas.market_data import MarketDataSnapshot, OnChainMetrics, MacroEconomicData
from app.schemas.indicators import TechnicalIndicators, EMAIndicators, RSIIndicator, MACDIndicator, BollingerBands, TradingSignals


class DataCollectionManager:
    """Manager to coordinate data collection from all sources"""

    def __init__(self):
        """Initialize all data collectors"""
        # Initialize collectors
        self.binance = BinanceCollector(
            api_key=settings.BINANCE_API_KEY, api_secret=settings.BINANCE_API_SECRET
        )

        self.glassnode = GlassnodeCollector(api_key=settings.GLASSNODE_API_KEY)

        self.fred = FREDCollector(api_key=settings.FRED_API_KEY)

        self.alternative_me = AlternativeMeCollector()

        # Free on-chain data collectors
        self.blockchain_info = BlockchainInfoCollector()
        self.mempool_space = MempoolSpaceCollector()

    async def collect_all(self) -> MarketDataSnapshot:
        """
        Collect data from all sources and create a complete snapshot

        Returns:
            MarketDataSnapshot with all market data

        Raises:
            Exception: If critical data collection fails
        """
        # Collect price data (critical)
        price_data = await self.binance.collect()
        btc_ohlcv = await self.binance.get_ohlcv(symbol="BTCUSDT", interval="1h", limit=168)  # 7 days

        # Collect on-chain data (optional - requires paid Glassnode subscription)
        onchain_data = None
        if self.glassnode.is_configured:
            try:
                glassnode_raw = await self.glassnode.collect()
                onchain_data = OnChainMetrics(**glassnode_raw["metrics"])
            except NotImplementedError as e:
                print(f"Info: On-chain data unavailable - {e}")
            except Exception as e:
                print(f"Error: Failed to collect on-chain data: {e}")
                raise  # Re-raise to expose real API errors

        # Collect macro data (required - FRED API)
        macro_data = None
        if self.fred.is_configured:
            fred_raw = await self.fred.collect()
            macro_data = MacroEconomicData(**fred_raw["data"])

        # Collect fear & greed index (required - Alternative.me API)
        fg_raw = await self.alternative_me.collect()
        fear_greed = fg_raw["index"]

        # Create snapshot
        snapshot = MarketDataSnapshot(
            timestamp=datetime.utcnow(),
            btc_price=price_data["btc"],
            eth_price=price_data.get("eth"),
            btc_ohlcv=btc_ohlcv,
            onchain=onchain_data,
            macro=macro_data,
            fear_greed=fear_greed,
        )

        return snapshot

    async def collect_for_macro_agent(self) -> dict:
        """
        Collect data specifically for MacroAgent

        Returns:
            Dictionary with macro-relevant data
        """
        snapshot = await self.collect_all()

        return {
            "btc_price": snapshot.btc_price.price,
            "price_change_24h": snapshot.btc_price.price_change_24h,
            "macro": snapshot.macro.dict() if snapshot.macro else {},
            "fear_greed": snapshot.fear_greed.dict() if snapshot.fear_greed else {},
        }

    async def collect_for_onchain_agent(self) -> dict:
        """
        Collect data specifically for OnChainAgent using free APIs

        Returns:
            Dictionary with on-chain relevant data
        """
        # Collect free on-chain data
        blockchain_data = await self.blockchain_info.collect()
        mempool_data = await self.mempool_space.collect()

        # Also get current price from Binance
        price_data = await self.binance.collect()

        return {
            "btc_price": price_data["btc"],
            "blockchain_info": blockchain_data,
            "mempool_space": mempool_data,
        }

    async def collect_for_ta_agent(
        self, symbol: str = "BTC/USDT", timeframe: str = "1h"
    ) -> dict:
        """
        Collect data specifically for TAAgent (Technical Analysis)
        Includes price data, OHLCV, and calculated technical indicators

        Args:
            symbol: Trading pair symbol (default: BTC/USDT)
            timeframe: Chart timeframe (default: 1h)

        Returns:
            Dictionary with technical analysis relevant data including indicators
        """
        snapshot = await self.collect_all()

        # Calculate technical indicators
        indicators_data = IndicatorCalculator.calculate_all(snapshot.btc_ohlcv)
        trading_signals = IndicatorCalculator.get_trading_signals(indicators_data)

        # Build structured indicators response
        ind = indicators_data["indicators"]
        indicators = TechnicalIndicators(
            symbol=symbol,
            timeframe=timeframe,
            data_points=len(snapshot.btc_ohlcv),
            ema=EMAIndicators(**ind["ema"]),
            rsi=RSIIndicator(**ind["rsi"], signal=trading_signals.get("rsi")),
            macd=MACDIndicator(**ind["macd"]),
            bollinger_bands=BollingerBands(**ind["bollinger_bands"]),
            signals=TradingSignals(**trading_signals),
        )

        return {
            "btc_price": snapshot.btc_price.price,
            "ohlcv": [candle.dict() for candle in snapshot.btc_ohlcv],
            "volume_24h": snapshot.btc_price.volume_24h,
            "indicators": indicators.dict(),
            "raw_series": indicators_data["series"],  # For charting
        }

    async def get_technical_analysis(
        self, symbol: str = "BTC/USDT", timeframe: str = "1h"
    ) -> TechnicalIndicators:
        """
        Get complete technical analysis with indicators

        Args:
            symbol: Trading pair symbol (default: BTC/USDT)
            timeframe: Chart timeframe (default: 1h)

        Returns:
            TechnicalIndicators object with all calculated indicators
        """
        snapshot = await self.collect_all()

        # Calculate all indicators
        indicators_data = IndicatorCalculator.calculate_all(snapshot.btc_ohlcv)
        trading_signals = IndicatorCalculator.get_trading_signals(indicators_data)

        # Build structured response
        ind = indicators_data["indicators"]
        return TechnicalIndicators(
            symbol=symbol,
            timeframe=timeframe,
            data_points=len(snapshot.btc_ohlcv),
            ema=EMAIndicators(**ind["ema"]),
            rsi=RSIIndicator(**ind["rsi"], signal=trading_signals.get("rsi")),
            macd=MACDIndicator(**ind["macd"]),
            bollinger_bands=BollingerBands(**ind["bollinger_bands"]),
            signals=TradingSignals(**trading_signals),
        )

    def get_collector_status(self) -> dict:
        """
        Get status of all collectors

        Returns:
            Dictionary with collector status
        """
        return {
            "binance": {
                "configured": self.binance.is_configured,
                "last_fetch": self.binance.last_fetch_time,
            },
            "glassnode": {
                "configured": self.glassnode.is_configured,
                "last_fetch": self.glassnode.last_fetch_time,
            },
            "fred": {
                "configured": self.fred.is_configured,
                "last_fetch": self.fred.last_fetch_time,
            },
            "alternative_me": {
                "configured": self.alternative_me.is_configured,
                "last_fetch": self.alternative_me.last_fetch_time,
            },
        }

    def clear_all_caches(self):
        """Clear all cached data from all collectors"""
        self.binance.clear_cache()
        self.glassnode.clear_cache()
        self.fred.clear_cache()
        self.alternative_me.clear_cache()


# Global data collection manager instance
data_manager = DataCollectionManager()
