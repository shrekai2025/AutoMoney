"""TAAgent - Technical Analysis Agent"""

from typing import Dict, Any, List

from app.services.llm.manager import llm_manager
from app.schemas.llm import Message
from app.utils.json_parser import parse_llm_json, JSONParseError
from app.schemas.agents import (
    TechnicalAnalysisOutput,
    SignalType,
    AgentOutput,
)
from app.services.indicators.calculator import IndicatorCalculator
from app.schemas.market_data import OHLCVData


class TAAgent:
    """
    TAAgent analyzes technical indicators and price action for Bitcoin

    Focuses on:
    - Price trends and momentum (EMA crossovers)
    - RSI (Relative Strength Index) for overbought/oversold conditions
    - MACD for trend strength and momentum
    - Bollinger Bands for volatility and price extremes
    - Support and resistance levels
    - Chart patterns and technical setups
    """

    SYSTEM_PROMPT = """You are a technical analysis expert specializing in cryptocurrency markets, particularly Bitcoin.

Your role is to analyze technical indicators and price action to generate trading signals.

Key indicators you should analyze:
1. **EMA (Exponential Moving Averages)**: Trend direction and crossovers (9, 20, 50, 200)
2. **RSI (Relative Strength Index)**: Overbought (>70) and oversold (<30) conditions
3. **MACD**: Momentum and trend strength via histogram and signal line crossovers
4. **Bollinger Bands**: Volatility, price extremes, and potential reversals
5. **Support/Resistance**: Key price levels based on recent price action

Analysis guidelines:
- **BULLISH signals**: Price above key EMAs, RSI recovering from oversold, positive MACD, price near lower Bollinger Band
- **BEARISH signals**: Price below key EMAs, RSI in overbought, negative MACD, price near upper Bollinger Band
- **NEUTRAL signals**: Mixed indicators, consolidation, lack of clear trend

⚠️ CRITICAL OUTPUT REQUIREMENTS:

1. ❌ ABSOLUTELY NO MARKDOWN in JSON string values (no **, ##, -, *, etc.)
2. ❌ NO markdown code blocks (no ```json or ```)
3. ❌ NO extra text before or after the JSON
4. ❌ NO thinking, explanations, or commentary outside JSON
5. ✅ Use plain text in "reasoning" and other string fields
6. ✅ Use \\n for line breaks in strings (NOT real newlines)
7. ✅ Start response with { and end with }
8. ✅ Use double quotes for all strings
9. ✅ Escape special characters properly

IMPORTANT: You must respond with ONLY valid JSON. Do not include any thinking or text before or after the JSON.
The JSON must match this exact structure with these exact field names:

{
    "signal": "BULLISH",
    "confidence": 0.75,
    "score": 72.5,
    "reasoning": "Detailed explanation of your technical analysis...",
    "technical_indicators": {
        "ema": {
            "ema_9": {"value": 95234.5, "vs_price": "above", "weight": 0.15},
            "ema_20": {"value": 94123.2, "vs_price": "above", "weight": 0.2},
            "ema_50": {"value": 92000.0, "vs_price": "above", "weight": 0.2},
            "ema_200": {"value": 85000.0, "vs_price": "above", "weight": 0.15},
            "trend": "bullish"
        },
        "rsi": {
            "value": 58.3,
            "status": "neutral",
            "impact": "NEUTRAL",
            "weight": 0.15
        },
        "macd": {
            "macd": 1234.5,
            "signal": 1100.2,
            "histogram": 134.3,
            "status": "bullish_crossover",
            "impact": "BULLISH",
            "weight": 0.15
        },
        "bollinger_bands": {
            "upper": 98000.0,
            "middle": 95000.0,
            "lower": 92000.0,
            "price_position": "middle",
            "bandwidth": "normal",
            "impact": "NEUTRAL",
            "weight": 0.1
        }
    },
    "support_levels": [92000.0, 90000.0, 88000.0],
    "resistance_levels": [96000.0, 98000.0, 100000.0],
    "trend_analysis": "Price is in a clear uptrend with higher highs and higher lows. All major EMAs are aligned bullishly.",
    "key_patterns": [
        "Bullish EMA alignment (9 > 20 > 50 > 200)",
        "MACD histogram turning positive",
        "Price holding above 20 EMA support"
    ]
}

CRITICAL REQUIREMENTS:
- "signal" MUST be one of: "BULLISH", "BEARISH", or "NEUTRAL" (no other values)
- "confidence" MUST be a decimal between 0.0 and 1.0 (NOT a percentage like 72, use 0.72 instead)
- "score" MUST be a number between -100.0 and 100.0 representing investment conviction:
  * -100 to -60: Strong bearish (recommend selling/shorting)
  * -60 to -20: Moderate bearish (reduce exposure)
  * -20 to +20: Neutral (hold current position)
  * +20 to +60: Moderate bullish (accumulate gradually)
  * +60 to +100: Strong bullish (aggressive buying)
- "technical_indicators" is the exact field name
- All field names must match exactly as shown above
- "support_levels" and "resistance_levels" must be arrays of numbers (floats)
- "key_patterns" must be an array of strings

🎯 UNDERSTAND THE DIFFERENCE:
- **confidence** (0-1): Your subjective certainty about this analysis. How reliable is your reading of the data?
- **score** (-100 to +100): Objective investment recommendation. How much should investors buy or sell?

Example:
- "I'm 80% confident (confidence=0.8) that the market is moderately bullish (score=+45)"
- "I'm only 50% confident (confidence=0.5) due to mixed signals, but the bullish signals are stronger (score=+30)"

Be objective, data-driven, and consider:
- Confluence of multiple indicators (more aligned = higher score magnitude)
- Strength of each signal
- Current price action and momentum
- Risk/reward at current levels

Your score calculation should reflect:
- Alignment of indicators (all pointing same direction = higher |score|)
- Strength of trend (strong trend = higher |score|, weak trend = closer to 0)
- Confirmation from multiple indicators
- Current risk/reward ratio

Your confidence should reflect:
- Data quality and completeness
- Clarity of signals (mixed signals = lower confidence)
- Market volatility and uncertainty

⚠️ FINAL REMINDER: Respond with ONLY the JSON object. NO MARKDOWN formatting in string values. Start with { and end with }.
"""

    def __init__(self):
        """Initialize TAAgent"""
        self.agent_name = "ta_agent"

    async def analyze(self, market_data: Dict[str, Any]) -> TechnicalAnalysisOutput:
        """
        Analyze technical indicators and generate trading signal

        Args:
            market_data: Dictionary containing:
                - btc_price: Current BTC price
                - price_change_24h: 24h price change percentage
                - ohlcv_data: List of OHLCVData for technical analysis
                - indicators: Pre-calculated indicators (optional)

        Returns:
            TechnicalAnalysisOutput with signal, confidence, and reasoning
        """
        # Calculate technical indicators if not provided
        indicators = market_data.get("indicators")
        if not indicators:
            ohlcv_data = market_data.get("ohlcv_data", [])
            if not ohlcv_data:
                raise ValueError("Either 'indicators' or 'ohlcv_data' must be provided")

            # Calculate all indicators
            indicators = IndicatorCalculator.calculate_all(ohlcv_data)

        # Build analysis prompt
        analysis_prompt = self._build_analysis_prompt(market_data, indicators)

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
        return TechnicalAnalysisOutput(
            agent_name=self.agent_name,
            signal=SignalType(analysis["signal"]),
            confidence=float(analysis["confidence"]),
            score=float(analysis["score"]),
            confidence_level=AgentOutput.get_confidence_level(
                float(analysis["confidence"])
            ),
            reasoning=analysis["reasoning"],
            technical_indicators=analysis["technical_indicators"],
            support_levels=analysis["support_levels"],
            resistance_levels=analysis["resistance_levels"],
            trend_analysis=analysis["trend_analysis"],
            key_patterns=analysis.get("key_patterns", []),
            # Add full conversation for UI display
            prompt_sent=full_prompt,
            llm_response=response.content,
        )

    def _build_analysis_prompt(
        self, market_data: Dict[str, Any], indicators: Dict[str, Any]
    ) -> str:
        """Build the analysis prompt with market data and indicators"""
        ind = indicators.get("indicators", {})

        # Extract current price
        btc_price = market_data.get("btc_price", 0)
        price_change_24h = market_data.get("price_change_24h", 0)

        # Extract indicator values with None handling
        ema = ind.get("ema", {})
        rsi = ind.get("rsi", {})
        macd = ind.get("macd", {})
        bb = ind.get("bollinger_bands", {})

        # Helper function to format values safely
        def safe_format(value, format_str=".2f", default="N/A"):
            if value is None:
                return default
            try:
                if format_str == ",.2f":
                    return f"{float(value):,.2f}"
                else:
                    return f"{float(value):.2f}"
            except (ValueError, TypeError):
                return default

        prompt = f"""Analyze the current technical setup and generate a trading signal for Bitcoin:

**Current Market Data:**
- BTC Price: ${btc_price:,.2f}
- 24h Change: {price_change_24h:+.2f}%

**Technical Indicators:**

**EMAs (Exponential Moving Averages):**
- EMA 9: ${safe_format(ema.get('period_9'), ',.2f')}
- EMA 20: ${safe_format(ema.get('period_20'), ',.2f')}
- EMA 50: ${safe_format(ema.get('period_50'), ',.2f')}
- EMA 200: ${safe_format(ema.get('period_200'), ',.2f')}

**RSI (Relative Strength Index):**
- Current RSI: {safe_format(rsi.get('value'))}
- Period: {rsi.get('period', 14)}

**MACD:**
- MACD Line: {safe_format(macd.get('macd'))}
- Signal Line: {safe_format(macd.get('signal'))}
- Histogram: {safe_format(macd.get('histogram'))}

**Bollinger Bands:**
- Upper Band: ${safe_format(bb.get('upper'), ',.2f')}
- Middle Band: ${safe_format(bb.get('middle'), ',.2f')}
- Lower Band: ${safe_format(bb.get('lower'), ',.2f')}

Provide a comprehensive technical analysis and generate a trading signal.

Remember to:
1. Assess the trend by comparing price to EMAs and looking for crossovers
2. Check for overbought/oversold conditions with RSI
3. Evaluate momentum with MACD histogram and crossovers
4. Identify if price is at extremes using Bollinger Bands
5. Identify key support and resistance levels based on recent price action
6. Look for confluence between multiple indicators
7. Assess risk/reward at current price levels

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
                "technical_indicators",
                "support_levels",
                "resistance_levels",
                "trend_analysis",
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

            # Validate support/resistance are lists
            if not isinstance(analysis["support_levels"], list):
                raise ValueError("support_levels must be a list")
            if not isinstance(analysis["resistance_levels"], list):
                raise ValueError("resistance_levels must be a list")

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
                "technical_indicators": {},
                "support_levels": [],
                "resistance_levels": [],
                "trend_analysis": "Unable to analyze due to parsing error",
                "key_patterns": ["Analysis parsing error - please review logs"],
            }


# Global TAAgent instance
ta_agent = TAAgent()
