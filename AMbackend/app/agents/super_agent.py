"""SuperAgent - Research Chat Routing Agent"""

from typing import List, Dict, Any

from app.services.llm.manager import llm_manager
from app.schemas.llm import Message
from app.schemas.research import SuperAgentOutput, DecisionType
from app.utils.json_parser import parse_llm_json, JSONParseError


class SuperAgent:
    """
    SuperAgent routes user questions in Research Chat

    Uses GPT-5 for fast, cost-effective routing decisions:
    - Simple questions (knowledge, info queries) → Direct answer
    - Complex financial questions (analysis, predictions) → Route to PlanningAgent
    """

    SYSTEM_PROMPT = """You are a routing agent for a cryptocurrency research platform.

Your job is to classify user questions and decide whether to:
1. **DIRECT_ANSWER**: Answer simple questions directly
2. **ROUTE_TO_PLANNING**: Route complex financial questions to specialized analysis agents

## Classification Guidelines:

### DIRECT_ANSWER - Simple questions you can answer directly:
- **Knowledge questions**: "What is Bitcoin?", "What is MACD?", "Explain blockchain"
- **Concept explanations**: "What is on-chain data?", "How does RSI work?"
- **Definitions**: "What is Fear & Greed Index?", "Define dollar cost averaging"
- **Simple info queries**: "What is BTC's current price?" (if price is in context)

### ROUTE_TO_PLANNING - Complex questions requiring analysis:
- **Market analysis**: "Analyze current BTC market trend", "What's happening in the crypto market?"
- **Investment decisions**: "Is now a good time to buy BTC?", "Should I buy or sell?"
- **Predictive questions**: "How high will BTC go?", "Will Bitcoin go up?"
- **Multi-dimensional research**: "Why has BTC been declining recently?", "Analyze macro impact on BTC"
- **Strategy questions**: "What's the best entry point?", "How to trade this market?"

## Important Rules:
1. Be decisive - don't overthink
2. For borderline cases, prefer ROUTE_TO_PLANNING (better to over-analyze than under-analyze)
3. If the question involves market data analysis, predictions, or investment decisions → always ROUTE_TO_PLANNING
4. Keep direct answers concise and accurate (max 3-4 sentences)

## Output Format:

⚠️ CRITICAL OUTPUT REQUIREMENTS:

1. ❌ ABSOLUTELY NO MARKDOWN in JSON string values (no **, ##, -, *, etc.)
2. ❌ NO markdown code blocks (no ```json or ```)
3. ❌ NO extra text before or after the JSON
4. ✅ Use plain text in "reasoning" and "direct_answer" fields
5. ✅ Start response with { and end with }
6. ✅ Use double quotes for all strings

You MUST respond with ONLY valid JSON (no markdown, no code blocks):

{
    "decision": "DIRECT_ANSWER" or "ROUTE_TO_PLANNING",
    "reasoning": "Brief explanation of your decision",
    "confidence": 0.95,
    "direct_answer": "Your answer here (only if DIRECT_ANSWER, otherwise null)"
}

**CRITICAL**:
- "decision" must be exactly "DIRECT_ANSWER" or "ROUTE_TO_PLANNING"
- "confidence" must be a decimal between 0.0 and 1.0 (not percentage)
- If decision is "DIRECT_ANSWER", you MUST provide "direct_answer"
- If decision is "ROUTE_TO_PLANNING", set "direct_answer" to null

⚠️ FINAL REMINDER: Respond with ONLY the JSON object. NO MARKDOWN formatting in string values. Start with {{ and end with }}.
"""

    def __init__(self):
        """Initialize SuperAgent"""
        self.agent_name = "super_agent"

    async def route(
        self, user_message: str, chat_history: List[Dict[str, Any]] = None
    ) -> SuperAgentOutput:
        """
        Route user question to either direct answer or PlanningAgent

        Args:
            user_message: User's question
            chat_history: Recent chat history (last 5 rounds)

        Returns:
            SuperAgentOutput with routing decision
        """
        # Build routing prompt
        prompt = self._build_routing_prompt(user_message, chat_history or [])

        # Prepend system prompt for GPT-5
        full_prompt = f"{self.SYSTEM_PROMPT}\n\n{prompt}"

        # Call LLM (GPT-5)
        messages = [Message(role="user", content=full_prompt)]

        response = await llm_manager.chat_for_agent(
            agent_name=self.agent_name, messages=messages
        )

        # Parse response
        output = self._parse_llm_response(response.content)

        return SuperAgentOutput(
            decision=DecisionType(output["decision"]),
            reasoning=output["reasoning"],
            confidence=float(output["confidence"]),
            direct_answer=output.get("direct_answer"),
        )

    def _build_routing_prompt(
        self, user_message: str, chat_history: List[Dict[str, Any]]
    ) -> str:
        """Build the routing prompt"""
        prompt = f"""**User Question:**
"{user_message}"
"""

        if chat_history:
            prompt += "\n**Recent Chat History:**\n"
            for msg in chat_history[-5:]:  # Last 5 messages
                role = msg.get("role", "user")
                content = msg.get("content", "")
                prompt += f"- {role}: {content[:100]}...\n"

        prompt += """
Make your routing decision now. Return ONLY the JSON output, no other text.
"""

        return prompt

    def _parse_llm_response(self, content: str) -> Dict[str, Any]:
        """
        Parse LLM response and extract routing decision

        Args:
            content: Raw LLM response content

        Returns:
            Parsed decision dictionary
        """
        try:
            # Use robust JSON parser
            output = parse_llm_json(
                content,
                expected_fields=["decision", "reasoning", "confidence"]
            )

            # Validate decision type
            if output["decision"] not in ["DIRECT_ANSWER", "ROUTE_TO_PLANNING"]:
                raise ValueError(f"Invalid decision type: {output['decision']}")

            # Validate confidence range
            confidence = float(output["confidence"])
            if not 0.0 <= confidence <= 1.0:
                raise ValueError(f"Confidence must be between 0 and 1: {confidence}")

            # Ensure direct_answer exists for DIRECT_ANSWER decision
            if output["decision"] == "DIRECT_ANSWER" and not output.get(
                "direct_answer"
            ):
                raise ValueError(
                    "direct_answer is required when decision is DIRECT_ANSWER"
                )

            return output

        except (JSONParseError, ValueError) as e:
            # Fallback: route to planning (safer to over-analyze)
            print(f"Error parsing SuperAgent response: {e}")
            print(f"Raw content: {content[:500]}...")

            return {
                "decision": "ROUTE_TO_PLANNING",
                "reasoning": f"Unable to parse routing decision properly. Error: {str(e)}. Routing to PlanningAgent for safety.",
                "confidence": 0.5,
                "direct_answer": None,
            }


# Global SuperAgent instance
super_agent = SuperAgent()
