"""Local OCR adapter using pytesseract and pdfplumber."""

import io
import logging
from typing import Any

import pdfplumber
import pytesseract
from PIL import Image

from order_shared.adapters.base import OCRAdapter, OCRResult

logger = logging.getLogger(__name__)


class LocalOCRAdapter(OCRAdapter):
    """OCR adapter using pytesseract for images and pdfplumber for PDFs.

    For local development — no AWS Textract dependency.
    Lower accuracy than Textract on complex scanned documents,
    but sufficient for prototyping and demo scenarios.
    """

    async def extract_text(self, file_bytes: bytes, file_type: str) -> OCRResult:
        file_type = file_type.lower().strip(".")

        if file_type == "pdf":
            return await self._extract_pdf(file_bytes)
        elif file_type in ("png", "jpg", "jpeg", "tiff", "bmp"):
            return await self._extract_image(file_bytes)
        else:
            logger.warning(f"Unsupported file type for OCR: {file_type}")
            return OCRResult(text="", confidence=0.0)

    async def extract_tables(self, file_bytes: bytes, file_type: str) -> list[dict[str, Any]]:
        file_type = file_type.lower().strip(".")

        if file_type == "pdf":
            return await self._extract_pdf_tables(file_bytes)
        else:
            # For images, table extraction is limited without Textract
            logger.info(f"Table extraction from {file_type} not supported locally; returning empty")
            return []

    async def _extract_pdf(self, file_bytes: bytes) -> OCRResult:
        """Extract text from PDF. Uses pdfplumber for digital PDFs,
        falls back to pytesseract OCR if text layer is sparse."""
        pages_data: list[dict[str, Any]] = []
        all_text_parts: list[str] = []

        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                pages_data.append({
                    "page": page_num,
                    "text": text,
                    "chars": len(text),
                })
                all_text_parts.append(text)

        combined_text = "\n\n".join(all_text_parts)

        # If very little text extracted, it's likely a scanned PDF — use OCR
        if len(combined_text.strip()) < 100:
            logger.info("PDF appears to be scanned (sparse text layer), using OCR fallback")
            return await self._ocr_pdf_pages(file_bytes)

        # Digital PDF: high confidence
        return OCRResult(
            text=combined_text,
            confidence=95.0,
            pages=pages_data,
        )

    async def _ocr_pdf_pages(self, file_bytes: bytes) -> OCRResult:
        """OCR each page of a scanned PDF by converting to images."""
        try:
            from pdf2image import convert_from_bytes

            images = convert_from_bytes(file_bytes)
            all_text_parts: list[str] = []
            pages_data: list[dict[str, Any]] = []
            confidences: list[float] = []

            for page_num, img in enumerate(images, start=1):
                data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
                text = pytesseract.image_to_string(img)
                # Calculate average confidence from non-empty entries
                confs = [int(c) for c in data["conf"] if int(c) > 0]
                avg_conf = sum(confs) / len(confs) if confs else 0.0
                confidences.append(avg_conf)
                pages_data.append({"page": page_num, "text": text, "confidence": avg_conf})
                all_text_parts.append(text)

            overall_conf = sum(confidences) / len(confidences) if confidences else 0.0
            return OCRResult(
                text="\n\n".join(all_text_parts),
                confidence=overall_conf,
                pages=pages_data,
            )
        except ImportError:
            logger.warning("pdf2image not installed; cannot OCR scanned PDF pages")
            return OCRResult(text="", confidence=0.0)

    async def _extract_image(self, file_bytes: bytes) -> OCRResult:
        """Extract text from an image using pytesseract."""
        image = Image.open(io.BytesIO(file_bytes))
        text = pytesseract.image_to_string(image)
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

        # Calculate average confidence
        confs = [int(c) for c in data["conf"] if int(c) > 0]
        avg_confidence = sum(confs) / len(confs) if confs else 0.0

        return OCRResult(
            text=text,
            confidence=avg_confidence,
            pages=[{"page": 1, "text": text, "confidence": avg_confidence}],
        )

    async def _extract_pdf_tables(self, file_bytes: bytes) -> list[dict[str, Any]]:
        """Extract tables from a PDF using pdfplumber's table detection."""
        tables: list[dict[str, Any]] = []

        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                page_tables = page.extract_tables()
                for table_idx, table in enumerate(page_tables):
                    if not table or len(table) < 2:
                        continue
                    # First row is headers
                    headers = [str(h).strip() if h else f"col_{i}" for i, h in enumerate(table[0])]
                    rows = []
                    for row in table[1:]:
                        row_dict = {}
                        for i, cell in enumerate(row):
                            key = headers[i] if i < len(headers) else f"col_{i}"
                            row_dict[key] = str(cell).strip() if cell else ""
                        rows.append(row_dict)
                    tables.append({
                        "page": page_num,
                        "table_index": table_idx,
                        "headers": headers,
                        "rows": rows,
                    })

        return tables
