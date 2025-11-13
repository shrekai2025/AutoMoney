"""Momentum Strategy Data Service

专为动量策略设计的数据采集服务,整合:
- 15分钟/60分钟K线数据 (多币种)
- 衍生品数据 (资金费率/持仓量/期货溢价)
- 宏观数据
- 市场情绪
"""

from typing import Dict, Any, List
from datetime import datetime
import logging

from app.services.data_collectors.binance import BinanceCollector
from app.services.data_collectors.binance_futures import BinanceFuturesCollector
from app.services.data_collectors.fred import FREDCollector
from app.services.data_collectors.alternative_me import AlternativeMeCollector
from app.services.data_collectors.blockchain_info import BlockchainInfoCollector
from app.core.config import settings
from app.schemas.market_data import OHLCVData

logger = logging.getLogger(__name__)


class MomentumDataService:
    """
    动量策略数据服务
    
    提供完整的数据采集功能for动量策略:
    - 多币种(BTC/ETH/SOL)的15分钟和60分钟K线
    - Binance Futures衍生品指标
    - 宏观经济数据
    - 市场情绪指标
    """
    
    def __init__(self):
        """初始化所有需要的数据采集器"""
        self.binance_spot = BinanceCollector(
            api_key=settings.BINANCE_API_KEY,
            api_secret=settings.BINANCE_API_SECRET
        )
        
        self.binance_futures = BinanceFuturesCollector(
            api_key=settings.BINANCE_API_KEY,
            api_secret=settings.BINANCE_API_SECRET
        )
        
        self.fred = FREDCollector(api_key=settings.FRED_API_KEY)
        
        self.alternative_me = AlternativeMeCollector()
        
        self.blockchain_info = BlockchainInfoCollector()
    
    async def collect_for_momentum_strategy(
        self,
        assets: List[str] = None
    ) -> Dict[str, Any]:
        """
        采集动量策略所需的全部数据
        
        Args:
            assets: 币种列表,默认["BTC", "ETH", "SOL"]
        
        Returns:
            {
                "timestamp": "2025-11-13T10:15:00Z",
                "assets": {
                    "BTC": {
                        "price": 95300.0,
                        "ohlcv_15m": [...],  // 200根K线
                        "ohlcv_60m": [...],  // 200根K线
                        "volume_24h": 28000000000,
                        "price_change_24h": 2.3,
                        "funding_rate": 0.0001,
                        "open_interest_change_24h": 5.2,
                        "futures_premium": 0.15
                    },
                    "ETH": {...},
                    "SOL": {...}
                },
                "macro": {
                    "etf_flow_7d": [100, 200, -50, 150, 300, 250, 400],
                    "dxy": 103.5,
                    "fed_rate": 3.87,
                    "treasury_10y": 4.25
                },
                "sentiment": {
                    "fear_greed_value": 65,
                    "fear_greed_classification": "Greed"
                },
                "onchain": {
                    "btc_mvrv_zscore": 2.5
                }
            }
        """
        if assets is None:
            assets = ["BTC", "ETH", "SOL"]
        
        logger.info(f"开始采集动量策略数据,币种: {assets}")
        
        try:
            # 并行采集所有数据
            assets_data = await self._collect_assets_data(assets)
            macro_data = await self._collect_macro_data()
            sentiment_data = await self._collect_sentiment_data()
            onchain_data = await self._collect_onchain_data()
            
            result = {
                "timestamp": datetime.utcnow().isoformat(),
                "assets": assets_data,
                "macro": macro_data,
                "sentiment": sentiment_data,
                "onchain": onchain_data
            }
            
            logger.info("动量策略数据采集完成")
            return result
            
        except Exception as e:
            logger.error(f"动量策略数据采集失败: {e}", exc_info=True)
            raise
    
    async def _collect_assets_data(self, assets: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        采集多币种数据
        
        对每个币种采集:
        - 当前价格和24h变化
        - 15分钟K线(200根 ≈ 50小时)
        - 60分钟K线(200根 ≈ 8天)
        - 衍生品指标(资金费率/持仓量/期货溢价)
        """
        assets_data = {}
        
        for asset in assets:
            symbol_spot = f"{asset}USDT"
            
            try:
                logger.info(f"采集 {asset} 数据...")
                
                # 1. 获取当前价格和24h数据
                price_data = await self.binance_spot._get_real_price_data(symbol_spot)
                
                # 2. 获取15分钟K线 (200根)
                ohlcv_15m = await self.binance_spot.get_ohlcv(
                    symbol=symbol_spot,
                    interval="15m",
                    limit=200
                )
                
                # 3. 获取60分钟K线 (200根)
                ohlcv_60m = await self.binance_spot.get_ohlcv(
                    symbol=symbol_spot,
                    interval="1h",
                    limit=200
                )
                
                # 4. 获取衍生品数据
                derivatives_data = await self._collect_derivatives_for_asset(symbol_spot)
                
                # 5. 整合数据
                assets_data[asset] = {
                    "price": price_data.price,
                    "volume_24h": price_data.volume_24h,
                    "price_change_24h": price_data.price_change_24h,
                    
                    # K线数据
                    "ohlcv_15m": [self._ohlcv_to_dict(candle) for candle in ohlcv_15m],
                    "ohlcv_60m": [self._ohlcv_to_dict(candle) for candle in ohlcv_60m],
                    
                    # 衍生品数据
                    "funding_rate": derivatives_data.get("funding_rate"),
                    "funding_rate_avg_8h": derivatives_data.get("funding_rate_avg_8h"),
                    "open_interest": derivatives_data.get("open_interest"),
                    "open_interest_change_24h": derivatives_data.get("open_interest_change_24h"),
                    "futures_premium": derivatives_data.get("futures_premium"),
                    
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                logger.info(f"{asset} 数据采集成功")
                
            except Exception as e:
                logger.error(f"采集 {asset} 数据失败: {e}")
                # 部分失败可接受,继续采集其他币种
                assets_data[asset] = {
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        return assets_data
    
    async def _collect_derivatives_for_asset(self, symbol: str) -> Dict[str, Any]:
        """
        采集单个币种的衍生品数据
        
        Returns:
            {
                "funding_rate": 0.0001,
                "funding_rate_avg_8h": 0.00012,
                "open_interest": 27097.55,
                "open_interest_change_24h": 5.2,
                "futures_premium": 0.15
            }
        """
        try:
            # 获取资金费率
            funding_data = await self.binance_futures.get_funding_rate(symbol)
            
            # 获取持仓量
            oi_data = await self.binance_futures.get_open_interest(symbol)
            
            # 获取期货溢价
            premium_data = await self.binance_futures.get_futures_premium(symbol)
            
            return {
                "funding_rate": funding_data.get("current_funding_rate"),
                "funding_rate_avg_8h": funding_data.get("avg_funding_rate_8h"),
                "open_interest": oi_data.get("open_interest"),
                "open_interest_change_24h": oi_data.get("open_interest_change_24h_pct"),
                "futures_premium": premium_data.get("premium_rate_pct")
            }
            
        except Exception as e:
            logger.error(f"采集 {symbol} 衍生品数据失败: {e}")
            return {
                "funding_rate": None,
                "funding_rate_avg_8h": None,
                "open_interest": None,
                "open_interest_change_24h": None,
                "futures_premium": None
            }
    
    async def _collect_macro_data(self) -> Dict[str, Any]:
        """
        采集宏观经济数据
        
        Returns:
            {
                "dxy": 103.5,
                "fed_rate": 3.87,
                "m2_growth": 0.47,
                "treasury_10y": 4.25
            }
        """
        try:
            if not self.fred.is_configured:
                logger.warning("FRED API未配置,跳过宏观数据采集")
                return {}
            
            fred_data = await self.fred.collect()
            macro = fred_data.get("data", {})
            
            return {
                "dxy": macro.get("dxy_index"),
                "fed_rate": macro.get("fed_funds_rate"),
                "m2_growth": macro.get("m2_growth_yoy"),
                "treasury_10y": macro.get("treasury_10y")
            }
            
        except Exception as e:
            logger.error(f"采集宏观数据失败: {e}")
            return {}
    
    async def _collect_sentiment_data(self) -> Dict[str, Any]:
        """
        采集市场情绪数据
        
        Returns:
            {
                "fear_greed_value": 65,
                "fear_greed_classification": "Greed"
            }
        """
        try:
            fg_data = await self.alternative_me.collect()
            
            return {
                "fear_greed_value": fg_data.get("value"),
                "fear_greed_classification": fg_data.get("value_classification")
            }
            
        except Exception as e:
            logger.error(f"采集情绪数据失败: {e}")
            return {
                "fear_greed_value": 50,  # 默认中性
                "fear_greed_classification": "Neutral"
            }
    
    async def _collect_onchain_data(self) -> Dict[str, Any]:
        """
        采集链上数据
        
        Returns:
            {
                "btc_mvrv_zscore": 2.5
            }
        """
        try:
            # 使用Blockchain.info的免费数据
            bc_data = await self.blockchain_info.collect()
            
            # 简化版MVRV计算(实际应该用Glassnode,但需要付费)
            # 这里先返回占位数据
            return {
                "btc_mvrv_zscore": None  # TODO: 实现真实的MVRV计算
            }
            
        except Exception as e:
            logger.error(f"采集链上数据失败: {e}")
            return {
                "btc_mvrv_zscore": None
            }
    
    def _ohlcv_to_dict(self, ohlcv: OHLCVData) -> Dict[str, Any]:
        """将OHLCV对象转换为字典"""
        return {
            "timestamp": ohlcv.timestamp.isoformat(),
            "open": float(ohlcv.open),
            "high": float(ohlcv.high),
            "low": float(ohlcv.low),
            "close": float(ohlcv.close),
            "volume": float(ohlcv.volume)
        }


# 全局实例
momentum_data_service = MomentumDataService()

