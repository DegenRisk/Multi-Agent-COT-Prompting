"""
Task and Intent Models
Data structures for task classification and routing
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class TaskCategory(str, Enum):
    """High-level task categories"""
    DOCUMENT_PROCESSING = "document_processing"
    DATA_ANALYSIS = "data_analysis"
    CODE_GENERATION = "code_generation"
    RESEARCH = "research"
    IMAGE_ANALYSIS = "image_analysis"
    WRITING = "writing"
    SQL_QUERY = "sql_query"
    API_INTEGRATION = "api_integration"
    WORKFLOW_AUTOMATION = "workflow_automation"
    GENERAL_CONVERSATION = "general_conversation"


class TaskIntent(BaseModel):
    """Classified user intent"""
    category: TaskCategory
    confidence: float = Field(ge=0.0, le=1.0)
    subcategory: Optional[str] = None
    detected_entities: Dict[str, Any] = Field(default_factory=dict)
    requires_multimodal: bool = False
    requires_tools: List[str] = Field(default_factory=list)
    requires_data_sources: List[str] = Field(default_factory=list)
    complexity: str = "simple"  # simple, moderate, complex
    reasoning: str = ""


class AgentCapability(str, Enum):
    """Agent capability tags"""
    DOCUMENT_EXTRACTION = "document_extraction"
    DATA_QUERY = "data_query"
    DATA_VISUALIZATION = "data_visualization"
    CODE_GENERATION = "code_generation"
    CODE_EXECUTION = "code_execution"
    WEB_SEARCH = "web_search"
    IMAGE_UNDERSTANDING = "image_understanding"
    IMAGE_GENERATION = "image_generation"
    TEXT_GENERATION = "text_generation"
    SQL_GENERATION = "sql_generation"
    API_INTERACTION = "api_interaction"
    FILE_MANIPULATION = "file_manipulation"


class AgentMetadata(BaseModel):
    """Metadata about an agent"""
    agent_id: str
    agent_name: str
    description: str
    capabilities: List[AgentCapability]
    supported_inputs: List[str]  # text, image, file, data
    supported_outputs: List[str]  # text, image, file, data, visualization
    cost_tier: str = "standard"  # low, standard, high
    average_latency_seconds: float = 5.0
    success_rate: float = 0.95


class TaskExecution(BaseModel):
    """Task execution plan"""
    task_id: str
    user_message: str
    intent: TaskIntent
    selected_agents: List[str]
    execution_plan: List[Dict[str, Any]]  # Sequential or parallel steps
    estimated_duration_seconds: float
    estimated_cost: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TaskResult(BaseModel):
    """Result from task execution"""
    task_id: str
    status: str  # success, partial_success, failed
    result_data: Dict[str, Any]
    agents_used: List[str]
    execution_time_seconds: float
    confidence_score: float
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    completed_at: datetime = Field(default_factory=datetime.utcnow)


class ConversationMessage(BaseModel):
    """Single message in conversation"""
    message_id: str
    role: str  # user, assistant, system
    content: str
    attachments: List[Dict[str, Any]] = Field(default_factory=list)
    task_execution: Optional[TaskExecution] = None
    task_result: Optional[TaskResult] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationContext(BaseModel):
    """Full conversation context"""
    conversation_id: str
    user_id: str
    messages: List[ConversationMessage] = Field(default_factory=list)
    user_preferences: Dict[str, Any] = Field(default_factory=dict)
    active_data_sources: List[str] = Field(default_factory=list)
    session_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
