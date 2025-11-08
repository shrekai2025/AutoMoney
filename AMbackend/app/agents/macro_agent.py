"""MacroAgent - Macroeconomic Analysis Agent"""

from typing import Dict, Any

from app.services.llm.manager import llm_manager
from app.schemas.llm import Message
from app.utils.json_parser import parse_llm_json, JSONParseError
from app.schemas.agents import (
    MacroAnalysisOutput,
    SignalType,
    AgentOutput,
)


class MacroAgent:
    """
    MacroAgent analyzes macroeconomic indicators and their impact on Bitcoin

    Focuses on:
    - Federal Funds Rate & monetary policy
    - M2 Money Supply growth
    - US Dollar Index (DXY)
    - Fear & Greed Index
    - Inflation expectations
    - Liquidity conditions
    """

    SYSTEM_PROMPT = """You are a macroeconomic analysis expert specializing in cryptocurrency markets, particularly Bitcoin.

Your role is to analyze macroeconomic indicators and their impact on Bitcoin price movements.

Key indicators you should analyze:
1. **Federal Funds Rate (DFF)**: Central bank interest rates affect liquidity and risk appetite
2. **M2 Money Supply Growth**: Money supply expansion/contraction impacts asset prices
3. **US Dollar Index (DXY)**: Bitcoin often moves inversely to USD strength
4. **Fear & Greed Index**: Market sentiment indicator
5. **10-Year Treasury Yield (DGS10)**: Risk-free rate benchmark

Analysis guidelines:
- **BULLISH signals**: Low/falling interest rates, increasing M2, weakening dollar, improving sentiment
- **BEARISH signals**: High/rising interest rates, contracting M2, strengthening dollar, extreme fear
- **NEUTRAL signals**: Mixed indicators, transitional periods

⚠️ CRITICAL OUTPUT REQUIREMENTS:

1. ❌ ABSOLUTELY NO MARKDOWN in JSON string values (no **, ##, -, *, etc.)
2. ❌ NO markdown code blocks (no ```json or ```)
3. ❌ NO extra text before or after the JSON
4. ❌ NO thinking, explanations, or commentary outside JSON
5. ✅ Use plain text in "reasoning" and other string fields
6. ✅ Use \n for line breaks in strings (NOT real newlines)
7. ✅ Start response with { and end with }
8. ✅ Use double quotes for all strings
9. ✅ Escape special characters properly

IMPORTANT: You must respond with ONLY valid JSON. Do not include any thinking or text before or after the JSON.
The JSON must match this exact structure with these exact field names:

{
    "signal": "BULLISH",
    "confidence": 0.75,
    "score": 45.0,
    "reasoning": "Detailed explanation of your analysis...",
    "macro_indicators": {
        "fed_funds_rate": {"value": 3.87, "impact": "BEARISH", "weight": 0.3},
        "m2_growth": {"value": 0.47, "impact": "NEUTRAL", "weight": 0.2},
        "dxy": {"value": 121.77, "impact": "BEARISH", "weight": 0.25},
        "fear_greed": {"value": 23, "classification": "Extreme Fear", "impact": "BEARISH", "weight": 0.15},
        "treasury_yield": {"value": 4.2, "impact": "BEARISH", "weight": 0.1}
    },
    "key_factors": [
        "High interest rates reducing liquidity",
        "Strong dollar creating headwinds",
        "Extreme fear sentiment"
    ],
    "risk_assessment": "High risk environment due to tight monetary policy and risk-off sentiment"
}

CRITICAL REQUIREMENTS:
- "signal" MUST be one of: "BULLISH", "BEARISH", or "NEUTRAL" (no other values like "HOLD")
- "confidence" MUST be a decimal between 0.0 and 1.0 (NOT a percentage like 72, use 0.72 instead)
- "score" MUST be a number between -100.0 and 100.0 representing investment conviction:
  * -100 to -60: Strong bearish (recommend selling/shorting)
  * -60 to -20: Moderate bearish (reduce exposure)
  * -20 to +20: Neutral (hold current position)
  * +20 to +60: Moderate bullish (accumulate gradually)
  * +60 to +100: Strong bullish (aggressive buying)
- "macro_indicators" is the exact field name (not "macroeconomic_analysis" or any other name)
- All field names must match exactly as shown above

🎯 UNDERSTAND THE DIFFERENCE:
- **confidence** (0-1): Your subjective certainty about this analysis. How reliable is your reading of the data?
- **score** (-100 to +100): Objective investment recommendation. How much should investors buy or sell?

Example:
- "I'm 80% confident (confidence=0.8) that the macro environment is moderately bullish (score=+45)"
- "I'm only 50% confident (confidence=0.5) due to mixed signals, but the bullish signals are stronger (score=+30)"

Be objective, data-driven, and consider the interplay between different macroeconomic forces.

Your score calculation should reflect:
- Alignment of indicators (all pointing same direction = higher |score|)
- Strength of each indicator's signal
- Current market regime and context
- Overall liquidity and risk appetite environment

Your confidence should reflect:
- Data quality and completeness
- Clarity of signals (mixed signals = lower confidence)
- Economic uncertainty and transition periods

⚠️ FINAL REMINDER: Respond with ONLY the JSON object. NO MARKDOWN formatting in string values. Start with { and end with }.
"""

    def __init__(self):
        """Initialize MacroAgent"""
        self.agent_name = "macro_agent"

    async def analyze(self, market_data: Dict[str, Any]) -> MacroAnalysisOutput:
        """
        Analyze macroeconomic conditions and generate trading signal

        Args:
            market_data: Dictionary containing:
                - btc_price: Current BTC price
                - price_change_24h: 24h price change percentage
                - macro: MacroEconomicData object (DFF, M2, DXY, DGS10)
                - fear_greed: Fear & Greed Index data

        Returns:
            MacroAnalysisOutput with signal, confidence, and reasoning
        """
        # Build analysis prompt
        analysis_prompt = self._build_analysis_prompt(market_data)

        # Prepend system prompt to user message for Claude thinking models
        full_prompt = f"{self.SYSTEM_PROMPT}\n\n{analysis_prompt}"

        # Call LLM
        messages = [Message(role="user", content=full_prompt)]

        response = await llm_manager.chat_for_agent(
            agent_name=self.agent_name, messages=messages
        )

        # Parse LLM response
        analysis = self._parse_llm_response(response.content)

        # Build output with full conversation
        return MacroAnalysisOutput(
            agent_name=self.agent_name,
            signal=SignalType(analysis["signal"]),
            confidence=float(analysis["confidence"]),
            score=float(analysis["score"]),
            confidence_level=AgentOutput.get_confidence_level(
                float(analysis["confidence"])
            ),
            reasoning=analysis["reasoning"],
            macro_indicators=analysis["macro_indicators"],
            key_factors=analysis["key_factors"],
            risk_assessment=analysis["risk_assessment"],
            # Add full conversation for UI display
            prompt_sent=full_prompt,
            llm_response=response.content,
        )

    def _build_analysis_prompt(self, market_data: Dict[str, Any]) -> str:
        """Build the analysis prompt with market data"""
        macro = market_data.get("macro", {})
        fear_greed = market_data.get("fear_greed", {})

        # Extract Treasury yield from metadata if available
        treasury_10y = "N/A"
        if macro.get('metadata') and 'dgs10_rate' in macro['metadata']:
            treasury_10y = f"{macro['metadata']['dgs10_rate']}"

        prompt = f"""Analyze the current macroeconomic environment and its impact on Bitcoin:

**Current Market Data:**
- BTC Price: ${market_data.get('btc_price', 0):,.2f}
- 24h Change: {market_data.get('price_change_24h', 0):+.2f}%

**Macroeconomic Indicators:**
- Federal Funds Rate: {macro.get('fed_rate_prob', 'N/A')}%
- M2 Growth Rate: {macro.get('m2_growth', 'N/A')}%
- US Dollar Index (DXY): {macro.get('dxy_index', 'N/A')}
- 10-Year Treasury Yield: {treasury_10y}%

**Market Sentiment:**
- Fear & Greed Index: {fear_greed.get('value', 'N/A')}/100
- Classification: {fear_greed.get('classification', 'N/A')}

Provide a comprehensive macroeconomic analysis and generate a trading signal.

Remember to:
1. Consider the interplay between monetary policy, liquidity, and dollar strength
2. Assess how current conditions compare to historical Bitcoin bull/bear markets
3. Weight different indicators appropriately based on their current relevance
4. Provide specific, actionable reasoning

Return your analysis in the specified JSON format."""

        return prompt

    def _parse_llm_response(self, content: str) -> Dict[str, Any]:
        """
        Parse LLM response and extract structured analysis

        Args:
            content: Raw LLM response content

        Returns:
            Parsed analysis dictionary
        """
        try:
            # Try to extract JSON from response
            # LLM might wrap JSON in markdown code blocks
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
            elif "```" in content:
                json_start = content.find("```") + 3
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
            else:
                # Assume entire response is JSON
                json_str = content.strip()

            # Parse JSON
            analysis = parse_llm_json(content)

            # Validate required fields
            required_fields = [
                "signal",
                "confidence",
                "score",
                "reasoning",
                "macro_indicators",
                "key_factors",
                "risk_assessment",
            ]
            for field in required_fields:
                if field not in analysis:
                    raise ValueError(f"Missing required field: {field}")

            # Validate signal type
            if analysis["signal"] not in ["BULLISH", "BEARISH", "NEUTRAL"]:
                raise ValueError(f"Invalid signal type: {analysis['signal']}")

            # Validate confidence range
            confidence = float(analysis["confidence"])
            if not 0.0 <= confidence <= 1.0:
                raise ValueError(f"Confidence must be between 0 and 1: {confidence}")

            # Validate score range
            score = float(analysis["score"])
            if not -100.0 <= score <= 100.0:
                raise ValueError(f"Score must be between -100 and 100: {score}")

            return analysis

        except (JSONParseError, ValueError) as e:
            # Fallback: return neutral signal with low confidence
            print(f"Error parsing LLM response: {e}")
            print(f"Raw content: {content[:500]}...")

            return {
                "signal": "NEUTRAL",
                "confidence": 0.3,
                "score": 0.0,
                "reasoning": f"Unable to parse LLM response properly. Error: {str(e)}. Raw response available in logs.",
                "macro_indicators": {},
                "key_factors": ["Analysis parsing error - please review logs"],
                "risk_assessment": "Unable to assess due to parsing error",
            }


# Global MacroAgent instance
macro_agent = MacroAgent()
