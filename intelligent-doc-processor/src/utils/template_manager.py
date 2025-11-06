"""
Template Manager
Manages extraction templates for different industries and document types
"""

from typing import Dict, Any, Optional
import json
from pathlib import Path
import structlog

from ..models.document import (
    ExtractionTemplate,
    TemplateField,
    IndustryType,
    DocumentType
)

logger = structlog.get_logger(__name__)


class TemplateManager:
    """Manages extraction templates"""

    def __init__(self, templates_dir: Optional[str] = None):
        """
        Initialize template manager

        Args:
            templates_dir: Directory containing template JSON files
        """
        self.templates_dir = Path(templates_dir or "templates")
        self.logger = logger.bind(component="template_manager")
        self._template_cache: Dict[str, ExtractionTemplate] = {}

        # Load templates
        self._load_templates()

    def _load_templates(self):
        """Load all templates from directory"""
        if not self.templates_dir.exists():
            self.logger.warning(f"Templates directory not found: {self.templates_dir}")
            return

        for template_file in self.templates_dir.rglob("*.json"):
            try:
                with open(template_file, 'r') as f:
                    template_data = json.load(f)
                    template = ExtractionTemplate(**template_data)
                    cache_key = f"{template.industry.value}_{template.document_type.value}"
                    self._template_cache[cache_key] = template

                    self.logger.info(
                        f"Loaded template: {template.template_name}",
                        industry=template.industry,
                        document_type=template.document_type
                    )
            except Exception as e:
                self.logger.error(f"Failed to load template {template_file}: {e}")

    def get_template(
        self,
        industry: IndustryType,
        document_type: DocumentType,
        custom_schema: Optional[Dict[str, Any]] = None
    ) -> ExtractionTemplate:
        """
        Get extraction template

        Args:
            industry: Industry type
            document_type: Document type
            custom_schema: Optional custom schema to override template

        Returns:
            ExtractionTemplate
        """
        cache_key = f"{industry.value}_{document_type.value}"

        # Try to get from cache
        if cache_key in self._template_cache:
            template = self._template_cache[cache_key]

            # Apply custom schema if provided
            if custom_schema:
                template = self._apply_custom_schema(template, custom_schema)

            return template

        # If not found, return generic template
        self.logger.warning(
            f"Template not found for {cache_key}, using generic",
            industry=industry,
            document_type=document_type
        )

        return self._create_generic_template(industry, document_type, custom_schema)

    def _apply_custom_schema(
        self,
        template: ExtractionTemplate,
        custom_schema: Dict[str, Any]
    ) -> ExtractionTemplate:
        """Apply custom schema modifications to template"""
        # Clone template
        import copy
        modified_template = copy.deepcopy(template)

        # Add custom fields
        if "fields" in custom_schema:
            for field_data in custom_schema["fields"]:
                field = TemplateField(**field_data)
                modified_template.fields.append(field)

        # Override instructions if provided
        if "instruction_prompt" in custom_schema:
            modified_template.instruction_prompt = custom_schema["instruction_prompt"]

        if "role_persona" in custom_schema:
            modified_template.role_persona = custom_schema["role_persona"]

        return modified_template

    def _create_generic_template(
        self,
        industry: IndustryType,
        document_type: DocumentType,
        custom_schema: Optional[Dict[str, Any]] = None
    ) -> ExtractionTemplate:
        """Create a generic template"""
        return ExtractionTemplate(
            template_id=f"generic_{industry.value}_{document_type.value}",
            template_name=f"Generic {industry.value.title()} - {document_type.value.title()}",
            industry=industry,
            document_type=document_type,
            description="Generic extraction template with basic fields",
            fields=custom_schema.get("fields", []) if custom_schema else [],
            role_persona=f"an expert {industry.value} analyst with deep knowledge of {document_type.value} documents",
            instruction_prompt=f"Extract all relevant information from this {document_type.value} document. Pay close attention to accuracy and completeness."
        )

    def list_templates(self, industry: Optional[IndustryType] = None) -> list[ExtractionTemplate]:
        """
        List available templates

        Args:
            industry: Optional filter by industry

        Returns:
            List of templates
        """
        templates = list(self._template_cache.values())

        if industry:
            templates = [t for t in templates if t.industry == industry]

        return templates
