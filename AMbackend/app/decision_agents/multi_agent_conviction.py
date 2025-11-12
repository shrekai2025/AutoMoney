"""Multi-Agent Conviction Decision - 多Agent信念决策引擎

整合ConvictionCalculator和SignalGenerator的决策逻辑
用于Multi-Agent BTC Strategy
"""

from typing import Dict, Any, Optional
import logging

from app.services.decision.conviction_calculator import ConvictionCalculator, ConvictionInput
from app.services.decision.signal_generator import SignalGenerator, TradeSignal

logger = logging.getLogger(__name__)


class MultiAgentConvictionDecision:
    """多Agent信念决策引擎
    
    决策流程：
    1. 使用ConvictionCalculator计算信念分数
    2. 使用SignalGenerator生成交易信号
    3. 返回完整的决策结果
    """
    
    def __init__(self):
        self.conviction_calculator = ConvictionCalculator()
        self.signal_generator = SignalGenerator()
    
    def decide(
        self,
        agent_outputs: Dict[str, Any],
        market_data: Dict[str, Any],
        instance_params: Dict[str, Any],
        portfolio_state: Optional[Dict[str, Any]] = None,
        current_position: float = 0.0,
    ) -> Dict[str, Any]:
        """
        执行决策
        
        Args:
            agent_outputs: 业务Agent输出 {"macro": {...}, "ta": {...}, "onchain": {...}}
            market_data: 市场数据快照
            instance_params: 策略实例参数
            portfolio_state: 组合运行时状态（连续信号计数等）
            current_position: 当前持仓比例 (0-1)
            
        Returns:
            决策结果字典
        """
        try:
            # Step 1: 计算信念分数
            conviction_input = ConvictionInput(
                macro_output=agent_outputs.get("macro", {}),
                ta_output=agent_outputs.get("ta", {}),
                onchain_output=agent_outputs.get("onchain", {}),
                market_data=market_data,
            )
            
            # 从instance_params获取agent_weights（如果有）
            custom_weights = instance_params.get("agent_weights")
            conviction_result = self.conviction_calculator.calculate(
                conviction_input,
                custom_weights=custom_weights
            )
            
            logger.info(f"Conviction Score: {conviction_result.score:.2f}")
            
            # Step 2: 准备portfolio_state
            if portfolio_state is None:
                portfolio_state = {}
            
            # 合并instance_params中的配置到portfolio_state
            portfolio_state_with_params = {
                **portfolio_state,
                **{k: v for k, v in instance_params.items() if k not in ["agent_weights"]}
            }
            
            # Step 3: 生成交易信号
            signal_result = self.signal_generator.generate_signal(
                conviction_score=conviction_result.score,
                market_data=market_data,
                current_position=current_position,
                portfolio_state=portfolio_state_with_params,
            )
            
            logger.info(
                f"Signal: {signal_result.signal.value}, "
                f"Position Size: {signal_result.position_size:.4f}, "
                f"Should Execute: {signal_result.should_execute}"
            )
            
            # Step 4: 返回决策结果
            return {
                # 信念分数相关
                "conviction_score": conviction_result.score,
                "conviction_details": conviction_result.details,
                
                # 交易信号相关
                "signal": signal_result.signal,
                "signal_strength": signal_result.signal_strength,
                "position_size": signal_result.position_size,
                "risk_level": signal_result.risk_level,
                "should_execute": signal_result.should_execute,
                "reasons": signal_result.reasons,
                "warnings": signal_result.warnings,
                
                # 连续信号相关
                "is_accelerated": signal_result.is_accelerated,
                "consecutive_count": signal_result.consecutive_count,
                "position_multiplier": signal_result.position_multiplier,
            }
            
        except Exception as e:
            logger.error(f"Decision failed: {e}", exc_info=True)
            # 返回一个安全的HOLD决策
            return {
                "conviction_score": 50.0,
                "signal": TradeSignal.HOLD,
                "signal_strength": 0.0,
                "position_size": 0.0,
                "risk_level": "HIGH",
                "should_execute": False,
                "reasons": [f"决策失败: {str(e)}"],
                "warnings": ["系统错误，已暂停交易"],
                "is_accelerated": False,
                "consecutive_count": 0,
                "position_multiplier": 1.0,
            }

