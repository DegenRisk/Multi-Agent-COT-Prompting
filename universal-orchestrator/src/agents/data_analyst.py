"""Data Analyst Agent - Handles data analysis"""
from .base_agent import BaseAgent
from ..models.task import AgentMetadata, AgentCapability, ConversationContext

class DataAnalystAgent(BaseAgent):
    def get_metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id="data_analyst",
            agent_name="Data Analyst",
            description="Analyzes data and creates visualizations",
            capabilities=[AgentCapability.DATA_QUERY, AgentCapability.DATA_VISUALIZATION],
            supported_inputs=["text", "data"],
            supported_outputs=["text", "data", "visualization"]
        )
    
    async def execute(self, input_data, context) -> dict:
        return self._format_success_response(
            "Data analyzed. In production, this would query databases and create charts.",
            data={"analysis": "Sample analysis results"}
        )
