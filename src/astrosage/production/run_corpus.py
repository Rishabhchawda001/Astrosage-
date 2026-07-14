"""
Production Corpus Processor — Phase 4

Processes the entire corpus with:
- Resume support (skip already-processed documents)
- Checkpoint saves (periodic progress persistence)
- Crash recovery (resume from last checkpoint)
- Quality gates (quarantine low-quality outputs)
- Provenance tracking (SHA256 → UUID chain)
- Incremental processing (process new documents only)

Usage:
    python -m src.astrosage.production.run_corpus --base-dir .
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import sys
import time
import traceback
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

PIPELINE_VERSION = "1.0.0"
PIPELINE_NAME = "Document Intelligence v1.0"
CHECKPOINT_INTERVAL = 5  # Save checkpoint every N documents
MAX_PAGE_TIME_SEC = 30  # Per-page timeout
MAX_DOC_TIME_SEC = 600  # Per-document timeout (10 min)
OCR_DPI = 150
MAX_OCR_PAGES = 100  # Max pages to OCR per document (production limit)


def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


class CorpusProcessor:
    """Production corpus processor with resume and checkpoint support."""

    def __init__(self, base_dir: str = "."):
        self.base = Path(base_dir)
        self.raw_dir = self.base / "knowledge" / "raw" / "source_library"
        self.bronze_dir = self.base / "knowledge" / "bronze" / "extracted_text"
        self.silver_dir = self.base / "knowledge" / "silver" / "structured_documents"
        self.quarantine_dir = self.base / "knowledge" / "quarantine"
        self.checkpoint_dir = self.base / "knowledge" / "checkpoints"
        self.reports_dir = self.base / "knowledge" / "reports"

        for d in [self.bronze_dir, self.silver_dir, self.quarantine_dir,
                  self.checkpoint_dir, self.reports_dir / "production"]:
            d.mkdir(parents=True, exist_ok=True)

        self.checkpoint_file = self.checkpoint_dir / "corpus_checkpoint.json"
        self.progress_file = self.reports_dir / "production" / "processing_progress.json"
        self.metrics_file = self.reports_dir / "production" / "corpus_metrics.json"

    def load_checkpoint(self) -> dict:
        """Load last checkpoint for resume."""
        if self.checkpoint_file.exists():
            try:
                return json.loads(self.checkpoint_file.read_text())
            except Exception:
                pass
        return {"processed": [], "failed": [], "quarantined": [], "last_index": 0, "start_time": None}

    def save_checkpoint(self, state: dict):
        """Save checkpoint for crash recovery."""
        state["checkpoint_time"] = datetime.now(timezone.utc).isoformat()
        self.checkpoint_file.write_text(json.dumps(state, indent=2, ensure_ascii=False))

    def get_all_pdfs(self) -> list[Path]:
        """Discover all PDFs in source library."""
        return sorted(self.raw_dir.rglob("*.pdf"))

    def is_processed(self, filepath: Path, state: dict) -> bool:
        """Check if document was already processed."""
        stem = filepath.stem
        # Check bronze output exists and is non-empty
        bronze_file = self.bronze_dir / f"{stem}.txt"
        if bronze_file.exists() and bronze_file.stat().st_size > 10:
            return True
        # Check quarantine
        quar_file = self.quarantine_dir / f"{stem}.json"
        if quar_file.exists():
            return True
        # Check checkpoint
        if filepath.name in state.get("processed", []):
            return True
        return False

    def process_single_document(self, filepath: Path) -> dict:
        """Process a single document through the complete pipeline."""
        from astrosage.forensics.page_classifier import classify_page
        import pymupdf
        import pytesseract
        from PIL import Image
        import io

        doc_start = time.time()
        sha256 = compute_sha256(filepath)
        doc_id = f"DOC-{sha256[:12].upper()}"

        result = {
            "document_id": doc_id,
            "filename": filepath.name,
            "sha256": sha256,
            "file_size": filepath.stat().st_size,
            "status": "processing",
            "page_count": 0,
            "pages_native": 0,
            "pages_scanned": 0,
            "pages_ocr": 0,
            "pages_blank": 0,
            "pages_failed": 0,
            "total_chars": 0,
            "ocr_confidence": 0.0,
            "quality_score": 100.0,
            "errors": [],
            "processing_time_sec": 0.0,
        }

        try:
            doc = pymupdf.open(str(filepath))
            result["page_count"] = len(doc)

            all_text = []
            ocr_conf_sum = 0.0
            ocr_count = 0
            quality_issues = []

            # Classify all pages
            page_classes = []
            classify_start = time.time()
            for i in range(len(doc)):
                if time.time() - classify_start > 120:
                    page_classes.extend(["unknown"] * (len(doc) - i))
                    break
                try:
                    signals = classify_page(doc[i], i + 1)
                    page_classes.append(signals.page_class)
                except Exception:
                    page_classes.append("unknown")

            class_counts = Counter(page_classes)
            most_common = class_counts.most_common(1)[0] if class_counts else ("unknown", 0)

            # Document language detection
            sample_text = ""
            for i in range(min(3, len(doc))):
                sample_text += doc[i].get_text("text")
            doc_lang, doc_script = self._detect_language(sample_text)

            # Process each page
            ocr_pages_done = 0
            doc_loop_start = time.time()

            for i in range(len(doc)):
                if time.time() - doc_loop_start > MAX_DOC_TIME_SEC:
                    result["errors"].append(f"Document timeout at page {i+1}")
                    break

                page = doc[i]
                page_class = page_classes[i] if i < len(page_classes) else "unknown"
                page_text = ""

                try:
                    t0 = time.time()

                    if page_class == "native_text":
                        page_text = page.get_text("text")
                        result["pages_native"] += 1

                    elif page_class in ("scanned_image", "ocr_overlay"):
                        if ocr_pages_done < MAX_OCR_PAGES:
                            page_text = self._ocr_page(page, doc_lang)
                            conf = self._ocr_confidence(page_text)
                            ocr_conf_sum += conf
                            ocr_count += 1
                            result["pages_ocr"] += 1
                            ocr_pages_done += 1
                        else:
                            result["pages_failed"] += 1

                    elif page_class == "hybrid":
                        page_text = page.get_text("text")
                        if len(page_text.strip()) < 50 and ocr_pages_done < MAX_OCR_PAGES:
                            page_text = self._ocr_page(page, doc_lang)
                            conf = self._ocr_confidence(page_text)
                            ocr_conf_sum += conf
                            ocr_count += 1
                            ocr_pages_done += 1
                        result["pages_native"] += 1

                    elif page_class == "blank":
                        result["pages_blank"] += 1
                        page_text = ""

                    else:
                        page_text = page.get_text("text")
                        result["pages_native"] += 1

                    # Unicode check
                    if "\ufffd" in page_text:
                        quality_issues.append(f"broken_unicode_page_{i+1}")
                        result["quality_score"] -= 1

                    result["total_chars"] += len(page_text.strip())
                    all_text.append(page_text)

                except Exception as e:
                    result["pages_failed"] += 1
                    result["errors"].append(f"Page {i+1}: {str(e)[:100]}")

            doc.close()

            # Aggregate
            if ocr_count > 0:
                result["ocr_confidence"] = round(ocr_conf_sum / ocr_count, 3)

            # Metadata
            result["language"] = doc_lang
            result["script"] = doc_script
            result["document_class"] = most_common[0]
            result["quality_issues"] = quality_issues

            # Write bronze
            bronze_path = self.bronze_dir / f"{filepath.stem}.txt"
            bronze_content = ""
            for idx, text in enumerate(all_text):
                if text.strip():
                    bronze_content += f"\n\n=== PAGE {idx + 1} ===\n\n{text.strip()}"
            bronze_path.write_text(bronze_content.strip(), encoding="utf-8")
            result["bronze_path"] = str(bronze_path.relative_to(self.base))

            # Write silver (structured Markdown)
            silver_path = self.silver_dir / f"{filepath.stem}.md"
            silver_lines = [
                f"# {filepath.stem}",
                "",
                f"**Document ID:** {doc_id}",
                f"**Language:** {doc_lang} ({doc_script})",
                f"**Pages:** {result['page_count']}",
                f"**Class:** {most_common[0]}",
                f"**SHA256:** `{sha256}`",
                f"**Pipeline:** {PIPELINE_NAME}",
                "",
                "---",
                "",
            ]
            for idx, text in enumerate(all_text):
                if text.strip():
                    silver_lines.append(f"## Page {idx + 1}")
                    silver_lines.append("")
                    silver_lines.append(text.strip())
                    silver_lines.append("")
            silver_path.write_text("\n".join(silver_lines), encoding="utf-8")
            result["silver_path"] = str(silver_path.relative_to(self.base))

            # Quality gate
            if result["quality_score"] < 30 or result["pages_failed"] > result["page_count"] * 0.5:
                result["status"] = "quarantined"
                quarantine_path = self.quarantine_dir / f"{filepath.stem}.json"
                quarantine_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                result["status"] = "complete"

        except Exception as e:
            result["status"] = "failed"
            result["errors"].append(f"Document-level: {str(e)[:200]}")
            # Write to quarantine
            quarantine_path = self.quarantine_dir / f"{filepath.stem}.json"
            quarantine_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))

        result["processing_time_sec"] = round(time.time() - doc_start, 2)
        return result

    def _ocr_page(self, page, lang_hint: str = "eng") -> str:
        """OCR a single page using Tesseract."""
        import pytesseract
        from PIL import Image
        import io

        pix = page.get_pixmap(dpi=OCR_DPI)
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))

        lang_map = {
            "english": "eng", "hindi": "hin", "sanskrit": "san",
            "devanagari": "hin", "latin": "eng", "mixed": "hin+eng",
        }
        tesseract_lang = lang_map.get(lang_hint, "eng")

        try:
            text = pytesseract.image_to_string(img, lang=tesseract_lang)
            return text
        except Exception:
            return pytesseract.image_to_string(img, lang="eng")

    def _ocr_confidence(self, text: str) -> float:
        """Estimate OCR confidence from output quality."""
        if not text.strip():
            return 0.0
        # Heuristic: longer text with proper word boundaries = higher confidence
        words = text.split()
        if len(words) < 3:
            return 0.3
        avg_word_len = sum(len(w) for w in words) / len(words)
        if avg_word_len > 3:
            return 0.85
        return 0.6

    def _detect_language(self, text: str) -> tuple[str, str]:
        """Detect language and script."""
        if not text.strip():
            return "unknown", "unknown"
        dev_count = sum(1 for ch in text if 0x0900 <= ord(ch) <= 0x097F)
        lat_count = sum(1 for ch in text if 0x0020 <= ord(ch) <= 0x007E)
        total = len(text.strip())
        if total == 0:
            return "unknown", "unknown"
        dev_pct = dev_count / total
        lat_pct = lat_count / total
        if dev_pct > 0.3:
            return "hindi", "devanagari"
        elif lat_pct > 0.5:
            return "english", "latin"
        return "mixed", "mixed"

    def run(self, resume: bool = True) -> dict:
        """Run the complete corpus processor."""
        start_time = time.time()
        state = self.load_checkpoint() if resume else {"processed": [], "failed": [], "quarantined": [], "last_index": 0}
        state["start_time"] = datetime.now(timezone.utc).isoformat()

        all_pdfs = self.get_all_pdfs()
        total = len(all_pdfs)
        logger.info(f"Found {total} PDFs in source library")

        # Skip already processed
        to_process = []
        for fp in all_pdfs:
            if not self.is_processed(fp, state):
                to_process.append(fp)

        logger.info(f"Already processed: {total - len(to_process)}, Remaining: {len(to_process)}")

        results = []
        processed_count = 0
        failed_count = 0
        quarantined_count = 0

        for idx, fp in enumerate(to_process):
            logger.info(f"[{idx + 1}/{len(to_process)}] Processing: {fp.name}")

            try:
                result = self.process_single_document(fp)
                results.append(result)

                if result["status"] == "complete":
                    state["processed"].append(fp.name)
                    processed_count += 1
                elif result["status"] == "quarantined":
                    state["quarantined"].append(fp.name)
                    quarantined_count += 1
                else:
                    state["failed"].append(fp.name)
                    failed_count += 1

            except Exception as e:
                logger.error(f"Failed: {fp.name}: {e}")
                state["failed"].append(fp.name)
                failed_count += 1

            # Checkpoint every N documents
            if (idx + 1) % CHECKPOINT_INTERVAL == 0:
                state["last_index"] = idx + 1
                self.save_checkpoint(state)
                logger.info(f"  Checkpoint saved: {processed_count} processed, {failed_count} failed, {quarantined_count} quarantined")

        # Final checkpoint
        state["last_index"] = len(to_process)
        state["end_time"] = datetime.now(timezone.utc).isoformat()
        self.save_checkpoint(state)

        elapsed = time.time() - start_time

        # Generate metrics
        metrics = {
            "pipeline_version": PIPELINE_VERSION,
            "start_time": state["start_time"],
            "end_time": datetime.now(timezone.utc).isoformat(),
            "total_pdfs": total,
            "already_processed": total - len(to_process),
            "newly_processed": processed_count,
            "failed": failed_count,
            "quarantined": quarantined_count,
            "processing_time_sec": round(elapsed, 1),
            "pages_per_minute": round(
                sum(r.get("page_count", 0) for r in results) / max(0.01, elapsed / 60), 1
            ),
            "total_pages": sum(r.get("page_count", 0) for r in results),
            "total_chars": sum(r.get("total_chars", 0) for r in results),
            "by_status": {
                "complete": processed_count,
                "failed": failed_count,
                "quarantined": quarantined_count,
            },
            "errors_summary": Counter(r.get("errors", [""])[0][:50] for r in results if r.get("errors")),
        }

        self.metrics_file.write_text(json.dumps(metrics, indent=2, ensure_ascii=False, default=str))
        logger.info(f"Corpus processing complete: {processed_count} processed, {failed_count} failed, {quarantined_count} quarantined")
        logger.info(f"Time: {elapsed:.0f}s, Pages: {metrics['total_pages']}, Chars: {metrics['total_chars']}")

        return metrics
