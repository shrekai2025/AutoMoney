"""Conviction Calculator - 计算投资信念分数

将 3 个 Agent (MacroAgent, TAAgent, OnChainAgent) 的分析结果转换为 0-100 的信念分数

🎯 核心逻辑:
1. 每个Agent直接输出 score (-100到+100) 作为投资建议强度
2. confidence (0-1) 仅供参考，不参与投资决策计算
3. 最终 conviction_score 只由 agent_score + weights + risk_factor 决定
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
    details: Dict[str, Any]    # 详细计算过程


class ConvictionCalculator:
    """
    信念分数计算器

    计算逻辑:
    1. 直接使用每个Agent的score (-100到+100)，不再从signal转换
    2. 应用Agent权重 (支持自定义权重，默认: Macro 40%, OnChain 40%, TA 20%)
    3. 根据风险指标调整 (恐惧指数, 波动率)
    4. 归一化到0-100

    ⚠️ confidence不参与计算，仅供UI展示参考
    """

    # 默认Agent权重配置
    DEFAULT_WEIGHTS = {
        "macro": 0.40,      # 宏观分析权重40%
        "onchain": 0.40,    # 链上分析权重40%
        "ta": 0.20,         # 技术分析权重20%
    }

    def calculate(
        self,
        input_data: ConvictionInput,
        custom_weights: Optional[Dict[str, float]] = None
    ) -> ConvictionResult:
        """
        计算信念分数

        Args:
            input_data: Agent输出和市场数据
            custom_weights: 自定义权重配置 (可选)，格式: {"macro": 0.4, "onchain": 0.4, "ta": 0.2}

        Returns:
            ConvictionResult: 信念分数和详细信息
        """
        # 使用自定义权重或默认权重
        weights = custom_weights if custom_weights else self.DEFAULT_WEIGHTS

        # 验证权重有效性
        self._validate_weights(weights)

        # Step 1: 获取每个Agent的score (直接使用，不再转换)
        macro_score = self._get_agent_score(input_data.macro_output)
        ta_score = self._get_agent_score(input_data.ta_output)
        onchain_score = self._get_agent_score(input_data.onchain_output)

        # Step 2: 应用权重
        weighted_score = (
            macro_score * weights.get("macro", 0.40)
            + onchain_score * weights.get("onchain", 0.40)
            + ta_score * weights.get("ta", 0.20)
        )

        # Step 3: 风险调整
        risk_factor = self._calculate_risk_factor(input_data.market_data)

        # Step 4: 应用调整 (移除confidence_factor)
        adjusted_score = weighted_score * risk_factor

        # Step 5: 归一化到0-100 (原来-100到+100)
        normalized_score = (adjusted_score + 100) / 2

        # 限制在0-100范围
        final_score = max(0, min(100, normalized_score))

        return ConvictionResult(
            score=final_score,
            raw_weighted_score=weighted_score,
            macro_contribution=macro_score * weights.get("macro", 0.40),
            ta_contribution=ta_score * weights.get("ta", 0.20),
            onchain_contribution=onchain_score * weights.get("onchain", 0.40),
            risk_adjustment=risk_factor,
            details={
                "agent_scores": {
                    "macro": macro_score,
                    "ta": ta_score,
                    "onchain": onchain_score,
                },
                "weights_used": weights,
                "weighted_score": weighted_score,
                "risk_factor": risk_factor,
                "adjusted_score": adjusted_score,
            }
        )

    def _validate_weights(self, weights: Dict[str, float]) -> None:
        """
        验证权重配置有效性

        Args:
            weights: 权重配置字典

        Raises:
            ValueError: 权重无效时抛出异常
        """
        required_keys = {"macro", "onchain", "ta"}
        if not required_keys.issubset(weights.keys()):
            raise ValueError(f"权重配置必须包含: {required_keys}")

        # 验证每个权重在0-1之间
        for key, value in weights.items():
            if not 0 <= value <= 1:
                raise ValueError(f"权重 '{key}' 必须在0-1之间，当前值: {value}")

        # 验证权重总和约等于1.0 (允许±0.01误差)
        total = sum(weights.values())
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"权重总和必须为1.0，当前总和: {total:.3f}")

    def _get_agent_score(self, agent_output: Dict[str, Any]) -> float:
        """
        获取Agent的score

        直接使用Agent输出的score (-100到+100)
        不再从signal转换，不再使用confidence调整

        Args:
            agent_output: Agent输出，必须包含"score"字段

        Returns:
            float: -100到+100的分数
        """
        score = agent_output.get("score", 0.0)

        # 验证score范围
        if not -100.0 <= score <= 100.0:
            print(f"Warning: Agent score {score} out of range [-100, 100], clamping to range")
            score = max(-100.0, min(100.0, score))

        return score

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


# 全局实例
conviction_calculator = ConvictionCalculator()
