# Getting Started with IntelliDoc Pro

## Introduction

Welcome to IntelliDoc Pro, the enterprise-grade document processing and data extraction service that delivers industry-leading 98%+ accuracy using advanced IRZ-CoT (Instructional, Role-Based, Zero-Shot Chain-of-Thought) methodology.

## Quick Start Guide

### Prerequisites

- Docker and Docker Compose (recommended)
- OR Python 3.9+ for local development
- API keys for LLM providers (OpenAI, Anthropic, or Google)
- Optional: AWS credentials for Textract OCR

### Installation

#### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-org/intellidoc-pro.git
cd intellidoc-pro

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env

# Start all services
docker-compose up -d

# Check service health
curl http://localhost:8000/health
```

#### Option 2: Local Development

```bash
# Clone the repository
git clone https://github.com/your-org/intellidoc-pro.git
cd intellidoc-pro

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env

# Run the server
python -m src.api.server
```

## Your First Document Processing

### Using the REST API

```python
import requests

# API endpoint
url = "http://localhost:8000/api/v1/process"

# Your API key (set in .env or get from admin panel)
headers = {
    "Authorization": "Bearer your-api-key-here"
}

# Upload and process a document
files = {
    "file": open("path/to/10K_report.pdf", "rb")
}

data = {
    "industry": "financial",
    "document_type": "sec_10k",
    "validation_level": "strict"
}

response = requests.post(url, headers=headers, files=files, data=data)
result = response.json()

# Access extracted data
print(f"Company: {result['extracted_data']['company_name']['field_value']}")
print(f"Revenue: {result['extracted_data']['total_revenue']['field_value']}")
print(f"Confidence: {result['overall_confidence']}")
```

### Using Python SDK

```python
from intellidoc import DocumentProcessor

# Initialize processor
processor = DocumentProcessor(
    api_key="your-api-key-here"
)

# Process document
result = processor.process(
    file_path="path/to/contract.pdf",
    industry="legal",
    document_type="contract",
    validation_level="strict"
)

# Access results
print(f"Contract Type: {result.data['contract_type']}")
print(f"Parties: {result.data['party_a_name']} & {result.data['party_b_name']}")
print(f"Effective Date: {result.data['effective_date']}")
print(f"Overall Confidence: {result.confidence_score}")
```

### Using cURL

```bash
# Process a document
curl -X POST http://localhost:8000/api/v1/process \
  -H "Authorization: Bearer your-api-key" \
  -F "file=@document.pdf" \
  -F "industry=financial" \
  -F "document_type=sec_10k" \
  -F "validation_level=strict"
```

## Understanding the Results

### Extraction Result Structure

```json
{
  "document_id": "doc_2024-01-15_abc123",
  "industry": "financial",
  "document_type": "sec_10k",
  "processing_status": "completed",
  "overall_confidence": 0.96,
  "fields_extracted": 15,
  "fields_validated": 14,
  "fields_corrected": 2,
  "extracted_data": {
    "company_name": {
      "field_name": "company_name",
      "field_value": "Apple Inc.",
      "confidence_score": 0.99,
      "extraction_method": "irz_cot",
      "validated": true,
      "reasoning": "Found in header section, confirmed by multiple references...",
      "location": "Page 1, Header section"
    },
    "total_revenue": {
      "field_name": "total_revenue",
      "field_value": 394328000000,
      "confidence_score": 0.98,
      "extraction_method": "irz_cot",
      "validated": true,
      "corrected": true,
      "original_value": 394328,
      "reasoning": "Extracted from consolidated statements...",
      "location": "Page 35, Table: Consolidated Statement of Operations"
    }
  },
  "validation_result": {
    "validated": true,
    "validation_score": 0.97,
    "corrections_made": 2,
    "validation_sources_used": ["sec_edgar", "financial_apis"],
    "issues_found": [],
    "warnings": ["Field 'employee_count': Borderline validation score"]
  },
  "processing_time_seconds": 45.2
}
```

### Key Metrics

- **overall_confidence**: Average confidence across all extracted fields (weighted by validation status)
- **fields_extracted**: Total number of fields extracted from the document
- **fields_validated**: Number of fields that passed external validation (RAV)
- **fields_corrected**: Number of fields auto-corrected based on validation (RAC)
- **validation_score**: Combined score from all validation sources

### Confidence Levels

- **0.95 - 1.00**: Very High - Use with full confidence
- **0.85 - 0.95**: High - Reliable for most applications
- **0.70 - 0.85**: Medium - Manual review recommended for critical applications
- **0.50 - 0.70**: Low - Requires manual verification
- **0.00 - 0.50**: Very Low - Likely extraction error

## Supported Industries & Document Types

### Financial Services
- SEC 10-K Annual Reports
- SEC 10-Q Quarterly Reports
- Earnings Reports
- Bank Statements
- Loan Applications
- Transaction Records

### Legal
- Contracts & Agreements
- Court Documents
- Discovery Files
- Legal Briefs
- Compliance Documents

### Insurance
- Claims Forms
- Policy Documents
- Underwriting Files
- Loss Reports

### Healthcare
- Medical Records (EMR/EHR)
- Clinical Trial Data
- Insurance Claims
- Lab Reports
- Patient Intake Forms

## Advanced Features

### Custom Templates

Define your own extraction schema:

```python
custom_schema = {
    "fields": [
        {
            "name": "project_name",
            "description": "Name of the project",
            "field_type": "string",
            "required": True
        },
        {
            "name": "budget",
            "description": "Total project budget",
            "field_type": "number",
            "required": True,
            "validation_rules": {
                "min": 0,
                "format": "currency"
            }
        }
    ],
    "instruction_prompt": "Extract project details from this proposal document.",
    "role_persona": "a senior project manager with expertise in proposal analysis"
}

