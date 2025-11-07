"""Conviction Calculator - 计算投资信念分数

将 3 个 Agent (MacroAgent, TAAgent, OnChainAgent) 的分析结果转换为 0-100 的信念分数
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ConvictionInput:
    """信念计算输入"""
    macro_output: Dict[str, Any]  # MacroAgent输出
    ta_output: Dict[str, Any]     # TAAgent输出
    onchain_output: Dict[str, Any]  # OnChainAgent输出
    market_data: Dict[str, Any]   # 当前市场数据


@dataclass
class ConvictionResult:
    """信念计算结果"""
    score: float  # 0-100
    raw_weighted_score: float  # 加权前原始分数
    macro_contribution: float  # MacroAgent贡献
    ta_contribution: float     # TAAgent贡献
    onchain_contribution: float  # OnChainAgent贡献
    risk_adjustment: float     # 风险调整因子
    confidence_adjustment: float  # 置信度调整因子
    details: Dict[str, Any]    # 详细计算过程


class ConvictionCalculator:
    """
    信念分数计算器

    计算逻辑:
    1. 将每个Agent的signal转换为基础分数 (-100到+100)
    2. 应用Agent权重 (Macro 40%, OnChain 40%, TA 20%)
    3. 根据风险指标调整 (恐惧指数, 波动率)
    4. 根据置信度调整
    5. 归一化到0-100
    """

    # Agent权重配置
    WEIGHTS = {
        "macro": 0.40,      # 宏观分析权重40%
        "onchain": 0.40,    # 链上分析权重40%
        "ta": 0.20,         # 技术分析权重20%
    }

    # Signal到分数的映射
    SIGNAL_SCORES = {
        "BULLISH": 100,
        "NEUTRAL": 0,
        "BEARISH": -100,
    }

    def calculate(self, input_data: ConvictionInput) -> ConvictionResult:
        """
        计算信念分数

        Args:
            input_data: Agent输出和市场数据

        Returns:
            ConvictionResult: 信念分数和详细信息
        """
        # Step 1: 获取每个Agent的基础分数
        macro_score = self._get_agent_score(input_data.macro_output)
        ta_score = self._get_agent_score(input_data.ta_output)
        onchain_score = self._get_agent_score(input_data.onchain_output)

        # Step 2: 应用权重
        weighted_score = (
            macro_score * self.WEIGHTS["macro"]
            + onchain_score * self.WEIGHTS["onchain"]
            + ta_score * self.WEIGHTS["ta"]
        )

        # Step 3: 风险调整
        risk_factor = self._calculate_risk_factor(input_data.market_data)

        # Step 4: 置信度调整
        confidence_factor = self._calculate_confidence_factor(input_data)

        # Step 5: 应用调整
        adjusted_score = weighted_score * risk_factor * confidence_factor

        # Step 6: 归一化到0-100 (原来-100到+100)
        normalized_score = (adjusted_score + 100) / 2

        # 限制在0-100范围
        final_score = max(0, min(100, normalized_score))

        return ConvictionResult(
            score=final_score,
            raw_weighted_score=weighted_score,
            macro_contribution=macro_score * self.WEIGHTS["macro"],
            ta_contribution=ta_score * self.WEIGHTS["ta"],
            onchain_contribution=onchain_score * self.WEIGHTS["onchain"],
            risk_adjustment=risk_factor,
            confidence_adjustment=confidence_factor,
            details={
                "agent_scores": {
                    "macro": macro_score,
                    "ta": ta_score,
                    "onchain": onchain_score,
                },
                "weighted_score": weighted_score,
                "risk_factor": risk_factor,
                "confidence_factor": confidence_factor,
                "adjusted_score": adjusted_score,
            }
        )

    def _get_agent_score(self, agent_output: Dict[str, Any]) -> float:
        """
        获取Agent的基础分数

        将signal (BULLISH/NEUTRAL/BEARISH) 和 confidence (0-1)
        转换为 -100到+100的分数
        """
        signal = agent_output.get("signal", "NEUTRAL")
        confidence = agent_output.get("confidence", 0.5)

        base_score = self.SIGNAL_SCORES.get(signal, 0)

        # 根据置信度调整: confidence越低,分数越靠近0
        adjusted_score = base_score * confidence

        return adjusted_score

    def _calculate_risk_factor(self, market_data: Dict[str, Any]) -> float:
        """
        计算风险调整因子 (0-1)

        考虑因素:
        - 恐惧贪婪指数 (Fear & Greed)
        - 价格波动率
        - DXY美元指数
        """
        risk_factor = 1.0

        # 1. 恐惧指数调整
        fg_value = market_data.get("fear_greed", {}).get("value", 50)
        if fg_value < 20:  # 极度恐惧
            risk_factor *= 0.7  # 降低30%
        elif fg_value > 80:  # 极度贪婪
            risk_factor *= 0.8  # 降低20%

        # 2. 波动率调整 (从价格变化推断)
        price_change = abs(market_data.get("btc_price_change_24h", 0))
        if price_change > 10:  # 24h波动超过10%
            risk_factor *= 0.75  # 降低25%
        elif price_change > 5:  # 24h波动超过5%
            risk_factor *= 0.9   # 降低10%

        # 3. 美元强度调整
        dxy = market_data.get("macro", {}).get("dxy_index", 100)
        if dxy > 110:  # 美元极强
            risk_factor *= 0.85  # 降低15%

        return risk_factor

    def _calculate_confidence_factor(self, input_data: ConvictionInput) -> float:
        """
        计算综合置信度因子 (0-1)

        如果所有Agent的置信度都很低,降低整体信念分数
        """
        confidences = [
            input_data.macro_output.get("confidence", 0.5),
            input_data.ta_output.get("confidence", 0.5),
            input_data.onchain_output.get("confidence", 0.5),
        ]

        avg_confidence = sum(confidences) / len(confidences)

        # 置信度低于0.4时开始降低因子
        if avg_confidence < 0.4:
            return 0.7
        elif avg_confidence < 0.5:
            return 0.85
        else:
            return 1.0


# 全局实例
conviction_calculator = ConvictionCalculator()
