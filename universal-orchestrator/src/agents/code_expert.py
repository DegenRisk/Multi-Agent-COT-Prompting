"""Code Expert Agent - Handles code generation"""
from .base_agent import BaseAgent
from ..models.task import AgentMetadata, AgentCapability, ConversationContext

class CodeExpertAgent(BaseAgent):
    def get_metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id="code_expert",
            agent_name="Code Expert",
            description="Generates and analyzes code",
            capabilities=[AgentCapability.CODE_GENERATION, AgentCapability.CODE_EXECUTION],
            supported_inputs=["text"],
            supported_outputs=["text", "code"]
        )
    
    async def execute(self, input_data, context) -> dict:
        code = "def example():\n    return 'Generated code'"
        return self._format_success_response(
            "Code generated successfully.",
            data={"code": code, "language": "python"}
        )
