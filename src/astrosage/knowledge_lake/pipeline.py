"""
Knowledge Lake Pipeline — Phase 2 Orchestrator.

Processes every document through:
  raw → bronze (extract text, classify, detect language, route OCR)
  bronze → silver (generate markdown, structured docs, metadata, document graph)

Produces:
  - manifest.csv + manifest.parquet
  - Classification reports
  - Language detection reports
  - Duplicate detection reports
  - OCR routing decisions
  - Knowledge Registry entries
  - Provenance graph
  - Knowledge Catalog
"""
from __future__ import annotations

import csv
import json
import logging
import os
import time
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from ..classifier.classifier import classify_document, ClassificationResult
from ..classifier.classifier import classify_batch
from ..language.detector import detect_language_from_file, LanguageDetectionResult
from ..ocr_router.router import route_document, get_routing_summary
from ..metadata.extractor import extract_metadata, DocumentMetadata
from ..duplicate_detection.detector import (
    detect_sha256_duplicates,
    detect_simhash_duplicates,
    DuplicateReport,
)
from ..registry.registry import KnowledgeRegistry, book_id
from ..provenance.graph import ProvenanceGraph
from ..versioning.versions import VersionRegistry, PipelineRun, DATASET_VERSION

logger = logging.getLogger(__name__)


