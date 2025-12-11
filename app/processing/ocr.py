"""OCR and document text extraction."""

from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: Path) -> Dict[str, Any]:
    """Extract text from PDF document."""
    text = ""
    tables = []

    try:
        # Try pdfplumber first for structured extraction
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

                # Extract tables if present
                page_tables = page.extract_tables()
                if page_tables:
                    tables.extend(page_tables)

        logger.info(f"Extracted text from PDF using pdfplumber: {len(text)} chars")
    except Exception as e:
        logger.warning(f"pdfplumber extraction failed: {e}, trying PyMuPDF")

        # Fallback to PyMuPDF
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
            logger.info(f"Extracted text from PDF using PyMuPDF: {len(text)} chars")
        except Exception as e2:
            logger.error(f"PyMuPDF extraction also failed: {e2}")
            raise

    return {
        "raw_text": text.strip(),
        "tables": tables,
        "page_count": text.count("\f") + 1 if text else 0,
    }


def extract_text_from_image(file_path: Path, lang: str = "en") -> Dict[str, Any]:
    """Extract text from image using OCR."""
    text = ""
    confidence = 0.0

    try:
        # Try PaddleOCR first (better for complex layouts)
        from paddleocr import PaddleOCR

        ocr = PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)
        result = ocr.ocr(str(file_path), cls=True)

        if result and result[0]:
            lines = []
            confidences = []
            for line in result[0]:
                if line and len(line) >= 2:
                    text_content = line[1][0] if isinstance(line[1], tuple) else line[1]
                    conf = line[1][1] if isinstance(line[1], tuple) and len(line[1]) > 1 else 1.0
                    lines.append(text_content)
                    confidences.append(conf)

            text = "\n".join(lines)
            confidence = sum(confidences) / len(confidences) if confidences else 0.0

        logger.info(f"Extracted text from image using PaddleOCR: {len(text)} chars, confidence: {confidence:.2f}")
    except Exception as e:
        logger.warning(f"PaddleOCR extraction failed: {e}, trying Tesseract")

        # Fallback to Tesseract
        try:
            import pytesseract
            from PIL import Image

            image = Image.open(file_path)
            text = pytesseract.image_to_string(image, lang=lang)
            confidence = 0.8  # Tesseract doesn't provide easy confidence scoring

            logger.info(f"Extracted text from image using Tesseract: {len(text)} chars")
        except Exception as e2:
            logger.error(f"Tesseract extraction also failed: {e2}")
            raise

    return {
        "raw_text": text.strip(),
        "confidence": confidence,
        "method": "paddleocr" if confidence != 0.8 else "tesseract",
    }


def extract_text_from_document(file_path: str, mime_type: str, lang: str = "en") -> Dict[str, Any]:
    """Extract text from document based on MIME type."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if mime_type == "application/pdf":
        return extract_text_from_pdf(path)
    elif mime_type in ["image/jpeg", "image/jpg", "image/png"]:
        return extract_text_from_image(path, lang)
    else:
        raise ValueError(f"Unsupported MIME type: {mime_type}")
