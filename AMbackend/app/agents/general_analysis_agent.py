"""GeneralAnalysisAgent - Research Result Synthesis and Final Answer Generation"""

import json
from typing import List, Dict, Any

from app.services.llm.manager import llm_manager
from app.schemas.llm import Message
from app.utils.json_parser import parse_llm_json, JSONParseError
from app.schemas.research import GeneralAnalysisOutput
from app.schemas.agents import AgentOutput


class GeneralAnalysisAgent:
    """
    GeneralAnalysisAgent synthesizes results from multiple business agents

    Uses Claude Sonnet 4.5 Thinking for deep synthesis:
    - Understands user's original question and context
    - Integrates findings from MacroAgent, TAAgent, OnChainAgent
    - Identifies consensus and conflicts between agents
    - Generates comprehensive, actionable answer for user
    """

    SYSTEM_PROMPT = """You are a synthesis agent for cryptocurrency market research.

Your role is to:
1. Understand the user's original research question
2. Analyze outputs from specialized business agents (MacroAgent, TAAgent, OnChainAgent)
3. Synthesize findings into a coherent, comprehensive answer
4. Provide actionable insights and recommendations

## Agent Output Interpretation:

### MacroAgent Output:
- **signal**: BULLISH/BEARISH/NEUTRAL - Macroeconomic outlook for Bitcoin
- **confidence**: 0.0-1.0 - Confidence in the signal
- **macro_indicators**: Detailed analysis of Fed rates, M2, DXY, Fear & Greed, Treasury yields
- **key_factors**: Main macro drivers affecting Bitcoin
- **risk_assessment**: Overall macro risk environment

### TAAgent Output:
- **signal**: BULLISH/BEARISH/NEUTRAL - Technical analysis signal
- **confidence**: 0.0-1.0 - Confidence in the technical signal
- **technical_indicators**: RSI, MACD, EMA, Bollinger Bands analysis
- **support_levels**: Key price support levels
- **resistance_levels**: Key price resistance levels
- **trend_analysis**: Current trend and momentum assessment

### OnChainAgent Output:
- **signal**: BULLISH/BEARISH/NEUTRAL - On-chain metrics signal
- **confidence**: 0.0-1.0 - Confidence in the on-chain signal
- **onchain_metrics**: Exchange flows, whale activity, network health
- **whale_activity**: Analysis of large holder behavior
- **network_health**: Blockchain network vitality metrics

## Synthesis Guidelines:

### 1. Signal Consensus:
- **Strong Consensus**: All agents agree (all BULLISH or all BEARISH)
  → High confidence answer, clear recommendation
- **Partial Consensus**: 2 out of 3 agree
  → Moderate confidence, nuanced recommendation
- **No Consensus**: Agents disagree (mixed signals)
  → Lower confidence, highlight uncertainty, suggest caution

### 2. Weighting by Confidence:
- Give more weight to agents with higher confidence scores
- An agent with 0.8 confidence carries more weight than one with 0.4
- Consider **why** an agent has low confidence (uncertainty vs lack of data)

### 3. Weighting by Relevance:
- For **investment decisions**: Macro > TA > OnChain
- For **entry/exit timing**: TA > Macro > OnChain
- For **long-term outlook**: Macro > OnChain > TA
- For **whale/smart money**: OnChain > TA > Macro

### 4. Answer Structure:
Your answer should be comprehensive but well-organized:

**Opening**: Direct answer to user's question (1-2 sentences)

**Key Insights** (3-5 bullet points):
- Most important findings from all agents
- Highlight consensus or key conflicts
- Include specific data points (e.g., "RSI at 28 indicates oversold")

**Detailed Analysis**:
- Macro perspective: What macro forces are at play?
- Technical perspective: What does price action tell us?
- On-chain perspective: What are whales/holders doing?
- Integration: How do these perspectives connect?

**Conclusion & Recommendation**:
- Clear, actionable recommendation
- Risk assessment and caveats
- What to watch for next

### 5. Tone & Style:
- Professional but accessible
- Data-driven, cite specific metrics
- Balanced (acknowledge both bullish and bearish factors)
- Honest about uncertainty
- **Chinese or English** based on user's question language

## Output Format:

⚠️ CRITICAL: Your response MUST be ONLY a valid JSON object. No text before or after. No markdown. No explanations.

**JSON Formatting Rules:**
1. ❌ NO markdown code blocks (no ```json or ```)
2. ❌ NO extra text before or after the JSON
3. ❌ NO real line breaks in strings (use \\n instead)
4. ✅ Use double quotes for all strings
5. ✅ Escape special characters: \\\\ for backslash, \\" for quote, \\n for newline
6. ✅ Multi-line text must use \\n, NOT real line breaks
7. ✅ Numbers must not have leading zeros (0.5, not .5)
8. ✅ Ensure all brackets and braces match correctly
9. ✅ Start response with { and end with }

**Correct Example:**
{
    "answer": "First paragraph.\\n\\nSecond paragraph with \\"quotes\\" properly escaped.",
    "summary": "Brief summary here.",
    "key_insights": [
        "Macro: Fed rate policy creates headwinds",
        "Technical: BTC oversold on RSI (28)"
    ],
    "confidence": 0.72,
    "sources": ["macro_agent"],
    "metadata": {
        "signal_consensus": "MIXED"
    }
}

**Wrong Example (DO NOT DO THIS):**
```json
{
    "answer": "First paragraph.

    Second paragraph"  // ❌ Real line breaks will break JSON
}
```

**Required Fields:**
- "answer": String - Comprehensive answer (3-10 paragraphs), use \\n for paragraphs
- "summary": String - Brief 2-3 sentence summary
- "key_insights": Array of strings - 3-5 bullet points with specific findings
- "confidence": Number - Between 0.0 and 1.0
- "sources": Array of strings - List of agents that contributed
- "metadata": Object (optional) - Additional tracking information

## Example:

User asks: "Is now a good time to buy BTC?"

MacroAgent: BEARISH (0.72) - High rates, strong dollar, extreme fear
TAAgent: NEUTRAL (0.55) - Oversold RSI but downtrend intact
OnChainAgent: BULLISH (0.64) - Whales accumulating

Your synthesis (NO MARKDOWN in JSON strings):
{
    "answer": "Based on current multi-dimensional analysis, I recommend cautious observation and waiting for clearer buy signals.\n\nMacro Environment: The Fed maintains high interest rates (3.87%) and the strong dollar (DXY 121.77) create significant pressure on BTC. Market sentiment is extremely fearful (Fear & Greed Index at 23), typically indicating continued near-term pressure. Overall macro environment is bearish.\n\nTechnical Analysis: BTC's RSI indicator has dropped to 28, showing clear oversold conditions, but the downtrend line remains intact. Key support level is at $65,000, with current price approaching that level. Technicals are neutral - oversold but trend not broken.\n\nOn-Chain Analysis: Interestingly, on-chain data shows whale addresses have been continuously accumulating during the recent decline. This is a potential bullish signal. Historically, whale accumulation during panic often signals mid-term bottoms.\n\nOverall Recommendation: There is currently signal divergence - macro bearishness vs on-chain accumulation. Suggest waiting for one of these signals before entry: 1) Technical breakout above downtrend line; 2) Fear & Greed Index recovery to 30+; 3) Signs of macro environment shift. If $65,000 support fails, wait for lower entry point.",
    "summary": "Current macro environment is bearish but BTC is oversold with whales accumulating. Significant signal divergence suggests cautious observation until clearer buy signals emerge from technicals or macro environment.",
    "key_insights": [
        "Macro environment: High rates (3.87%) and strong dollar (DXY 121.77) creating pressure, extreme fear (F&G 23)",
        "Technicals: RSI oversold (28) but downtrend unbroken, key support at $65,000",
        "On-chain signal: Whales accumulating, historically a mid-term bottom indicator",
        "Recommendation: Cautious observation, wait for trend reversal or support confirmation before entry"
    ],
    "confidence": 0.68,
    "sources": ["macro_agent", "ta_agent", "onchain_agent"],
    "metadata": {
        "signal_consensus": "MIXED",
        "consensus_strength": "LOW",
        "primary_driver": "MACRO",
        "risk_level": "HIGH"
    }
}

Be thorough, insightful, and actionable. Your synthesis is the final output users see.

⚠️ REMINDER: Respond with ONLY the JSON object. Start with {{ and end with }}. No other text.
"""

    def __init__(self):
        """Initialize GeneralAnalysisAgent"""
        self.agent_name = "general_analysis_agent"

    async def synthesize(
        self,
        user_message: str,
        agent_outputs: Dict[str, AgentOutput],
        chat_history: List[Dict[str, Any]] = None,
    ) -> GeneralAnalysisOutput:
        """
        Synthesize results from multiple business agents into final answer

        Args:
            user_message: User's original question
            agent_outputs: Dictionary of agent outputs {agent_name: AgentOutput}
            chat_history: Recent chat history

        Returns:
            GeneralAnalysisOutput with synthesized answer
        """
        # Build synthesis prompt
        prompt = self._build_synthesis_prompt(
            user_message, agent_outputs, chat_history or []
        )

        # Prepend system prompt for Claude Thinking
        full_prompt = f"{self.SYSTEM_PROMPT}\n\n{prompt}"

        # Call LLM (Claude Sonnet 4.5 Thinking)
        messages = [Message(role="user", content=full_prompt)]

        response = await llm_manager.chat_for_agent(
            agent_name=self.agent_name, messages=messages
        )

        # Parse response
        output = self._parse_llm_response(response.content)

        return GeneralAnalysisOutput(
            answer=output["answer"],
            summary=output["summary"],
            key_insights=output["key_insights"],
            confidence=float(output["confidence"]),
            sources=output["sources"],
            metadata=output.get("metadata"),
        )

    def _build_synthesis_prompt(
        self,
        user_message: str,
        agent_outputs: Dict[str, AgentOutput],
        chat_history: List[Dict[str, Any]],
    ) -> str:
        """Build the synthesis prompt with all agent outputs"""
        prompt = f"""**User's Original Question:**
"{user_message}"
"""

        if chat_history:
            prompt += "\n**Chat Context:**\n"
            for msg in chat_history[-3:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                prompt += f"- {role}: {content[:80]}...\n"

        prompt += "\n**Business Agent Analyses:**\n\n"

        # Add each agent's output
        for agent_name, output in agent_outputs.items():
            prompt += f"### {agent_name.upper()}\n"
            prompt += f"- Signal: {output.signal.value}\n"
            prompt += f"- Confidence: {output.confidence:.2f} ({output.confidence_level.value})\n"
            prompt += f"- Reasoning: {output.reasoning}\n"

            # Add agent-specific fields
            if hasattr(output, "macro_indicators"):
                prompt += f"- Macro Indicators: {json.dumps(output.macro_indicators, indent=2)}\n"
                prompt += f"- Key Factors: {output.key_factors}\n"
                prompt += f"- Risk Assessment: {output.risk_assessment}\n"
            elif hasattr(output, "technical_indicators"):
                prompt += f"- Technical Indicators: {json.dumps(output.technical_indicators, indent=2)}\n"
                prompt += f"- Support Levels: {output.support_levels}\n"
                prompt += f"- Resistance Levels: {output.resistance_levels}\n"
                prompt += f"- Trend Analysis: {output.trend_analysis}\n"
            elif hasattr(output, "onchain_metrics"):
                prompt += f"- OnChain Metrics: {json.dumps(output.onchain_metrics, indent=2)}\n"
                prompt += f"- Network Health: {output.network_health}\n"
                if output.key_observations:
                    prompt += f"- Key Observations: {', '.join(output.key_observations)}\n"

            prompt += "\n"

        prompt += """
Now synthesize these analyses into a comprehensive answer for the user.

Consider:
1. Do the agents agree or disagree?
2. Which agents have higher confidence and why?
3. What are the most important insights across all analyses?
4. What should the user do based on this research?

Return ONLY the JSON output, no other text.
"""

        return prompt

    def _parse_llm_response(self, content: str) -> Dict[str, Any]:
        """
        Parse LLM response and extract synthesis output

        Args:
            content: Raw LLM response content

        Returns:
            Parsed synthesis dictionary
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
                json_str = content.strip()

            # Parse JSON
            output = parse_llm_json(content)

            # Validate required fields
            required_fields = ["answer", "summary", "key_insights", "confidence", "sources"]
            for field in required_fields:
                if field not in output:
                    raise ValueError(f"Missing required field: {field}")

            # Validate confidence range
            confidence = float(output["confidence"])
            if not 0.0 <= confidence <= 1.0:
                raise ValueError(f"Confidence must be between 0 and 1: {confidence}")

            return output

        except (JSONParseError, ValueError) as e:
            # Fallback: return error message
            print(f"Error parsing GeneralAnalysisAgent response: {e}")
            print(f"Raw content: {content[:500]}...")

            return {
                "answer": f"Sorry, an error occurred during analysis synthesis. Raw analysis data has been collected but structured response could not be generated. Error: {str(e)}",
                "summary": "Analysis synthesis failed, please check raw agent outputs",
                "key_insights": [
                    "Analysis data collected but synthesis failed",
                    "Recommend reviewing individual agent raw outputs",
                    "May need to rephrase question for complete analysis",
                ],
                "confidence": 0.3,
                "sources": [],
                "metadata": {"error": str(e)},
            }


# Global GeneralAnalysisAgent instance
general_analysis_agent = GeneralAnalysisAgent()
