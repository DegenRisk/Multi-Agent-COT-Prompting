"""
Universal AI Orchestrator
Main orchestration engine that routes tasks to specialized agents
"""

from typing import Dict, List, Optional, Any
import uuid
import structlog
from datetime import datetime

from ..models.task import (
    TaskIntent,
    TaskCategory,
    TaskExecution,
    TaskResult,
    ConversationContext,
    ConversationMessage,
    AgentMetadata
)
from .intent_classifier import IntentClassifier
from .task_router import TaskRouter
from ..agents.registry import AgentRegistry

logger = structlog.get_logger(__name__)


class UniversalOrchestrator:
    """
    Universal AI Orchestrator

    Provides ChatGPT-like simplicity while intelligently routing
    to specialized agents, tools, and data sources.

    Architecture:
    1. Receive user input (text, files, images, etc.)
    2. Classify intent and determine task category
    3. Route to appropriate specialist agent(s)
    4. Coordinate multi-agent workflows if needed
    5. Return unified response to user
    6. Learn from feedback and adapt
    """

    def __init__(self):
        """Initialize orchestrator with all components"""
        self.logger = logger.bind(component="orchestrator")

        # Core components
        self.intent_classifier = IntentClassifier()
        self.task_router = TaskRouter()
        self.agent_registry = AgentRegistry()

        # Active conversations
        self.conversations: Dict[str, ConversationContext] = {}

        self.logger.info("Universal Orchestrator initialized")

    async def process_message(
        self,
        user_message: str,
        conversation_id: Optional[str] = None,
        user_id: str = "default_user",
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Process a user message through the orchestration pipeline

        Args:
            user_message: User's input text
            conversation_id: Optional conversation ID for context
            user_id: User identifier
            attachments: Optional file attachments

        Returns:
            Dict with response and metadata
        """
        # Get or create conversation context
        if conversation_id and conversation_id in self.conversations:
            context = self.conversations[conversation_id]
        else:
            conversation_id = conversation_id or str(uuid.uuid4())
            context = ConversationContext(
                conversation_id=conversation_id,
                user_id=user_id
            )
            self.conversations[conversation_id] = context

        # Add user message to context
        user_msg = ConversationMessage(
            message_id=str(uuid.uuid4()),
            role="user",
            content=user_message,
            attachments=attachments or []
        )
        context.messages.append(user_msg)

        self.logger.info(
            "Processing message",
            conversation_id=conversation_id,
            message_length=len(user_message),
            has_attachments=bool(attachments)
        )

        try:
            # Step 1: Classify intent
            intent = await self.intent_classifier.classify(
                message=user_message,
                context=context,
                attachments=attachments
            )

            self.logger.info(
                "Intent classified",
                category=intent.category,
                confidence=intent.confidence,
                complexity=intent.complexity
            )

            # Step 2: Create execution plan
            execution_plan = await self.task_router.plan_execution(
                intent=intent,
                context=context,
                agent_registry=self.agent_registry
            )

            self.logger.info(
                "Execution planned",
                task_id=execution_plan.task_id,
                agents=execution_plan.selected_agents,
                steps=len(execution_plan.execution_plan)
            )

            # Step 3: Execute task
            result = await self.execute_task(
                execution_plan=execution_plan,
                context=context
            )

            # Step 4: Format response
            response = await self.format_response(
                result=result,
                intent=intent,
                context=context
            )

            # Step 5: Add assistant response to context
            assistant_msg = ConversationMessage(
                message_id=str(uuid.uuid4()),
                role="assistant",
                content=response["message"],
                task_execution=execution_plan,
                task_result=result
            )
            context.messages.append(assistant_msg)
            context.updated_at = datetime.utcnow()

            # Step 6: Learn from interaction (async, non-blocking)
            await self.learn_from_interaction(
                intent=intent,
                execution_plan=execution_plan,
                result=result,
                context=context
            )

            return response

        except Exception as e:
            self.logger.error(
                "Message processing failed",
                error=str(e),
                exc_info=True
            )

            return {
                "message": "I encountered an error processing your request. Could you please try rephrasing or provide more details?",
                "error": str(e),
                "conversation_id": conversation_id
            }

    async def execute_task(
        self,
        execution_plan: TaskExecution,
        context: ConversationContext
    ) -> TaskResult:
        """
        Execute a task using the planned agents and steps

        Args:
            execution_plan: Planned execution strategy
            context: Conversation context

        Returns:
            TaskResult with execution outcome
        """
        start_time = datetime.utcnow()
        agents_used = []
        result_data = {}
        errors = []
        warnings = []

        try:
            # Execute each step in the plan
            for step in execution_plan.execution_plan:
                step_type = step.get("type")  # sequential or parallel
                agent_tasks = step.get("tasks", [])

                if step_type == "sequential":
                    # Execute agents one after another
                    for task in agent_tasks:
                        agent_id = task["agent_id"]
                        agent_input = task.get("input", {})

                        # Get agent from registry
                        agent = self.agent_registry.get_agent(agent_id)

                        if not agent:
                            errors.append(f"Agent not found: {agent_id}")
                            continue

                        # Execute agent
                        agent_result = await agent.execute(
                            input_data=agent_input,
                            context=context
                        )

                        agents_used.append(agent_id)
                        result_data[agent_id] = agent_result

                        # Pass result to next agent if needed
                        if len(agent_tasks) > 1:
                            # Update input for next task
                            pass

                elif step_type == "parallel":
                    # Execute agents in parallel
                    import asyncio

                    parallel_tasks = []
                    for task in agent_tasks:
                        agent_id = task["agent_id"]
                        agent_input = task.get("input", {})

                        agent = self.agent_registry.get_agent(agent_id)
                        if agent:
                            parallel_tasks.append(
                                agent.execute(
                                    input_data=agent_input,
                                    context=context
                                )
                            )
                            agents_used.append(agent_id)

                    # Wait for all parallel tasks
                    if parallel_tasks:
                        parallel_results = await asyncio.gather(*parallel_tasks, return_exceptions=True)

                        for i, agent_result in enumerate(parallel_results):
                            if isinstance(agent_result, Exception):
                                errors.append(str(agent_result))
                            else:
                                result_data[agent_tasks[i]["agent_id"]] = agent_result

            # Determine overall status
            if errors:
                status = "partial_success" if result_data else "failed"
            else:
                status = "success"

            # Calculate confidence
            confidence_scores = [
                r.get("confidence", 0.5)
                for r in result_data.values()
                if isinstance(r, dict)
            ]
            confidence_score = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.5

            execution_time = (datetime.utcnow() - start_time).total_seconds()

            return TaskResult(
                task_id=execution_plan.task_id,
                status=status,
                result_data=result_data,
                agents_used=agents_used,
                execution_time_seconds=execution_time,
                confidence_score=confidence_score,
                errors=errors,
                warnings=warnings
            )

        except Exception as e:
            self.logger.error("Task execution failed", error=str(e), exc_info=True)
            execution_time = (datetime.utcnow() - start_time).total_seconds()

            return TaskResult(
                task_id=execution_plan.task_id,
                status="failed",
                result_data=result_data,
                agents_used=agents_used,
                execution_time_seconds=execution_time,
                confidence_score=0.0,
                errors=[str(e)]
            )

    async def format_response(
        self,
        result: TaskResult,
        intent: TaskIntent,
        context: ConversationContext
    ) -> Dict[str, Any]:
        """
        Format task result into user-friendly response

        Args:
            result: Task execution result
            intent: Original classified intent
            context: Conversation context

        Returns:
            Formatted response dict
        """
        # Extract main result
        main_result = result.result_data.get(result.agents_used[0]) if result.agents_used else {}

        if isinstance(main_result, dict):
            message = main_result.get("message", main_result.get("result", "Task completed."))
        else:
            message = str(main_result)

        response = {
            "message": message,
            "conversation_id": context.conversation_id,
            "task_id": result.task_id,
            "status": result.status,
            "confidence": result.confidence_score,
            "metadata": {
                "agents_used": result.agents_used,
                "execution_time": result.execution_time_seconds,
                "intent_category": intent.category.value
            }
        }

        # Add structured data if available
        if "data" in main_result:
            response["data"] = main_result["data"]

        # Add visualizations if available
        if "visualization" in main_result:
            response["visualization"] = main_result["visualization"]

        # Add errors/warnings
        if result.errors:
            response["errors"] = result.errors
        if result.warnings:
            response["warnings"] = result.warnings

        return response

    async def learn_from_interaction(
        self,
        intent: TaskIntent,
        execution_plan: TaskExecution,
        result: TaskResult,
        context: ConversationContext
    ):
        """
        Learn from user interactions to improve routing and responses

        Args:
            intent: Classified intent
            execution_plan: Execution plan used
            result: Task result
            context: Conversation context
        """
        # Track intent classification accuracy
        # Track agent performance
        # Update user preferences
        # Improve routing decisions

        # This is a placeholder for ML-based learning
        pass

    def get_conversation(self, conversation_id: str) -> Optional[ConversationContext]:
        """Get conversation context by ID"""
        return self.conversations.get(conversation_id)

    def list_capabilities(self) -> List[Dict[str, Any]]:
        """List all available capabilities"""
        agents = self.agent_registry.list_agents()

        return [
            {
                "agent_id": agent.agent_id,
                "name": agent.agent_name,
                "description": agent.description,
                "capabilities": [c.value for c in agent.capabilities]
            }
            for agent in agents
        ]
