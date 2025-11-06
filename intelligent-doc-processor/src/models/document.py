"""
Document Models
Data models for document processing and extraction
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator


class IndustryType(str, Enum):
    """Supported industry types"""
    FINANCIAL = "financial"
    LEGAL = "legal"
    INSURANCE = "insurance"
    HEALTHCARE = "healthcare"


class DocumentType(str, Enum):
    """Document type classifications"""
    # Financial
    SEC_10K = "sec_10k"
    SEC_10Q = "sec_10q"
    EARNINGS_REPORT = "earnings_report"
    BANK_STATEMENT = "bank_statement"
    LOAN_APPLICATION = "loan_application"
    TRANSACTION_RECORD = "transaction_record"

    # Legal
    CONTRACT = "contract"
    COURT_DOCUMENT = "court_document"
    DISCOVERY_FILE = "discovery_file"
    LEGAL_BRIEF = "legal_brief"
    COMPLIANCE_DOC = "compliance_doc"

    # Insurance
    CLAIMS_FORM = "claims_form"
    POLICY_DOCUMENT = "policy_document"
    UNDERWRITING_FILE = "underwriting_file"
    LOSS_REPORT = "loss_report"

    # Healthcare
    MEDICAL_RECORD = "medical_record"
    CLINICAL_TRIAL = "clinical_trial"
    INSURANCE_CLAIM = "insurance_claim"
    LAB_REPORT = "lab_report"
    PATIENT_INTAKE = "patient_intake"

    # Generic
    GENERIC = "generic"


class ProcessingStatus(str, Enum):
    """Document processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    EXTRACTING = "extracting"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_COMPLETED = "partially_completed"


class ValidationLevel(str, Enum):
    """Validation strictness levels"""
    NONE = "none"
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"
    MAXIMUM = "maximum"


class ConfidenceLevel(str, Enum):
    """Confidence level classifications"""
    VERY_LOW = "very_low"  # < 0.5
    LOW = "low"  # 0.5 - 0.7
    MEDIUM = "medium"  # 0.7 - 0.85
    HIGH = "high"  # 0.85 - 0.95
    VERY_HIGH = "very_high"  # > 0.95


class ExtractionMethod(str, Enum):
    """Extraction methodology used"""
    IRZ_COT = "irz_cot"  # Instructional, Role-Based, Zero-Shot CoT
    STANDARD_COT = "standard_cot"
    ZERO_SHOT = "zero_shot"
    FEW_SHOT = "few_shot"
    TEMPLATE_BASED = "template_based"


class DocumentMetadata(BaseModel):
    """Document metadata"""
    filename: str
    file_size_bytes: int
    file_format: str
    mime_type: str
    page_count: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    uploaded_by: Optional[str] = None
    source_system: Optional[str] = None
    checksum: Optional[str] = None


class ExtractedField(BaseModel):
    """Individual extracted data field"""
    field_name: str
    field_value: Any
    confidence_score: float
    extraction_method: ExtractionMethod
    validated: bool = False
    corrected: bool = False
    original_value: Optional[Any] = None
    validation_source: Optional[str] = None
    location: Optional[Dict[str, Any]] = None  # Page, bbox, etc.
    reasoning: Optional[str] = None  # CoT reasoning trace

    @validator("confidence_score")
    def validate_confidence(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("Confidence score must be between 0 and 1")
        return v

    @property
    def confidence_level(self) -> ConfidenceLevel:
        """Get confidence level classification"""
        if self.confidence_score < 0.5:
            return ConfidenceLevel.VERY_LOW
        elif self.confidence_score < 0.7:
            return ConfidenceLevel.LOW
        elif self.confidence_score < 0.85:
            return ConfidenceLevel.MEDIUM
        elif self.confidence_score < 0.95:
            return ConfidenceLevel.HIGH
        else:
            return ConfidenceLevel.VERY_HIGH


class ValidationResult(BaseModel):
    """Validation result for extracted data"""
    validated: bool
    validation_score: float
    corrections_made: int = 0
    validation_sources_used: List[str] = Field(default_factory=list)
    issues_found: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    validation_timestamp: datetime = Field(default_factory=datetime.utcnow)


class ExtractionResult(BaseModel):
    """Complete extraction result"""
    document_id: str
    industry: IndustryType
    document_type: DocumentType
    extracted_data: Dict[str, ExtractedField]
    metadata: DocumentMetadata
    processing_status: ProcessingStatus
    validation_result: Optional[ValidationResult] = None

    # Performance metrics
    processing_time_seconds: float
    extraction_time_seconds: float
    validation_time_seconds: Optional[float] = None

    # Quality metrics
    overall_confidence: float
    fields_extracted: int
    fields_validated: int = 0
    fields_corrected: int = 0

    # Timestamps
    started_at: datetime
    completed_at: Optional[datetime] = None

    # Error handling
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calculate success rate of extraction"""
        if self.fields_extracted == 0:
            return 0.0
        return self.fields_validated / self.fields_extracted


class ProcessingRequest(BaseModel):
    """Request to process a document"""
    industry: IndustryType
    document_type: DocumentType
    validation_level: ValidationLevel = ValidationLevel.STANDARD
    extraction_method: ExtractionMethod = ExtractionMethod.IRZ_COT
    custom_schema: Optional[Dict[str, Any]] = None
    enable_rav: bool = True
    enable_rac: bool = True
    webhook_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BatchProcessingRequest(BaseModel):
    """Request to process multiple documents"""
    documents: List[ProcessingRequest]
    batch_name: Optional[str] = None
    priority: int = Field(default=5, ge=1, le=10)
    webhook_url: Optional[str] = None


class TemplateField(BaseModel):
    """Field definition in extraction template"""
    name: str
    description: str
    field_type: str  # string, number, date, boolean, array, object
    required: bool = False
    validation_rules: Optional[Dict[str, Any]] = None
    example_values: Optional[List[str]] = None


class ExtractionTemplate(BaseModel):
    """Template for document extraction"""
    template_id: str
    template_name: str
    industry: IndustryType
    document_type: DocumentType
    description: str
    fields: List[TemplateField]
    role_persona: str  # Role-based prompt for IRZ-CoT
    instruction_prompt: str  # Instructional prompt for IRZ-CoT
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0"
