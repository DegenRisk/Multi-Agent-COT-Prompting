"""
Base Agent
Abstract base class for all specialist agents
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import structlog

from ..models.task import AgentMetadata, ConversationContext

logger = structlog.get_logger(__name__)


class BaseAgent(ABC):
    """Base class for all specialist agents"""

    def __init__(self):
        """Initialize base agent"""
        self.logger = logger.bind(agent=self.__class__.__name__)

    @abstractmethod
    def get_metadata(self) -> AgentMetadata:
        """Get agent metadata"""
        pass

    @abstractmethod
    async def execute(
        self,
        input_data: Dict[str, Any],
        context: ConversationContext
    ) -> Dict[str, Any]:
        """
        Execute agent task

        Args:
            input_data: Input data for the task
            context: Conversation context

        Returns:
            Dict with result data
        """
        pass

    def _format_success_response(
        self,
        message: str,
        data: Any = None,
        confidence: float = 0.9
    ) -> Dict[str, Any]:
        """Format successful response"""
        response = {
            "success": True,
            "message": message,
            "confidence": confidence
        }

        if data is not None:
            response["data"] = data

        return response

    def _format_error_response(
        self,
        error: str,
        details: str = ""
    ) -> Dict[str, Any]:
        """Format error response"""
        return {
            "success": False,
            "error": error,
            "details": details,
            "confidence": 0.0
        }
