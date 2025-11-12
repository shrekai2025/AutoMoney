"""Decision Agents - 决策引擎模块

每个策略模板使用一个决策Agent来：
1. 整合业务Agent的分析结果
2. 根据策略参数生成交易决策
3. 输出交易信号和仓位大小
"""

from app.decision_agents.multi_agent_conviction import MultiAgentConvictionDecision

__all__ = ["MultiAgentConvictionDecision"]

