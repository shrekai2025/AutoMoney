"""Agent Registry - Manages available business agents"""

from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class AgentInfo:
    """Information about a registered agent"""

    name: str
    display_name: str
    description: str
    specialization: str
    data_sources: List[str]
    use_cases: List[str]
    priority_hint: str  # "high", "medium", "low" - suggested priority for most questions
    is_available: bool  # Whether the agent is implemented and ready to use


class AgentRegistry:
    """
    Registry of available business agents for Research Chat

    PlanningAgent queries this registry to know which agents are available
    """

    def __init__(self):
        """Initialize agent registry"""
        self._agents: Dict[str, AgentInfo] = {}
        self._register_default_agents()

    def _register_default_agents(self):
        """Register all business agents"""

        # MacroAgent - AVAILABLE
        self.register(
            AgentInfo(
                name="macro_agent",
                display_name="MacroAgent",
                description="Macroeconomic analysis expert, analyzing monetary policy, dollar strength, and market sentiment's impact on BTC",
                specialization="Macroeconomic analysis and Bitcoin correlation",
                data_sources=[
                    "Federal Funds Rate (DFF)",
                    "M2 Money Supply growth",
                    "US Dollar Index (DXY)",
                    "Fear & Greed Index",
                    "10-Year Treasury Yield (DGS10)",
                ],
                use_cases=[
                    "Macro environment impact on BTC",
                    "Interest rate and monetary policy analysis",
                    "Dollar strength and liquidity",
                    "Market sentiment and risk appetite",
                    "Long-term investment environment assessment",
                ],
                priority_hint="high",
                is_available=True,  # ✅ Already implemented
            )
        )

        # TAAgent - AVAILABLE
        self.register(
            AgentInfo(
                name="ta_agent",
                display_name="TAAgent",
                description="Technical analysis expert, analyzing price trends, technical indicators, support and resistance levels",
                specialization="Technical analysis and price action",
                data_sources=[
                    "OHLCV (candlestick data)",
                    "Moving averages (EMA, SMA)",
                    "RSI, MACD, Bollinger Bands",
                    "Volume analysis",
                    "Support/resistance levels",
                ],
                use_cases=[
                    "Price trend and pattern analysis",
                    "Technical indicator signals",
                    "Entry/exit timing",
                    "Support/resistance identification",
                    "Short-term trading strategies",
                ],
                priority_hint="high",
                is_available=True,  # ✅ Already implemented
            )
        )

        # OnChainAgent - NOW AVAILABLE
        self.register(
            AgentInfo(
                name="onchain_agent",
                display_name="OnChainAgent",
                description="On-chain data analysis expert, analyzing network activity, transaction fees, and chain health",
                specialization="On-chain metrics and blockchain network health",
                data_sources=[
                    "Active addresses",
                    "Transaction volume",
                    "Network fees",
                    "Mempool congestion",
                    "Simplified NVT ratio",
                    "Hash rate and difficulty",
                ],
                use_cases=[
                    "Network activity analysis",
                    "Transaction fee trends",
                    "On-chain health assessment",
                    "Network congestion status",
                    "Simplified valuation metrics",
                ],
                priority_hint="medium",
                is_available=True,  # ✅ Now implemented with free APIs
            )
        )

    def register(self, agent_info: AgentInfo):
        """Register an agent"""
        self._agents[agent_info.name] = agent_info

    def get_available_agents(self) -> List[AgentInfo]:
        """Get list of available (implemented) agents"""
        return [agent for agent in self._agents.values() if agent.is_available]

    def get_all_agents(self) -> List[AgentInfo]:
        """Get list of all registered agents (including unavailable ones)"""
        return list(self._agents.values())

    def get_agent_info(self, agent_name: str) -> AgentInfo:
        """Get info for a specific agent"""
        return self._agents.get(agent_name)

    def is_agent_available(self, agent_name: str) -> bool:
        """Check if an agent is available"""
        agent = self._agents.get(agent_name)
        return agent.is_available if agent else False

    def get_available_agent_names(self) -> List[str]:
        """Get list of available agent names"""
        return [agent.name for agent in self.get_available_agents()]

    def get_agent_descriptions_for_llm(self) -> str:
        """
        Get formatted agent descriptions for LLM prompt
        Only includes available agents
        """
        available_agents = self.get_available_agents()

        if not available_agents:
            return "**No business agents currently available.**"

        descriptions = []
        for i, agent in enumerate(available_agents, 1):
            desc = f"""### {i}. {agent.display_name} ({agent.name})
**Expertise**: {agent.description}
**Specialization**: {agent.specialization}
**Data Sources**:
{chr(10).join(f'- {source}' for source in agent.data_sources)}

**Use Cases**:
{chr(10).join(f'- {use_case}' for use_case in agent.use_cases)}

**Priority Hint**: {agent.priority_hint}
"""
            descriptions.append(desc)

        return "\n---\n\n".join(descriptions)


# Global agent registry instance
agent_registry = AgentRegistry()