class KnowledgeLakePipeline:
    """
    Orchestrates the Phase 2 pipeline.
    
    Input:  knowledge/raw/source_library/ (751 raw files)
    Output: knowledge/bronze/ + knowledge/silver/ + reports
    """
    
    def __init__(
        self,
        base_dir: str = ".",
    ):
        self.base_dir = Path(base_dir)
        self.raw_dir = self.base_dir / "knowledge" / "raw" / "source_library"
        self.bronze_dir = self.base_dir / "knowledge" / "bronze"
        self.silver_dir = self.base_dir / "knowledge" / "silver"
        self.reports_dir = self.base_dir / "knowledge" / "reports"
        self.logs_dir = self.base_dir / "knowledge" / "logs"
        
        # Ensure directories exist
        for d in [self.bronze_dir, self.silver_dir, self.reports_dir, self.logs_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        # Initialize subsystems
        self.registry = KnowledgeRegistry()
        self.provenance = ProvenanceGraph()
        self.version_registry = VersionRegistry(str(self.logs_dir))
        
        # Pipeline state
        self._classifications: list[ClassificationResult] = []
        self._languages: list[LanguageDetectionResult] = []
        self._metadata: list[DocumentMetadata] = []
        self._routing_decisions = []
        self._file_paths: list[Path] = []
    
    def run(self) -> dict:
        """Execute the complete Phase 2 pipeline."""
        start_time = time.time()
        run_id = f"phase2_{int(start_time)}"
        
        logger.info("=" * 70)
        logger.info("KNOWLEDGE LAKE PIPELINE — PHASE 2")
        logger.info("=" * 70)
        
        run = PipelineRun(
            run_id=run_id,
            pipeline_name="knowledge_lake_phase2",
            pipeline_version="0.1.0",
        )
        
        # ── Step 1: Discover files ──
        logger.info("STEP 1: Discovering files in raw/source_library...")
        self._file_paths = self._discover_files()
        run.input_count = len(self._file_paths)
        logger.info(f"  Found {len(self._file_paths)} files")
        
        # ── Step 2: Classify documents ──
        logger.info("STEP 2: Classifying documents...")
        self._classifications = classify_batch(self._file_paths)
        
        # ── Step 3: Detect languages ──
        logger.info("STEP 3: Detecting languages...")
        self._detect_languages()
        
        # ── Step 4: Extract metadata ──
        logger.info("STEP 4: Extracting metadata...")
        self._extract_all_metadata()
        
        # ── Step 5: Register books ──
        logger.info("STEP 5: Registering books in Knowledge Registry...")
        self._register_books()
        
        # ── Step 6: OCR routing ──
        logger.info("STEP 6: Determining OCR routing...")
        self._route_ocr()
        
        # ── Step 7: Duplicate detection ──
        logger.info("STEP 7: Detecting duplicates...")
        self._detect_duplicates()
        
        # ── Step 8: Extract text (bronze layer) ──
        logger.info("STEP 8: Extracting text to bronze layer...")
        extracted_count = self._extract_text_bronze()
        
        # ── Step 9: Generate markdown (silver layer) ──
        logger.info("STEP 9: Generating markdown for silver layer...")
        markdown_count = self._generate_markdown_silver()
        
        # ── Step 10: Save all outputs ──
        logger.info("STEP 10: Saving manifest, reports, and catalog...")
        self._save_manifest()
        self._save_reports()
        self._save_catalog()
        self._save_provenance()
        
        # ── Complete ──
        elapsed = time.time() - start_time
        run.output_count = len(self._metadata)
        run.complete(success=True)
        self.version_registry.record_run(run)
        self.version_registry.save_version_manifest()
        
        summary = {
            "pipeline": "knowledge_lake_phase2",
            "version": "0.1.0",
            "dataset_version": DATASET_VERSION,
            "elapsed_seconds": round(elapsed, 1),
            "files_discovered": len(self._file_paths),
            "classified": len(self._classifications),
            "languages_detected": len(self._languages),
            "metadata_extracted": len(self._metadata),
            "books_registered": len(self.registry.books),
            "text_extracted": extracted_count,
            "markdown_generated": markdown_count,
        }
        
        logger.info("=" * 70)
        logger.info("PHASE 2 PIPELINE COMPLETE")
        logger.info(f"  Files: {summary['files_discovered']}")
        logger.info(f"  Metadata: {summary['metadata_extracted']}")
        logger.info(f"  Books registered: {summary['books_registered']}")
        logger.info(f"  Text extracted: {summary['text_extracted']}")
        logger.info(f"  Markdown generated: {summary['markdown_generated']}")
        logger.info(f"  Elapsed: {elapsed:.1f}s")
        logger.info("=" * 70)
        
        return summary
    
    def _discover_files(self) -> list[Path]:
        """Discover all processable files in the raw layer."""
        extensions = {
            ".pdf", ".docx", ".doc", ".epub", ".txt", ".md",
            ".jpg", ".jpeg", ".png", ".gif", ".tiff",
            ".mp3", ".mp4", ".zip",
        }
        files = []
        for ext in extensions:
            files.extend(self.raw_dir.rglob(f"*{ext}"))
            files.extend(self.raw_dir.rglob(f"*{ext.upper()}"))
        return sorted(set(files))
    
    def _detect_languages(self):
        """Detect language for all files."""
        self._languages = []
        for i, fp in enumerate(self._file_paths):
            if (i + 1) % 100 == 0:
                logger.info(f"  Language detection: {i+1}/{len(self._file_paths)}")
            try:
                result = detect_language_from_file(fp)
                self._languages.append(result)
            except Exception as e:
                logger.warning(f"  Language detection failed for {fp.name}: {e}")
                self._languages.append(LanguageDetectionResult(
                    filename=fp.name,
                    primary_language="unknown",
                    primary_script="unknown",
                    confidence=0.0,
                    is_multilingual=False,
                    detected_languages=[],
                    detected_scripts=[],
                    script_ratios={},
                    source="error",
                ))
    
    def _extract_all_metadata(self):
        """Extract metadata for all files."""
        self._metadata = []
        for i, (fp, cls, lang) in enumerate(
            zip(self._file_paths, self._classifications, self._languages)
        ):
            if (i + 1) % 100 == 0:
                logger.info(f"  Metadata extraction: {i+1}/{len(self._file_paths)}")
            try:
                meta = extract_metadata(
                    fp,
                    classification=cls,
                    language_result=lang,
                )
                self._metadata.append(meta)
            except Exception as e:
                logger.warning(f"  Metadata extraction failed for {fp.name}: {e}")
                self._metadata.append(DocumentMetadata(
                    original_filename=fp.name,
                    relative_path=str(fp),
                    extension=fp.suffix.lower(),
                    file_size_bytes=fp.stat().st_size,
                    notes=f"Metadata extraction failed: {e}",
                ))
    
    def _register_books(self):
        """Register all documents in the Knowledge Registry."""
        for meta in self._metadata:
            bid = self.registry.register_book(
                meta.sha256,
                {
                    "filename": meta.original_filename,
                    "path": meta.relative_path,
                    "language": meta.language,
                    "title": meta.title,
                }
            )
            meta.uuid = bid
    
    def _route_ocr(self):
        """Determine OCR routing for all documents."""
        self._routing_decisions = []
        for cls, lang in zip(self._classifications, self._languages):
            try:
                decision = route_document(cls, lang)
                self._routing_decisions.append(decision)
            except Exception as e:
                from ..ocr_router.router import OCRDecision, ExtractionRoute
                self._routing_decisions.append(OCRDecision(
                    route=ExtractionRoute.UNSUPPORTED,
                    reason=str(e),
                    needs_ocr=False,
                    ocr_engine="none",
                    ocr_pages=[],
                    text_pages=[],
                    confidence=0.0,
                ))
    
    def _detect_duplicates(self):
        """Run duplicate detection."""
        report = DuplicateReport(total_files=len(self._file_paths))
        
        # SHA256 duplicates
        report.sha256_groups = detect_sha256_duplicates(self._file_paths)
        report.unique_sha256 = len(self._file_paths) - report.sha256_duplicate_count
        
        # Save duplicate report
        dup_data = {
            "total_files": report.total_files,
            "unique_sha256": report.unique_sha256,
            "sha256_duplicate_groups": len(report.sha256_groups),
            "sha256_duplicate_files": report.sha256_duplicate_count,
            "groups": [
                {
                    "sha256": g.files[0]["sha256"][:32],
                    "file_count": len(g.files),
                    "files": [f["path"] for f in g.files],
                }
                for g in report.sha256_groups
            ],
        }
        
        dup_file = self.reports_dir / "duplicates.json"
        with open(dup_file, "w", encoding="utf-8") as f:
            json.dump(dup_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"  SHA256 duplicates: {report.sha256_duplicate_count} files in {len(report.sha256_groups)} groups")
    
    def _extract_text_bronze(self) -> int:
        """Extract text from PDFs to the bronze layer."""
        extracted = 0
        for i, (fp, cls, decision) in enumerate(
            zip(self._file_paths, self._classifications, self._routing_decisions)
        ):
            if not cls.is_pdf:
                continue
            
            if decision.route.value in ("direct_text", "ocr_hybrid"):
                try:
                    import pymupdf
                    doc = pymupdf.open(str(fp))
                    text_parts = []
                    for page_num in range(len(doc)):
                        page = doc[page_num]
                        text = page.get_text()
                        if text.strip():
                            text_parts.append(text)
                    doc.close()
                    
                    if text_parts:
                        # Save to bronze
                        rel_path = fp.relative_to(self.raw_dir)
                        out_path = self.bronze_dir / "extracted_text" / str(rel_path).replace(fp.suffix, ".txt")
                        out_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        with open(out_path, "w", encoding="utf-8") as f:
                            f.write("\n\n".join(text_parts))
                        
                        extracted += 1
                        
                        # Record provenance
                        if i < len(self._metadata):
                            meta = self._metadata[i]
                            source_node = self.provenance.add_source(
                                meta.uuid, str(fp)
                            )
                            self.provenance.add_extraction(
                                meta.uuid, source_node,
                                str(fp), str(out_path),
                                "pymupdf", "0.1.0",
                                metadata={"pages": len(text_parts)},
                            )
                except Exception as e:
                    logger.warning(f"  Text extraction failed for {fp.name}: {e}")
            
            if (i + 1) % 50 == 0:
                logger.info(f"  Bronze extraction: {i+1}/{len(self._file_paths)}, {extracted} extracted")
        
        return extracted
    
    def _generate_markdown_silver(self) -> int:
        """Generate markdown files in the silver layer from extracted text."""
        generated = 0
        bronze_text_dir = self.bronze_dir / "extracted_text"
        
        for txt_file in sorted(bronze_text_dir.rglob("*.txt")):
            try:
                text = txt_file.read_text(encoding="utf-8", errors="replace")
                
                # Convert to markdown (basic formatting)
                md_content = self._text_to_markdown(text, txt_file.stem)
                
                # Save to silver
                rel_path = txt_file.relative_to(bronze_text_dir)
                out_path = self.silver_dir / "markdown" / str(rel_path).replace(".txt", ".md")
                out_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(md_content)
                
                generated += 1
            except Exception as e:
                logger.warning(f"  Markdown generation failed for {txt_file.name}: {e}")
        
        return generated
    
    def _text_to_markdown(self, text: str, title: str) -> str:
        """Convert extracted text to clean markdown."""
        lines = text.split("\n")
        md_lines = []
        
        # Add title
        md_lines.append(f"# {title}\n")
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                md_lines.append("")
                continue
            
            # Detect potential headers (lines that are short, uppercase, or end with :)
            if len(stripped) < 80 and (
                stripped.isupper() or
                stripped.endswith(":") or
                (stripped[0].isdigit() and "." in stripped[:5])
            ):
                md_lines.append(f"\n## {stripped}\n")
            else:
                md_lines.append(stripped)
        
        return "\n".join(md_lines)
    
    def _save_manifest(self):
        """Save the knowledge manifest as CSV and Parquet."""
        # CSV
        csv_path = self.reports_dir / "manifest.csv"
        fieldnames = [
            "uuid", "sha256", "original_filename", "relative_path",
            "mime_type", "extension", "file_size_bytes", "page_count",
            "language", "script", "ocr_required", "native_pdf", "mixed_pdf",
            "author", "publisher", "edition", "title", "subject",
            "import_timestamp", "processing_status", "pipeline_version",
            "metadata_confidence", "extraction_method", "notes",
        ]
        
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for meta in self._metadata:
                row = meta.to_dict()
                # Convert tags to string
                row["tags"] = ",".join(row.get("tags", []))
                writer.writerow(row)
        
        logger.info(f"  Manifest CSV saved: {csv_path} ({len(self._metadata)} records)")
        
        # Try Parquet
        try:
            import pandas as pd
            records = [meta.to_dict() for meta in self._metadata]
            df = pd.DataFrame(records)
            parquet_path = self.reports_dir / "manifest.parquet"
            df.to_parquet(parquet_path, index=False)
            logger.info(f"  Manifest Parquet saved: {parquet_path}")
        except ImportError:
            logger.info("  Parquet export skipped (pandas/pyarrow not installed)")
        except Exception as e:
            logger.warning(f"  Parquet export failed: {e}")
    
    def _save_reports(self):
        """Generate and save all classification and language reports."""
        
        # Classification report
        type_counts = {}
        pdf_type_counts = {}
        ocr_needed = 0
        for cls in self._classifications:
            type_counts[cls.file_type] = type_counts.get(cls.file_type, 0) + 1
            if cls.is_pdf:
                pdf_type_counts[cls.pdf_type] = pdf_type_counts.get(cls.pdf_type, 0) + 1
            if cls.ocr_required:
                ocr_needed += 1
        
        classification_report = {
            "total_files": len(self._classifications),
            "by_type": type_counts,
            "pdf_analysis": pdf_type_counts,
            "ocr_required_count": ocr_needed,
            "invalid_files": sum(1 for c in self._classifications if not c.is_valid),
        }
        
        with open(self.reports_dir / "classification_report.json", "w") as f:
            json.dump(classification_report, f, indent=2)
        
        # Language report
        lang_counts = {}
        script_counts = {}
        multilingual_count = 0
        for lang in self._languages:
            lang_counts[lang.primary_language] = lang_counts.get(lang.primary_language, 0) + 1
            script_counts[lang.primary_script] = script_counts.get(lang.primary_script, 0) + 1
            if lang.is_multilingual:
                multilingual_count += 1
        
        language_report = {
            "total_files": len(self._languages),
            "by_language": lang_counts,
            "by_script": script_counts,
            "multilingual_count": multilingual_count,
            "average_confidence": sum(l.confidence for l in self._languages) / max(1, len(self._languages)),
        }
        
        with open(self.reports_dir / "language_report.json", "w") as f:
            json.dump(language_report, f, indent=2)
        
        # OCR routing report
        routing_summary = get_routing_summary(self._routing_decisions)
        
        with open(self.reports_dir / "ocr_routing_report.json", "w") as f:
            json.dump(routing_summary, f, indent=2)
        
        # Registry summary
        with open(self.reports_dir / "registry_summary.json", "w") as f:
            json.dump(self.registry.summary(), f, indent=2)
        
        logger.info(f"  Reports saved to {self.reports_dir}")
    
    def _save_catalog(self):
        """Generate the Knowledge Catalog."""
        catalog = {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "dataset_version": DATASET_VERSION,
            "total_documents": len(self._metadata),
            "subjects": {},
            "languages": {},
            "media_types": {},
            "processing_status": {},
            "duplicate_groups": 0,
            "missing_metadata": [],
            "pipeline_status": self.version_registry.get_all_versions(),
        }
        
        for meta in self._metadata:
            # By language
            lang = meta.language or "unknown"
            catalog["languages"][lang] = catalog["languages"].get(lang, 0) + 1
            
            # By media type
            mt = meta.extension or "unknown"
            catalog["media_types"][mt] = catalog["media_types"].get(mt, 0) + 1
            
            # By processing status
            status = meta.processing_status or "pending"
            catalog["processing_status"][status] = catalog["processing_status"].get(status, 0) + 1
            
            # Missing metadata
            missing = []
            if not meta.title or meta.title == meta.original_filename:
                missing.append("title")
            if not meta.author:
                missing.append("author")
            if not meta.language or meta.language == "unknown":
                missing.append("language")
            if missing:
                catalog["missing_metadata"].append({
                    "filename": meta.original_filename,
                    "missing_fields": missing,
                })
        
        # Subject extraction from folder paths
        subjects = {}
        for meta in self._metadata:
            parts = Path(meta.relative_path).parts
            if len(parts) > 1:
                subject = parts[-2] if parts[-1] == meta.original_filename else parts[-3] if len(parts) > 2 else "root"
                subjects[subject] = subjects.get(subject, 0) + 1
        catalog["subjects"] = dict(sorted(subjects.items(), key=lambda x: -x[1]))
        
        with open(self.reports_dir / "knowledge_catalog.json", "w", encoding="utf-8") as f:
            json.dump(catalog, f, indent=2, ensure_ascii=False)
        
        logger.info(f"  Knowledge Catalog saved")
    
    def _save_provenance(self):
        """Save the provenance graph."""
        provenance_path = self.reports_dir / "provenance_graph.json"
        self.provenance.save(provenance_path)
        logger.info(f"  Provenance graph saved: {self.provenance.summary()}")
