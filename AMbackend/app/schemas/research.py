"""Schemas for Research Chat agents"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class DecisionType(str, Enum):
    """SuperAgent decision types"""

    DIRECT_ANSWER = "DIRECT_ANSWER"
    ROUTE_TO_PLANNING = "ROUTE_TO_PLANNING"


class SuperAgentOutput(BaseModel):
    """Output schema for SuperAgent"""

    decision: DecisionType = Field(description="Routing decision")
    reasoning: str = Field(description="Reasoning for the decision")
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence in the decision"
    )
    direct_answer: Optional[str] = Field(
        default=None, description="Direct answer if decision is DIRECT_ANSWER"
    )


class AgentPlan(BaseModel):
    """Plan for a single agent in the analysis phase"""

    agent: str = Field(description="Agent name (e.g., macro_agent, ta_agent)")
    reason: str = Field(description="Why this agent is needed")
    data_required: List[str] = Field(description="Data required by this agent")
    priority: str = Field(description="Priority level: high, medium, low")
    note: Optional[str] = Field(default=None, description="Additional notes")


class ExecutionStrategy(BaseModel):
    """Strategy for executing the agent plan"""

    parallel_agents: List[str] = Field(
        description="Agents that can be executed in parallel"
    )
    sequential_after: List[str] = Field(
        description="Agents that must run after parallel agents complete"
    )
    estimated_time: str = Field(description="Estimated time to complete")


class TaskBreakdown(BaseModel):
    """Task breakdown with analysis and decision phases"""

    analysis_phase: List[AgentPlan] = Field(
        description="Business agents to run in analysis phase"
    )
    decision_phase: Dict[str, Any] = Field(
        description="GeneralAnalysisAgent configuration for decision phase"
    )


class PlanningAgentOutput(BaseModel):
    """Output schema for PlanningAgent"""

    task_breakdown: TaskBreakdown = Field(description="Breakdown of analysis tasks")
    execution_strategy: ExecutionStrategy = Field(
        description="Strategy for executing the plan"
    )
    reasoning: str = Field(description="Overall reasoning for the plan")


class GeneralAnalysisOutput(BaseModel):
    """Output schema for GeneralAnalysisAgent"""

    answer: str = Field(description="Final answer to user's question")
    summary: str = Field(description="Summary of all agent analyses")
    key_insights: List[str] = Field(
        description="Key insights from all analyses combined"
    )
    confidence: float = Field(
        ge=0.0, le=1.0, description="Overall confidence in the answer"
    )
    sources: List[str] = Field(
        description="Which agents contributed to this answer"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional metadata"
    )


class ResearchChatMessage(BaseModel):
    """Message in research chat"""

    role: str = Field(description="Message role: user, assistant, system")
    content: str = Field(description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Message metadata (agent info, etc.)"
    )
