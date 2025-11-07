"""Signal Generator - 生成交易信号

根据信念分数生成具体的交易信号和仓位大小
"""

from typing import Optional, List
from dataclasses import dataclass
from enum import Enum


class TradeSignal(str, Enum):
    """交易信号"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass
class SignalOutput:
    """信号输出"""
    signal: TradeSignal
    signal_strength: float  # 0-1
    position_size: float    # 0-1 (占总资金的比例)
    risk_level: RiskLevel
    should_execute: bool    # 是否应该执行交易
    reasons: List[str]      # 决策原因
    warnings: List[str]     # 风险警告


@dataclass
class CircuitBreaker:
    """熔断规则"""
    is_triggered: bool
    rule_name: str
    description: str


class SignalGenerator:
    """
    交易信号生成器

    规则:
    1. Conviction < 30: SELL
    2. 30 <= Conviction < 45: HOLD (偏空)
    3. 45 <= Conviction < 55: HOLD (中性)
    4. 55 <= Conviction < 70: HOLD (偏多)
    5. Conviction >= 70: BUY

    熔断机制:
    - 极度恐惧 (Fear < 20): 暂停买入
    - 美元极强 (DXY > 115): 降低仓位
    - 极度波动 (24h > 15%): 暂停交易
    """

    # 信号阈值
    SELL_THRESHOLD = 30
    WEAK_HOLD_THRESHOLD = 45
    NEUTRAL_THRESHOLD = 55
    STRONG_HOLD_THRESHOLD = 70

    # 仓位配置
    MIN_POSITION_SIZE = 0.002  # 最小0.2% (原0.25%调整为更保守)
    MAX_POSITION_SIZE = 0.005  # 最大0.5% (原0.75%调整为更保守)

    def generate_signal(
        self,
        conviction_score: float,
        market_data: dict,
        current_position: Optional[float] = None
    ) -> SignalOutput:
        """
        生成交易信号

        Args:
            conviction_score: 信念分数 (0-100)
            market_data: 市场数据
            current_position: 当前持仓比例 (0-1)

        Returns:
            SignalOutput: 交易信号和详细信息
        """
        reasons = []
        warnings = []
        current_position = current_position or 0.0

        # Step 1: 检查熔断规则
        circuit_breaker = self._check_circuit_breaker(market_data)
        if circuit_breaker.is_triggered:
            warnings.append(f"⚠️ 熔断触发: {circuit_breaker.description}")
            return SignalOutput(
                signal=TradeSignal.HOLD,
                signal_strength=0.0,
                position_size=0.0,
                risk_level=RiskLevel.HIGH,
                should_execute=False,
                reasons=[f"熔断: {circuit_breaker.description}"],
                warnings=warnings,
            )

        # Step 2: 根据conviction_score确定信号
        if conviction_score >= self.STRONG_HOLD_THRESHOLD:
            signal = TradeSignal.BUY
            signal_strength = (conviction_score - self.STRONG_HOLD_THRESHOLD) / 30
            reasons.append(f"✅ 强烈看多 (信念分数: {conviction_score:.1f}/100)")

        elif conviction_score < self.SELL_THRESHOLD:
            signal = TradeSignal.SELL
            signal_strength = (self.SELL_THRESHOLD - conviction_score) / 30
            reasons.append(f"🔴 强烈看空 (信念分数: {conviction_score:.1f}/100)")

        else:
            signal = TradeSignal.HOLD
            signal_strength = 0.0

            if conviction_score < self.WEAK_HOLD_THRESHOLD:
                reasons.append(f"⚪ 持币观望 - 偏空 (信念分数: {conviction_score:.1f}/100)")
            elif conviction_score < self.NEUTRAL_THRESHOLD:
                reasons.append(f"⚪ 持币观望 - 中性 (信念分数: {conviction_score:.1f}/100)")
            else:
                reasons.append(f"⚪ 持币观望 - 偏多 (信念分数: {conviction_score:.1f}/100)")

        # Step 3: 计算仓位大小
        position_size = self._calculate_position_size(
            conviction_score,
            signal,
            signal_strength,
            market_data
        )

        # Step 4: 评估风险等级
        risk_level = self._assess_risk_level(market_data, conviction_score)

        # Step 5: 决定是否执行
        should_execute = self._should_execute(
            signal,
            position_size,
            current_position,
            market_data
        )

        if not should_execute and signal != TradeSignal.HOLD:
            reasons.append(f"⏸️ 暂不执行 (仓位限制或风控)")

        # Step 6: 添加市场警告
        self._add_market_warnings(market_data, warnings)

        return SignalOutput(
            signal=signal,
            signal_strength=signal_strength,
            position_size=position_size,
            risk_level=risk_level,
            should_execute=should_execute,
            reasons=reasons,
            warnings=warnings,
        )

    def _check_circuit_breaker(self, market_data: dict) -> CircuitBreaker:
        """检查熔断规则"""

        # 1. 极度恐惧
        fg_value = market_data.get("fear_greed", {}).get("value", 50)
        if fg_value < 20:
            return CircuitBreaker(
                is_triggered=True,
                rule_name="extreme_fear",
                description=f"市场极度恐惧 (Fear & Greed: {fg_value})"
            )

        # 2. 美元极强
        dxy = market_data.get("macro", {}).get("dxy_index", 100)
        if dxy > 115:
            return CircuitBreaker(
                is_triggered=True,
                rule_name="strong_dollar",
                description=f"美元极度强势 (DXY: {dxy:.2f})"
            )

        # 3. 极度波动
        price_change = abs(market_data.get("btc_price_change_24h", 0))
        if price_change > 15:
            return CircuitBreaker(
                is_triggered=True,
                rule_name="high_volatility",
                description=f"价格极度波动 (24h: {price_change:.1f}%)"
            )

        return CircuitBreaker(
            is_triggered=False,
            rule_name="none",
            description=""
        )

    def _calculate_position_size(
        self,
        conviction_score: float,
        signal: TradeSignal,
        signal_strength: float,
        market_data: dict
    ) -> float:
        """
        计算仓位大小

        策略:
        - 信念分数越高,仓位越大
        - 波动率越高,仓位越小
        - 风险指标不好时,仓位越小
        """
        if signal == TradeSignal.HOLD:
            return 0.0

        # 基础仓位 (根据信念分数)
        if signal == TradeSignal.BUY:
            # Conviction 70-100 -> position 0.2%-0.5%
            base_position = self.MIN_POSITION_SIZE + (
                signal_strength * (self.MAX_POSITION_SIZE - self.MIN_POSITION_SIZE)
            )
        else:  # SELL
            # 卖出时清空所有仓位
            return 1.0

        # 波动率调整
        price_change = abs(market_data.get("btc_price_change_24h", 0))
        if price_change > 10:
            base_position *= 0.5  # 高波动减半
        elif price_change > 5:
            base_position *= 0.75  # 中等波动减25%

        # 恐惧指数调整
        fg_value = market_data.get("fear_greed", {}).get("value", 50)
        if fg_value < 30:  # 恐惧
            base_position *= 0.8

        return base_position

    def _assess_risk_level(self, market_data: dict, conviction_score: float) -> RiskLevel:
        """评估风险等级"""

        risk_score = 0

        # 恐惧指数
        fg_value = market_data.get("fear_greed", {}).get("value", 50)
        if fg_value < 30 or fg_value > 75:
            risk_score += 1

        # 波动率
        price_change = abs(market_data.get("btc_price_change_24h", 0))
        if price_change > 7:
            risk_score += 1
        if price_change > 12:
            risk_score += 1

        # 信念分数
        if conviction_score < 40 or conviction_score > 85:
            risk_score += 1

        if risk_score >= 3:
            return RiskLevel.HIGH
        elif risk_score >= 1:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _should_execute(
        self,
        signal: TradeSignal,
        position_size: float,
        current_position: float,
        market_data: dict
    ) -> bool:
        """决定是否应该执行交易"""

        # HOLD信号不执行
        if signal == TradeSignal.HOLD:
            return False

        # BUY: 检查仓位限制
        if signal == TradeSignal.BUY:
            # 已经接近满仓,不再买入
            if current_position > 0.95:
                return False

            # 仓位太小不值得买入
            if position_size < self.MIN_POSITION_SIZE:
                return False

        # SELL: 检查是否有持仓
        if signal == TradeSignal.SELL:
            if current_position < 0.01:  # 几乎没有持仓
                return False

        return True

    def _add_market_warnings(self, market_data: dict, warnings: List[str]):
        """添加市场风险警告"""

        # 恐惧指数
        fg_value = market_data.get("fear_greed", {}).get("value", 50)
        if fg_value < 25:
            warnings.append(f"⚠️ 市场恐惧 (Fear & Greed: {fg_value})")
        elif fg_value > 75:
            warnings.append(f"⚠️ 市场贪婪 (Fear & Greed: {fg_value})")

        # 波动率
        price_change = abs(market_data.get("btc_price_change_24h", 0))
        if price_change > 10:
            warnings.append(f"⚠️ 高波动 (24h: {price_change:.1f}%)")


# 全局实例
signal_generator = SignalGenerator()
