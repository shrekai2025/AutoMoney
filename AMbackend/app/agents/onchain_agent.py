"""OnChain Agent - Analyzes on-chain metrics and network health"""

from typing import Dict, Any
from app.schemas.agents import OnChainAnalysisOutput
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

    def __init__(self):
        self.name = "onchain_agent"
        self.description = "链上数据分析专家，分析网络活跃度、交易费用和链上健康度"

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
        prompt = self._build_analysis_prompt(user_query, market_data)

        # Get LLM response
        messages = [Message(role="user", content=prompt)]
        llm_response = await llm_manager.chat_for_agent(
            agent_name="onchain_agent",
            messages=messages,
        )

        # Parse LLM response
        response_text = llm_response.content
        
        try:
            # Parse JSON output from LLM
            result_dict = parse_llm_json(response_text)

            # Auto-calculate confidence_level if LLM didn't provide it
            if 'confidence_level' not in result_dict:
                confidence = result_dict.get('confidence', 0.5)
                result_dict['confidence_level'] = OnChainAnalysisOutput.get_confidence_level(confidence)

            # Create OnChainAnalysisOutput
            response = OnChainAnalysisOutput(**result_dict)

            # Store full conversation for UI
            response.prompt_sent = prompt
            response.llm_response = response_text

            return response
            
        except (JSONParseError, Exception) as e:
            print(f"Error parsing OnChainAgent response: {e}")
            print(f"Raw response: {response_text}")
            raise

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

**Output Format:**
Please provide your analysis in the following JSON structure:
{{
  "signal": "BULLISH" | "NEUTRAL" | "BEARISH",
  "confidence": 0.0 to 1.0,
  "reasoning": "Brief explanation of your analysis and signal",
  "onchain_metrics": {{
    "active_addresses": {active_addresses if active_addresses else 0},
    "daily_transactions": {tx_count.get('avg_30d', 0)},
    "transaction_fees_sat_vb": {fees.get('fastestFee', 0)},
    "mempool_tx_count": {mempool_stats.get('count', 0)},
    "nvt_ratio": {nvt_ratio if nvt_ratio else "null"},
    "hash_rate_eh": {network_stats.get('hash_rate', 0) / 1e9:.2f}
  }},
  "network_health": "Assessment of network health: HEALTHY, MODERATE, or CONGESTED",
  "key_observations": ["List 2-4 key observations from the on-chain data"]
}}

Focus on actionable insights that help understand network adoption, usage patterns, and valuation relative to network activity."""

        return prompt

    @property
    def is_available(self) -> bool:
        """OnChain agent is now available with free APIs"""
        return True
