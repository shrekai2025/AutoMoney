"""RegimeFilterAgent - 市场制度过滤器

评估市场环境的整体健康度,输出Regime Score (0-100)
用于动量策略的制度确认层
"""

from typing import Dict, Any
import logging

from app.services.llm.manager import llm_manager
from app.schemas.llm import Message
from app.utils.json_parser import parse_llm_json

logger = logging.getLogger(__name__)


class RegimeFilterAgent:
    """
    市场制度过滤器Agent
    
    职责:
    - 综合评估宏观/情绪/衍生品/链上数据
    - 输出Regime Score (0-100) 表示市场健康度
    - 提供文字解释
    
    权重分配:
    - 宏观流动性: 35% (ETF流入25% + DXY5% + 降息预期5%)
    - 市场情绪: 20% (Fear & Greed)
    - 衍生品健康度: 40% (资金费率15% + 持仓量10% + 期货溢价15%)
    - 链上信号: 5% (MVRV)
    """
    
    # 默认权重配置
    DEFAULT_WEIGHTS = {
        "etf_flow": 0.25,
        "dxy": 0.05,
        "fed_rate": 0.05,
        "fear_greed": 0.20,
        "funding_rate": 0.15,
        "open_interest": 0.10,
        "futures_premium": 0.15,
        "mvrv": 0.05
    }
    
    SYSTEM_PROMPT = """你是一个市场环境评估专家,专门分析加密货币市场的整体健康度。

你的任务是综合多维度指标,输出一个Regime Score (0-100),表示市场环境对交易的适宜程度:
- 0-20: 极度危险 (应大幅减仓)
- 20-40: 危险 (应减仓)
- 40-60: 中性 (正常交易)
- 60-80: 健康 (可加仓)
- 80-100: 极度健康 (可大幅加仓)

⚠️ 重要提示:
你的评分会影响仓位大小(通过0.3x-1.6x的乘数),但不会完全阻止交易。
即使Score<20,技术信号仍可触发交易(只是仓位会缩小到0.3x)。

你必须返回ONLY有效的JSON,格式如下:

{
    "regime_score": 72.5,
    "regime_classification": "HEALTHY",
    "confidence": 0.85,
    "reasoning": "市场环境分析...",
    "component_scores": {
        "macro_liquidity": 0.6,
        "market_sentiment": 0.7,
        "derivatives_health": 0.5,
        "onchain_signal": 0.3
    },
    "key_factors": ["因素1", "因素2", "因素3"],
    "risk_level": "MEDIUM",
    "recommended_multiplier": 1.3
}

字段说明:
- regime_score: 0-100的浮点数
- regime_classification: "DANGEROUS"(<40), "NEUTRAL"(40-60), "HEALTHY"(60-80), "VERY_HEALTHY"(>=80)
- confidence: 0-1的浮点数
- reasoning: 详细的分析说明
- component_scores: 各维度分数(-1到+1)
- key_factors: 关键影响因素列表
- risk_level: "LOW", "MEDIUM", "HIGH"
- recommended_multiplier: 建议的仓位乘数(0.3-1.6)

⚠️ 输出要求:
1. 只返回JSON,不要任何其他文字
2. 不要使用markdown格式
3. 字符串中不要使用**加粗**或其他markdown语法
4. 确保JSON格式完全正确
"""
    
    def __init__(self):
        """初始化RegimeFilterAgent"""
        self.agent_name = "regime_filter_agent"
    
    async def analyze(
        self, 
        market_data: Dict[str, Any],
        custom_weights: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        分析市场环境,输出Regime Score
        
        Args:
            market_data: 市场数据快照 {
                "macro": {"dxy": 103.5, "fed_rate": 3.87, ...},
                "sentiment": {"fear_greed_value": 65, ...},
                "assets": {
                    "BTC": {"funding_rate": 0.0001, "open_interest_change_24h": 5.2, ...},
                    "ETH": {...},
                    "SOL": {...}
                },
                "onchain": {"btc_mvrv_zscore": 2.5}
            }
            custom_weights: 自定义权重(可选)
        
        Returns:
            {
                "regime_score": 72.5,
                "regime_classification": "HEALTHY",
                "confidence": 0.85,
                "reasoning": "...",
                "component_scores": {...},
                "recommended_multiplier": 1.3,
                ...
            }
        """
        try:
            logger.info("RegimeFilterAgent开始分析市场环境...")
            
            # Step 1: 预处理指标,标准化到[-1, +1]
            normalized_scores = self._normalize_indicators(market_data)
            
            # Step 2: 计算加权Base Score
            weights = custom_weights or self.DEFAULT_WEIGHTS
            base_score = self._calculate_base_score(normalized_scores, weights)
            
            # Step 3: 构建分析prompt
            analysis_prompt = self._build_analysis_prompt(
                market_data, 
                normalized_scores, 
                base_score
            )
            
            # Step 4: 调用LLM (可选增强)
            full_prompt = f"{self.SYSTEM_PROMPT}\n\n{analysis_prompt}"
            messages = [Message(role="user", content=full_prompt)]
            
            response = await llm_manager.chat_for_agent(
                agent_name=self.agent_name,
                messages=messages
            )
            
            # Step 5: 解析LLM响应
            result = self._parse_llm_response(response.content, base_score)
            
            logger.info(f"Regime Score: {result['regime_score']:.2f}, 分类: {result['regime_classification']}")
            
            return result
            
        except Exception as e:
            logger.error(f"RegimeFilterAgent分析失败: {e}", exc_info=True)
            # 返回中性默认值
            return self._get_default_output(base_score=50.0)
    
    def _normalize_indicators(self, market_data: Dict[str, Any]) -> Dict[str, float]:
        """
        将各指标标准化到[-1, +1]
        
        正值: 对市场有利 (看多)
        负值: 对市场不利 (看空)
        0: 中性
        """
        scores = {}
        
        # 1. 宏观数据
        macro = market_data.get("macro", {})
        
        # DXY (美元指数): 低于100看多,高于110看空
        dxy = macro.get("dxy")
        if dxy:
            if dxy < 100:
                scores["dxy"] = min((100 - dxy) / 10, 1.0)  # 90 → +1.0
            elif dxy > 110:
                scores["dxy"] = max((110 - dxy) / 10, -1.0)  # 120 → -1.0
            else:
                scores["dxy"] = 0.0
        else:
            scores["dxy"] = 0.0
        
        # Fed Rate (联邦基金利率): <3%看多, >5%看空
        fed_rate = macro.get("fed_rate")
        if fed_rate:
            if fed_rate < 3.0:
                scores["fed_rate"] = 0.8
            elif fed_rate > 5.0:
                scores["fed_rate"] = -0.8
            else:
                scores["fed_rate"] = 0.0
        else:
            scores["fed_rate"] = 0.0
        
        # 2. 市场情绪
        sentiment = market_data.get("sentiment", {})
        fg_value = sentiment.get("fear_greed_value", 50)
        
        # Fear & Greed: <20极度恐惧→-1, >80极度贪婪→+1
        if fg_value < 20:
            scores["fear_greed"] = -1.0
        elif fg_value > 80:
            scores["fear_greed"] = 1.0
        else:
            # 线性映射 20-80 → -0.5到+0.5
            scores["fear_greed"] = (fg_value - 50) / 60
        
        # 3. 衍生品数据 (取BTC为主)
        assets = market_data.get("assets", {})
        btc_data = assets.get("BTC", {})
        
        # 资金费率: <0看多, >0.05%看空
        funding_rate = btc_data.get("funding_rate", 0)
        if funding_rate < 0:
            scores["funding_rate"] = 0.5  # 负费率→看多
        elif funding_rate > 0.0005:  # 0.05%
            scores["funding_rate"] = -0.8  # 过高费率→看空
        elif funding_rate > 0.0003:  # 0.03%
            scores["funding_rate"] = -0.3  # 略高→略微看空
        else:
            scores["funding_rate"] = 0.2  # 正常正值→略微看多
        
        # 持仓量变化: 大幅增长(>10%)→略微看空(过热), 大幅下降(<-10%)→看空
        oi_change = btc_data.get("open_interest_change_24h", 0)
        if oi_change > 15:
            scores["open_interest"] = -0.5  # 过度杠杆
        elif oi_change > 5:
            scores["open_interest"] = 0.3  # 健康增长
        elif oi_change < -15:
            scores["open_interest"] = -0.7  # 大量平仓
        else:
            scores["open_interest"] = 0.0
        
        # 期货溢价: <0看空, >0.5%看多但警惕, >2%过热看空
        futures_premium = btc_data.get("futures_premium", 0)
        if futures_premium < -0.5:
            scores["futures_premium"] = -0.8  # 期货折价→看空
        elif futures_premium > 2.0:
            scores["futures_premium"] = -0.5  # 过度溢价→过热
        elif futures_premium > 0.2:
            scores["futures_premium"] = 0.6  # 健康溢价→看多
        else:
            scores["futures_premium"] = 0.0
        
        # 4. 链上数据
        onchain = market_data.get("onchain", {})
        mvrv = onchain.get("btc_mvrv_zscore")
        if mvrv:
            if mvrv > 7:
                scores["mvrv"] = -1.0  # 泡沫区
            elif mvrv > 3:
                scores["mvrv"] = -0.3  # 过热
            elif mvrv < 1:
                scores["mvrv"] = 1.0  # 低估
            else:
                scores["mvrv"] = 0.3  # 健康
        else:
            scores["mvrv"] = 0.0  # 数据缺失
        
        # ETF流入 (TODO: 需要添加到数据源)
        # 暂时使用占位值
        scores["etf_flow"] = 0.3
        
        return scores
    
    def _calculate_base_score(
        self, 
        normalized_scores: Dict[str, float],
        weights: Dict[str, float]
    ) -> float:
        """
        计算加权Base Score并归一化到[0, 100]
        
        公式:
        1. Weighted Sum: sum(score[i] × weight[i]) → [-1, +1]
        2. Normalize: (weighted_sum + 1) × 50 → [0, 100]
        """
        weighted_sum = sum(
            normalized_scores.get(key, 0.0) * weight
            for key, weight in weights.items()
        )
        
        # 限制在[-1, +1]
        weighted_sum = max(-1.0, min(1.0, weighted_sum))
        
        # 归一化到[0, 100]
        base_score = (weighted_sum + 1.0) * 50.0
        
        return base_score
    
    def _build_analysis_prompt(
        self,
        market_data: Dict[str, Any],
        normalized_scores: Dict[str, float],
        base_score: float
    ) -> str:
        """构建分析prompt"""
        
        # 提取关键指标
        macro = market_data.get("macro", {})
        sentiment = market_data.get("sentiment", {})
        btc = market_data.get("assets", {}).get("BTC", {})
        
        prompt = f"""请分析当前市场环境并输出Regime Score:

**规则引擎已计算的初步分数**: {base_score:.2f}/100

**各维度标准化分数** (范围-1到+1, 正值看多/负值看空):
- 宏观流动性:
  * DXY美元指数: {normalized_scores.get('dxy', 0):.2f} (实际值: {macro.get('dxy', 'N/A')})
  * 联邦基金利率: {normalized_scores.get('fed_rate', 0):.2f} (实际值: {macro.get('fed_rate', 'N/A')}%)
  * ETF流入: {normalized_scores.get('etf_flow', 0):.2f}

- 市场情绪:
  * Fear & Greed: {normalized_scores.get('fear_greed', 0):.2f} (实际值: {sentiment.get('fear_greed_value', 'N/A')})

- 衍生品健康度:
  * 资金费率: {normalized_scores.get('funding_rate', 0):.2f} (实际值: {btc.get('funding_rate', 'N/A')})
  * 持仓量变化24h: {normalized_scores.get('open_interest', 0):.2f} (实际值: {btc.get('open_interest_change_24h', 'N/A')}%)
  * 期货溢价率: {normalized_scores.get('futures_premium', 0):.2f} (实际值: {btc.get('futures_premium', 'N/A')}%)

- 链上信号:
  * MVRV Z-Score: {normalized_scores.get('mvrv', 0):.2f}

**你的任务**:
1. 验证初步分数{base_score:.2f}是否合理
2. 考虑指标间的非线性关系和特殊情况
3. 可以微调分数(±10分以内)
4. 给出最终Regime Score (0-100)
5. 提供清晰的reasoning解释

记住: 你的分数会影响仓位乘数(0.3x-1.6x),但不会完全阻止交易。
"""
        
        return prompt
    
    def _parse_llm_response(self, content: str, base_score: float) -> Dict[str, Any]:
        """解析LLM响应"""
        try:
            result = parse_llm_json(content)
            
            # 验证必需字段
            if "regime_score" not in result:
                raise ValueError("Missing regime_score field")
            
            regime_score = float(result["regime_score"])
            
            # 限制在[0, 100]
            regime_score = max(0.0, min(100.0, regime_score))
            
            # 计算推荐乘数
            multiplier = self._calculate_multiplier(regime_score)
            
            # 分类
            classification = self._classify_regime(regime_score)
            
            # 评估风险等级
            risk_level = self._assess_risk_level(regime_score)
            
            return {
                "regime_score": regime_score,
                "regime_classification": classification,
                "confidence": result.get("confidence", 0.7),
                "reasoning": result.get("reasoning", ""),
                "component_scores": result.get("component_scores", {}),
                "key_factors": result.get("key_factors", []),
                "risk_level": risk_level,
                "recommended_multiplier": multiplier,
                "base_score": base_score,  # 保留规则引擎分数
                "llm_adjustment": regime_score - base_score  # LLM的调整量
            }
            
        except Exception as e:
            logger.error(f"解析LLM响应失败: {e}")
            # 使用base_score作为fallback
            return self._get_default_output(base_score)
    
    def _calculate_multiplier(self, regime_score: float) -> float:
        """根据Regime Score计算推荐的仓位乘数"""
        if regime_score < 20:
            return 0.3
        elif regime_score < 40:
            return 0.6
        elif regime_score < 60:
            return 1.0
        elif regime_score < 80:
            return 1.3
        else:
            return 1.6
    
    def _classify_regime(self, regime_score: float) -> str:
        """分类Regime"""
        if regime_score < 40:
            return "DANGEROUS"
        elif regime_score < 60:
            return "NEUTRAL"
        elif regime_score < 80:
            return "HEALTHY"
        else:
            return "VERY_HEALTHY"
    
    def _assess_risk_level(self, regime_score: float) -> str:
        """评估风险等级"""
        if regime_score < 30:
            return "HIGH"
        elif regime_score < 70:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _get_default_output(self, base_score: float) -> Dict[str, Any]:
        """返回默认输出(当LLM失败时)"""
        regime_score = base_score
        return {
            "regime_score": regime_score,
            "regime_classification": self._classify_regime(regime_score),
            "confidence": 0.5,
            "reasoning": "使用规则引擎默认分数(LLM不可用)",
            "component_scores": {},
            "key_factors": [],
            "risk_level": self._assess_risk_level(regime_score),
            "recommended_multiplier": self._calculate_multiplier(regime_score),
            "base_score": base_score,
            "llm_adjustment": 0.0
        }


# 全局实例
regime_filter_agent = RegimeFilterAgent()

