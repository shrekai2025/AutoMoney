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
    # 连续信号相关
    is_accelerated: bool = False  # 是否触发加速积累
    consecutive_count: int = 0     # 当前连续次数
    position_multiplier: float = 1.0  # 仓位乘数


@dataclass
class CircuitBreaker:
    """熔断规则"""
    is_triggered: bool
    rule_name: str
    description: str


class SignalGenerator:
    """
    交易信号生成器（新版交易逻辑）

    规则:
    1. Conviction >= 50: BUY (买入0.2%-0.5%)
    2. 45 <= Conviction < 50: 部分SELL (动态减仓0%-50%)
       - Conviction=50: 卖0%
       - Conviction=47.5: 卖25%
       - Conviction=45: 卖50%
    3. Conviction < 45: 全部SELL (清仓100%)

    加速积累:
    - 连续30次(可配置)>=50: 触发加速积累,仓位乘数1.1-2.0(可配置)

    熔断机制:
    - 极度恐惧 (Fear < 配置阈值): 暂停交易
    - 极度波动 (24h > 15%): 暂停交易
    """

    # 信号阈值（新的交易逻辑）
    FULL_SELL_THRESHOLD = 45       # < 45 全部清仓
    PARTIAL_SELL_THRESHOLD = 50    # 45-50 部分减仓
    BUY_THRESHOLD = 50             # >= 50 买入

    # 仓位配置
    MIN_POSITION_SIZE = 0.002  # 最小0.2%
    MAX_POSITION_SIZE = 0.005  # 最大0.5%
    DEFENSIVE_SELL_SIZE = 0.01  # 防御性减仓1%

    def generate_signal(
        self,
        conviction_score: float,
        market_data: dict,
        current_position: Optional[float] = None,
        portfolio_state: Optional[dict] = None
    ) -> SignalOutput:
        """
        生成交易信号

        Args:
            conviction_score: 信念分数 (0-100)
            market_data: 市场数据
            current_position: 当前持仓比例 (0-1)
            portfolio_state: 组合状态字典,包含:
                - consecutive_bullish_count: 连续看涨次数
                - last_conviction_score: 上次信念分数
                - consecutive_signal_threshold: 连续信号阈值(默认30)
                - acceleration_multiplier_min: 最小乘数(默认1.1)
                - acceleration_multiplier_max: 最大乘数(默认2.0)
                - fg_circuit_breaker_threshold: Fear & Greed熔断阈值(默认20)
                - fg_position_adjust_threshold: Fear & Greed仓位调整阈值(默认30)
                - buy_threshold: 买入阈值(默认50)
                - full_sell_threshold: 全部清仓阈值(默认45)
                注: 部分减仓区间为 [full_sell_threshold, buy_threshold)

        Returns:
            SignalOutput: 交易信号和详细信息
        """
        reasons = []
        warnings = []
        current_position = current_position or 0.0
        portfolio_state = portfolio_state or {}

        # 提取连续信号相关参数
        consecutive_count = portfolio_state.get("consecutive_bullish_count", 0)
        consecutive_threshold = portfolio_state.get("consecutive_signal_threshold", 30)
        multiplier_min = portfolio_state.get("acceleration_multiplier_min", 1.1)
        multiplier_max = portfolio_state.get("acceleration_multiplier_max", 2.0)

        # 提取交易阈值参数
        fg_circuit_breaker = portfolio_state.get("fg_circuit_breaker_threshold", 20)
        fg_position_adjust = portfolio_state.get("fg_position_adjust_threshold", 30)
        buy_threshold = portfolio_state.get("buy_threshold", 50)
        full_sell_threshold = portfolio_state.get("full_sell_threshold", 45)
        # 移除 partial_sell_threshold,直接使用 buy_threshold 作为部分减仓的上界

        # Step 1: 检查熔断规则
        circuit_breaker = self._check_circuit_breaker(market_data, fg_circuit_breaker)
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
                is_accelerated=False,
                consecutive_count=consecutive_count,
                position_multiplier=1.0,
            )

        # Step 2: 根据conviction_score确定信号（使用配置的阈值）
        if conviction_score >= buy_threshold:
            # >= buy_threshold: 买入
            signal = TradeSignal.BUY
            signal_strength = (conviction_score - buy_threshold) / 50  # buy_threshold-100映射到0-1
            reasons.append(f"✅ 看多买入 (信念分数: {conviction_score:.1f}/100, 阈值: {buy_threshold})")

        elif conviction_score >= full_sell_threshold:
            # full_sell_threshold - buy_threshold: 部分减仓
            signal = TradeSignal.SELL
            signal_strength = (buy_threshold - conviction_score) / (buy_threshold - full_sell_threshold) if (buy_threshold - full_sell_threshold) > 0 else 0
            reasons.append(f"🟡 部分减仓 (信念分数: {conviction_score:.1f}/100, 阈值: {full_sell_threshold}-{buy_threshold})")

        else:
            # < full_sell_threshold: 全部清仓
            signal = TradeSignal.SELL
            signal_strength = (full_sell_threshold - conviction_score) / full_sell_threshold if full_sell_threshold > 0 else 1.0
            reasons.append(f"🔴 全部清仓 (信念分数: {conviction_score:.1f}/100, 阈值: <{full_sell_threshold})")

        # Step 3: 计算连续信号乘数
        position_multiplier = 1.0
        is_accelerated = False

        if signal == TradeSignal.BUY and consecutive_count >= consecutive_threshold:
            # 触发加速积累机制
            is_accelerated = True
            position_multiplier = self._calculate_acceleration_multiplier(
                consecutive_count,
                consecutive_threshold,
                multiplier_min,
                multiplier_max
            )
            reasons.append(
                f"🚀 触发加速积累 (连续{consecutive_count}次 >= {consecutive_threshold}, "
                f"仓位乘数: {position_multiplier:.2f}x)"
            )

        # Step 4: 计算仓位大小
        position_size = self._calculate_position_size(
            conviction_score,
            signal,
            signal_strength,
            market_data,
            position_multiplier,
            fg_position_adjust,
            full_sell_threshold,
            buy_threshold
        )

        # Step 5: 评估风险等级
        risk_level = self._assess_risk_level(market_data, conviction_score)

        # Step 6: 决定是否执行
        should_execute = self._should_execute(
            signal,
            position_size,
            current_position,
            market_data
        )

        if not should_execute and signal != TradeSignal.HOLD:
            reasons.append(f"⏸️ 暂不执行 (仓位限制或风控)")

        # Step 7: 添加市场警告
        self._add_market_warnings(market_data, warnings)

        return SignalOutput(
            signal=signal,
            signal_strength=signal_strength,
            position_size=position_size,
            risk_level=risk_level,
            should_execute=should_execute,
            reasons=reasons,
            warnings=warnings,
            is_accelerated=is_accelerated,
            consecutive_count=consecutive_count,
            position_multiplier=position_multiplier,
        )

    def _check_circuit_breaker(self, market_data: dict, fg_circuit_breaker_threshold: int = 20) -> CircuitBreaker:
        """检查熔断规则"""

        # 1. 极度恐惧
        fg_value = market_data.get("fear_greed", {}).get("value", 50)
        if fg_value < fg_circuit_breaker_threshold:
            return CircuitBreaker(
                is_triggered=True,
                rule_name="extreme_fear",
                description=f"市场极度恐惧 (Fear & Greed: {fg_value}, 阈值: <{fg_circuit_breaker_threshold})"
            )

        # 2. 美元极强 - 已移除DXY熔断机制
        # DXY数据可能不准确，移除此熔断规则以允许正常交易
        # dxy = market_data.get("macro", {}).get("dxy_index", 100)
        # if dxy > 115:
        #     return CircuitBreaker(
        #         is_triggered=True,
        #         rule_name="strong_dollar",
        #         description=f"美元极度强势 (DXY: {dxy:.2f})"
        #     )

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
        market_data: dict,
        position_multiplier: float = 1.0,
        fg_position_adjust_threshold: int = 30,
        full_sell_threshold: float = 45,
        buy_threshold: float = 50
    ) -> float:
        """
        计算仓位大小

        策略:
        - 信念分数越高,仓位越大
        - 波动率越高,仓位越小
        - 风险指标不好时,仓位越小
        - 连续信号触发时,应用乘数
        """
        if signal == TradeSignal.HOLD:
            return 0.0

        # 基础仓位 (根据信念分数)
        if signal == TradeSignal.BUY:
            # Conviction buy_threshold-100 -> position 0.2%-0.5%
            base_position = self.MIN_POSITION_SIZE + (
                signal_strength * (self.MAX_POSITION_SIZE - self.MIN_POSITION_SIZE)
            )
            # 应用连续信号乘数
            base_position *= position_multiplier

        elif conviction_score >= full_sell_threshold:
            # full_sell_threshold - buy_threshold: 部分减仓，动态计算卖出比例
            # conviction_score从full_sell_threshold到buy_threshold，卖出比例从50%线性减少到0%
            sell_ratio = (buy_threshold - conviction_score) / (buy_threshold - full_sell_threshold) if (buy_threshold - full_sell_threshold) > 0 else 0
            return 0.5 * sell_ratio  # 最多卖出50%

        else:  # conviction_score < full_sell_threshold
            # 全部清仓: 卖出100%
            return 1.0

        # 波动率调整
        price_change = abs(market_data.get("btc_price_change_24h", 0))
        if price_change > 10:
            base_position *= 0.5  # 高波动减半
        elif price_change > 5:
            base_position *= 0.75  # 中等波动减25%

        # 恐惧指数调整（使用配置的阈值）
        fg_value = market_data.get("fear_greed", {}).get("value", 50)
        if fg_value < fg_position_adjust_threshold:  # 恐惧
            base_position *= 0.8

        # 确保调整后不低于最小仓位（BUY信号时）
        if signal == TradeSignal.BUY:
            base_position = max(base_position, self.MIN_POSITION_SIZE)

        return base_position

    def _calculate_acceleration_multiplier(
        self,
        consecutive_count: int,
        threshold: int,
        multiplier_min: float,
        multiplier_max: float
    ) -> float:
        """
        计算加速积累乘数

        公式: multiplier = min(multiplier_min + (count - threshold) * increment, multiplier_max)

        Args:
            consecutive_count: 当前连续次数
            threshold: 触发阈值
            multiplier_min: 最小乘数
            multiplier_max: 最大乘数

        Returns:
            float: 乘数值 (multiplier_min ~ multiplier_max)
        """
        if consecutive_count < threshold:
            return 1.0

        # 计算超出阈值的次数
        extra_count = consecutive_count - threshold

        # 假设在100次内线性增长到max (可调整)
        # increment = (max - min) / 100
        max_extra_count = 100
        increment = (multiplier_max - multiplier_min) / max_extra_count

        multiplier = multiplier_min + (extra_count * increment)

        # 限制在[min, max]范围
        return min(multiplier, multiplier_max)

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
