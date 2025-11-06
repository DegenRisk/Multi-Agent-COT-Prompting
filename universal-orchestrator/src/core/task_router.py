"""
Task Router
Routes tasks to appropriate agents based on intent
"""

from typing import List, Dict, Any
import uuid
import structlog

from ..models.task import TaskIntent, TaskExecution, ConversationContext, AgentCapability
from ..agents.registry import AgentRegistry

logger = structlog.get_logger(__name__)


class TaskRouter:
    """Routes tasks to appropriate specialist agents"""

    def __init__(self):
        """Initialize task router"""
        self.logger = logger.bind(component="task_router")

        # Intent to capability mapping
        self.intent_capability_map = {
            "document_processing": [AgentCapability.DOCUMENT_EXTRACTION],
            "data_analysis": [AgentCapability.DATA_QUERY, AgentCapability.DATA_VISUALIZATION],
            "code_generation": [AgentCapability.CODE_GENERATION],
            "research": [AgentCapability.WEB_SEARCH, AgentCapability.TEXT_GENERATION],
            "image_analysis": [AgentCapability.IMAGE_UNDERSTANDING],
            "writing": [AgentCapability.TEXT_GENERATION],
            "sql_query": [AgentCapability.SQL_GENERATION, AgentCapability.DATA_QUERY],
            "api_integration": [AgentCapability.API_INTERACTION],
        }

    async def plan_execution(
        self,
        intent: TaskIntent,
        context: ConversationContext,
        agent_registry: AgentRegistry
    ) -> TaskExecution:
        """
        Plan task execution based on intent

        Args:
            intent: Classified task intent
            context: Conversation context
            agent_registry: Registry of available agents

        Returns:
            TaskExecution plan
        """
        task_id = str(uuid.uuid4())

        # Get required capabilities
        required_capabilities = self.intent_capability_map.get(
            intent.category.value,
            []
        )

        # Find suitable agents
        suitable_agents = agent_registry.find_agents_by_capabilities(required_capabilities)

        if not suitable_agents:
            # Fall back to general assistant
            suitable_agents = [agent_registry.get_agent("general_assistant")]

        # Select best agent(s)
        selected_agents = self._select_agents(suitable_agents, intent)

        # Create execution steps
        execution_plan = self._create_execution_plan(selected_agents, intent, context)

        # Estimate duration
        estimated_duration = sum(
            agent.average_latency_seconds
            for agent in selected_agents
        )

        return TaskExecution(
            task_id=task_id,
            user_message=context.messages[-1].content,
            intent=intent,
            selected_agents=[agent.agent_id for agent in selected_agents],
            execution_plan=execution_plan,
            estimated_duration_seconds=estimated_duration
        )

    def _select_agents(
        self,
        suitable_agents: List[Any],
        intent: TaskIntent
    ) -> List[Any]:
        """Select best agents for the task"""
        # Simple selection: take first suitable agent
        # In production, use ML-based selection
        return suitable_agents[:1] if suitable_agents else []

    def _create_execution_plan(
        self,
        agents: List[Any],
        intent: TaskIntent,
        context: ConversationContext
    ) -> List[Dict[str, Any]]:
        """Create execution plan steps"""
        if intent.complexity == "simple":
            # Single agent execution
            return [
                {
                    "type": "sequential",
                    "tasks": [
                        {
                            "agent_id": agents[0].agent_id,
                            "input": {
                                "message": context.messages[-1].content,
                                "intent": intent.dict()
                            }
                        }
                    ]
                }
            ]
        else:
            # Multi-step execution for complex tasks
            return [
                {
                    "type": "sequential",
                    "tasks": [
                        {
                            "agent_id": agent.agent_id,
                            "input": {
                                "message": context.messages[-1].content,
                                "intent": intent.dict()
                            }
                        }
                        for agent in agents
                    ]
                }
            ]
