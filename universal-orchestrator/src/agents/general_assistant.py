"""
General Assistant Agent
Handles general conversation and simple tasks
"""

from typing import Dict, Any

from .base_agent import BaseAgent
from ..models.task import AgentMetadata, AgentCapability, ConversationContext


class GeneralAssistant(BaseAgent):
    """General-purpose conversational agent"""

    def get_metadata(self) -> AgentMetadata:
        """Get agent metadata"""
        return AgentMetadata(
            agent_id="general_assistant",
            agent_name="General Assistant",
            description="General-purpose assistant for conversations and simple tasks",
            capabilities=[
                AgentCapability.TEXT_GENERATION
            ],
            supported_inputs=["text"],
            supported_outputs=["text"],
            cost_tier="low",
            average_latency_seconds=2.0,
            success_rate=0.98
        )

    async def execute(
        self,
        input_data: Dict[str, Any],
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Execute general assistant task"""
        message = input_data.get("message", "")

        # Simple response generation (would use LLM in production)
        response = f"I understand you said: '{message}'. I'm the general assistant and can help with various tasks. What would you like to do?"

        return self._format_success_response(
            message=response,
            confidence=0.85
        )
