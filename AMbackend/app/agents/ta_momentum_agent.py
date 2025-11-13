"""TAMomentumAgent - 多币种技术动量分析

分析BTC/ETH/SOL的多时间框架技术指标
输出最佳交易机会
"""

from typing import Dict, Any, List, Optional, Tuple
import logging
from datetime import datetime

from app.services.llm.manager import llm_manager
from app.schemas.llm import Message
from app.utils.json_parser import parse_llm_json
from app.services.indicators.calculator import IndicatorCalculator

logger = logging.getLogger(__name__)


class TAMomentumAgent:
    """
    技术动量分析Agent
    
    职责:
    - 分析BTC/ETH/SOL的15分钟和60分钟K线
    - 计算多时间框架EMA/RSI/MACD/ATR
    - 评估动量强度和方向
    - 输出最佳交易机会(币种+方向+强度+止损止盈)
    
    技术指标:
    - EMA: 9/21/50/200 (趋势和支撑阻力)
    - RSI: 14周期 (超买超卖和背离)
    - MACD: 12/26/9 (动量和趋势确认)
    - Bollinger Bands: 20周期 (波动率和均值回归)
    - ATR: 14周期 (止损距离计算)
    - Volume: 成交量确认
    """
    
    # 支持的交易品种
    SUPPORTED_ASSETS = ["BTC", "ETH", "SOL"]
    
    # 时间框架权重
    TIMEFRAME_WEIGHTS = {
        "15m": 0.3,  # 短期信号
        "60m": 0.7   # 中期趋势(更重要)
    }
    
    SYSTEM_PROMPT = """你是一个顶级的加密货币技术分析专家,专注于多时间框架动量交易策略。

你的任务是分析提供的技术指标数据,找出最佳的交易机会。

⚠️ 核心原则:
1. **技术分析主导**: 你的分析是交易决策的核心(80%权重)
2. **趋势是朋友**: 优先顺趋势交易,逆势需要极强的信号
3. **多时间框架确认**: 15分钟+60分钟共振更可靠
4. **严格风控**: 必须基于ATR计算止损位
5. **只做高确定性交易**: 信号不强就返回NEUTRAL

分析框架:
1. **趋势识别** (30%权重):
   - EMA排列: 多头排列(9>21>50>200)或空头排列
   - 价格与EMA关系: 站上/跌破关键均线
   - MACD方向: DIF与DEA的位置和交叉

2. **动量确认** (35%权重):
   - RSI区间: <30超卖(买入机会), >70超买(卖出机会)
   - MACD柱状图: 柱子加速放大→强势, 缩小→动能减弱
   - 成交量配合: 突破伴随放量更可靠

3. **入场时机** (25%权重):
   - 价格触及支撑/阻力后反弹
   - RSI背离信号(价格新高/新低但RSI不创新)
   - MACD金叉/死叉
   - 布林带突破或均值回归

4. **风险评估** (10%权重):
   - ATR大小: 波动率高→缩小仓位
   - 当前位置: 是否在关键阻力/支撑附近
   - 多时间框架一致性

输出要求:
你必须返回ONLY有效的JSON,格式如下:

{
    "asset_analyses": {
        "BTC": {
            "signal": "LONG",
            "signal_strength": 0.85,
            "confidence": 0.8,
            "entry_price": 43250.0,
            "stop_loss_distance_atr": 1.5,
            "take_profit_rr": 2.5,
            "reasoning": "60分钟多头排列,15分钟RSI从超卖反弹,MACD金叉,成交量放大确认...",
            "technical_scores": {
                "trend": 0.8,
                "momentum": 0.9,
                "timing": 0.7,
                "risk": 0.6
            },
            "key_levels": {
                "support": [42000, 41500],
                "resistance": [44000, 45000]
            },
            "timeframe_alignment": 0.85
        },
        "ETH": {...},
        "SOL": {...}
    },
    "best_opportunity": {
        "asset": "BTC",
        "signal": "LONG",
        "signal_strength": 0.85,
        "confidence": 0.8,
        "reasoning": "BTC展现最强多头动量..."
    },
    "overall_momentum_strength": 0.7,
    "market_trend": "UPTREND",
    "reasoning": "综合来看,BTC和ETH都显示强劲上涨动量,SOL相对中性..."
}

字段说明:
- signal: "LONG"(做多), "SHORT"(做空), "NEUTRAL"(观望)
- signal_strength: 0-1的浮点数,表示信号强度
- confidence: 0-1的浮点数,你对这个分析的信心
- entry_price: 建议入场价(使用最新收盘价)
- stop_loss_distance_atr: 止损距离(ATR倍数,通常1.5-3.0)
- take_profit_rr: 止盈风险回报比(通常1.5-3.0)
- technical_scores: 各维度分数(0-1)
- timeframe_alignment: 多时间框架一致性(0-1, >0.7表示共振)
- market_trend: "STRONG_UPTREND"(强势上涨), "UPTREND"(上涨), "NEUTRAL"(中性), "DOWNTREND"(下跌), "STRONG_DOWNTREND"(强势下跌)

⚠️ 重要:
1. 只返回JSON,不要任何其他文字
2. 不要使用markdown格式
3. 确保JSON格式完全正确
4. 如果所有币种都没有明确信号,signal设为"NEUTRAL",signal_strength设为0.0
"""
    
    def __init__(self):
        """初始化TAMomentumAgent"""
        self.agent_name = "ta_momentum_agent"
        self.indicator_calculator = IndicatorCalculator()
    
    async def analyze(
        self, 
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析多币种技术指标,输出最佳交易机会
        
        Args:
            market_data: {
                "assets": {
                    "BTC": {
                        "current_price": 43250.0,
                        "price_change_24h": 3.5,
                        "ohlcv_15m": [...],  # 最近100根15分钟K线
                        "ohlcv_60m": [...],  # 最近100根60分钟K线
                        "funding_rate": 0.0001,
                        ...
                    },
                    "ETH": {...},
                    "SOL": {...}
                }
            }
        
        Returns:
            {
                "asset_analyses": {...},
                "best_opportunity": {...},
                "overall_momentum_strength": 0.7,
                "market_trend": "UPTREND",
                "reasoning": "..."
            }
        """
        try:
            logger.info("TAMomentumAgent开始分析技术指标...")
            
            assets = market_data.get("assets", {})
            
            # Step 1: 计算每个币种的技术指标
            indicators_by_asset = {}
            for asset in self.SUPPORTED_ASSETS:
                if asset not in assets:
                    logger.warning(f"缺少{asset}的数据,跳过")
                    continue
                
                asset_data = assets[asset]
                indicators = self._calculate_indicators(asset, asset_data)
                indicators_by_asset[asset] = indicators
            
            if not indicators_by_asset:
                logger.error("没有可用的技术指标数据")
                return self._get_default_output()
            
            # Step 2: 构建分析prompt
            analysis_prompt = self._build_analysis_prompt(
                assets,
                indicators_by_asset
            )
            
            # Step 3: 调用LLM进行综合分析
            full_prompt = f"{self.SYSTEM_PROMPT}\n\n{analysis_prompt}"
            messages = [Message(role="user", content=full_prompt)]
            
            response = await llm_manager.chat_for_agent(
                agent_name=self.agent_name,
                messages=messages
            )
            
            # Step 4: 解析LLM响应
            result = self._parse_llm_response(response.content, indicators_by_asset)
            
            if result.get("best_opportunity"):
                best = result["best_opportunity"]
                logger.info(
                    f"最佳交易机会: {best['asset']} {best['signal']} "
                    f"(强度:{best['signal_strength']:.2f}, 信心:{best['confidence']:.2f})"
                )
            else:
                logger.info("当前无明确交易机会")
            
            return result
            
        except Exception as e:
            logger.error(f"TAMomentumAgent分析失败: {e}", exc_info=True)
            return self._get_default_output()
    
    def _calculate_indicators(
        self, 
        asset: str, 
        asset_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        计算单个币种的所有技术指标
        
        Returns:
            {
                "15m": {
                    "ema_9": 43200.0,
                    "ema_21": 43000.0,
                    "ema_50": 42800.0,
                    "ema_200": 42000.0,
                    "rsi_14": 65.0,
                    "macd": {"dif": 50.0, "dea": 30.0, "histogram": 20.0},
                    "bbands": {"upper": 44000, "middle": 43000, "lower": 42000},
                    "atr_14": 500.0,
                    "volume": 1234.5,
                    "volume_avg_20": 1000.0
                },
                "60m": {...},
                "current_price": 43250.0
            }
        """
        indicators = {
            "current_price": asset_data.get("current_price", 0.0),
            "price_change_24h": asset_data.get("price_change_24h", 0.0)
        }
        
        # 分析两个时间框架
        for tf in ["15m", "60m"]:
            ohlcv_key = f"ohlcv_{tf}"
            ohlcv_data = asset_data.get(ohlcv_key, [])
            
            if not ohlcv_data or len(ohlcv_data) < 200:
                logger.warning(f"{asset} {tf}数据不足")
                indicators[tf] = {}
                continue
            
            # 提取价格和成交量
            closes = [candle[4] for candle in ohlcv_data]  # close price
            highs = [candle[2] for candle in ohlcv_data]
            lows = [candle[3] for candle in ohlcv_data]
            volumes = [candle[5] for candle in ohlcv_data]
            
            # 计算指标
            tf_indicators = {}
            
            # EMA
            for period in [9, 21, 50, 200]:
                ema_values = self._calculate_ema(closes, period)
                tf_indicators[f"ema_{period}"] = ema_values[-1] if ema_values else 0.0
            
            # RSI
            rsi_values = self._calculate_rsi(closes, 14)
            tf_indicators["rsi_14"] = rsi_values[-1] if rsi_values else 50.0
            
            # MACD
            macd_data = self._calculate_macd(closes)
            tf_indicators["macd"] = macd_data
            
            # Bollinger Bands
            bbands = self._calculate_bbands(closes, 20, 2.0)
            tf_indicators["bbands"] = bbands
            
            # ATR
            atr_values = self._calculate_atr(highs, lows, closes, 14)
            tf_indicators["atr_14"] = atr_values[-1] if atr_values else 0.0
            
            # 成交量
            tf_indicators["volume"] = volumes[-1] if volumes else 0.0
            tf_indicators["volume_avg_20"] = (
                sum(volumes[-20:]) / 20 if len(volumes) >= 20 else volumes[-1]
            )
            
            indicators[tf] = tf_indicators
        
        return indicators
    
    def _calculate_ema(self, prices: List[float], period: int) -> List[float]:
        """计算EMA"""
        if len(prices) < period:
            return []
        
        k = 2 / (period + 1)
        ema_values = [sum(prices[:period]) / period]  # 初始SMA
        
        for price in prices[period:]:
            ema_values.append(price * k + ema_values[-1] * (1 - k))
        
        return ema_values
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> List[float]:
        """计算RSI"""
        if len(prices) < period + 1:
            return []
        
        changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [max(0, change) for change in changes]
        losses = [abs(min(0, change)) for change in changes]
        
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        rsi_values = []
        for i in range(period, len(gains)):
            if avg_loss == 0:
                rsi_values.append(100.0)
            else:
                rs = avg_gain / avg_loss
                rsi_values.append(100 - (100 / (1 + rs)))
            
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
        return rsi_values
    
    def _calculate_macd(
        self, 
        prices: List[float],
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Dict[str, float]:
        """计算MACD"""
        if len(prices) < slow + signal:
            return {"dif": 0.0, "dea": 0.0, "histogram": 0.0}
        
        ema_fast = self._calculate_ema(prices, fast)
        ema_slow = self._calculate_ema(prices, slow)
        
        # DIF = EMA_fast - EMA_slow
        dif = [ema_fast[i] - ema_slow[i] for i in range(len(ema_slow))]
        
        # DEA = EMA(DIF, signal)
        dea = self._calculate_ema(dif, signal)
        
        # Histogram = DIF - DEA
        histogram = dif[-1] - dea[-1] if dea else 0.0
        
        return {
            "dif": dif[-1],
            "dea": dea[-1] if dea else 0.0,
            "histogram": histogram
        }
    
    def _calculate_bbands(
        self, 
        prices: List[float],
        period: int = 20,
        std_dev: float = 2.0
    ) -> Dict[str, float]:
        """计算布林带"""
        if len(prices) < period:
            return {"upper": 0.0, "middle": 0.0, "lower": 0.0}
        
        recent = prices[-period:]
        middle = sum(recent) / period
        variance = sum((p - middle) ** 2 for p in recent) / period
        std = variance ** 0.5
        
        return {
            "upper": middle + std_dev * std,
            "middle": middle,
            "lower": middle - std_dev * std
        }
    
    def _calculate_atr(
        self,
        highs: List[float],
        lows: List[float],
        closes: List[float],
        period: int = 14
    ) -> List[float]:
        """计算ATR (Average True Range)"""
        if len(highs) < period + 1:
            return []
        
        true_ranges = []
        for i in range(1, len(highs)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
            )
            true_ranges.append(tr)
        
        # 计算ATR (简单移动平均)
        atr_values = []
        for i in range(period - 1, len(true_ranges)):
            atr = sum(true_ranges[i-period+1:i+1]) / period
            atr_values.append(atr)
        
        return atr_values
    
    def _build_analysis_prompt(
        self,
        assets: Dict[str, Any],
        indicators_by_asset: Dict[str, Dict[str, Any]]
    ) -> str:
        """构建分析prompt"""
        
        prompt = "请分析以下技术指标数据并输出最佳交易机会:\n\n"
        
        for asset in self.SUPPORTED_ASSETS:
            if asset not in indicators_by_asset:
                continue
            
            indicators = indicators_by_asset[asset]
            asset_data = assets.get(asset, {})
            
            prompt += f"## {asset}\n"
            prompt += f"**当前价格**: {indicators.get('current_price', 0):.2f}\n"
            prompt += f"**24h涨跌**: {indicators.get('price_change_24h', 0):.2f}%\n"
            prompt += f"**资金费率**: {asset_data.get('funding_rate', 0):.4f}%\n\n"
            
            # 15分钟指标
            ind_15m = indicators.get("15m", {})
            if ind_15m:
                prompt += "**15分钟级别**:\n"
                prompt += f"- EMA: 9={ind_15m.get('ema_9', 0):.2f}, 21={ind_15m.get('ema_21', 0):.2f}, "
                prompt += f"50={ind_15m.get('ema_50', 0):.2f}, 200={ind_15m.get('ema_200', 0):.2f}\n"
                prompt += f"- RSI(14): {ind_15m.get('rsi_14', 0):.2f}\n"
                macd_15 = ind_15m.get('macd', {})
                prompt += f"- MACD: DIF={macd_15.get('dif', 0):.2f}, DEA={macd_15.get('dea', 0):.2f}, "
                prompt += f"Histogram={macd_15.get('histogram', 0):.2f}\n"
                bbands_15 = ind_15m.get('bbands', {})
                prompt += f"- 布林带: Upper={bbands_15.get('upper', 0):.2f}, Middle={bbands_15.get('middle', 0):.2f}, "
                prompt += f"Lower={bbands_15.get('lower', 0):.2f}\n"
                prompt += f"- ATR(14): {ind_15m.get('atr_14', 0):.2f}\n"
                prompt += f"- 成交量: 当前={ind_15m.get('volume', 0):.2f}, 20均={ind_15m.get('volume_avg_20', 0):.2f}\n\n"
            
            # 60分钟指标
            ind_60m = indicators.get("60m", {})
            if ind_60m:
                prompt += "**60分钟级别**:\n"
                prompt += f"- EMA: 9={ind_60m.get('ema_9', 0):.2f}, 21={ind_60m.get('ema_21', 0):.2f}, "
                prompt += f"50={ind_60m.get('ema_50', 0):.2f}, 200={ind_60m.get('ema_200', 0):.2f}\n"
                prompt += f"- RSI(14): {ind_60m.get('rsi_14', 0):.2f}\n"
                macd_60 = ind_60m.get('macd', {})
                prompt += f"- MACD: DIF={macd_60.get('dif', 0):.2f}, DEA={macd_60.get('dea', 0):.2f}, "
                prompt += f"Histogram={macd_60.get('histogram', 0):.2f}\n"
                bbands_60 = ind_60m.get('bbands', {})
                prompt += f"- 布林带: Upper={bbands_60.get('upper', 0):.2f}, Middle={bbands_60.get('middle', 0):.2f}, "
                prompt += f"Lower={bbands_60.get('lower', 0):.2f}\n"
                prompt += f"- ATR(14): {ind_60m.get('atr_14', 0):.2f}\n"
                prompt += f"- 成交量: 当前={ind_60m.get('volume', 0):.2f}, 20均={ind_60m.get('volume_avg_20', 0):.2f}\n\n"
        
        prompt += """
请基于以上数据:
1. 评估每个币种的趋势、动量、入场时机
2. 计算多时间框架一致性
3. 选出最佳交易机会(或返回NEUTRAL如果没有明确信号)
4. 提供止损止盈建议(基于ATR)
"""
        
        return prompt
    
    def _parse_llm_response(
        self, 
        content: str,
        indicators_by_asset: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """解析LLM响应"""
        try:
            result = parse_llm_json(content)
            
            # 验证必需字段
            if "asset_analyses" not in result:
                raise ValueError("Missing asset_analyses field")
            
            # 确保所有分析的币种都有indicators数据
            for asset, analysis in result.get("asset_analyses", {}).items():
                if asset not in indicators_by_asset:
                    logger.warning(f"{asset}的分析结果缺少指标数据")
            
            # 计算overall_momentum_strength (如果LLM没提供)
            if "overall_momentum_strength" not in result:
                strengths = [
                    a.get("signal_strength", 0.0) 
                    for a in result["asset_analyses"].values()
                    if a.get("signal") != "NEUTRAL"
                ]
                result["overall_momentum_strength"] = (
                    sum(strengths) / len(strengths) if strengths else 0.0
                )
            
            # 确定market_trend
            if "market_trend" not in result:
                result["market_trend"] = self._determine_market_trend(
                    result["asset_analyses"]
                )
            
            return result
            
        except Exception as e:
            logger.error(f"解析LLM响应失败: {e}")
            return self._get_default_output()
    
    def _determine_market_trend(self, asset_analyses: Dict[str, Dict[str, Any]]) -> str:
        """根据各币种信号确定整体市场趋势"""
        long_count = sum(
            1 for a in asset_analyses.values() if a.get("signal") == "LONG"
        )
        short_count = sum(
            1 for a in asset_analyses.values() if a.get("signal") == "SHORT"
        )
        
        total = len(asset_analyses)
        if total == 0:
            return "NEUTRAL"
        
        long_ratio = long_count / total
        short_ratio = short_count / total
        
        if long_ratio >= 0.67:
            return "STRONG_UPTREND"
        elif long_ratio >= 0.5:
            return "UPTREND"
        elif short_ratio >= 0.67:
            return "STRONG_DOWNTREND"
        elif short_ratio >= 0.5:
            return "DOWNTREND"
        else:
            return "NEUTRAL"
    
    def _get_default_output(self) -> Dict[str, Any]:
        """返回默认输出(当分析失败时)"""
        return {
            "asset_analyses": {
                asset: {
                    "signal": "NEUTRAL",
                    "signal_strength": 0.0,
                    "confidence": 0.0,
                    "reasoning": "数据不足或分析失败",
                    "technical_scores": {
                        "trend": 0.0,
                        "momentum": 0.0,
                        "timing": 0.0,
                        "risk": 0.0
                    }
                }
                for asset in self.SUPPORTED_ASSETS
            },
            "best_opportunity": None,
            "overall_momentum_strength": 0.0,
            "market_trend": "NEUTRAL",
            "reasoning": "技术分析失败,建议观望"
        }


# 全局实例
ta_momentum_agent = TAMomentumAgent()

