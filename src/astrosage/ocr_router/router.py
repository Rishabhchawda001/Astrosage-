"""
OCR Routing Engine.

Routes documents through the appropriate extraction path:

  Native PDF → Direct text extraction (PyMuPDF) — NO OCR
  Scanned PDF → PaddleOCR / Tesseract
  Mixed PDF → Hybrid: extract text pages directly, OCR scanned pages
  Images → PaddleOCR
  DOCX → python-docx (no OCR)
  TXT/MD → Direct read (no OCR)

Never OCR native text unnecessarily.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ExtractionRoute(str, Enum):
    """The extraction route for a document."""
    DIRECT_TEXT = "direct_text"           # Native PDF text extraction
    OCR_FULL = "ocr_full"                # Full OCR needed
    OCR_HYBRID = "ocr_hybrid"            # Mixed: some text, some OCR
    DOCX_EXTRACT = "docx_extract"        # DOCX parsing
    TEXT_READ = "text_read"              # Plain text/markdown read
    METADATA_ONLY = "metadata_only"      # Audio/video/images without OCR
    UNSUPPORTED = "unsupported"          # Cannot process


@dataclass
class OCRDecision:
    """The routing decision for a document."""
    route: ExtractionRoute
    reason: str
    needs_ocr: bool
    ocr_engine: str  # "paddleocr", "tesseract", "none"
    ocr_pages: list[int]  # Which pages need OCR (for hybrid)
    text_pages: list[int]  # Which pages have extractable text
    confidence: float  # Confidence in the routing decision
    estimated_time_seconds: float = 0.0


def route_document(classification, language_result=None) -> OCRDecision:
    """
    Route a document to the appropriate extraction pipeline.
    
    Args:
        classification: ClassificationResult from the classifier
        language_result: Optional LanguageDetectionResult
    
    Returns:
        OCRDecision with the routing decision
    """
    ext = classification.extension.lower()
    
    # PDF routing
    if classification.is_pdf:
        if classification.is_native_pdf:
            return OCRDecision(
                route=ExtractionRoute.DIRECT_TEXT,
                reason="Native PDF with extractable text. No OCR needed.",
                needs_ocr=False,
                ocr_engine="none",
                ocr_pages=[],
                text_pages=list(range(1, classification.page_count + 1)),
                confidence=0.95,
            )
        
        elif classification.is_scanned_pdf:
            engine = _select_ocr_engine(language_result)
            return OCRDecision(
                route=ExtractionRoute.OCR_FULL,
                reason="Scanned PDF — all pages require OCR.",
                needs_ocr=True,
                ocr_engine=engine,
                ocr_pages=list(range(1, classification.page_count + 1)),
                text_pages=[],
                confidence=0.9,
                estimated_time_seconds=classification.page_count * 5,  # ~5 sec/page
            )
        
        elif classification.is_mixed_pdf:
            engine = _select_ocr_engine(language_result)
            return OCRDecision(
                route=ExtractionRoute.OCR_HYBRID,
                reason="Mixed PDF — extract text from text pages, OCR for scanned pages.",
                needs_ocr=True,
                ocr_engine=engine,
                ocr_pages=[],  # Determined during extraction
                text_pages=[],  # Determined during extraction
                confidence=0.85,
                estimated_time_seconds=classification.page_count * 2,
            )
        
        else:
            # Unknown PDF type — try text extraction first
            return OCRDecision(
                route=ExtractionRoute.DIRECT_TEXT,
                reason="Unknown PDF type — attempting text extraction.",
                needs_ocr=False,
                ocr_engine="none",
                ocr_pages=[],
                text_pages=[],
                confidence=0.5,
            )
    
    # DOCX routing
    elif ext in (".docx", ".doc"):
        return OCRDecision(
            route=ExtractionRoute.DOCX_EXTRACT,
            reason="DOCX document — parse with python-docx.",
            needs_ocr=False,
            ocr_engine="none",
            ocr_pages=[],
            text_pages=[1],
            confidence=0.95,
        )
    
    # Text/Markdown routing
    elif ext in (".txt", ".md", ".markdown", ".html", ".htm", ".csv", ".json", ".xml"):
        return OCRDecision(
            route=ExtractionRoute.TEXT_READ,
            reason=f"Text-based file ({ext}) — direct read.",
            needs_ocr=False,
            ocr_engine="none",
            ocr_pages=[],
            text_pages=[1],
            confidence=0.99,
        )
    
    # Image routing
    elif ext in (".jpg", ".jpeg", ".png", ".gif", ".tiff", ".tif", ".bmp", ".webp"):
        engine = _select_ocr_engine(language_result)
        return OCRDecision(
            route=ExtractionRoute.OCR_FULL,
            reason="Image file — OCR required.",
            needs_ocr=True,
            ocr_engine=engine,
            ocr_pages=[1],
            text_pages=[],
            confidence=0.8,
        )
    
    # Audio/Video — metadata only
    elif ext in (".mp3", ".wav", ".flac", ".ogg", ".mp4", ".avi", ".mkv", ".webm"):
        return OCRDecision(
            route=ExtractionRoute.METADATA_ONLY,
            reason=f"Media file ({ext}) — metadata extraction only.",
            needs_ocr=False,
            ocr_engine="none",
            ocr_pages=[],
            text_pages=[],
            confidence=0.9,
        )
    
    # Archive
    elif ext in (".zip", ".tar", ".gz", ".rar", ".7z"):
        return OCRDecision(
            route=ExtractionRoute.UNSUPPORTED,
            reason=f"Archive file ({ext}) — not directly processable.",
            needs_ocr=False,
            ocr_engine="none",
            ocr_pages=[],
            text_pages=[],
            confidence=0.7,
        )
    
    else:
        return OCRDecision(
            route=ExtractionRoute.UNSUPPORTED,
            reason=f"Unknown file type ({ext}).",
            needs_ocr=False,
            ocr_engine="none",
            ocr_pages=[],
            text_pages=[],
            confidence=0.3,
        )


def _select_ocr_engine(language_result=None) -> str:
    """Select the best OCR engine based on language."""
    if language_result:
        lang = language_result.primary_language
        script = language_result.primary_script
        
        if script == "devanagari":
            return "paddleocr"  # Best for Hindi/Sanskrit
        elif lang == "english":
            return "paddleocr"  # Good for English too
        else:
            return "paddleocr"  # Default to PaddleOCR
    
    return "paddleocr"  # Default


def get_routing_summary(decisions: list[OCRDecision]) -> dict:
    """Summarize routing decisions across a batch."""
    route_counts = {}
    engine_counts = {}
    needs_ocr = 0
    total_pages_needing_ocr = 0
    
    for d in decisions:
        route_counts[d.route.value] = route_counts.get(d.route.value, 0) + 1
        if d.needs_ocr:
            needs_ocr += 1
            total_pages_needing_ocr += len(d.ocr_pages)
        engine_counts[d.ocr_engine] = engine_counts.get(d.ocr_engine, 0) + 1
    
    return {
        "total_documents": len(decisions),
        "routes": route_counts,
        "ocr_engines": engine_counts,
        "documents_needing_ocr": needs_ocr,
        "total_pages_needing_ocr": total_pages_needing_ocr,
        "estimated_total_time_seconds": sum(d.estimated_time_seconds for d in decisions),
    }
