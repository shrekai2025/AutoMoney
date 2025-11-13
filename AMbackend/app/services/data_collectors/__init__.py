"""Data collectors for market data"""

from app.services.data_collectors.base import DataCollector
from app.services.data_collectors.binance import BinanceCollector
from app.services.data_collectors.binance_futures import BinanceFuturesCollector
from app.services.data_collectors.glassnode import GlassnodeCollector
from app.services.data_collectors.fred import FREDCollector
from app.services.data_collectors.alternative_me import AlternativeMeCollector
from app.services.data_collectors.manager import DataCollectionManager, data_manager
from app.services.data_collectors.momentum_data_service import MomentumDataService

__all__ = [
    "DataCollector",
    "BinanceCollector",
    "BinanceFuturesCollector",
    "GlassnodeCollector",
    "FREDCollector",
    "AlternativeMeCollector",
    "DataCollectionManager",
    "data_manager",
    "MomentumDataService",
]
