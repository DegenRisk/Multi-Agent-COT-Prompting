"""
Document Processor
Main orchestrator for the document processing pipeline
Coordinates OCR, extraction, validation, and correction
"""

from typing import Dict, Any, Optional
import asyncio
from datetime import datetime
import hashlib
import structlog
from pathlib import Path

from ..models.document import (
    ProcessingRequest,
    ExtractionResult,
    ProcessingStatus,
    DocumentMetadata,
    ExtractedField,
    ValidationResult,
    IndustryType,
    DocumentType
)
from ..extractors.irz_cot_extractor import IRZCoTExtractor
from ..validators.rav_rac_validator import RAVRACValidator
from ..utils.ocr_engine import OCREngine
from ..utils.template_manager import TemplateManager
from config.settings import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class DocumentProcessor:
    """
    Main document processing pipeline

    Pipeline stages:
    1. Document Ingestion & Validation
    2. OCR / Text Extraction
    3. IRZ-CoT Data Extraction
    4. RAV/RAC Validation & Correction
    5. Quality Assurance & Metrics
    6. Result Formatting & Storage
    """

    def __init__(self):
        """Initialize document processor"""
        self.settings = settings
        self.logger = logger.bind(component="document_processor")

        # Initialize components
        self.ocr_engine = OCREngine()
        self.irz_cot_extractor = IRZCoTExtractor()
        self.rav_rac_validator = RAVRACValidator()
        self.template_manager = TemplateManager()

        self.logger.info("Document processor initialized")

    async def process(
        self,
        file_path: str,
        request: ProcessingRequest
    ) -> ExtractionResult:
        """
        Process a document through the complete pipeline

        Args:
            file_path: Path to document file
            request: Processing request with configuration

        Returns:
            ExtractionResult with all extracted and validated data
        """
        document_id = self._generate_document_id(file_path)
        start_time = datetime.utcnow()

        self.logger.info(
            "Starting document processing",
            document_id=document_id,
            industry=request.industry,
            document_type=request.document_type
        )

        try:
            # Initialize result object
            result = ExtractionResult(
                document_id=document_id,
                industry=request.industry,
                document_type=request.document_type,
                extracted_data={},
                metadata=DocumentMetadata(
                    filename=Path(file_path).name,
                    file_size_bytes=Path(file_path).stat().st_size,
                    file_format=Path(file_path).suffix[1:],
                    mime_type=self._get_mime_type(file_path)
                ),
                processing_status=ProcessingStatus.PROCESSING,
                processing_time_seconds=0.0,
                extraction_time_seconds=0.0,
                overall_confidence=0.0,
                fields_extracted=0,
                started_at=start_time
            )

            # Stage 1: Validate file
            self.logger.info("Stage 1: Validating file", document_id=document_id)
            self._validate_file(file_path)

            # Stage 2: OCR / Text Extraction
            self.logger.info("Stage 2: Performing OCR", document_id=document_id)
            result.processing_status = ProcessingStatus.PROCESSING
            ocr_start = datetime.utcnow()

            document_text, document_structure = await self.ocr_engine.extract_text(
                file_path,
                engine=self.settings.ocr_engine
            )

            result.metadata.page_count = document_structure.get("page_count", 0)

            # Stage 3: Load extraction template
            self.logger.info("Stage 3: Loading extraction template", document_id=document_id)
            template = self.template_manager.get_template(
                industry=request.industry,
                document_type=request.document_type,
                custom_schema=request.custom_schema
            )

            # Stage 4: IRZ-CoT Extraction
            self.logger.info("Stage 4: Performing IRZ-CoT extraction", document_id=document_id)
            result.processing_status = ProcessingStatus.EXTRACTING
            extraction_start = datetime.utcnow()

            extracted_fields = await self.irz_cot_extractor.extract(
                document_text=document_text,
                template=template,
                page_metadata=document_structure
            )

            result.extraction_time_seconds = (datetime.utcnow() - extraction_start).total_seconds()
            result.fields_extracted = len(extracted_fields)

            # Stage 5: RAV/RAC Validation & Correction
            if request.enable_rav or request.enable_rac:
                self.logger.info("Stage 5: Performing RAV/RAC validation", document_id=document_id)
                result.processing_status = ProcessingStatus.VALIDATING
                validation_start = datetime.utcnow()

                extracted_fields, validation_result = await self.rav_rac_validator.validate_and_correct(
                    extracted_fields=extracted_fields,
                    document_context={
                        "document_id": document_id,
                        "document_type": request.document_type.value,
                        "industry": request.industry.value,
                        "text": document_text,
                        "structure": document_structure
                    }
                )

                result.validation_time_seconds = (datetime.utcnow() - validation_start).total_seconds()
                result.validation_result = validation_result
                result.fields_validated = sum(1 for f in extracted_fields.values() if f.validated)
                result.fields_corrected = validation_result.corrections_made
            else:
                # Skip validation
                result.fields_validated = 0
                result.fields_corrected = 0

            # Stage 6: Calculate quality metrics
            self.logger.info("Stage 6: Calculating quality metrics", document_id=document_id)
            result.extracted_data = extracted_fields
            result.overall_confidence = self._calculate_overall_confidence(extracted_fields)

            # Finalize result
            result.processing_status = ProcessingStatus.COMPLETED
            result.completed_at = datetime.utcnow()
            result.processing_time_seconds = (result.completed_at - start_time).total_seconds()

            self.logger.info(
                "Document processing completed",
                document_id=document_id,
                fields_extracted=result.fields_extracted,
                fields_validated=result.fields_validated,
                overall_confidence=result.overall_confidence,
                processing_time=result.processing_time_seconds
            )

            return result

        except Exception as e:
            self.logger.error(
                "Document processing failed",
                document_id=document_id,
                error=str(e),
                exc_info=True
            )

            # Create failed result
            result.processing_status = ProcessingStatus.FAILED
            result.errors.append(str(e))
            result.completed_at = datetime.utcnow()
            result.processing_time_seconds = (result.completed_at - start_time).total_seconds()

            return result

    async def process_batch(
        self,
        file_paths: list[str],
        requests: list[ProcessingRequest],
        max_concurrent: Optional[int] = None
    ) -> list[ExtractionResult]:
        """
        Process multiple documents in parallel

        Args:
            file_paths: List of file paths
            requests: List of processing requests
            max_concurrent: Maximum concurrent processing (None = use settings)

        Returns:
            List of extraction results
        """
        max_concurrent = max_concurrent or self.settings.concurrent_processing_limit

        self.logger.info(
            "Starting batch processing",
            batch_size=len(file_paths),
            max_concurrent=max_concurrent
        )

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_with_semaphore(file_path, request):
            async with semaphore:
                return await self.process(file_path, request)

        # Process all documents
        tasks = [
            process_with_semaphore(file_path, request)
            for file_path, request in zip(file_paths, requests)
        ]

        results = await asyncio.gather(*tasks)

        self.logger.info(
            "Batch processing completed",
            total=len(results),
            successful=sum(1 for r in results if r.processing_status == ProcessingStatus.COMPLETED),
            failed=sum(1 for r in results if r.processing_status == ProcessingStatus.FAILED)
        )

        return results

    def _validate_file(self, file_path: str) -> None:
        """Validate file exists and meets requirements"""
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not path.is_file():
            raise ValueError(f"Not a file: {file_path}")

        # Check file size
        file_size = path.stat().st_size
        if file_size > self.settings.max_file_size_bytes:
            raise ValueError(
                f"File too large: {file_size} bytes (max: {self.settings.max_file_size_bytes})"
            )

        # Check file format
        file_format = path.suffix[1:].lower()
        if file_format not in self.settings.supported_formats_list:
            raise ValueError(
                f"Unsupported format: {file_format} (supported: {self.settings.supported_formats_list})"
            )

    def _generate_document_id(self, file_path: str) -> str:
        """Generate unique document ID"""
        timestamp = datetime.utcnow().isoformat()
        path_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
        return f"doc_{timestamp}_{path_hash}"

    def _get_mime_type(self, file_path: str) -> str:
        """Get MIME type of file"""
        import mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or "application/octet-stream"

    def _calculate_overall_confidence(
        self,
        extracted_fields: Dict[str, ExtractedField]
    ) -> float:
        """Calculate overall confidence score across all fields"""
        if not extracted_fields:
            return 0.0

        # Weight by field importance (validated fields count more)
        total_score = 0.0
        total_weight = 0.0

        for field in extracted_fields.values():
            weight = 1.5 if field.validated else 1.0
            total_score += field.confidence_score * weight
            total_weight += weight

        return total_score / total_weight if total_weight > 0 else 0.0
