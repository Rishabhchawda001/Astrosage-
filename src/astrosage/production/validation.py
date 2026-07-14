"""
Phase 3.5 Validation Harness.

Runs the production pipeline on a representative corpus subset
and produces comprehensive metrics.
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
import traceback
from pathlib import Path
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ValidationHarness:
    def __init__(self, base_dir: str = "."):
        self.base = Path(base_dir)
        self.raw_dir = self.base / "knowledge" / "raw" / "source_library"
        self.forensics_dir = self.base / "knowledge" / "benchmarks" / "forensics"
        self.reports_dir = self.base / "knowledge" / "reports"
        self.benchmarks_dir = self.base / "knowledge" / "benchmarks"
        self.manifest_path = self.base / "knowledge" / "reports" / "manifest.csv"
        
        # Ensure output dirs exist
        for d in [self.reports_dir / "production", self.benchmarks_dir / "production",
                  self.base / "knowledge" / "bronze" / "extracted_text",
                  self.base / "knowledge" / "silver" / "structured_documents"]:
            d.mkdir(parents=True, exist_ok=True)

    def run(self, max_samples: int = 60) -> dict:
        """Run complete Phase 3.5 validation."""
        logger.info("=" * 70)
        logger.info("PHASE 3.5 — PRODUCTION PIPELINE VALIDATION")
        logger.info("=" * 70)

        # Step 1: Build validation corpus
        logger.info("STEP 1: Building representative validation corpus")
        from astrosage.production.sampler import build_validation_corpus
        
        samples, summary = build_validation_corpus(
            forensics_results_path=self.forensics_dir / "forensic_results.json",
            raw_dir=self.raw_dir,
            manifest_path=self.manifest_path,
            max_samples=max_samples,
        )
        logger.info(f"  Selected {len(samples)} documents ({summary['total_pages']} pages)")
        logger.info(f"  By class: {summary['by_class']}")
        logger.info(f"  By language: {summary['by_language']}")

        # Save corpus manifest
        corpus_manifest = {
            "summary": summary,
            "samples": [{"filename": s["filename"], "class": s["document_class"],
                        "language": s["language"], "pages": s["page_count"]} for s in samples],
        }
        (self.benchmarks_dir / "production" / "validation_corpus.json").write_text(
            json.dumps(corpus_manifest, indent=2, ensure_ascii=False)
        )

        # Step 2: Run production pipeline
        logger.info("STEP 2: Running production pipeline")
        from astrosage.production.pipeline import ProductionPipeline
        
        pipeline = ProductionPipeline(str(self.base))
        report = pipeline.run_validation(samples)

        # Save results
        results_data = []
        for r in pipeline.results:
            rd = asdict(r) if hasattr(r, '__dataclass_fields__') else r
            results_data.append(rd)
        
        (self.benchmarks_dir / "production" / "pipeline_results.json").write_text(
            json.dumps(results_data, indent=1, ensure_ascii=False, default=str)
        )
        (self.benchmarks_dir / "production" / "pipeline_report.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False, default=str)
        )

        # Step 3: Knowledge Lake validation
        logger.info("STEP 3: Validating Knowledge Lake")
        kl_report = self._validate_knowledge_lake(pipeline.results)
        report["knowledge_lake_validation"] = kl_report

        # Step 4: Provenance validation
        logger.info("STEP 4: Validating provenance")
        prov_report = self._validate_provenance(pipeline.results)
        report["provenance_validation"] = prov_report

        # Step 5: Output validation (Unicode, structure)
        logger.info("STEP 5: Validating output quality")
        output_report = self._validate_outputs(pipeline.results)
        report["output_validation"] = output_report

        # Step 6: Performance extrapolation
        logger.info("STEP 6: Extrapolating performance to full corpus")
        perf_report = self._extrapolate_performance(report)
        report["performance_extrapolation"] = perf_report

        # Step 7: Failure analysis
        logger.info("STEP 7: Analyzing failures")
        failure_report = self._analyze_failures(pipeline.results)
        report["failure_analysis"] = failure_report

        # Step 8: Final summary
        logger.info("STEP 8: Generating final report")
        (self.benchmarks_dir / "production" / "pipeline_report.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False, default=str)
        )
        
        self._write_production_report(report, summary)
        self._write_adr_008(report)

        logger.info("=" * 70)
        logger.info(f"GO/NO-GO: {report['go_nogo']['recommendation']}")
        if report['go_nogo']['blockers']:
            for b in report['go_nogo']['blockers']:
                logger.info(f"  BLOCKER: {b}")
        logger.info("=" * 70)

        return report

    def _validate_knowledge_lake(self, results) -> dict:
        """Verify bronze and silver layers are complete and consistent."""
        bronze_dir = self.base / "knowledge" / "bronze" / "extracted_text"
        silver_dir = self.base / "knowledge" / "silver" / "structured_documents"
        
        bronze_files = list(bronze_dir.glob("*.txt")) if bronze_dir.exists() else []
        silver_files = list(silver_dir.glob("*.md")) if silver_dir.exists() else []
        
        # Check for orphaned files
        processed_names = {r.filename.replace(".pdf", "") for r in results if not r.error}
        bronze_names = {f.stem for f in bronze_files}
        silver_names = {f.stem for f in silver_files}
        
        missing_bronze = processed_names - bronze_names
        missing_silver = processed_names - silver_names
        orphaned_bronze = bronze_names - processed_names
        
        # Check file sizes
        empty_bronze = [f for f in bronze_files if f.stat().st_size < 10]
        empty_silver = [f for f in silver_files if f.stat().st_size < 100]
        
        return {
            "bronze_files": len(bronze_files),
            "silver_files": len(silver_files),
            "missing_bronze": list(missing_bronze),
            "missing_silver": list(missing_silver),
            "orphaned_bronze": list(orphaned_bronze),
            "empty_bronze": len(empty_bronze),
            "empty_silver": len(empty_silver),
            "integrity": "PASS" if not missing_bronze and not missing_silver else "FAIL",
        }

    def _validate_provenance(self, results) -> dict:
        """Verify every artifact traces back to its source."""
        issues = []
        for r in results:
            if r.error:
                continue
            if not r.document_id:
                issues.append(f"{r.filename}: missing document_id")
            if not r.sha256:
                issues.append(f"{r.filename}: missing sha256")
            if not r.bronze_path:
                issues.append(f"{r.filename}: missing bronze output")
            if not r.silver_path:
                issues.append(f"{r.filename}: missing silver output")
            
            # Check page-level provenance
            for pr in r.page_results:
                if "page_number" not in pr:
                    issues.append(f"{r.filename}: page missing page_number")
                if "extraction_method" not in pr:
                    issues.append(f"{r.filename} p{pr.get('page_number')}: missing extraction_method")
        
        return {
            "total_artifacts": sum(len(r.page_results) + 2 for r in results if not r.error),
            "issues": issues,
            "issue_count": len(issues),
            "integrity": "PASS" if len(issues) == 0 else "FAIL",
        }

    def _validate_outputs(self, results) -> dict:
        """Validate output quality: Unicode, structure, headings, etc."""
        devanagari_ok = 0
        latin_ok = 0
        has_headings = 0
        has_page_markers = 0
        broken_unicode = 0
        total_with_text = 0

        for r in results:
            if r.error:
                continue
            for pr in r.page_results:
                text = pr.get("text", "")
                if not text.strip():
                    continue
                total_with_text += 1

                # Unicode check
                if "\ufffd" in text:
                    broken_unicode += 1

                # Script check
                dev_pct = sum(1 for ch in text if 0x0900 <= ord(ch) <= 0x097F) / max(1, len(text))
                lat_pct = sum(1 for ch in text if 0x0020 <= ord(ch) <= 0x007E) / max(1, len(text))

                if dev_pct > 0.3:
                    devanagari_ok += 1
                elif lat_pct > 0.5:
                    latin_ok += 1

                # Structure checks
                if pr.get("has_heading"):
                    has_headings += 1

        return {
            "pages_with_text": total_with_text,
            "devanagari_pages": devanagari_ok,
            "latin_pages": latin_ok,
            "pages_with_headings": has_headings,
            "broken_unicode_pages": broken_unicode,
            "unicode_integrity_pct": round((1 - broken_unicode / max(1, total_with_text)) * 100, 1),
        }

    def _extrapolate_performance(self, report: dict) -> dict:
        """Extrapolate performance to full 194,577-page corpus."""
        pages_done = report["pages"]["total"]
        elapsed = report["processing_time_sec"]
        total_corpus_pages = 194_577

        if pages_done == 0 or elapsed == 0:
            return {"error": "No data to extrapolate"}

        rate = pages_done / elapsed  # pages per second
        est_total_time = total_corpus_pages / rate

        avg_page_size = report["extraction"]["avg_chars_per_page"]
        est_total_chars = total_corpus_pages * avg_page_size

        return {
            "validation_pages": pages_done,
            "full_corpus_pages": total_corpus_pages,
            "pages_per_second": round(rate, 2),
            "estimated_total_time_sec": round(est_total_time, 0),
            "estimated_total_time_hours": round(est_total_time / 3600, 1),
            "estimated_total_chars": int(est_total_chars),
            "estimated_storage_mb": round(est_total_chars / (1024 * 1024), 0),
            "estimated_throughput_pages_min": round(rate * 60, 1),
        }

    def _analyze_failures(self, results) -> dict:
        """Analyze all failures and categorize them."""
        errors = []
        timeout_count = 0
        ocr_failures = 0
        extraction_failures = 0
        other_failures = 0

        for r in results:
            if r.error:
                errors.append({"file": r.filename, "error": r.error, "type": "document_level"})
                if "timeout" in r.error.lower():
                    timeout_count += 1
                elif "ocr" in r.error.lower():
                    ocr_failures += 1
                else:
                    other_failures += 1

            for pr in r.page_results:
                if pr.get("error"):
                    errors.append({
                        "file": r.filename,
                        "page": pr.get("page_number"),
                        "error": pr["error"],
                        "type": "page_level"
                    })
                    extraction_failures += 1

        return {
            "total_errors": len(errors),
            "document_level_errors": sum(1 for e in errors if e["type"] == "document_level"),
            "page_level_errors": sum(1 for e in errors if e["type"] == "page_level"),
            "timeout_count": timeout_count,
            "ocr_failures": ocr_failures,
            "extraction_failures": extraction_failures,
            "other_failures": other_failures,
            "error_details": errors[:50],
        }

    def _write_production_report(self, report: dict, corpus_summary: dict):
        """Write human-readable production report."""
        lines = [
            "# Phase 3.5 — Production Pipeline Validation Report",
            "",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}",
            f"**Pipeline:** {report['pipeline_name']} v{report['pipeline_version']}",
            f"**GO/NO-GO:** {'🟢 GO' if report['go_nogo']['recommendation'] == 'GO' else '🔴 NO-GO'}",
            "",
            "---",
            "",
            "## Validation Corpus",
            "",
            f"- **Documents:** {corpus_summary['total_selected']}",
            f"- **Total pages:** {corpus_summary['total_pages']}",
            f"- **By class:** {corpus_summary['by_class']}",
            f"- **By language:** {corpus_summary['by_language']}",
            "",
            "## Processing Results",
            "",
            f"- **Processing time:** {report['processing_time_sec']:.1f}s",
            f"- **Pages per minute:** {report['pages_per_minute']:.1f}",
            f"- **Documents processed:** {report['documents']['processed']}",
            f"- **Documents failed:** {report['documents']['failed']}",
            f"- **Failure rate:** {report['documents']['failure_rate_pct']}%",
            "",
            "## Page Statistics",
            "",
            f"| Class | Count |",
            f"|-------|-------|",
            f"| Native text | {report['pages']['native']} |",
            f"| Scanned | {report['pages']['scanned']} |",
            f"| OCR overlay | {report['pages']['ocr_overlay']} |",
            f"| Mixed | {report['pages']['mixed']} |",
            f"| Blank | {report['pages']['blank']} |",
            f"| Failed | {report['pages']['failed']} |",
            f"| **Total** | **{report['pages']['total']}** |",
            "",
            "## Quality",
            "",
            f"- **Text success rate:** {report['pages']['text_success_rate_pct']}%",
            f"- **Average quality score:** {report['quality']['avg_quality_score']}/100",
            f"- **Avg OCR confidence:** {report['extraction']['avg_ocr_confidence']:.1%}",
            f"- **Total characters extracted:** {report['extraction']['total_chars']:,}",
            "",
        ]

        # Performance extrapolation
        perf = report.get("performance_extrapolation", {})
        if perf and "estimated_total_time_hours" in perf:
            lines.extend([
                "## Performance Extrapolation (194,577 pages)",
                "",
                f"- **Estimated total time:** {perf['estimated_total_time_hours']} hours",
                f"- **Throughput:** {perf['estimated_throughput_pages_min']} pages/min",
                f"- **Estimated total chars:** {perf['estimated_total_chars']:,}",
                f"- **Estimated storage:** {perf['estimated_storage_mb']} MB",
                "",
            ])

        # Knowledge Lake validation
        kl = report.get("knowledge_lake_validation", {})
        lines.extend([
            "## Knowledge Lake Validation",
            "",
            f"- **Integrity:** {kl.get('integrity', 'N/A')}",
            f"- **Bronze files:** {kl.get('bronze_files', 0)}",
            f"- **Silver files:** {kl.get('silver_files', 0)}",
            f"- **Missing bronze:** {len(kl.get('missing_bronze', []))}",
            f"- **Missing silver:** {len(kl.get('missing_silver', []))}",
            f"- **Empty bronze:** {kl.get('empty_bronze', 0)}",
            "",
        ])

        # Provenance validation
        prov = report.get("provenance_validation", {})
        lines.extend([
            "## Provenance Validation",
            "",
            f"- **Integrity:** {prov.get('integrity', 'N/A')}",
            f"- **Total artifacts:** {prov.get('total_artifacts', 0)}",
            f"- **Issues:** {prov.get('issue_count', 0)}",
            "",
        ])

        # Output validation
        out = report.get("output_validation", {})
        lines.extend([
            "## Output Validation",
            "",
            f"- **Unicode integrity:** {out.get('unicode_integrity_pct', 0)}%",
            f"- **Broken Unicode pages:** {out.get('broken_unicode_pages', 0)}",
            f"- **Devanagari pages:** {out.get('devanagari_pages', 0)}",
            f"- **Latin pages:** {out.get('latin_pages', 0)}",
            f"- **Pages with headings:** {out.get('pages_with_headings', 0)}",
            "",
        ])

        # Failure analysis
        fa = report.get("failure_analysis", {})
        lines.extend([
            "## Failure Analysis",
            "",
            f"- **Total errors:** {fa.get('total_errors', 0)}",
            f"- **Document-level:** {fa.get('document_level_errors', 0)}",
            f"- **Page-level:** {fa.get('page_level_errors', 0)}",
            f"- **Timeouts:** {fa.get('timeout_count', 0)}",
            "",
        ])

        # GO/NO-GO
        gng = report["go_nogo"]
        lines.extend([
            "## GO / NO-GO Decision",
            "",
            f"### Recommendation: **{gng['recommendation']}**",
            "",
        ])
        if gng["blockers"]:
            lines.append("**Blockers:**")
            for b in gng["blockers"]:
                lines.append(f"- {b}")
        else:
            lines.append("No blockers identified. The production pipeline is ready for full-corpus execution.")

        lines.extend([
            "",
            "---",
            f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}*",
        ])

        (self.reports_dir / "production" / "PRODUCTION_VALIDATION_REPORT.md").write_text(
            "\n".join(lines)
        )

    def _write_adr_008(self, report: dict):
        """Write ADR-008 for architecture lock."""
        adr = f"""# ADR-008: Production Pipeline Architecture Lock

