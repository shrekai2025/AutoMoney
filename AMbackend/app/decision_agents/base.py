"""Base Decision Agent - 决策Agent抽象基类

预留用于未来扩展，当有第二种决策逻辑时启用
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class DecisionOutput:
    """决策输出"""
    signal: str  # "BUY", "SELL", "HOLD", "LONG", "SHORT"
    signal_strength: float  # 0-1
    position_size: float  # 0-1
    conviction_score: float  # 0-100
    risk_level: str  # "LOW", "MEDIUM", "HIGH"
    should_execute: bool
    reasons: list
    warnings: list
    metadata: Dict[str, Any]  # 其他信息
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典(用于兼容旧的决策Agent)"""
        return {
            "signal": self.signal,
            "signal_strength": self.signal_strength,
            "position_size": self.position_size,
            "conviction_score": self.conviction_score,
            "risk_level": self.risk_level,
            "should_execute": self.should_execute,
            "reasons": self.reasons,
            "warnings": self.warnings,
            **self.metadata  # 展开metadata到顶层
        }


class BaseDecisionAgent(ABC):
    """决策Agent抽象基类
    
    未来当有多种决策逻辑时，所有决策Agent都应继承此基类
    """
    
    @abstractmethod
    def decide(
        self,
        agent_outputs: Dict[str, Any],
        market_data: Dict[str, Any],
        instance_params: Dict[str, Any],
        current_position: float = 0.0,
    ) -> DecisionOutput:
        """
        根据业务Agent输出和策略参数做出交易决策
        
        Args:
            agent_outputs: 业务Agent的分析结果
            market_data: 市场数据快照
            instance_params: 策略实例参数
            current_position: 当前持仓比例
            
        Returns:
            DecisionOutput: 决策结果
        """
        pass

