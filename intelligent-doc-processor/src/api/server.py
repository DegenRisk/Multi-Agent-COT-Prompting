"""
IntelliDoc Pro REST API Server
FastAPI-based REST API for document processing
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, BackgroundTasks, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List
import structlog
from datetime import datetime
from pathlib import Path
import tempfile
import uuid

from ..core.document_processor import DocumentProcessor
from ..models.document import (
    ProcessingRequest,
    ExtractionResult,
    IndustryType,
    DocumentType,
    ValidationLevel,
    ExtractionMethod
)
from ..utils.template_manager import TemplateManager
from config.settings import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title="IntelliDoc Pro API",
    description="Enterprise-grade document processing and data extraction service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize processors
document_processor = DocumentProcessor()
template_manager = TemplateManager()

# In-memory job tracking (use Redis/DB in production)
processing_jobs = {}


# Authentication dependency
async def verify_api_key(authorization: Optional[str] = Header(None)):
    """Verify API key from Authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing API key")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")

    api_key = authorization.replace("Bearer ", "")

    # Validate API key (implement actual validation in production)
    # This is a placeholder
    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return api_key


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "IntelliDoc Pro API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.app_version
    }


@app.post("/api/v1/process", response_model=ExtractionResult)
async def process_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    industry: IndustryType = IndustryType.FINANCIAL,
    document_type: DocumentType = DocumentType.GENERIC,
    validation_level: ValidationLevel = ValidationLevel.STANDARD,
    extraction_method: ExtractionMethod = ExtractionMethod.IRZ_COT,
    enable_rav: bool = True,
    enable_rac: bool = True,
    webhook_url: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """
    Process a document and extract structured data

    Args:
        file: Document file to process
        industry: Industry type (financial, legal, insurance, healthcare)
        document_type: Type of document
        validation_level: Validation strictness
        extraction_method: Extraction method to use
        enable_rav: Enable retrieval-augmented validation
        enable_rac: Enable retrieval-augmented correction
        webhook_url: Optional webhook for async notification

    Returns:
        ExtractionResult with extracted and validated data
    """
    logger.info(
        "Processing document request",
        filename=file.filename,
        industry=industry,
        document_type=document_type
    )

    # Save uploaded file to temp location
    temp_dir = tempfile.mkdtemp()
    temp_file_path = Path(temp_dir) / file.filename

    try:
        # Save file
        with open(temp_file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Create processing request
        request = ProcessingRequest(
            industry=industry,
            document_type=document_type,
            validation_level=validation_level,
            extraction_method=extraction_method,
            enable_rav=enable_rav,
            enable_rac=enable_rac,
            webhook_url=webhook_url
        )

        # Process document
        result = await document_processor.process(
            file_path=str(temp_file_path),
            request=request
        )

        # Send webhook notification if provided
        if webhook_url:
            background_tasks.add_task(send_webhook, webhook_url, result)

        return result

    except Exception as e:
        logger.error(f"Document processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Cleanup temp file
        if temp_file_path.exists():
            temp_file_path.unlink()


@app.post("/api/v1/process/async")
async def process_document_async(
    file: UploadFile = File(...),
    industry: IndustryType = IndustryType.FINANCIAL,
    document_type: DocumentType = DocumentType.GENERIC,
    validation_level: ValidationLevel = ValidationLevel.STANDARD,
    webhook_url: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """
    Submit a document for asynchronous processing

    Returns:
        Job ID for tracking processing status
    """
    job_id = str(uuid.uuid4())

    logger.info(
        "Creating async processing job",
        job_id=job_id,
        filename=file.filename
    )

    # Save file
    temp_dir = Path(tempfile.mkdtemp())
    temp_file_path = temp_dir / file.filename

    with open(temp_file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Create job tracking
    processing_jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "created_at": datetime.utcnow().isoformat(),
        "file_path": str(temp_file_path),
        "industry": industry,
        "document_type": document_type,
        "validation_level": validation_level,
        "webhook_url": webhook_url
    }

    # Queue processing (in production, use Celery or similar)
    # For now, this is a placeholder

    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Document queued for processing"
    }


@app.get("/api/v1/job/{job_id}")
async def get_job_status(
    job_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get status of an async processing job"""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    return processing_jobs[job_id]


@app.post("/api/v1/batch")
async def process_batch(
    files: List[UploadFile] = File(...),
    industry: IndustryType = IndustryType.FINANCIAL,
    document_type: DocumentType = DocumentType.GENERIC,
    api_key: str = Depends(verify_api_key)
):
    """
    Process multiple documents in batch

    Returns:
        Batch job ID
    """
    batch_id = str(uuid.uuid4())

    logger.info(
        "Creating batch processing job",
        batch_id=batch_id,
        file_count=len(files)
    )

    # In production, queue all files for processing
    return {
        "batch_id": batch_id,
        "file_count": len(files),
        "status": "queued",
        "message": f"Batch of {len(files)} documents queued for processing"
    }


@app.get("/api/v1/templates")
async def list_templates(
    industry: Optional[IndustryType] = None,
    api_key: str = Depends(verify_api_key)
):
    """List available extraction templates"""
    templates = template_manager.list_templates(industry=industry)

    return {
        "count": len(templates),
        "templates": [
            {
                "template_id": t.template_id,
                "template_name": t.template_name,
                "industry": t.industry,
                "document_type": t.document_type,
                "field_count": len(t.fields)
            }
            for t in templates
        ]
    }


@app.get("/api/v1/templates/{template_id}")
async def get_template(
    template_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get details of a specific template"""
    # Find template
    templates = template_manager.list_templates()
    template = next((t for t in templates if t.template_id == template_id), None)

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return template


@app.get("/api/v1/industries")
async def list_industries():
    """List supported industries"""
    return {
        "industries": [
            {
                "value": industry.value,
                "name": industry.value.replace("_", " ").title()
            }
            for industry in IndustryType
        ]
    }


@app.get("/api/v1/document-types")
async def list_document_types(industry: Optional[str] = None):
    """List supported document types"""
    # Filter by industry if provided (simplified implementation)
    doc_types = [
        {
            "value": doc_type.value,
            "name": doc_type.value.replace("_", " ").title()
        }
        for doc_type in DocumentType
    ]

    return {"document_types": doc_types}


@app.get("/api/v1/metrics")
async def get_metrics(api_key: str = Depends(verify_api_key)):
    """Get processing metrics (placeholder for monitoring)"""
    return {
        "total_documents_processed": len(processing_jobs),
        "success_rate": 0.98,
        "average_processing_time": 45.2,
        "average_confidence": 0.96
    }


async def send_webhook(webhook_url: str, result: ExtractionResult):
    """Send webhook notification with processing result"""
    import httpx

    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                webhook_url,
                json=result.dict(),
                timeout=30.0
            )
        logger.info(f"Webhook sent successfully to {webhook_url}")
    except Exception as e:
        logger.error(f"Failed to send webhook: {e}")


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.server:app",
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers,
        reload=settings.debug
    )
