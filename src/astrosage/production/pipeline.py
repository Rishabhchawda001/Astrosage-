"""
Production Document Pipeline v1.0

Complete pipeline: Document → Classification → Routing → Extraction → Parsing → Validation → Knowledge Lake

Architecture:
  Raw PDF
    ↓ Stage 1: Multi-Signal Page Classifier
    ↓ Stage 2: Document Classification
    ↓ Stage 3: Per-Page Routing
    ↓ Stage 4: Text Extraction (PyMuPDF for native, Tesseract for scanned)
    ↓ Stage 5: Language Detection
    ↓ Stage 6: Metadata Extraction
    ↓ Stage 7: Quality Validation
    ↓ Stage 8: Knowledge Lake Ingestion (bronze → silver)
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import time
import traceback
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

PIPELINE_VERSION = "1.0.0"
PIPELINE_NAME = "Document Intelligence v1.0"


# ── Data Classes ──────────────────────────────────────────────────

@dataclass
class PageResult:
    page_number: int
    page_class: str  # native_text, scanned_image, ocr_overlay, mixed_content, blank
    text: str
    char_count: int = 0
    extraction_method: str = ""
    ocr_confidence: float = 0.0
    processing_time_ms: float = 0.0
    error: Optional[str] = None
    language: str = "unknown"
    script: str = "unknown"
    font_count: int = 0
    image_count: int = 0
    has_heading: bool = False
    has_table: bool = False


@dataclass
class DocumentResult:
    document_id: str
    filename: str
    relative_path: str
    sha256: str
    file_size: int
    total_pages: int
    pages_processed: int = 0
    pages_failed: int = 0
    document_class: str = "unknown"
    page_results: list = field(default_factory=list)
    full_text: str = ""
    metadata: dict = field(default_factory=dict)
    language: str = "unknown"
    script: str = "unknown"
    overall_ocr_confidence: float = 0.0
    quality_score: float = 0.0
    processing_time_sec: float = 0.0
    error: Optional[str] = None
    bronze_path: Optional[str] = None
    silver_path: Optional[str] = None


@dataclass
class PipelineMetrics:
    start_time: float = 0.0
    end_time: float = 0.0
    documents_processed: int = 0
    documents_failed: int = 0
    total_pages: int = 0
    pages_native: int = 0
    pages_scanned: int = 0
    pages_ocr_overlay: int = 0
    pages_mixed: int = 0
    pages_blank: int = 0
    pages_failed: int = 0
    total_chars_extracted: int = 0
    total_ocr_time_sec: float = 0.0
    total_extraction_time_sec: float = 0.0
    avg_ocr_confidence: float = 0.0
    avg_processing_time_sec: float = 0.0
    errors: list = field(default_factory=list)
    page_processing_times: list = field(default_factory=list)


# ── Utility ───────────────────────────────────────────────────────

def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def generate_document_id(filename: str, sha256: str) -> str:
    return f"DOC-{sha256[:12].upper()}"


# ── Stage 1 & 2: Classification ─────────────────────────────────

def classify_document(filepath: Path) -> dict:
    """Classify all pages and determine document class."""
    import pymupdf
    from astrosage.forensics.page_classifier import classify_page, PageSignals

    doc = pymupdf.open(str(filepath))
    page_classes = []
    page_signals_list = []
    
    for i in range(len(doc)):
        page = doc[i]
        try:
            signals = classify_page(page, i + 1)
            page_classes.append(signals.page_class)
            page_signals_list.append(asdict(signals))
        except Exception:
            page_classes.append("unknown")
            page_signals_list.append({"page_number": i + 1, "page_class": "unknown"})
    
    doc.close()

    class_counts = Counter(page_classes)
    if not class_counts:
        return {"document_class": "error", "page_classes": page_classes, "page_signals": page_signals_list,
                "class_counts": {}, "most_common": "error"}

    most_common = class_counts.most_common(1)[0]
    doc_class = most_common[0]
    
    # Detect hybrid: if no single class exceeds 80% of pages
    if most_common[1] < len(page_classes) * 0.8 and len(class_counts) > 1:
        doc_class = "hybrid"

    return {
        "document_class": doc_class,
        "page_classes": page_classes,
        "page_signals": page_signals_list,
        "class_counts": dict(class_counts),
        "most_common": most_common[0],
        "total_pages": len(page_classes),
    }


# ── Stage 3 & 4: Routing and Extraction ─────────────────────────

def extract_page_text_native(page) -> tuple[str, dict]:
    """Extract text from a native PDF page using PyMuPDF."""
    text = page.get_text("text")
    text_dict = page.get_text("dict")
    
    font_count = 0
    block_count = 0
    for block in text_dict.get("blocks", []):
        if block.get("type") == 0:
            block_count += 1
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    if span.get("font"):
                        font_count += 1

    meta = {
        "font_count": font_count,
        "text_blocks": block_count,
        "has_heading": any(
            span.get("size", 0) > 14
            for block in text_dict.get("blocks", [])
            if block.get("type") == 0
            for line in block.get("lines", [])
            for span in line.get("spans", [])
        ),
    }
    return text, meta


def extract_page_text_ocr(page, lang_hint: str = "eng") -> tuple[str, float, dict]:
    """Extract text from a scanned page using Tesseract OCR."""
    import pytesseract
    from PIL import Image
    import io

    # Render page to image
    pix = page.get_pixmap(dpi=150)
    img_data = pix.tobytes("png")
    img = Image.open(io.BytesIO(img_data))

    # Map language hint to Tesseract language codes
    lang_map = {
        "english": "eng",
        "hindi": "hin",
        "sanskrit": "san",
        "devanagari": "hin",
        "latin": "eng",
        "unknown": "eng",
        "mixed": "hin+eng",
    }
    tesseract_lang = lang_map.get(lang_hint, "eng")

    # Run OCR
    ocr_data = pytesseract.image_to_data(img, lang=tesseract_lang, output_type=pytesseract.Output.DICT)
    text = pytesseract.image_to_string(img, lang=tesseract_lang)
    
    # Calculate confidence
    confs = [int(c) for c in ocr_data["conf"] if int(c) > 0]
    avg_conf = sum(confs) / max(1, len(confs)) / 100.0

    meta = {
        "ocr_engine": "tesseract",
        "ocr_lang": tesseract_lang,
        "word_count": len([w for w in ocr_data["text"] if w.strip()]),
    }
    return text, avg_conf, meta


# ── Stage 5: Language Detection ──────────────────────────────────

def detect_page_language(text: str) -> tuple[str, str]:
    """Detect language and script of extracted text."""
    if not text.strip():
        return "unknown", "unknown"

    devanagari_count = sum(1 for ch in text if 0x0900 <= ord(ch) <= 0x097F)
    latin_count = sum(1 for ch in text if 0x0020 <= ord(ch) <= 0x007E)
    total = len(text.strip())

    if total == 0:
        return "unknown", "unknown"

    devanagari_pct = devanagari_count / total
    latin_pct = latin_count / total

    if devanagari_pct > 0.3:
        script = "devanagari"
        # Could be Hindi or Sanskrit — heuristic: Sanskrit has more diacritics
        language = "hindi"  # default for Devanagari
    elif latin_pct > 0.5:
        script = "latin"
        language = "english"
    else:
        script = "mixed"
        language = "mixed"

    return language, script


# ── Stage 6: Metadata Extraction ─────────────────────────────────

def extract_metadata(filepath: Path, doc_info: dict) -> dict:
    """Extract metadata from the PDF."""
    import pymupdf

    meta = {
        "title": "",
        "author": "",
        "subject": "",
        "creator": "",
        "producer": "",
        "creation_date": "",
        "mod_date": "",
    }

    try:
        doc = pymupdf.open(str(filepath))
        pdf_meta = doc.metadata
        if pdf_meta:
            for key in ["title", "author", "subject", "creator", "producer", "creationDate", "modDate"]:
                val = pdf_meta.get(key, "")
                if val:
                    clean_key = key.lower().replace("date", "_date")
                    meta[clean_key] = str(val)[:200]
        doc.close()
    except Exception:
        pass

    meta["filename"] = filepath.name
    meta["file_size"] = filepath.stat().st_size
    meta["sha256"] = doc_info.get("sha256", "")
    meta["total_pages"] = doc_info.get("total_pages", 0)
    meta["document_class"] = doc_info.get("document_class", "unknown")
    meta["pipeline_version"] = PIPELINE_VERSION
    meta["import_timestamp"] = datetime.now(timezone.utc).isoformat()
    
    return meta


# ── Stage 7: Quality Validation ──────────────────────────────────

def validate_page_quality(page_result: dict) -> dict:
    """Validate quality of extracted page content."""
    text = page_result.get("text", "")
    char_count = len(text.strip())
    
    issues = []
    score = 100.0

    # Check for empty extraction
    if char_count == 0 and page_result.get("page_class") != "blank":
        issues.append("empty_extraction")
        score -= 50

    # Check for OCR quality
    if page_result.get("ocr_confidence", 1.0) < 0.5:
        issues.append("low_ocr_confidence")
        score -= 20

    # Check for replacement characters (broken Unicode)
    if "\ufffd" in text:
        issues.append("broken_unicode")
        score -= 15

    # Check for excessive short lines (potential column merge)
    lines = [l for l in text.split("\n") if l.strip()]
    short_lines = sum(1 for l in lines if len(l.strip()) < 3)
    if lines and short_lines / max(1, len(lines)) > 0.5:
        issues.append("many_short_lines")
        score -= 10

    return {
        "quality_score": max(0, score),
        "issues": issues,
        "char_count": char_count,
        "line_count": len(lines),
    }


# ── Stage 8: Knowledge Lake Ingestion ────────────────────────────

def write_bronze(doc_result: dict, output_dir: Path) -> str:
    """Write extracted text to bronze layer."""
    bronze_dir = output_dir / "bronze" / "extracted_text"
    bronze_dir.mkdir(parents=True, exist_ok=True)

    doc_id = doc_result["document_id"]
    filename = doc_result["filename"].replace(".pdf", ".txt")
    out_path = bronze_dir / filename

    # Write all page texts with page markers
    content = ""
    for pr in doc_result.get("page_results", []):
        content += f"\n\n=== PAGE {pr.get('page_number', '?')} ===\n\n"
        content += pr.get("text", "")

    out_path.write_text(content, encoding="utf-8")
    return str(out_path.relative_to(output_dir.parent.parent))


def write_silver(doc_result: dict, output_dir: Path) -> str:
    """Write structured markdown to silver layer."""
    silver_dir = output_dir / "silver" / "structured_documents"
    silver_dir.mkdir(parents=True, exist_ok=True)

    filename = doc_result["filename"].replace(".pdf", ".md")
    out_path = silver_dir / filename

    lines = [
        f"# {doc_result.get('metadata', {}).get('title', doc_result['filename'])}",
        "",
        f"**Author:** {doc_result.get('metadata', {}).get('author', 'Unknown')}",
        f"**Language:** {doc_result.get('language', 'unknown')}",
        f"**Pages:** {doc_result.get('total_pages', 0)}",
        f"**Document Class:** {doc_result.get('document_class', 'unknown')}",
        f"**Pipeline:** {PIPELINE_NAME}",
        f"**SHA256:** `{doc_result.get('sha256', '')}`",
        "",
        "---",
        "",
    ]

    for pr in doc_result.get("page_results", []):
        if pr.get("text", "").strip():
            lines.append(f"## Page {pr.get('page_number', '?')}")
            lines.append("")
            lines.append(pr["text"].strip())
            lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return str(out_path.relative_to(output_dir.parent.parent))


# ── Main Pipeline ────────────────────────────────────────────────

class ProductionPipeline:
    """Complete production document processing pipeline."""

    def __init__(self, base_dir: str = ".", max_page_time_sec: float = 30.0):
        self.base = Path(base_dir)
        self.raw_dir = self.base / "knowledge" / "raw" / "source_library"
        self.output_dir = self.base / "knowledge"
        self.reports_dir = self.base / "knowledge" / "reports"
        self.benchmarks_dir = self.base / "knowledge" / "benchmarks"
        self.max_page_time_sec = max_page_time_sec
        self.metrics = PipelineMetrics()
        self.results: list[DocumentResult] = []

    def process_document(self, filepath: Path) -> DocumentResult:
        """Process a single document through the complete pipeline."""
        doc_start = time.time()
        sha256 = compute_sha256(filepath)
        doc_id = generate_document_id(filepath.name, sha256)
        
        result = DocumentResult(
            document_id=doc_id,
            filename=filepath.name,
            relative_path=str(filepath.relative_to(self.raw_dir)),
            sha256=sha256,
            file_size=filepath.stat().st_size,
            total_pages=0,
        )

        try:
            # Stage 1-2: Classify
            classification = classify_document(filepath)
            result.document_class = classification["document_class"]
            result.total_pages = classification["total_pages"]

            # Detect document-level language from first few pages
            import pymupdf
            doc = pymupdf.open(str(filepath))
            max_ocr_pages = 50  # Limit OCR for validation speed
            sample_text = ""
            for i in range(min(3, len(doc))):
                sample_text += doc[i].get_text("text")
            doc.close()
            result.language, result.script = detect_page_language(sample_text)

            # Stage 3-4: Route and extract per page
            doc = pymupdf.open(str(filepath))
            page_classes = classification["page_classes"]
            all_text_parts = []
            total_ocr_conf = 0.0
            ocr_count = 0

            doc_start_loop = time.time()
            for i in range(len(doc)):
                page = doc[i]
                page_class = page_classes[i] if i < len(page_classes) else "unknown"
                pr = {"page_number": i + 1, "page_class": page_class}

                try:
                    t0 = time.time()
                    
                    if page_class == "native_text":
                        text, meta = extract_page_text_native(page)
                        pr["text"] = text
                        pr["extraction_method"] = "pymupdf"
                        pr["char_count"] = len(text.strip())
                        pr["has_heading"] = meta.get("has_heading", False)
                        pr["font_count"] = meta.get("font_count", 0)

                    elif page_class in ("scanned_image", "ocr_overlay"):
                        ocr_done = sum(1 for pr2 in result.page_results if pr2.get("extraction_method", "").startswith("tesseract"))
                        if ocr_done >= max_ocr_pages:
                            pr["text"] = ""
                            pr["extraction_method"] = "ocr_skipped_limit"
                            pr["char_count"] = 0
                        else:
                            lang_hint = result.language if result.language != "unknown" else "eng"
                            text, conf, meta = extract_page_text_ocr(page, lang_hint)
                        pr["text"] = text
                        pr["extraction_method"] = f"tesseract_{meta.get('ocr_lang', 'eng')}"
                        pr["ocr_confidence"] = conf
                        pr["char_count"] = len(text.strip())
                        total_ocr_conf += conf
                        ocr_count += 1

                    elif page_class == "hybrid":
                        # Try native first, fall back to OCR if empty
                        text, meta = extract_page_text_native(page)
                        if len(text.strip()) < 50:
                            lang_hint = result.language if result.language != "unknown" else "eng"
                            text, conf, meta2 = extract_page_text_ocr(page, lang_hint)
                            pr["extraction_method"] = f"tesseract_{meta2.get('ocr_lang', 'eng')}_fallback"
                            pr["ocr_confidence"] = conf
                            total_ocr_conf += conf
                            ocr_count += 1
                        else:
                            pr["extraction_method"] = "pymupdf"
                            pr["font_count"] = meta.get("font_count", 0)
                        pr["text"] = text
                        pr["char_count"] = len(text.strip())

                    elif page_class == "blank":
                        pr["text"] = ""
                        pr["extraction_method"] = "skip_blank"
                        pr["char_count"] = 0

                    else:
                        # unknown — try native
                        text, meta = extract_page_text_native(page)
                        pr["text"] = text
                        pr["extraction_method"] = "pymupdf_unknown"
                        pr["char_count"] = len(text.strip())

                    # Stage 5: Language detection per page
                    pr["language"], pr["script"] = detect_page_language(pr.get("text", ""))

                    # Stage 7: Quality validation
                    validation = validate_page_quality(pr)
                    pr["quality_score"] = validation["quality_score"]
                    pr["quality_issues"] = validation["issues"]

                    pr["processing_time_ms"] = (time.time() - t0) * 1000
                    if time.time() - doc_start_loop > 300:
                        logger.warning(f"Document timeout after 300s at page {i+1}/{len(doc)}")
                        break
                    self.metrics.page_processing_times.append(pr["processing_time_ms"])
                    self.metrics.total_chars_extracted += pr.get("char_count", 0)

                    # Count page classes
                    if page_class == "native_text":
                        self.metrics.pages_native += 1
                    elif page_class == "scanned_image":
                        self.metrics.pages_scanned += 1
                    elif page_class == "ocr_overlay":
                        self.metrics.pages_ocr_overlay += 1
                    elif page_class == "hybrid":
                        self.metrics.pages_mixed += 1
                    elif page_class == "blank":
                        self.metrics.pages_blank += 1

                    result.pages_processed += 1
                    all_text_parts.append(pr["text"])

                except Exception as e:
                    pr["error"] = str(e)
                    pr["text"] = ""
                    result.pages_failed += 1
                    self.metrics.pages_failed += 1

                result.page_results.append(pr)

            doc.close()

            # Aggregate
            result.full_text = "\n\n".join(all_text_parts)
            if ocr_count > 0:
                result.overall_ocr_confidence = total_ocr_conf / ocr_count

            # Stage 6: Metadata extraction
            doc_info = {
                "sha256": sha256,
                "total_pages": result.total_pages,
                "document_class": result.document_class,
            }
            result.metadata = extract_metadata(filepath, doc_info)

            # Quality score
            page_scores = [pr.get("quality_score", 0) for pr in result.page_results if pr.get("quality_score") is not None]
            result.quality_score = sum(page_scores) / max(1, len(page_scores))

            # Stage 8: Write to Knowledge Lake
            result.bronze_path = write_bronze(asdict(result) if hasattr(result, '__dataclass_fields__') else {
                "document_id": result.document_id,
                "filename": result.filename,
                "page_results": result.page_results,
                "sha256": result.sha256,
                "total_pages": result.total_pages,
                "document_class": result.document_class,
            }, self.output_dir)
            result.silver_path = write_silver({
                "filename": result.filename,
                "page_results": result.page_results,
                "language": result.language,
                "total_pages": result.total_pages,
                "document_class": result.document_class,
                "sha256": result.sha256,
                "metadata": result.metadata,
            }, self.output_dir)

        except Exception as e:
            result.error = str(e)
            result.pages_failed += 1
            self.metrics.documents_failed += 1
            self.metrics.errors.append({"file": filepath.name, "error": str(e)})
            logger.error(f"Pipeline failed for {filepath.name}: {e}")

        result.processing_time_sec = time.time() - doc_start
        self.metrics.documents_processed += 1
        self.metrics.total_pages += result.total_pages

        return result

    def run_validation(self, samples: list[dict]) -> dict:
        """Run the pipeline on a validation set and return metrics."""
        self.metrics.start_time = time.time()
        
        for i, sample in enumerate(samples):
            fp = Path(sample["filepath"])
            logger.info(f"[{i+1}/{len(samples)}] Processing: {sample['filename']}")
            result = self.process_document(fp)
            self.results.append(result)
            
            if (i + 1) % 10 == 0:
                logger.info(f"  Processed {i+1}/{len(samples)} documents")

        self.metrics.end_time = time.time()
        
        elapsed = self.metrics.end_time - self.metrics.start_time
        self.metrics.avg_processing_time_sec = elapsed / max(1, len(samples))
        
        if self.metrics.page_processing_times:
            self.metrics.avg_ocr_confidence = sum(
                r.overall_ocr_confidence for r in self.results if r.overall_ocr_confidence > 0
            ) / max(1, sum(1 for r in self.results if r.overall_ocr_confidence > 0))

        return self.get_report()

    def get_report(self) -> dict:
        """Generate comprehensive pipeline metrics report."""
        elapsed = self.metrics.end_time - self.metrics.start_time
        total_pages = max(1, self.metrics.total_pages)
        pages_with_text = sum(
            pr.get("char_count", 0) > 0
            for r in self.results
            for pr in r.page_results
        )

        report = {
            "pipeline_name": PIPELINE_NAME,
            "pipeline_version": PIPELINE_VERSION,
            "validation_timestamp": datetime.now(timezone.utc).isoformat(),
            "processing_time_sec": round(elapsed, 1),
            "pages_per_minute": round(total_pages / max(0.01, elapsed / 60), 1),
            "documents": {
                "processed": self.metrics.documents_processed,
                "failed": self.metrics.documents_failed,
                "failure_rate_pct": round(
                    self.metrics.documents_failed / max(1, self.metrics.documents_processed) * 100, 1
                ),
            },
            "pages": {
                "total": total_pages,
                "native": self.metrics.pages_native,
                "scanned": self.metrics.pages_scanned,
                "ocr_overlay": self.metrics.pages_ocr_overlay,
                "mixed": self.metrics.pages_mixed,
                "blank": self.metrics.pages_blank,
                "failed": self.metrics.pages_failed,
                "with_text": pages_with_text,
                "text_success_rate_pct": round(pages_with_text / total_pages * 100, 1),
            },
            "extraction": {
                "total_chars": self.metrics.total_chars_extracted,
                "avg_chars_per_page": round(self.metrics.total_chars_extracted / total_pages, 0),
                "avg_ocr_confidence": round(self.metrics.avg_ocr_confidence, 3),
            },
            "performance": {
                "avg_page_time_ms": round(
                    sum(self.metrics.page_processing_times) / max(1, len(self.metrics.page_processing_times)), 0
                ),
                "total_ocr_time_sec": round(self.metrics.total_extraction_time_sec, 1),
            },
            "quality": {
                "avg_quality_score": round(
                    sum(r.quality_score for r in self.results) / max(1, len(self.results)), 1
                ),
                "documents_above_80": sum(1 for r in self.results if r.quality_score >= 80),
                "documents_below_50": sum(1 for r in self.results if r.quality_score < 50),
            },
            "knowledge_lake": {
                "bronze_files": sum(1 for r in self.results if r.bronze_path),
                "silver_files": sum(1 for r in self.results if r.silver_path),
            },
            "errors": self.metrics.errors,
        }

        # GO / NO-GO
        failure_rate = report["documents"]["failure_rate_pct"]
        text_rate = report["pages"]["text_success_rate_pct"]
        quality_avg = report["quality"]["avg_quality_score"]

        blockers = []
        if failure_rate > 10:
            blockers.append(f"Document failure rate {failure_rate}% exceeds 10% threshold")
        if text_rate < 80:
            blockers.append(f"Text success rate {text_rate}% below 80% threshold")

        report["go_nogo"] = {
            "recommendation": "GO" if not blockers else "NO-GO",
            "blockers": blockers,
            "thresholds": {
                "max_failure_rate": "10%",
                "min_text_success_rate": "80%",
                "min_avg_quality_score": "50",
            },
        }

        return report
