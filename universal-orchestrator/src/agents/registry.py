"""
Agent Registry
Central registry of all specialist agents
"""

from typing import Dict, List, Optional
import structlog

from ..models.task import AgentMetadata, AgentCapability
from .base_agent import BaseAgent
from .general_assistant import GeneralAssistant
from .document_processor import DocumentProcessorAgent
from .data_analyst import DataAnalystAgent
from .code_expert import CodeExpertAgent
from .research_assistant import ResearchAssistant

logger = structlog.get_logger(__name__)


class AgentRegistry:
    """Registry of all available specialist agents"""

    def __init__(self):
        """Initialize agent registry"""
        self.logger = logger.bind(component="agent_registry")
        self.agents: Dict[str, BaseAgent] = {}
        self.metadata: Dict[str, AgentMetadata] = {}

        # Register all agents
        self._register_agents()

        self.logger.info(f"Agent registry initialized with {len(self.agents)} agents")

    def _register_agents(self):
        """Register all available agents"""
        # General Assistant
        self.register(GeneralAssistant())

        # Document Processor
        self.register(DocumentProcessorAgent())

        # Data Analyst
        self.register(DataAnalystAgent())

        # Code Expert
        self.register(CodeExpertAgent())

        # Research Assistant
        self.register(ResearchAssistant())

    def register(self, agent: BaseAgent):
        """Register an agent"""
        metadata = agent.get_metadata()
        self.agents[metadata.agent_id] = agent
        self.metadata[metadata.agent_id] = metadata

        self.logger.info(f"Registered agent: {metadata.agent_name}")

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get agent by ID"""
        return self.agents.get(agent_id)

    def list_agents(self) -> List[AgentMetadata]:
        """List all agent metadata"""
        return list(self.metadata.values())

    def find_agents_by_capabilities(
        self,
        capabilities: List[AgentCapability]
    ) -> List[AgentMetadata]:
        """Find agents with specific capabilities"""
        matching_agents = []

        for metadata in self.metadata.values():
            if any(cap in metadata.capabilities for cap in capabilities):
                matching_agents.append(metadata)

        return matching_agents
