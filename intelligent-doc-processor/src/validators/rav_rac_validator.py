"""
RAV/RAC Validator
Retrieval-Augmented Validation (RAV) and Retrieval-Augmented Correction (RAC)
External knowledge validation and automatic correction system
"""

from typing import Dict, List, Any, Optional, Tuple
import asyncio
import structlog
from datetime import datetime

from ..models.document import ExtractedField, ValidationResult
from config.settings import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class RAVRACValidator:
    """
    RAV/RAC Validator combining:
    - RAV: Retrieval-Augmented Validation - verify against external sources
    - RAC: Retrieval-Augmented Correction - auto-correct based on validation

    This is critical for achieving 98%+ accuracy by catching and correcting
    hallucinations and extraction errors.
    """

    def __init__(self, knowledge_sources: Optional[List[str]] = None):
        """
        Initialize RAV/RAC validator

        Args:
            knowledge_sources: List of knowledge sources to use for validation
        """
        self.settings = settings
        self.logger = logger.bind(component="rav_rac_validator")
        self.knowledge_sources = knowledge_sources or settings.validation_sources_list

        # Initialize knowledge source clients
        self.validators = {
            "wikipedia": WikipediaValidator(),
            "sec_edgar": SECEdgarValidator(),
            "pubmed": PubMedValidator(),
            "legal_databases": LegalDatabaseValidator(),
            "financial_apis": FinancialAPIValidator()
        }

    async def validate_and_correct(
        self,
        extracted_fields: Dict[str, ExtractedField],
        document_context: Dict[str, Any]
    ) -> Tuple[Dict[str, ExtractedField], ValidationResult]:
        """
        Validate and optionally correct extracted fields

        Args:
            extracted_fields: Dictionary of extracted fields
            document_context: Original document context for reference

        Returns:
            Tuple of (corrected_fields, validation_result)
        """
        self.logger.info(
            "Starting RAV/RAC validation",
            field_count=len(extracted_fields),
            sources=self.knowledge_sources
        )

        corrections_made = 0
        issues_found = []
        warnings = []
        sources_used = set()

        corrected_fields = {}

        # Validate each field
        for field_name, field in extracted_fields.items():
            self.logger.debug(f"Validating field: {field_name}")

            # Perform RAV (Retrieval-Augmented Validation)
            validation_results = await self._validate_field(field, document_context)

            # Analyze validation results
            validation_score = self._calculate_validation_score(validation_results)
            sources_used.update([r["source"] for r in validation_results])

            # Check if correction is needed
            if validation_score < settings.confidence_threshold:
                issues_found.append(
                    f"Field '{field_name}': Low validation score {validation_score:.2f}"
                )

                # Perform RAC (Retrieval-Augmented Correction) if enabled
                if settings.enable_rac and validation_score >= settings.auto_correct_threshold - 0.1:
                    corrected_value = await self._correct_field(field, validation_results)

                    if corrected_value != field.field_value:
                        self.logger.info(
                            f"Auto-corrected field '{field_name}'",
                            original=field.field_value,
                            corrected=corrected_value
                        )

                        field.original_value = field.field_value
                        field.field_value = corrected_value
                        field.corrected = True
                        corrections_made += 1

            # Update field with validation info
            field.validated = validation_score >= settings.confidence_threshold
            field.validation_source = ", ".join(sources_used)

            # Add warnings for borderline cases
            if settings.confidence_threshold <= validation_score < settings.auto_correct_threshold:
                warnings.append(
                    f"Field '{field_name}': Borderline validation score {validation_score:.2f}"
                )

            corrected_fields[field_name] = field

        # Create overall validation result
        validation_result = ValidationResult(
            validated=all(f.validated for f in corrected_fields.values()),
            validation_score=sum(
                self._calculate_validation_score(
                    await self._validate_field(f, document_context)
                )
                for f in corrected_fields.values()
            ) / len(corrected_fields) if corrected_fields else 0.0,
            corrections_made=corrections_made,
            validation_sources_used=list(sources_used),
            issues_found=issues_found,
            warnings=warnings
        )

        self.logger.info(
            "RAV/RAC validation completed",
            validation_score=validation_result.validation_score,
            corrections_made=corrections_made,
            issues_found=len(issues_found)
        )

        return corrected_fields, validation_result

    async def _validate_field(
        self,
        field: ExtractedField,
        document_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Validate a field against external knowledge sources (RAV)

        Args:
            field: Field to validate
            document_context: Document context

        Returns:
            List of validation results from different sources
        """
        validation_tasks = []

        # Select appropriate validators based on field type and document type
        relevant_validators = self._select_validators(field, document_context)

        # Run validations in parallel
        for validator_name in relevant_validators:
            if validator_name in self.validators:
                validator = self.validators[validator_name]
                validation_tasks.append(
                    validator.validate(field, document_context)
                )

        # Wait for all validations
        if validation_tasks:
            results = await asyncio.gather(*validation_tasks, return_exceptions=True)

            # Filter out exceptions and return valid results
            return [
                r for r in results
                if not isinstance(r, Exception)
            ]

        return []

    def _select_validators(
        self,
        field: ExtractedField,
        document_context: Dict[str, Any]
    ) -> List[str]:
        """
        Select appropriate validators based on field and document type

        Args:
            field: Field to validate
            document_context: Document context

        Returns:
            List of validator names to use
        """
        validators = []
        doc_type = document_context.get("document_type", "")

        # Financial document validators
        if "financial" in doc_type or "sec" in doc_type:
            validators.extend(["sec_edgar", "financial_apis"])

        # Healthcare document validators
        if "healthcare" in doc_type or "medical" in doc_type:
            validators.append("pubmed")

        # Legal document validators
        if "legal" in doc_type or "contract" in doc_type:
            validators.append("legal_databases")

        # General knowledge validation
        validators.append("wikipedia")

        # Filter based on enabled sources
        return [v for v in validators if v in self.knowledge_sources]

    def _calculate_validation_score(
        self,
        validation_results: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate overall validation score from multiple sources

        Args:
            validation_results: Results from different validators

        Returns:
            Combined validation score (0.0 to 1.0)
        """
        if not validation_results:
            return 0.5  # Neutral score if no validation

        # Weight different sources
        source_weights = {
            "sec_edgar": 1.0,
            "pubmed": 1.0,
            "legal_databases": 1.0,
            "financial_apis": 0.9,
            "wikipedia": 0.7
        }

        weighted_sum = 0.0
        total_weight = 0.0

        for result in validation_results:
            source = result.get("source", "unknown")
            score = result.get("score", 0.5)
            weight = source_weights.get(source, 0.5)

            weighted_sum += score * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.5

    async def _correct_field(
        self,
        field: ExtractedField,
        validation_results: List[Dict[str, Any]]
    ) -> Any:
        """
        Attempt to correct field value based on validation results (RAC)

        Args:
            field: Field to correct
            validation_results: Validation results

        Returns:
            Corrected value or original if no correction possible
        """
        # Find the most trusted correction suggestion
        corrections = [
            r.get("suggested_correction")
            for r in validation_results
            if r.get("suggested_correction") and r.get("score", 0) > 0.8
        ]

        if corrections:
            # If multiple sources suggest same correction, use it
            from collections import Counter
            correction_counts = Counter(corrections)
            most_common = correction_counts.most_common(1)[0]

            if most_common[1] >= 2 or most_common[1] == len(corrections):
                return most_common[0]

        return field.field_value


# Knowledge Source Validators

class WikipediaValidator:
    """Validate against Wikipedia"""

    async def validate(
        self,
        field: ExtractedField,
        document_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate field against Wikipedia"""
        # Implementation would query Wikipedia API
        # This is a placeholder

        return {
            "source": "wikipedia",
            "score": 0.85,
            "confidence": 0.85,
            "found": True,
            "suggested_correction": None
        }


class SECEdgarValidator:
    """Validate against SEC EDGAR database"""

    async def validate(
        self,
        field: ExtractedField,
        document_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate field against SEC EDGAR"""
        # Would query SEC EDGAR API for financial data validation
        # Placeholder implementation

        import aiohttp

        # Example: Validate company ticker, financial figures, etc.
        return {
            "source": "sec_edgar",
            "score": 0.95,
            "confidence": 0.95,
            "found": True,
            "suggested_correction": None,
            "metadata": {
                "filing_date": "2024-01-15",
                "form_type": "10-K"
            }
        }


class PubMedValidator:
    """Validate against PubMed medical database"""

    async def validate(
        self,
        field: ExtractedField,
        document_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate field against PubMed"""
        # Would query PubMed API for medical information validation
        # Placeholder implementation

        return {
            "source": "pubmed",
            "score": 0.90,
            "confidence": 0.90,
            "found": True,
            "suggested_correction": None
        }


class LegalDatabaseValidator:
    """Validate against legal databases"""

    async def validate(
        self,
        field: ExtractedField,
        document_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate field against legal databases"""
        # Would query legal databases for contract terms, case law, etc.
        # Placeholder implementation

        return {
            "source": "legal_databases",
            "score": 0.88,
            "confidence": 0.88,
            "found": True,
            "suggested_correction": None
        }


class FinancialAPIValidator:
    """Validate against financial data APIs"""

    async def validate(
        self,
        field: ExtractedField,
        document_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate field against financial APIs"""
        # Would query financial data APIs (Alpha Vantage, Yahoo Finance, etc.)
        # Placeholder implementation

        return {
            "source": "financial_apis",
            "score": 0.92,
            "confidence": 0.92,
            "found": True,
            "suggested_correction": None
        }