## Status
**{report['go_nogo']['recommendation']}**

## Date
{datetime.now().strftime('%Y-%m-%d')}

## Problem
Certify the production document pipeline is stable enough for full-corpus (194,577 page) processing.

## Evidence
- Validated on {report['documents']['processed']} documents ({report['pages']['total']} pages)
- Text success rate: {report['pages']['text_success_rate_pct']}%
- Failure rate: {report['documents']['failure_rate_pct']}%
- Average quality score: {report['quality']['avg_quality_score']}/100
- Unicode integrity: {report.get('output_validation', {}).get('unicode_integrity_pct', 'N/A')}%

## Architecture Lock

The following components are frozen as **Document Intelligence v1.0**:

| Component | Version | Status |
|-----------|---------|--------|
| Document Classifier | v1.0 | LOCKED |
| OCR Routing | v1.0 | LOCKED |
| Text Extraction (PyMuPDF) | v1.0 | LOCKED |
| OCR Engine (Tesseract) | v1.0 | LOCKED |
| Language Detection | v1.0 | LOCKED |
| Metadata Extraction | v1.0 | LOCKED |
| Quality Validation | v1.0 | LOCKED |
| Knowledge Lake Schema | v1.0 | LOCKED |
| Provenance Model | v1.0 | LOCKED |

## Change Policy
Future changes to any locked component require:
1. Updated benchmarks
2. Regression testing
3. Updated ADR
4. Explicit approval

## Tradeoffs
- Locked architecture may miss newer/better tools
- Mitigated by modular design — individual components can be swapped behind the same interfaces
"""
        (self.base / "adrs" / "ADR-008-production-pipeline-lock.md").write_text(adr)
