"""
Intent Classifier
Classifies user intent to determine appropriate routing
"""

from typing import Dict, List, Optional, Any
import re
import structlog

from ..models.task import TaskIntent, TaskCategory, ConversationContext

logger = structlog.get_logger(__name__)


class IntentClassifier:
    """
    Classifies user intent from natural language input

    Uses combination of:
    1. Pattern matching for common intents
    2. Keyword detection
    3. LLM-powered classification for complex cases
    4. Context from conversation history
    """

    def __init__(self):
        """Initialize intent classifier"""
        self.logger = logger.bind(component="intent_classifier")

        # Intent patterns
        self.patterns = self._load_intent_patterns()

    def _load_intent_patterns(self) -> Dict[TaskCategory, List[Dict[str, Any]]]:
        """Load intent detection patterns"""
        return {
            TaskCategory.DOCUMENT_PROCESSING: [
                {
                    "keywords": ["extract", "parse", "analyze document", "read pdf", "contract", "invoice", "form"],
                    "patterns": [
                        r"extract.*from.*document",
                        r"analyze.*contract",
                        r"parse.*pdf",
                        r"read.*file"
                    ],
                    "requires_file": True
                }
            ],
            TaskCategory.DATA_ANALYSIS: [
                {
                    "keywords": ["analyze data", "statistics", "trends", "chart", "graph", "visualize", "correlation"],
                    "patterns": [
                        r"show.*trend",
                        r"analyze.*data",
                        r"create.*chart",
                        r"visualize.*",
                        r"statistics.*"
                    ],
                    "requires_data": True
                }
            ],
            TaskCategory.CODE_GENERATION: [
                {
                    "keywords": ["write code", "function", "script", "program", "implement", "algorithm"],
                    "patterns": [
                        r"write.*function",
                        r"create.*script",
                        r"implement.*algorithm",
                        r"code.*to",
                        r"program.*that"
                    ]
                }
            ],
            TaskCategory.RESEARCH: [
                {
                    "keywords": ["research", "search", "find information", "latest", "what is", "tell me about"],
                    "patterns": [
                        r"what.*latest",
                        r"research.*about",
                        r"find.*information",
                        r"tell me about",
                        r"search.*for"
                    ]
                }
            ],
            TaskCategory.IMAGE_ANALYSIS: [
                {
                    "keywords": ["image", "picture", "photo", "what's in", "describe image", "ocr"],
                    "patterns": [
                        r"what.*in.*image",
                        r"analyze.*image",
                        r"describe.*picture",
                        r"extract.*text.*image"
                    ],
                    "requires_image": True
                }
            ],
            TaskCategory.WRITING: [
                {
                    "keywords": ["write", "draft", "compose", "create document", "email", "report", "summary"],
                    "patterns": [
                        r"write.*email",
                        r"draft.*report",
                        r"create.*summary",
                        r"compose.*"
                    ]
                }
            ],
            TaskCategory.SQL_QUERY: [
                {
                    "keywords": ["database", "sql", "query", "table", "select from", "database"],
                    "patterns": [
                        r"query.*database",
                        r"sql.*select",
                        r"from.*table",
                        r"database.*query"
                    ],
                    "requires_database": True
                }
            ],
            TaskCategory.API_INTEGRATION: [
                {
                    "keywords": ["api", "endpoint", "fetch from", "call api", "http request"],
                    "patterns": [
                        r"call.*api",
                        r"fetch.*from",
                        r"api.*request",
                        r"get.*from.*endpoint"
                    ]
                }
            ],
            TaskCategory.WORKFLOW_AUTOMATION: [
                {
                    "keywords": ["automate", "workflow", "then", "after that", "pipeline"],
                    "patterns": [
                        r"first.*then.*",
                        r"automate.*process",
                        r"workflow.*",
                        r"step.*1.*step.*2"
                    ],
                    "is_complex": True
                }
            ]
        }

    async def classify(
        self,
        message: str,
        context: ConversationContext,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> TaskIntent:
        """
        Classify user intent from message

        Args:
            message: User message
            context: Conversation context
            attachments: Optional file attachments

        Returns:
            TaskIntent with classification results
        """
        message_lower = message.lower()
        attachments = attachments or []

        # Check for file/image attachments
        has_document = any(a.get("type") in ["pdf", "docx", "doc", "txt"] for a in attachments)
        has_image = any(a.get("type") in ["png", "jpg", "jpeg", "gif"] for a in attachments)
        has_data = any(a.get("type") in ["csv", "xlsx", "json"] for a in attachments)

        # Try pattern matching first (fast path)
        pattern_match = self._match_patterns(message_lower, has_document, has_image, has_data)

        if pattern_match:
            self.logger.info(
                "Intent matched by pattern",
                category=pattern_match["category"],
                confidence=pattern_match["confidence"]
            )

            return TaskIntent(
                category=pattern_match["category"],
                confidence=pattern_match["confidence"],
                detected_entities=pattern_match.get("entities", {}),
                requires_multimodal=has_image or has_document,
                requires_tools=pattern_match.get("tools", []),
                requires_data_sources=pattern_match.get("data_sources", []),
                complexity=pattern_match.get("complexity", "simple"),
                reasoning=pattern_match.get("reasoning", "Pattern-based classification")
            )

        # Fall back to LLM classification for complex cases
        llm_classification = await self._classify_with_llm(message, context)

        return llm_classification

    def _match_patterns(
        self,
        message: str,
        has_document: bool,
        has_image: bool,
        has_data: bool
    ) -> Optional[Dict[str, Any]]:
        """Match message against intent patterns"""

        best_match = None
        best_score = 0.0

        for category, pattern_list in self.patterns.items():
            for pattern_config in pattern_list:
                score = 0.0
                matches = 0

                # Check keywords
                keywords = pattern_config.get("keywords", [])
                for keyword in keywords:
                    if keyword in message:
                        matches += 1
                        score += 0.3

                # Check regex patterns
                patterns = pattern_config.get("patterns", [])
                for pattern in patterns:
                    if re.search(pattern, message):
                        matches += 1
                        score += 0.5

                # Check file requirements
                if pattern_config.get("requires_file") and has_document:
                    score += 0.3
                if pattern_config.get("requires_image") and has_image:
                    score += 0.3
                if pattern_config.get("requires_data") and has_data:
                    score += 0.3

                # Normalize score
                if matches > 0:
                    confidence = min(score / 1.5, 1.0)

                    if confidence > best_score:
                        best_score = confidence
                        best_match = {
                            "category": category,
                            "confidence": confidence,
                            "complexity": "complex" if pattern_config.get("is_complex") else "simple",
                            "reasoning": f"Matched {matches} keywords/patterns"
                        }

        if best_match and best_score >= 0.6:
            return best_match

        return None

    async def _classify_with_llm(
        self,
        message: str,
        context: ConversationContext
    ) -> TaskIntent:
        """Use LLM for complex intent classification"""

        # Build classification prompt
        prompt = f"""Classify the user's intent into one of these categories:

Categories:
- document_processing: Extracting or analyzing documents
- data_analysis: Analyzing data, creating visualizations
- code_generation: Writing code or scripts
- research: Web search, finding information
- image_analysis: Understanding or editing images
- writing: Creating text content, emails, reports
- sql_query: Database queries
- api_integration: Working with APIs
- workflow_automation: Multi-step automated processes
- general_conversation: General chat, questions

User message: "{message}"

Respond with JSON:
{{
    "category": "category_name",
    "confidence": 0.0-1.0,
    "reasoning": "why you chose this category",
    "complexity": "simple|moderate|complex",
    "required_tools": ["list", "of", "tools"],
    "required_data_sources": ["list", "of", "sources"]
}}"""

        # Call LLM (placeholder - implement with actual LLM)
        # For now, return general conversation as fallback
        return TaskIntent(
            category=TaskCategory.GENERAL_CONVERSATION,
            confidence=0.5,
            reasoning="LLM classification not implemented yet",
            complexity="simple"
        )
