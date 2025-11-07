"""Data collectors for market data"""

from app.services.data_collectors.base import DataCollector
from app.services.data_collectors.binance import BinanceCollector
from app.services.data_collectors.glassnode import GlassnodeCollector
from app.services.data_collectors.fred import FREDCollector
from app.services.data_collectors.alternative_me import AlternativeMeCollector
from app.services.data_collectors.manager import DataCollectionManager, data_manager

__all__ = [
    "DataCollector",
    "BinanceCollector",
    "GlassnodeCollector",
    "FREDCollector",
    "AlternativeMeCollector",
    "DataCollectionManager",
    "data_manager",
]
