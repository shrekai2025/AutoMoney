"""MomentumRegimeDecision - 动量策略决策引擎

整合RegimeFilterAgent和TAMomentumAgent的输出
动态调制参数,生成带止损止盈的OCO订单
"""

from typing import Dict, Any, Optional, Tuple
import logging
from dataclasses import dataclass, asdict
from decimal import Decimal

from app.decision_agents.base import BaseDecisionAgent, DecisionOutput

logger = logging.getLogger(__name__)


@dataclass
class OCOOrder:
    """OCO订单(One-Cancels-Other)"""
    asset: str  # BTC/ETH/SOL
    side: str  # "LONG" or "SHORT"
    entry_price: float
    entry_amount: float  # 实际交易数量
    stop_loss_price: float
    take_profit_price: float
    stop_loss_trigger_type: str = "mark_price"  # mark_price for SL
    take_profit_trigger_type: str = "last_price"  # last_price for TP
    leverage: float = 1.0  # 杠杆倍数(模拟交易暂不使用)
    
    def to_dict(self) -> Dict[str, Any]:
        """转为字典"""
        return asdict(self)
    
    def validate(self) -> Tuple[bool, list]:
        """
        验证OCO订单的合法性
        
        Returns:
            (is_valid, errors)
        """
        errors = []
        
        # 1. 价格必须为正
        if self.entry_price <= 0:
            errors.append(f"入场价格必须为正: {self.entry_price}")
        if self.stop_loss_price <= 0:
            errors.append(f"止损价格必须为正: {self.stop_loss_price}")
        if self.take_profit_price <= 0:
            errors.append(f"止盈价格必须为正: {self.take_profit_price}")
        
        # 2. 数量必须为正
        if self.entry_amount <= 0:
            errors.append(f"交易数量必须为正: {self.entry_amount}")
        
        # 3. 做多逻辑: SL < Entry < TP
        if self.side == "LONG":
            if self.stop_loss_price >= self.entry_price:
                errors.append(
                    f"做多止损价必须低于入场价: SL={self.stop_loss_price}, Entry={self.entry_price}"
                )
            if self.take_profit_price <= self.entry_price:
                errors.append(
                    f"做多止盈价必须高于入场价: TP={self.take_profit_price}, Entry={self.entry_price}"
                )
        
        # 4. 做空逻辑: TP < Entry < SL
        elif self.side == "SHORT":
            if self.stop_loss_price <= self.entry_price:
                errors.append(
                    f"做空止损价必须高于入场价: SL={self.stop_loss_price}, Entry={self.entry_price}"
                )
            if self.take_profit_price >= self.entry_price:
                errors.append(
                    f"做空止盈价必须低于入场价: TP={self.take_profit_price}, Entry={self.entry_price}"
                )
        else:
            errors.append(f"无效的方向: {self.side}")
        
        # 5. 止损距离范围检查(0.5%-10%)
        sl_distance_pct = abs(self.entry_price - self.stop_loss_price) / self.entry_price * 100
        if sl_distance_pct < 0.5:
            errors.append(f"止损距离过小(<0.5%): {sl_distance_pct:.2f}%")
        if sl_distance_pct > 10.0:
            errors.append(f"止损距离过大(>10%): {sl_distance_pct:.2f}%")
        
        # 6. 风险回报比检查(至少1.5:1)
        if self.side == "LONG":
            risk = self.entry_price - self.stop_loss_price
            reward = self.take_profit_price - self.entry_price
        else:  # SHORT
            risk = self.stop_loss_price - self.entry_price
            reward = self.entry_price - self.take_profit_price
        
        if risk > 0:
            rr_ratio = reward / risk
            if rr_ratio < 1.5:
                errors.append(f"风险回报比过低(<1.5:1): {rr_ratio:.2f}:1")
        else:
            errors.append("风险为0或负数,无法计算RR比")
        
        return len(errors) == 0, errors


