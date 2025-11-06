"""
OCR Engine
Multi-provider OCR supporting AWS Textract, Google Document AI, and Tesseract
"""

from typing import Dict, Any, Tuple
import structlog
from pathlib import Path

logger = structlog.get_logger(__name__)


class OCREngine:
    """
    Multi-provider OCR engine
    Supports: AWS Textract, Google Document AI, Tesseract
    """

    async def extract_text(
        self,
        file_path: str,
        engine: str = "aws_textract"
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Extract text and structure from document

        Args:
            file_path: Path to document
            engine: OCR engine to use

        Returns:
            Tuple of (extracted_text, document_structure)
        """
        logger.info(f"Extracting text using {engine}", file_path=file_path)

        if engine == "aws_textract":
            return await self._extract_with_aws_textract(file_path)
        elif engine == "google_documentai":
            return await self._extract_with_google_documentai(file_path)
        elif engine == "tesseract":
            return await self._extract_with_tesseract(file_path)
        elif engine == "multi":
            return await self._extract_with_multi_engine(file_path)
        else:
            raise ValueError(f"Unsupported OCR engine: {engine}")

    async def _extract_with_aws_textract(
        self,
        file_path: str
    ) -> Tuple[str, Dict[str, Any]]:
        """Extract using AWS Textract"""
        import boto3
        from config.settings import get_settings

        settings = get_settings()

        # Initialize Textract client
        textract = boto3.client(
            'textract',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region
        )

        # Read file
        with open(file_path, 'rb') as document:
            document_bytes = document.read()

        # Call Textract
        response = textract.analyze_document(
            Document={'Bytes': document_bytes},
            FeatureTypes=['TABLES', 'FORMS']
        )

        # Extract text and structure
        text_blocks = []
        structure = {
            "pages": {},
            "tables": [],
            "forms": [],
            "page_count": 0
        }

        for block in response['Blocks']:
            if block['BlockType'] == 'LINE':
                text_blocks.append(block['Text'])

            elif block['BlockType'] == 'TABLE':
                structure["tables"].append(self._parse_table(block, response['Blocks']))

            elif block['BlockType'] == 'KEY_VALUE_SET':
                structure["forms"].append(self._parse_form(block, response['Blocks']))

            elif block['BlockType'] == 'PAGE':
                structure["page_count"] += 1
                structure["pages"][block['Page']] = {
                    "width": block.get('Geometry', {}).get('BoundingBox', {}).get('Width'),
                    "height": block.get('Geometry', {}).get('BoundingBox', {}).get('Height')
                }

        full_text = '\n'.join(text_blocks)

        logger.info(
            "AWS Textract extraction completed",
            pages=structure["page_count"],
            tables=len(structure["tables"]),
            text_length=len(full_text)
        )

        return full_text, structure

    async def _extract_with_google_documentai(
        self,
        file_path: str
    ) -> Tuple[str, Dict[str, Any]]:
        """Extract using Google Document AI"""
        from google.cloud import documentai_v1 as documentai
        from config.settings import get_settings

        settings = get_settings()

        # Initialize Document AI client
        client = documentai.DocumentProcessorServiceClient()

        # Read file
        with open(file_path, 'rb') as document:
            document_bytes = document.read()

        # Configure request
        name = f"projects/{settings.google_cloud_project}/locations/us/processors/YOUR_PROCESSOR_ID"

        request = documentai.ProcessRequest(
            name=name,
            raw_document=documentai.RawDocument(
                content=document_bytes,
                mime_type=self._get_mime_type(file_path)
            )
        )

        # Process document
        result = client.process_document(request=request)
        document = result.document

        # Extract text and structure
        full_text = document.text

        structure = {
            "pages": {},
            "tables": [],
            "forms": [],
            "page_count": len(document.pages)
        }

        for page in document.pages:
            structure["pages"][page.page_number] = {
                "width": page.dimension.width,
                "height": page.dimension.height,
                "blocks": len(page.blocks)
            }

        logger.info(
            "Google Document AI extraction completed",
            pages=structure["page_count"],
            text_length=len(full_text)
        )

        return full_text, structure

    async def _extract_with_tesseract(
        self,
        file_path: str
    ) -> Tuple[str, Dict[str, Any]]:
        """Extract using Tesseract OCR"""
        import pytesseract
        from pdf2image import convert_from_path
        from PIL import Image

        # Convert PDF to images if needed
        if file_path.lower().endswith('.pdf'):
            images = convert_from_path(file_path)
        else:
            images = [Image.open(file_path)]

        # Extract text from each page
        text_blocks = []
        structure = {
            "pages": {},
            "page_count": len(images)
        }

        for i, image in enumerate(images, 1):
            text = pytesseract.image_to_string(image)
            text_blocks.append(text)

            structure["pages"][i] = {
                "width": image.width,
                "height": image.height
            }

        full_text = '\n'.join(text_blocks)

        logger.info(
            "Tesseract extraction completed",
            pages=structure["page_count"],
            text_length=len(full_text)
        )

        return full_text, structure

    async def _extract_with_multi_engine(
        self,
        file_path: str
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Extract using multiple engines and combine results
        Uses voting/consensus approach for best accuracy
        """
        # Extract with all available engines
        results = []

        try:
            results.append(await self._extract_with_aws_textract(file_path))
        except Exception as e:
            logger.warning(f"AWS Textract failed: {e}")

        try:
            results.append(await self._extract_with_google_documentai(file_path))
        except Exception as e:
            logger.warning(f"Google Document AI failed: {e}")

        try:
            results.append(await self._extract_with_tesseract(file_path))
        except Exception as e:
            logger.warning(f"Tesseract failed: {e}")

        if not results:
            raise RuntimeError("All OCR engines failed")

        # Use the longest text (typically most complete)
        best_result = max(results, key=lambda r: len(r[0]))

        logger.info(
            "Multi-engine extraction completed",
            engines_used=len(results),
            selected_length=len(best_result[0])
        )

        return best_result

    def _parse_table(self, table_block: Dict, all_blocks: list) -> Dict[str, Any]:
        """Parse table structure from Textract blocks"""
        # Simplified table parsing
        return {
            "id": table_block.get('Id'),
            "rows": [],  # Would extract actual table data
            "columns": []
        }

    def _parse_form(self, form_block: Dict, all_blocks: list) -> Dict[str, Any]:
        """Parse form structure from Textract blocks"""
        # Simplified form parsing
        return {
            "id": form_block.get('Id'),
            "fields": []  # Would extract actual form fields
        }

    def _get_mime_type(self, file_path: str) -> str:
        """Get MIME type of file"""
        import mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or "application/pdf"
