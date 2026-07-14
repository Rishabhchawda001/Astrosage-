"""
Metadata Extraction Engine.

Extracts every metadata field available from documents.
Never overwrites existing metadata.
Records provenance and extraction confidence.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


@dataclass
class DocumentMetadata:
    """Complete metadata for a document."""
    # Identity
    uuid: str = ""
    sha256: str = ""
    
    # Source
    original_filename: str = ""
    relative_path: str = ""
    mime_type: str = ""
    extension: str = ""
    file_size_bytes: int = 0
    
    # PDF metadata
    page_count: int = 0
    pdf_version: str = ""
    is_encrypted: bool = False
    
    # Document metadata
    title: str = ""
    author: str = ""
    publisher: str = ""
    edition: str = ""
    subject: str = ""
    language: str = ""
    script: str = ""
    creation_date: str = ""
    modification_date: str = ""
    
    # Classification
    ocr_required: bool = False
    native_pdf: bool = False
    mixed_pdf: bool = False
    scanned_pdf: bool = False
    pdf_type: str = ""
    
    # Pipeline state
    import_timestamp: str = ""
    processing_status: str = "pending"
    pipeline_version: str = "0.1.0"
    
    # Confidence
    metadata_confidence: float = 0.0
    extraction_method: str = ""
    
    # Notes
    notes: str = ""
    tags: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


def _compute_sha256(filepath: Path) -> str:
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()


def _extract_pdf_metadata(filepath: Path) -> dict:
    """Extract metadata from a PDF file."""
    metadata = {}
    try:
        import pymupdf
        doc = pymupdf.open(str(filepath))
        
        metadata["page_count"] = len(doc)
        metadata["pdf_version"] = doc.metadata.get("format", "")
        metadata["title"] = doc.metadata.get("title", "")
        metadata["author"] = doc.metadata.get("author", "")
        metadata["subject"] = doc.metadata.get("subject", "")
        metadata["creator"] = doc.metadata.get("creator", "")
        metadata["producer"] = doc.metadata.get("producer", "")
        metadata["creation_date"] = doc.metadata.get("creationDate", "")
        metadata["modification_date"] = doc.metadata.get("modDate", "")
        
        # Check encryption
        metadata["is_encrypted"] = doc.is_encrypted
        
        doc.close()
    except Exception:
        pass
    
    return metadata


def _extract_docx_metadata(filepath: Path) -> dict:
    """Extract metadata from a DOCX file."""
    metadata = {}
    try:
        from docx import Document as DocxDocument
        doc = DocxDocument(str(filepath))
        
        core = doc.core_properties
        metadata["title"] = core.title or ""
        metadata["author"] = core.author or ""
        metadata["subject"] = core.subject or ""
        metadata["publisher"] = core.publisher or ""
        metadata["language"] = core.language or ""
        metadata["page_count"] = len(doc.paragraphs)  # Approximate
        
        if core.created:
            metadata["creation_date"] = str(core.created)
        if core.modified:
            metadata["modification_date"] = str(core.modified)
    except Exception:
        pass
    
    return metadata


def _extract_title_from_filename(filename: str) -> str:
    """Try to extract a meaningful title from the filename."""
    # Remove extension
    name = Path(filename).stem
    
    # Remove common prefixes/suffixes
    name = re.sub(r"^\d{4}\.\d+\.", "", name)  # ArXiv-style prefixes
    name = re.sub(r"_", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    
    # Remove trailing numbers/versions
    name = re.sub(r"\s*\(\d+\)\s*$", "", name)
    name = re.sub(r"\s*v\d+\s*$", "", name)
    
    return name


def extract_metadata(
    filepath: Path,
    sha256: str = "",
    classification=None,
    language_result=None,
    uuid: str = "",
) -> DocumentMetadata:
    """
    Extract complete metadata from a document.
    
    Combines:
    1. File system metadata (size, timestamps)
    2. Document-internal metadata (PDF/DOCX properties)
    3. Filename-derived metadata
    4. Classification results
    5. Language detection results
    """
    filepath = Path(filepath)
    
    # File system metadata
    stat = filepath.stat()
    
    # SHA256
    if not sha256:
        sha256 = _compute_sha256(filepath)
    
    # Base metadata
    meta = DocumentMetadata(
        uuid=uuid,
        sha256=sha256,
        original_filename=filepath.name,
        relative_path=str(filepath),
        extension=filepath.suffix.lower(),
        file_size_bytes=stat.st_size,
        import_timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        title=_extract_title_from_filename(filepath.name),
    )
    
    # MIME type detection
    try:
        with open(filepath, "rb") as f:
            header = f.read(16)
        if header.startswith(b"%PDF"):
            meta.mime_type = "application/pdf"
        elif header.startswith(b"PK"):
            if meta.extension == ".docx":
                meta.mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            else:
                meta.mime_type = "application/zip"
        elif header.startswith(b"\xff\xd8\xff"):
            meta.mime_type = "image/jpeg"
        elif header.startswith(b"\x89PNG"):
            meta.mime_type = "image/png"
        else:
            meta.mime_type = "application/octet-stream"
    except Exception:
        meta.mime_type = "application/octet-stream"
    
    # Format-specific metadata
    ext = filepath.suffix.lower()
    if ext == ".pdf":
        pdf_meta = _extract_pdf_metadata(filepath)
        meta.page_count = pdf_meta.get("page_count", 0)
        meta.pdf_version = pdf_meta.get("pdf_version", "")
        meta.is_encrypted = pdf_meta.get("is_encrypted", False)
        if pdf_meta.get("title"):
            meta.title = pdf_meta["title"]
        if pdf_meta.get("author"):
            meta.author = pdf_meta["author"]
        if pdf_meta.get("subject"):
            meta.subject = pdf_meta["subject"]
        if pdf_meta.get("creation_date"):
            meta.creation_date = pdf_meta["creation_date"]
        if pdf_meta.get("modification_date"):
            meta.modification_date = pdf_meta["modification_date"]
        meta.extraction_method = "pymupdf"
        meta.metadata_confidence = 0.8
    
    elif ext == ".docx":
        docx_meta = _extract_docx_metadata(filepath)
        for key, value in docx_meta.items():
            if value and hasattr(meta, key):
                setattr(meta, key, value)
        meta.extraction_method = "python-docx"
        meta.metadata_confidence = 0.7
    
    else:
        meta.extraction_method = "filename_heuristic"
        meta.metadata_confidence = 0.4
    
    # Apply classification results
    if classification:
        meta.page_count = classification.page_count or meta.page_count
        meta.ocr_required = classification.ocr_required
        meta.native_pdf = classification.is_native_pdf
        meta.mixed_pdf = classification.is_mixed_pdf
        meta.scanned_pdf = classification.is_scanned_pdf
        meta.pdf_type = classification.pdf_type
    
    # Apply language results
    if language_result:
        meta.language = language_result.primary_language
        meta.script = language_result.primary_script
    
    return meta