class MomentumRegimeDecision(BaseDecisionAgent):
    """
    动量策略决策引擎
    
    决策流程:
    1. Technical Analysis Layer (80%权重) - 主导决策
       - 确定"交易什么"(币种+方向+强度)
       - 计算基础仓位大小
    
    2. Regime Confirmation Layer (20%权重) - 确认和增幅
       - 过滤极端逆势信号
       - 调制仓位/杠杆/止盈(通过Regime Multiplier)
    
    3. Risk Management Layer - 强制风控
       - 必须设置止损止盈
       - 生成OCO订单
       - 拒绝裸交易
    """
    
    # 默认参数
    DEFAULT_PARAMS = {
        "base_risk_pct": 2.0,  # 基础风险比例(账户的%)
        "base_leverage": 3.0,  # 基础杠杆(模拟交易暂不生效)
        "max_leverage": 5.0,   # 最大杠杆
        "min_signal_strength": 0.6,  # 最低信号强度
        "regime_weight": 0.2,  # Regime影响权重
        "ta_weight": 0.8,      # TA影响权重
        "extreme_regime_threshold": 25.0,  # 极端Regime阈值(低于此值拒绝逆势)
    }
    
    def __init__(self, custom_params: Dict[str, Any] = None):
        """
        初始化决策引擎
        
        Args:
            custom_params: 自定义参数(覆盖默认值)
        """
        self.params = {**self.DEFAULT_PARAMS}
        if custom_params:
            self.params.update(custom_params)
        
        logger.info(f"MomentumRegimeDecision初始化,参数: {self.params}")
    
    def decide(
        self,
        agent_outputs: Dict[str, Any],
        market_data: Dict[str, Any],
        instance_params: Dict[str, Any],
        portfolio_state: Optional[Dict[str, Any]] = None,
        current_position: float = 0.0,
    ) -> DecisionOutput:
        """
        执行决策逻辑
        
        Args:
            agent_outputs: {
                "regime_filter": {...},  # RegimeFilterAgent输出
                "ta_momentum": {...}     # TAMomentumAgent输出
            }
            market_data: 市场数据快照
            instance_params: 策略实例参数(覆盖默认参数)
            portfolio_state: 组合运行时状态(暂不使用,预留接口)
            current_position: 当前持仓(暂时未使用,未来支持多持仓)
        
        Returns:
            DecisionOutput
        """
        try:
            logger.info("=" * 60)
            logger.info("MomentumRegimeDecision开始决策...")
            
            # Step 1: 提取Agent输出
            regime_output = agent_outputs.get("regime_filter", {})
            ta_output = agent_outputs.get("ta_momentum", {})
            
            if not regime_output or not ta_output:
                return self._create_hold_decision(
                    "缺少必要的Agent输出",
                    ["regime_filter或ta_momentum输出缺失"]
                )
            
            # Step 2: 合并参数
            effective_params = {**self.params, **instance_params}
            
            # Step 3: Technical Analysis Layer - 主导决策
            ta_decision = self._analyze_ta_signal(ta_output, effective_params)
            
            if ta_decision["signal"] == "HOLD":
                return self._create_hold_decision(
                    ta_decision["reason"],
                    ta_decision.get("warnings", [])
                )
            
            # Step 4: Regime Confirmation Layer - 确认和调制
            regime_score = regime_output.get("regime_score", 50.0)
            regime_multiplier = self._calculate_regime_multiplier(regime_score)
            
            # 检查极端逆势
            if self._is_extreme_counter_trend(ta_decision, regime_score, effective_params):
                return self._create_hold_decision(
                    f"Regime极端逆势,拒绝交易 (Score={regime_score:.1f}, 信号={ta_decision['signal']})",
                    [f"市场环境评分过低: {regime_score:.1f}/100"]
                )
            
            # Step 5: 计算有效参数(Regime调制)
            effective_risk_pct = effective_params["base_risk_pct"] * regime_multiplier
            effective_leverage = min(
                effective_params["base_leverage"] * (regime_multiplier ** 0.5),
                effective_params["max_leverage"]
            )
            effective_tp_rr = ta_decision["take_profit_rr"] * regime_multiplier
            
            logger.info(f"Regime调制: Score={regime_score:.1f}, Multiplier={regime_multiplier:.2f}")
            logger.info(f"有效参数: Risk={effective_risk_pct:.2f}%, Leverage={effective_leverage:.1f}x, TP_RR={effective_tp_rr:.1f}")
            
            # Step 6: Risk Management Layer - 生成OCO订单
            oco_order = self._generate_oco_order(
                ta_decision=ta_decision,
                regime_multiplier=regime_multiplier,
                effective_risk_pct=effective_risk_pct,
                effective_leverage=effective_leverage,
                effective_tp_rr=effective_tp_rr,
                market_data=market_data,
                portfolio_value=instance_params.get("portfolio_value", 10000.0)
            )
            
            if not oco_order:
                return self._create_hold_decision(
                    "OCO订单生成失败",
                    ["无法计算有效的止损止盈"]
                )
            
            # Step 7: 验证OCO订单
            is_valid, errors = oco_order.validate()
            if not is_valid:
                return self._create_hold_decision(
                    "OCO订单验证失败",
                    errors
                )
            
            # Step 8: 生成最终决策
            decision = self._create_trade_decision(
                oco_order=oco_order,
                ta_decision=ta_decision,
                regime_score=regime_score,
                regime_multiplier=regime_multiplier,
                effective_params=effective_params
            )
            
            logger.info(f"✅ 决策完成: {decision.signal} {oco_order.asset}")
            logger.info(f"   入场: {oco_order.entry_price:.2f}, 数量: {oco_order.entry_amount:.4f}")
            logger.info(f"   止损: {oco_order.stop_loss_price:.2f}, 止盈: {oco_order.take_profit_price:.2f}")
            logger.info("=" * 60)
            
            return decision
            
        except Exception as e:
            logger.error(f"决策过程出错: {e}", exc_info=True)
            return self._create_hold_decision(
                "决策引擎内部错误",
                [str(e)]
            )
    
    def _analyze_ta_signal(
        self, 
        ta_output: Dict[str, Any],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析TA信号,确定最佳交易机会
        
        Returns:
            {
                "signal": "BUY"/"SELL"/"HOLD",
                "asset": "BTC",
                "signal_strength": 0.85,
                "confidence": 0.8,
                "entry_price": 43250.0,
                "stop_loss_distance_atr": 1.5,
                "take_profit_rr": 2.5,
                "reason": "...",
                "warnings": [...]
            }
        """
        best_opp = ta_output.get("best_opportunity")
        
        if not best_opp:
            return {
                "signal": "HOLD",
                "reason": "TA Agent未发现明确交易机会",
                "warnings": []
            }
        
        signal = best_opp.get("signal", "NEUTRAL")
        signal_strength = best_opp.get("signal_strength", 0.0)
        confidence = best_opp.get("confidence", 0.0)
        
        # 检查信号强度
        min_strength = params.get("min_signal_strength", 0.6)
        if signal == "NEUTRAL" or signal_strength < min_strength:
            return {
                "signal": "HOLD",
                "reason": f"信号强度不足 ({signal_strength:.2f} < {min_strength})",
                "warnings": [f"TA信号: {signal}, 强度: {signal_strength:.2f}"]
            }
        
        # 映射信号方向
        if signal == "LONG":
            decision_signal = "BUY"
        elif signal == "SHORT":
            decision_signal = "SELL"
        else:
            return {
                "signal": "HOLD",
                "reason": f"未知的TA信号类型: {signal}",
                "warnings": []
            }
        
        # 提取止损止盈参数
        asset = best_opp.get("asset", "BTC")
        entry_price = best_opp.get("entry_price", 0.0)
        sl_distance_atr = best_opp.get("stop_loss_distance_atr", 2.0)
        tp_rr = best_opp.get("take_profit_rr", 2.0)
        reasoning = best_opp.get("reasoning", "")
        
        return {
            "signal": decision_signal,
            "asset": asset,
            "signal_strength": signal_strength,
            "confidence": confidence,
            "entry_price": entry_price,
            "stop_loss_distance_atr": sl_distance_atr,
            "take_profit_rr": tp_rr,
            "reason": reasoning,
            "warnings": []
        }
    
    def _is_extreme_counter_trend(
        self,
        ta_decision: Dict[str, Any],
        regime_score: float,
        params: Dict[str, Any]
    ) -> bool:
        """
        判断是否为极端逆势信号
        
        规则:
        - 如果Regime Score < 阈值(默认25) 且 TA信号为BUY(做多),拒绝
        - 如果Regime Score > (100 - 阈值) 且 TA信号为SELL(做空),拒绝
        """
        threshold = params.get("extreme_regime_threshold", 25.0)
        signal = ta_decision.get("signal")
        
        # 极度危险环境下做多
        if regime_score < threshold and signal == "BUY":
            logger.warning(f"极端逆势: Regime={regime_score:.1f} < {threshold}, 信号=BUY")
            return True
        
        # 极度健康环境下做空(暂时不启用,允许高位做空)
        # if regime_score > (100 - threshold) and signal == "SELL":
        #     logger.warning(f"极端逆势: Regime={regime_score:.1f} > {100-threshold}, 信号=SELL")
        #     return True
        
        return False
    
    def _calculate_regime_multiplier(self, regime_score: float) -> float:
        """
        根据Regime Score计算仓位乘数
        
        映射关系(分段线性):
        - 0-20: 0.3x
        - 20-40: 0.3x → 0.6x
        - 40-60: 0.6x → 1.0x
        - 60-80: 1.0x → 1.3x
        - 80-100: 1.3x → 1.6x
        """
        if regime_score < 20:
            return 0.3
        elif regime_score < 40:
            # 线性插值
            return 0.3 + (regime_score - 20) / 20 * (0.6 - 0.3)
        elif regime_score < 60:
            return 0.6 + (regime_score - 40) / 20 * (1.0 - 0.6)
        elif regime_score < 80:
            return 1.0 + (regime_score - 60) / 20 * (1.3 - 1.0)
        else:  # 80-100
            return 1.3 + (regime_score - 80) / 20 * (1.6 - 1.3)
    
    def _generate_oco_order(
        self,
        ta_decision: Dict[str, Any],
        regime_multiplier: float,
        effective_risk_pct: float,
        effective_leverage: float,
        effective_tp_rr: float,
        market_data: Dict[str, Any],
        portfolio_value: float
    ) -> Optional[OCOOrder]:
        """
        生成OCO订单
        
        计算逻辑:
        1. 从market_data获取ATR
        2. Stop_Loss = Entry ± (ATR × SL_Distance_ATR)
        3. Take_Profit = Entry ± (|Entry - SL| × TP_RR)
        4. Position_Size = (Portfolio × Risk% × Leverage) / |Entry - SL|
        5. Entry_Amount = Position_Size / Entry_Price
        """
        asset = ta_decision["asset"]
        signal = ta_decision["signal"]
        entry_price = ta_decision["entry_price"]
        sl_distance_atr = ta_decision["stop_loss_distance_atr"]
        
        # 获取ATR
        assets_data = market_data.get("assets", {})
        asset_data = assets_data.get(asset, {})
        
        # 优先使用60分钟ATR(更稳定)
        atr = asset_data.get("ohlcv_60m_atr", asset_data.get("ohlcv_15m_atr", 0))
        
        if atr == 0:
            logger.error(f"{asset}缺少ATR数据,无法计算止损")
            return None
        
        # 计算止损价格
        if signal == "BUY":
            stop_loss_price = entry_price - (atr * sl_distance_atr)
            side = "LONG"
        else:  # SELL
            stop_loss_price = entry_price + (atr * sl_distance_atr)
            side = "SHORT"
        
        # 计算止盈价格
        risk_per_unit = abs(entry_price - stop_loss_price)
        if signal == "BUY":
            take_profit_price = entry_price + (risk_per_unit * effective_tp_rr)
        else:  # SELL
            take_profit_price = entry_price - (risk_per_unit * effective_tp_rr)
        
        # 计算仓位大小
        # Position_Value = (Portfolio × Risk% × Leverage) / (Risk_Per_Unit / Entry_Price)
        # 简化: Entry_Amount = (Portfolio × Risk% × Leverage) / Risk_Per_Unit
        risk_amount = portfolio_value * (effective_risk_pct / 100)
        position_value = risk_amount * effective_leverage
        
        if risk_per_unit == 0:
            logger.error("风险距离为0,无法计算仓位")
            return None
        
        entry_amount = position_value / risk_per_unit
        
        # 转换为实际币数量
        entry_amount_coins = entry_amount / entry_price
        
        logger.info(f"仓位计算: Risk={risk_amount:.2f} USD, Leverage={effective_leverage:.1f}x, Amount={entry_amount_coins:.6f} {asset}")
        
        # 创建OCO订单
        oco_order = OCOOrder(
            asset=asset,
            side=side,
            entry_price=entry_price,
            entry_amount=entry_amount_coins,
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price,
            leverage=effective_leverage
        )
        
        return oco_order
    
    def _create_trade_decision(
        self,
        oco_order: OCOOrder,
        ta_decision: Dict[str, Any],
        regime_score: float,
        regime_multiplier: float,
        effective_params: Dict[str, Any]
    ) -> DecisionOutput:
        """创建交易决策"""
        
        # 计算综合conviction score (-100到+100)
        # TA主导(80%) + Regime调制(20%)
        ta_strength = ta_decision["signal_strength"]  # 0-1
        ta_confidence = ta_decision["confidence"]  # 0-1
        ta_score = (ta_strength + ta_confidence) / 2  # 0-1
        
        # 映射到-100到+100
        if oco_order.side == "LONG":
            base_conviction = ta_score * 100  # 0-100
        else:  # SHORT
            base_conviction = -ta_score * 100  # -100到0
        
        # Regime调制(±20分)
        regime_adjustment = (regime_score - 50) / 50 * 20  # -20到+20
        final_conviction = base_conviction + regime_adjustment
        
        # 限制在[-100, 100]
        final_conviction = max(-100, min(100, final_conviction))
        
        # 构建决策理由
        reasons = [
            f"TA信号: {oco_order.side} {oco_order.asset} (强度:{ta_strength:.2f}, 信心:{ta_confidence:.2f})",
            f"Regime Score: {regime_score:.1f}/100 (乘数:{regime_multiplier:.2f}x)",
            f"入场价: {oco_order.entry_price:.2f}",
            f"止损价: {oco_order.stop_loss_price:.2f} ({abs(oco_order.entry_price - oco_order.stop_loss_price)/oco_order.entry_price*100:.2f}%)",
            f"止盈价: {oco_order.take_profit_price:.2f}",
            ta_decision["reason"][:200]  # 截断过长的理由
        ]
        
        # 风险等级
        if regime_score < 40:
            risk_level = "HIGH"
        elif regime_score < 70:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return DecisionOutput(
            signal=oco_order.side,  # "LONG" or "SHORT"
            signal_strength=ta_strength,
            position_size=ta_strength * regime_multiplier,  # 综合仓位比例
            conviction_score=final_conviction,
            risk_level=risk_level,
            should_execute=True,
            reasons=reasons,
            warnings=[],
            metadata={
                "oco_order": oco_order.to_dict(),
                "ta_decision": ta_decision,
                "regime_score": regime_score,
                "regime_multiplier": regime_multiplier,
                "effective_params": effective_params,
                "strategy_type": "momentum_regime"
            }
        )
    
    def _create_hold_decision(
        self, 
        reason: str, 
        warnings: list = None
    ) -> DecisionOutput:
        """创建持仓/观望决策"""
        return DecisionOutput(
            signal="HOLD",
            signal_strength=0.0,
            position_size=0.0,
            conviction_score=0.0,
            risk_level="LOW",
            should_execute=False,
            reasons=[reason],
            warnings=warnings or [],
            metadata={"strategy_type": "momentum_regime"}
        )


# 全局实例(使用默认参数)
momentum_regime_decision = MomentumRegimeDecision()

