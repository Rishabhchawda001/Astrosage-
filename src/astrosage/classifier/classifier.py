"""
Document Classification Engine.

Classifies every file into one of:
  - Native PDF (extractable text)
  - Scanned PDF (image-based, needs OCR)
  - Mixed PDF (some text, some scanned pages)
  - DOCX, EPUB, TXT, Markdown
  - JPEG, PNG, GIF, TIFF (images)
  - MP3, MP4 (audio/video)
  - ZIP (archive)
  - Google Workspace export
  - Unknown

Also detects:
  - Whether OCR is required
  - Number of pages
  - File integrity (not corrupted)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """Result of classifying a single document."""
    filepath: str
    filename: str
    extension: str
    mime_type: str
    file_type: str  # pdf, docx, image, audio, video, archive, text, unknown
    
    # PDF-specific
    is_pdf: bool = False
    pdf_type: str = ""  # native, scanned, mixed
    is_native_pdf: bool = False
    is_scanned_pdf: bool = False
    is_mixed_pdf: bool = False
    
    # Content properties
    page_count: int = 0
    has_extractable_text: bool = False
    ocr_required: bool = False
    
    # Integrity
    is_valid: bool = True
    corruption_reason: str = ""
    header_bytes: bytes = b""
    
    # Size
    file_size_bytes: int = 0


# ── Magic bytes for file type detection ──
MAGIC_BYTES = {
    b"%PDF": "pdf",
    b"PK": "zip_or_docx",  # ZIP-based formats
    b"\xff\xd8\xff": "jpeg",
    b"\x89PNG": "png",
    b"GIF8": "gif",
    b"II\x2a\x00": "tiff",
    b"MM\x00\x2a": "tiff",
    b"RIFF": "webp_or_wav",
    b"\x1a\x45\xdf\xa3": "webm_or_mkv",
    b"\x00\x00\x00": "mp4_or_m4a",  # ftyp box
}

EXTENSION_MAP = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".doc": "doc",
    ".epub": "epub",
    ".txt": "text",
    ".md": "markdown",
    ".markdown": "markdown",
    ".html": "text",
    ".htm": "text",
    ".csv": "text",
    ".json": "text",
    ".xml": "text",
    ".jpg": "image",
    ".jpeg": "image",
    ".png": "image",
    ".gif": "image",
    ".tiff": "image",
    ".tif": "image",
    ".bmp": "image",
    ".webp": "image",
    ".mp3": "audio",
    ".wav": "audio",
    ".flac": "audio",
    ".ogg": "audio",
    ".mp4": "video",
    ".avi": "video",
    ".mkv": "video",
    ".webm": "video",
    ".zip": "archive",
    ".tar": "archive",
    ".gz": "archive",
    ".rar": "archive",
    ".7z": "archive",
}


def _detect_mime(filepath: Path) -> str:
    """Detect MIME type from content (magic bytes)."""
    try:
        with open(filepath, "rb") as f:
            header = f.read(16)
    except Exception:
        return "application/octet-stream"
    
    for magic, fmt in MAGIC_BYTES.items():
        if header.startswith(magic):
            if fmt == "pdf":
                return "application/pdf"
            elif fmt == "zip_or_docx":
                # Check extension to distinguish
                ext = filepath.suffix.lower()
                if ext == ".docx":
                    return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                elif ext == ".epub":
                    return "application/epub+zip"
                return "application/zip"
            elif fmt == "jpeg":
                return "image/jpeg"
            elif fmt == "png":
                return "image/png"
            elif fmt == "gif":
                return "image/gif"
            elif fmt == "tiff":
                return "image/tiff"
            elif fmt == "mp4_or_m4a":
                return "video/mp4"
    
    return "application/octet-stream"


def _check_pdf_type(filepath: Path) -> tuple[str, int, bool]:
    """
    Determine if a PDF is native, scanned, or mixed.
    
    Returns: (pdf_type, page_count, has_extractable_text)
    """
    try:
        import pymupdf
        doc = pymupdf.open(str(filepath))
        page_count = len(doc)
        
        text_chars_per_page = []
        for i in range(min(page_count, 20)):  # Sample up to 20 pages
            page = doc[i]
            text = page.get_text()
            text_chars_per_page.append(len(text.strip()))
        
        doc.close()
        
        if page_count == 0:
            return "unknown", 0, False
        
        avg_chars = sum(text_chars_per_page) / len(text_chars_per_page)
        pages_with_text = sum(1 for c in text_chars_per_page if c > 50)
        
        if avg_chars > 200:
            return "native", page_count, True
        elif pages_with_text == 0:
            return "scanned", page_count, False
        else:
            return "mixed", page_count, True
            
    except Exception as e:
        logger.warning(f"PDF analysis failed for {filepath.name}: {e}")
        return "unknown", 0, False


def _check_zip_content(filepath: Path) -> Optional[str]:
    """Check if a ZIP file is actually DOCX or EPUB."""
    try:
        import zipfile
        with zipfile.ZipFile(str(filepath), "r") as zf:
            names = zf.namelist()
            if any(n.startswith("word/") for n in names):
                return "docx"
            if any(n.startswith("EPUB/") or n.endswith(".xhtml") for n in names):
                return "epub"
    except Exception:
        pass
    return None


def classify_document(filepath: Path) -> ClassificationResult:
    """
    Classify a single document.
    
    Performs:
    1. Extension-based classification
    2. Magic byte verification
    3. Content analysis (PDF type detection)
    4. Integrity check
    """
    filepath = Path(filepath)
    
    ext = filepath.suffix.lower()
    file_type = EXTENSION_MAP.get(ext, "unknown")
    
    # File size
    try:
        file_size = filepath.stat().st_size
    except Exception:
        return ClassificationResult(
            filepath=str(filepath),
            filename=filepath.name,
            extension=ext,
            mime_type="unknown",
            file_type="unknown",
            is_valid=False,
            corruption_reason="File not accessible",
        )
    
    # Read header for magic byte detection
    try:
        with open(filepath, "rb") as f:
            header = f.read(16)
    except Exception:
        header = b""
    
    mime_type = _detect_mime(filepath)
    
    # Initialize result
    result = ClassificationResult(
        filepath=str(filepath),
        filename=filepath.name,
        extension=ext,
        mime_type=mime_type,
        file_type=file_type,
        file_size_bytes=file_size,
        header_bytes=header,
    )
    
    # PDF-specific analysis
    if file_type == "pdf" or (file_type == "zip_or_docx" and ext == ".pdf"):
        result.is_pdf = True
        
        # Check if it's actually a PDF
        if not header.startswith(b"%PDF"):
            # Not a real PDF — check if it's HTML error page
            if header.startswith(b"<!") or header.startswith(b"<html"):
                result.is_valid = False
                result.corruption_reason = "HTML file masquerading as PDF"
                return result
        
        pdf_type, page_count, has_text = _check_pdf_type(filepath)
        result.page_count = page_count
        result.has_extractable_text = has_text
        result.pdf_type = pdf_type
        result.is_native_pdf = pdf_type == "native"
        result.is_scanned_pdf = pdf_type == "scanned"
        result.is_mixed_pdf = pdf_type == "mixed"
        result.ocr_required = pdf_type in ("scanned", "mixed")
    
    # DOCX from ZIP
    elif file_type == "zip_or_docx":
        content_type = _check_zip_content(filepath)
        if content_type == "docx":
            result.file_type = "docx"
            result.mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif content_type == "epub":
            result.file_type = "epub"
            result.mime_type = "application/epub+zip"
    
    # Images
    elif file_type == "image":
        result.ocr_required = True  # Images need OCR for text extraction
    
    # Audio/Video — metadata only
    elif file_type in ("audio", "video"):
        result.page_count = 0
        result.has_extractable_text = False
    
    return result


def classify_batch(filepaths: list[Path]) -> list[ClassificationResult]:
    """Classify a batch of files."""
    results = []
    for fp in filepaths:
        try:
            result = classify_document(fp)
            results.append(result)
        except Exception as e:
            logger.error(f"Classification failed for {fp}: {e}")
            results.append(ClassificationResult(
                filepath=str(fp),
                filename=fp.name,
                extension=fp.suffix.lower(),
                mime_type="unknown",
                file_type="unknown",
                is_valid=False,
                corruption_reason=str(e),
            ))
    return results
