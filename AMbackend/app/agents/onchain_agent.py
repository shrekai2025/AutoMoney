"""OnChain Agent - Analyzes on-chain metrics and network health"""

from typing import Dict, Any
from app.schemas.agents import OnChainAnalysisOutput, SignalType, AgentOutput
from app.services.llm.manager import llm_manager
from app.schemas.llm import Message
from app.utils.json_parser import parse_llm_json, JSONParseError


class OnChainAgent:
    """
    OnChain Agent analyzes blockchain metrics and network health

    Specializes in:
    - Network activity (active addresses, transaction volume)
    - Network health (fees, mempool congestion)
    - Simplified valuation metrics (NVT approximation)
    - Chain activity trends
    """

    SYSTEM_PROMPT = """You are an on-chain analysis expert specializing in cryptocurrency markets, particularly Bitcoin.

Your role is to analyze blockchain metrics and network health to generate trading signals.

Key metrics you should analyze:
1. **Network Activity**: Active addresses, transaction volume, hash rate
2. **Network Health**: Transaction fees, mempool congestion, block times
3. **Valuation Metrics**: NVT ratio (Network Value to Transactions)
4. **Mining & Security**: Hash rate, difficulty adjustments

Analysis guidelines:
- **BULLISH signals**: Rising active addresses, healthy transaction volume, reasonable fees, strong hash rate
- **BEARISH signals**: Declining network activity, congestion, extreme NVT values
- **NEUTRAL signals**: Mixed indicators, stable metrics

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
  "score": 60.0,
  "reasoning": "Brief explanation of your analysis and signal",
  "onchain_metrics": {
    "active_addresses": 950000,
    "daily_transactions": 300000,
    "transaction_fees_sat_vb": 50,
    "mempool_tx_count": 25000,
    "nvt_ratio": 85.5,
    "hash_rate_eh": 450.5
  },
  "network_health": "HEALTHY",
  "key_observations": [
    "Rising active addresses indicating growing adoption",
    "Transaction fees are reasonable",
    "Strong hash rate securing the network"
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
- "network_health" MUST be one of: "HEALTHY", "MODERATE", or "CONGESTED"
- "key_observations" must be an array of strings (2-4 observations)
- All field names must match exactly as shown above

🎯 UNDERSTAND THE DIFFERENCE:
- **confidence** (0-1): Your subjective certainty about this analysis. How reliable is your reading of the data?
- **score** (-100 to +100): Objective investment recommendation. How much should investors buy or sell?

Example:
- "I'm 80% confident (confidence=0.8) that the on-chain fundamentals are strong bullish (score=+65)"
- "I'm only 60% confident (confidence=0.6) due to some mixed signals, but the bullish indicators dominate (score=+40)"

Be objective, data-driven, and consider:
- Network adoption trends (rising/falling activity)
- Network congestion and usability
- Valuation relative to network activity (NVT)
- Security and mining health

Your score calculation should reflect:
- Strength of network activity trends
- Health of the network (congestion, fees)
- Valuation metrics (NVT ratio)
- Overall on-chain fundamentals

Your confidence should reflect:
- Data quality and completeness
- Clarity of trends (mixed signals = lower confidence)
- Unusual market conditions

⚠️ FINAL REMINDER: Respond with ONLY the JSON object. NO MARKDOWN formatting in string values. Start with { and end with }.
"""

    def __init__(self):
        self.name = "onchain_agent"
        self.agent_name = "onchain_agent"
        self.description = "On-chain data analysis expert, analyzing network activity, transaction fees, and chain health"

    async def analyze(self, user_query: str, market_data: Dict[str, Any]) -> OnChainAnalysisOutput:
        """
        Analyze on-chain metrics and generate insights

        Args:
            user_query: User's question
            market_data: Dictionary containing on-chain data from collectors

        Returns:
            OnChainAnalysisOutput with analysis results
        """
        # Build analysis prompt
        analysis_prompt = self._build_analysis_prompt(user_query, market_data)

        # Prepend system prompt to user message
        full_prompt = f"{self.SYSTEM_PROMPT}\n\n{analysis_prompt}"

        # Get LLM response
        messages = [Message(role="user", content=full_prompt)]
        llm_response = await llm_manager.chat_for_agent(
            agent_name=self.agent_name,
            messages=messages,
        )

        # Parse LLM response
        analysis = self._parse_llm_response(llm_response.content)

        # Build output with full conversation
        return OnChainAnalysisOutput(
            agent_name=self.agent_name,
            signal=SignalType(analysis["signal"]),
            confidence=float(analysis["confidence"]),
            score=float(analysis["score"]),
            confidence_level=AgentOutput.get_confidence_level(
                float(analysis["confidence"])
            ),
            reasoning=analysis["reasoning"],
            onchain_metrics=analysis["onchain_metrics"],
            network_health=analysis["network_health"],
            key_observations=analysis["key_observations"],
            # Add full conversation for UI display
            prompt_sent=full_prompt,
            llm_response=llm_response.content,
        )

    def _build_analysis_prompt(self, user_query: str, market_data: Dict[str, Any]) -> str:
        """Build the analysis prompt for LLM"""

        # Extract blockchain.info data
        blockchain_data = market_data.get("blockchain_info", {})
        network_stats = blockchain_data.get("network_stats", {})
        active_addresses = blockchain_data.get("active_addresses_24h")
        tx_count = blockchain_data.get("transaction_count_30d", {})
        market_cap = blockchain_data.get("market_cap")

        # Extract mempool.space data
        mempool_data = market_data.get("mempool_space", {})
        fees = mempool_data.get("recommended_fees", {})
        mempool_stats = mempool_data.get("mempool_stats", {})
        difficulty_adj = mempool_data.get("difficulty_adjustment", {})

        # Calculate simplified NVT ratio
        nvt_ratio = None
        if market_cap and tx_count.get("avg_30d"):
            # Simplified NVT = Market Cap / (Daily TX Count * Avg TX Value estimate)
            # Using a rough estimate of avg tx value from network stats
            daily_tx_volume_btc = network_stats.get("estimated_btc_sent", 0) / 100000000  # Convert satoshi to BTC
            if daily_tx_volume_btc > 0:
                daily_tx_volume_usd = daily_tx_volume_btc * network_stats.get("market_price_usd", 0)
                if daily_tx_volume_usd > 0:
                    nvt_ratio = market_cap / daily_tx_volume_usd

        prompt = f"""Analyze the current on-chain data and generate a signal for Bitcoin:

**User Question:** {user_query}

**Network Activity Metrics:**
- Active Addresses (24h): {f"{active_addresses:,}" if active_addresses else "N/A"}
- Daily Transactions (30d avg): {tx_count.get('avg_30d', 0):,}
- Latest Daily TX: {tx_count.get('latest_daily', 0):,}
- Hash Rate: {network_stats.get('hash_rate', 0) / 1e9:.2f} EH/s
- Difficulty: {network_stats.get('difficulty', 0):,.0f}

**Network Health:**
- Transaction Fees:
  - Fastest: {fees.get('fastestFee', 0)} sat/vB
  - Half Hour: {fees.get('halfHourFee', 0)} sat/vB
  - Economy: {fees.get('economyFee', 0)} sat/vB
- Mempool Status:
  - Pending TX: {mempool_stats.get('count', 0):,}
  - Mempool Size: {mempool_stats.get('vsize', 0) / 1e6:.2f} MB
- Block Time: {network_stats.get('minutes_between_blocks', 10):.2f} minutes

**Valuation Metrics:**
- Market Cap: {"$" + f"{market_cap:,.0f}" if market_cap else "N/A"}
- Simplified NVT Ratio: {f"{nvt_ratio:.2f}" if nvt_ratio else "N/A"} (Higher = potentially overvalued, typical range: 40-150)

**Mining & Network Security:**
- Blocks Mined (24h): {network_stats.get('n_blocks_mined', 0)}
- Difficulty Adjustment Progress: {difficulty_adj.get('progressPercent', 0):.1f}%
- Estimated Difficulty Change: {difficulty_adj.get('difficultyChange', 0):+.2f}%

**Analysis Requirements:**
1. Assess overall network health based on activity metrics
2. Evaluate whether the network is congested or underutilized based on fees and mempool
3. Provide valuation perspective using NVT ratio (if available)
4. Identify any concerning trends or positive signals
5. Generate a signal: BULLISH (strong on-chain fundamentals), NEUTRAL (mixed signals), or BEARISH (weak fundamentals)

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
                "onchain_metrics",
                "network_health",
                "key_observations",
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

            # Validate network_health
            if analysis["network_health"] not in ["HEALTHY", "MODERATE", "CONGESTED"]:
                raise ValueError(f"Invalid network_health: {analysis['network_health']}")

            # Validate key_observations is a list
            if not isinstance(analysis["key_observations"], list):
                raise ValueError("key_observations must be a list")

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
                "onchain_metrics": {},
                "network_health": "MODERATE",
                "key_observations": ["Analysis parsing error - please review logs"],
            }

    @property
    def is_available(self) -> bool:
        """OnChain agent is now available with free APIs"""
        return True
