"""PDF text extraction with PyMuPDF primary and pdfplumber fallback.

Extracts text content from PDF bytes. When both extractors yield
insufficient text (< 100 chars), flags the document as needing
vision-based extraction (scanned PDF / image-only pages).
"""

from __future__ import annotations

import io

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Minimum character threshold below which we assume the PDF is scanned/image-only
_MIN_TEXT_THRESHOLD = 100


async def extract_pdf_text(pdf_bytes: bytes) -> dict:
    """Extract text from a PDF provided as raw bytes.

    Extraction strategy:
      1. Try PyMuPDF (fitz) -- fast C-based extractor.
      2. If fitz unavailable or yields < threshold, try pdfplumber.
      3. If both yield < threshold, flag as ``vision_needed``.

    Args:
        pdf_bytes: Raw bytes of the PDF file.

    Returns:
        dict with keys:
          - text (str): Extracted text (may be empty if vision_needed).
          - method (str): "pymupdf" | "pdfplumber" | "vision_needed"
          - page_count (int): Number of pages in the document.
          - confidence (float): 0.0-1.0 heuristic confidence in extraction quality.
    """
    text = ""
    method = "vision_needed"
    page_count = 0
    confidence = 0.0

    # --- Attempt 1: PyMuPDF (fitz) ---
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page_count = len(doc)
        pages_text: list[str] = []
        for page in doc:
            pages_text.append(page.get_text())
        doc.close()

        combined = "\n".join(pages_text).strip()
        if len(combined) >= _MIN_TEXT_THRESHOLD:
            text = combined
            method = "pymupdf"
            # Confidence heuristic: ratio of pages that yielded text
            pages_with_text = sum(1 for t in pages_text if len(t.strip()) > 20)
            confidence = round(pages_with_text / max(page_count, 1), 2)
            confidence = max(confidence, 0.5)  # floor at 0.5 if we got enough text
            logger.info(
                "PDF extracted via PyMuPDF",
                chars=len(text),
                pages=page_count,
                confidence=confidence,
            )
            return {
                "text": text,
                "method": method,
                "page_count": page_count,
                "confidence": confidence,
            }
        else:
            logger.info(
                "PyMuPDF yielded insufficient text, trying pdfplumber",
                chars=len(combined),
            )
    except ImportError:
        logger.warning("PyMuPDF (fitz) not installed, falling back to pdfplumber")
    except Exception as exc:
        logger.warning("PyMuPDF extraction failed", error=str(exc))

    # --- Attempt 2: pdfplumber ---
    try:
        import pdfplumber

        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            page_count = len(pdf.pages)
            pages_text_pb: list[str] = []
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                pages_text_pb.append(page_text)

            combined_pb = "\n".join(pages_text_pb).strip()
            if len(combined_pb) >= _MIN_TEXT_THRESHOLD:
                text = combined_pb
                method = "pdfplumber"
                pages_with_text = sum(
                    1 for t in pages_text_pb if len(t.strip()) > 20
                )
                confidence = round(pages_with_text / max(page_count, 1), 2)
                confidence = max(confidence, 0.4)
                logger.info(
                    "PDF extracted via pdfplumber",
                    chars=len(text),
                    pages=page_count,
                    confidence=confidence,
                )
                return {
                    "text": text,
                    "method": method,
                    "page_count": page_count,
                    "confidence": confidence,
                }
            else:
                logger.info(
                    "pdfplumber also yielded insufficient text",
                    chars=len(combined_pb),
                )
    except ImportError:
        logger.warning("pdfplumber not installed")
    except Exception as exc:
        logger.warning("pdfplumber extraction failed", error=str(exc))

    # --- Fallback: vision needed ---
    logger.info(
        "Text extraction insufficient, vision extraction needed",
        page_count=page_count,
    )
    return {
        "text": text,
        "method": "vision_needed",
        "page_count": page_count,
        "confidence": 0.0,
    }
