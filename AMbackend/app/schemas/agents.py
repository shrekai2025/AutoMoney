"""Schemas for AI Agents"""

from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class SignalType(str, Enum):
    """Trading signal types"""

    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class ConfidenceLevel(str, Enum):
    """Confidence levels for signals"""

    VERY_LOW = "VERY_LOW"  # 0-20%
    LOW = "LOW"  # 20-40%
    MEDIUM = "MEDIUM"  # 40-60%
    HIGH = "HIGH"  # 60-80%
    VERY_HIGH = "VERY_HIGH"  # 80-100%


class AgentInput(BaseModel):
    """Base input schema for all agents"""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    market_data: Dict[str, Any] = Field(description="Market data snapshot")
    context: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional context"
    )


class AgentOutput(BaseModel):
    """Base output schema for all agents"""

    agent_name: str = Field(description="Name of the agent")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    signal: SignalType = Field(description="Trading signal")
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence score between 0 and 1"
    )
    confidence_level: ConfidenceLevel = Field(description="Confidence level category")
    reasoning: str = Field(description="Detailed reasoning for the signal")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional metadata"
    )

    @property
    def confidence_percentage(self) -> int:
        """Get confidence as percentage"""
        return int(self.confidence * 100)

    @staticmethod
    def get_confidence_level(confidence: float) -> ConfidenceLevel:
        """Convert confidence float to ConfidenceLevel"""
        if confidence < 0.2:
            return ConfidenceLevel.VERY_LOW
        elif confidence < 0.4:
            return ConfidenceLevel.LOW
        elif confidence < 0.6:
            return ConfidenceLevel.MEDIUM
        elif confidence < 0.8:
            return ConfidenceLevel.HIGH
        else:
            return ConfidenceLevel.VERY_HIGH


class MacroAnalysisOutput(AgentOutput):
    """Output schema for MacroAgent"""

    agent_name: str = Field(default="macro_agent")

    # Macro-specific analysis
    macro_indicators: Dict[str, Any] = Field(
        description="Analyzed macroeconomic indicators"
    )
    key_factors: list[str] = Field(description="Key factors influencing the signal")
    risk_assessment: str = Field(description="Risk assessment based on macro conditions")

    # Full conversation for UI display
    prompt_sent: Optional[str] = Field(default=None, description="Full prompt sent to LLM")
    llm_response: Optional[str] = Field(default=None, description="Raw LLM response")


class OnChainAnalysisOutput(AgentOutput):
    """Output schema for OnChainAgent"""

    agent_name: str = Field(default="onchain_agent")

    # On-chain specific analysis
    onchain_metrics: Dict[str, Any] = Field(description="Analyzed on-chain metrics")
    network_health: str = Field(description="Network health assessment")
    key_observations: list[str] = Field(
        default=[], description="Key observations from on-chain data"
    )

    # Full conversation for UI display
    prompt_sent: Optional[str] = Field(default=None, description="Full prompt sent to LLM")
    llm_response: Optional[str] = Field(default=None, description="Raw LLM response")


class TechnicalAnalysisOutput(AgentOutput):
    """Output schema for TAAgent"""

    agent_name: str = Field(default="ta_agent")

    # Technical analysis specific
    technical_indicators: Dict[str, Any] = Field(
        description="Technical indicators analysis"
    )
    support_levels: list[float] = Field(description="Key support levels")
    resistance_levels: list[float] = Field(description="Key resistance levels")
    trend_analysis: str = Field(description="Trend analysis")
    key_patterns: list[str] = Field(
        default=[], description="Identified technical patterns"
    )

    # Full conversation for UI display
    prompt_sent: Optional[str] = Field(default=None, description="Full prompt sent to LLM")
    llm_response: Optional[str] = Field(default=None, description="Raw LLM response")


class AggregatedAnalysis(BaseModel):
    """Aggregated analysis from all agents"""

    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Individual agent outputs
    macro_analysis: Optional[MacroAnalysisOutput] = None
    onchain_analysis: Optional[OnChainAnalysisOutput] = None
    technical_analysis: Optional[TechnicalAnalysisOutput] = None

    # Aggregated signal
    final_signal: SignalType = Field(description="Final aggregated signal")
    overall_confidence: float = Field(
        ge=0.0, le=1.0, description="Overall confidence score"
    )
    confidence_level: ConfidenceLevel = Field(description="Overall confidence level")

    # Summary
    summary: str = Field(description="Summary of all analyses")
    consensus: bool = Field(
        description="Whether all agents agree on the signal direction"
    )
    action_recommendation: str = Field(
        description="Recommended action based on analysis"
    )

    @property
    def overall_confidence_percentage(self) -> int:
        """Get overall confidence as percentage"""
        return int(self.overall_confidence * 100)
