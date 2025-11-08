"""Real Market Data Service - 真实市场数据服务

从真实 API 获取市场数据，替换所有模拟数据
"""

from typing import Dict, Any
from decimal import Decimal
from datetime import datetime
import logging

from app.services.data_collectors.manager import data_manager
from app.services.indicators.calculator import IndicatorCalculator

logger = logging.getLogger(__name__)


class RealMarketDataService:
    """
    真实市场数据服务

    从 CoinGecko, Binance, Alternative.me, FRED 等真实 API 获取数据
    """

    async def get_complete_market_snapshot(self) -> Dict[str, Any]:
        """
        获取完整的市场数据快照

        Returns:
            包含所有市场数据的字典
        """
        try:
            # 使用现有的 data_manager 收集所有数据
            snapshot = await data_manager.collect_all()

            # 提取关键数据 - 使用正确的字段名
            btc_data = snapshot.btc_price
            fear_greed_data = snapshot.fear_greed
            macro_data = snapshot.macro

            # 计算技术指标（为TAAgent准备）
            indicators_dict = None
            if snapshot.btc_ohlcv and len(snapshot.btc_ohlcv) > 0:
                try:
                    indicators_data = IndicatorCalculator.calculate_all(snapshot.btc_ohlcv)
                    indicators_dict = indicators_data.get("indicators", {})
                except Exception as ind_error:
                    logger.warning(f"计算技术指标失败: {ind_error}")

            # 构建市场快照
            market_snapshot = {
                # BTC 价格数据
                "btc_price": float(btc_data.price),
                "btc_price_change_24h": btc_data.price_change_24h,
                "btc_volume_24h": float(btc_data.volume_24h) if btc_data.volume_24h else 0,

                # ETH 价格数据（可选）
                "eth_price": float(snapshot.eth_price.price) if snapshot.eth_price else None,
                "eth_price_change_24h": snapshot.eth_price.price_change_24h if snapshot.eth_price else None,

                # 恐惧贪婪指数
                "fear_greed": {
                    "value": fear_greed_data.value if fear_greed_data else 50,
                    "classification": fear_greed_data.classification if fear_greed_data else "Neutral",
                },

                # 宏观经济数据
                "macro": {
                    "dxy_index": self._get_macro_value(macro_data, "dxy_index", 103.0),
                    "fed_funds_rate": self._get_macro_value(macro_data, "fed_funds_rate", 5.5),
                    "m2_growth": self._get_macro_value(macro_data, "m2_growth", 2.5),
                    "treasury_10y": self._get_macro_value(macro_data, "treasury_10y", 4.5),
                    "vix": self._get_macro_value(macro_data, "vix", 15.0),
                },

                # 技术指标（为TAAgent准备）
                "indicators": indicators_dict,

                # 时间戳
                "timestamp": datetime.utcnow().isoformat(),
                "last_updated": snapshot.timestamp.isoformat() if snapshot.timestamp else datetime.utcnow().isoformat(),
            }

            logger.info(f"成功获取市场数据 - BTC: ${market_snapshot['btc_price']}, F&G: {market_snapshot['fear_greed']['value']}")

            return market_snapshot

        except Exception as e:
            logger.error(f"获取市场数据失败: {e}", exc_info=True)
            # 如果获取失败，抛出异常而不是返回模拟数据
            raise RuntimeError(f"无法获取真实市场数据: {e}")

    def _get_macro_value(self, macro_data: Any, key: str, default: float) -> float:
        """
        安全地从宏观数据中提取值

        Args:
            macro_data: 宏观数据对象
            key: 键名
            default: 默认值（仅在数据不可用时使用）

        Returns:
            提取的值或默认值
        """
        try:
            if not macro_data:
                logger.warning(f"宏观数据不可用，使用默认值: {key}={default}")
                return default

            if hasattr(macro_data, key):
                value = getattr(macro_data, key)
                if value is not None:
                    return float(value)

            logger.warning(f"宏观数据字段缺失: {key}，使用默认值: {default}")
            return default

        except Exception as e:
            logger.warning(f"提取宏观数据失败 {key}: {e}，使用默认值: {default}")
            return default

    async def get_btc_price(self) -> Decimal:
        """
        获取当前 BTC 价格

        Returns:
            BTC 价格（Decimal）
        """
        try:
            data = await data_manager.binance.collect()
            return Decimal(str(data["btc"].price))
        except Exception as e:
            logger.error(f"获取 BTC 价格失败: {e}")
            raise RuntimeError(f"无法获取 BTC 价格: {e}")

    async def get_fear_greed_index(self) -> int:
        """
        获取恐惧贪婪指数

        Returns:
            恐惧贪婪指数 (0-100)
        """
        try:
            data = await data_manager.alternative_me.collect()
            return data["index"].value
        except Exception as e:
            logger.error(f"获取恐惧贪婪指数失败: {e}")
            raise RuntimeError(f"无法获取恐惧贪婪指数: {e}")


# 全局实例
real_market_data_service = RealMarketDataService()