result = processor.process(
    file_path="proposal.pdf",
    industry="financial",
    document_type="generic",
    custom_schema=custom_schema
)
```

### Batch Processing

Process multiple documents efficiently:

```python
results = processor.process_batch(
    file_paths=[
        "doc1.pdf",
        "doc2.pdf",
        "doc3.pdf"
    ],
    industry="legal",
    document_type="contract"
)

for result in results:
    print(f"Document: {result.document_id}")
    print(f"Status: {result.processing_status}")
    print(f"Confidence: {result.overall_confidence}")
```

### Async Processing with Webhooks

For long-running documents:

```python
# Submit for async processing
job = processor.process_async(
    file_path="large_document.pdf",
    industry="healthcare",
    document_type="medical_record",
    webhook_url="https://your-server.com/webhook"
)

print(f"Job ID: {job['job_id']}")

# Later, check status
status = processor.get_job_status(job['job_id'])
print(f"Status: {status['status']}")
```

## Best Practices

### 1. Choose the Right Validation Level

- **none**: Fastest, no external validation (not recommended for production)
- **basic**: Quick validation, basic consistency checks
- **standard**: Balanced accuracy and speed (recommended for most use cases)
- **strict**: Maximum accuracy, multiple validation sources
- **maximum**: Slowest but highest accuracy, comprehensive validation

### 2. Enable RAV/RAC for Critical Data

Always enable Retrieval-Augmented Validation (RAV) and Correction (RAC) for:
- Financial data that impacts decisions
- Legal documents with contractual obligations
- Healthcare records affecting patient care
- Regulatory filings and compliance documents

### 3. Review Low-Confidence Extractions

Set up automated workflows to flag extractions with:
- Overall confidence < 0.85
- Any field with confidence < 0.70
- Validation warnings

### 4. Use Industry-Specific Templates

Always use the most specific template available for your document type. This significantly improves accuracy.

## Troubleshooting

### Common Issues

**Issue**: "Failed to extract text from document"
- **Solution**: Ensure document is not password-protected or corrupted. Try different OCR engine.

**Issue**: "Low confidence scores across all fields"
- **Solution**: Document may be poor quality. Try enhancing image quality or using multi-engine OCR.

**Issue**: "Validation failed for all fields"
- **Solution**: Check that validation sources are accessible. Verify API keys for validation services.

**Issue**: "Processing timeout"
- **Solution**: Increase `processing_timeout_seconds` in settings for large documents.

## Next Steps

- Read the [API Reference](api-reference.md) for complete API documentation
- Explore [Industry Templates](templates.md) for pre-configured extraction schemas
- Learn about [Security & Compliance](security.md)
- Check out [Performance Tuning](performance.md) guide

## Support

- Documentation: https://docs.intellidoc.ai
- Email Support: support@intellidoc.ai
- Enterprise Support: enterprise@intellidoc.ai
- Community Forum: https://community.intellidoc.ai

## License

Copyright © 2024 IntelliDoc Pro. All rights reserved.
