"""
Phase 2.5 Pipeline — Corpus Intelligence & Quality Analysis.

Runs all analysis engines on the Knowledge Lake:
  1. Corpus Intelligence Report
  2. Document Quality Scoring
  3. Metadata Validation
  4. OCR Benchmark Dataset
  5. Semantic Corpus Analysis
  6. Golden Evaluation Dataset
  7. Search Baseline Benchmark
  8. Corpus Health Dashboard
  9. Knowledge Catalog Enhancement
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)


class Phase25Pipeline:
    def __init__(self, base_dir: str = "."):
        self.base = Path(base_dir)
        self.raw_dir = self.base / "knowledge" / "raw" / "source_library"
        self.bronze_dir = self.base / "knowledge" / "bronze"
        self.reports_dir = self.base / "knowledge" / "reports"
        self.logs_dir = self.base / "knowledge" / "logs"
        self.benchmarks_dir = self.base / "knowledge" / "benchmarks"
        
        for d in [self.reports_dir, self.logs_dir, self.benchmarks_dir]:
            d.mkdir(parents=True, exist_ok=True)
    
    def run(self) -> dict:
        start = time.time()
        logger.info("=" * 70)
        logger.info("PHASE 2.5 — CORPUS INTELLIGENCE & QUALITY ANALYSIS")
        logger.info("=" * 70)
        
        results = {}
        
        # ── 1. Corpus Intelligence ──
        logger.info("STEP 1: Corpus Intelligence Report")
        from .corpus_intel.analyzer import analyze_corpus, save_corpus_profile
        profile = analyze_corpus(self.raw_dir, self.reports_dir / "manifest.csv")
        save_corpus_profile(profile, self.reports_dir)
        results["corpus_intelligence"] = {
            "total_files": profile.total_files,
            "total_size_gb": round(profile.total_size_bytes / 1048576 / 1024, 1),
            "total_pages": profile.total_pages,
            "native_pdfs": profile.native_pdf_count,
            "scanned_pdfs": profile.scanned_pdf_count,
            "languages": profile.by_language,
        }
        
        # ── 2. Document Quality Scoring ──
        logger.info("STEP 2: Document Quality Scoring")
        from .quality_scoring.scorer import score_batch, save_quality_scores
        files = sorted([f for f in self.raw_dir.rglob("*") if f.is_file()])
        scores = score_batch(files, self.reports_dir / "manifest.csv")
        save_quality_scores(scores, self.reports_dir)
        results["quality_scoring"] = {
            "total_scored": len(scores),
            "average_score": round(sum(s.overall_score for s in scores) / max(1, len(scores)), 1),
            "needs_ocr": sum(1 for s in scores if s.needs_ocr),
            "is_duplicate": sum(1 for s in scores if s.is_duplicate),
        }
        
        # ── 3. Metadata Validation ──
        logger.info("STEP 3: Metadata Validation")
        from .metadata_validation.validator import validate_manifest, save_validation_report
        manifest = self.reports_dir / "manifest.csv"
        if manifest.exists():
            val_report = validate_manifest(manifest)
            save_validation_report(val_report, self.reports_dir)
            results["metadata_validation"] = {
                "total": val_report.total_documents,
                "with_issues": val_report.documents_with_issues,
                "by_severity": val_report.issues_by_severity,
            }
        
        # ── 4. Semantic Corpus Analysis ──
        logger.info("STEP 4: Semantic Corpus Analysis")
        from .semantic_analysis.analyzer import analyze_corpus_semantics, save_semantic_profile
        text_dir = self.bronze_dir / "extracted_text"
        if text_dir.exists() and any(text_dir.rglob("*.txt")):
            semantic = analyze_corpus_semantics(text_dir)
            save_semantic_profile(semantic, self.reports_dir)
            results["semantic_analysis"] = {
                "entities_found": semantic.total_entities_found,
                "unique_terms": semantic.unique_terms,
                "scriptures": len(semantic.scriptures),
                "people": len(semantic.people),
                "concepts": len(semantic.concepts),
            }
        
        # ── 5. Golden Evaluation Dataset ──
        logger.info("STEP 5: Golden Evaluation Dataset")
        from .golden_eval.generator import generate_eval_questions, save_eval_dataset
        if text_dir.exists() and any(text_dir.rglob("*.txt")):
            questions = generate_eval_questions(text_dir, max_questions=1000)
            save_eval_dataset(questions, self.reports_dir)
            results["golden_eval"] = {
                "total_questions": len(questions),
            }
        
        # ── 6. Search Baseline ──
        logger.info("STEP 6: Search Baseline Benchmark")
        from .search_baseline.benchmark import BaselineSearchEngine, save_search_baseline
        engine = BaselineSearchEngine(self.raw_dir, self.reports_dir / "manifest.csv")
        engine.build_index()
        
        benchmark_queries = [
            "Bhagavad Gita",
            "Ayurveda medicine",
            "Sanskrit grammar",
            "Vedic astrology",
            "yoga meditation",
            "Rigveda hymns",
            "Chanakya niti",
            "Hanuman chalisa",
            "Brahma Sutras",
            "Ramayana",
            "purana stories",
            "tantra mantra",
            "vedic mathematics",
            "Sushruta surgery",
            "Kundalini yoga",
        ]
        benchmarks = engine.benchmark_queries(benchmark_queries)
        save_search_baseline(benchmarks, self.benchmarks_dir)
        results["search_baseline"] = {
            "queries_tested": len(benchmark_queries),
        }
        
        # ── 7. Corpus Health Dashboard ──
        logger.info("STEP 7: Corpus Health Dashboard")
        dashboard = self._build_dashboard(profile, scores, results)
        with open(self.reports_dir / "corpus_health_dashboard.json", "w") as f:
            json.dump(dashboard, f, indent=2, ensure_ascii=False)
        results["dashboard"] = "generated"
        
        # ── Complete ──
        elapsed = time.time() - start
        results["elapsed_seconds"] = round(elapsed, 1)
        
        logger.info("=" * 70)
        logger.info("PHASE 2.5 COMPLETE")
        logger.info(f"  Elapsed: {elapsed:.1f}s")
        logger.info("=" * 70)
        
        return results
    
    def _build_dashboard(self, profile, scores, results) -> dict:
        """Build the corpus health dashboard."""
        return {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "library": {
                "total_files": profile.total_files,
                "total_size_gb": round(profile.total_size_bytes / 1048576 / 1024, 1),
                "total_pages": profile.total_pages,
                "pdfs": {
                    "total": profile.pdf_count,
                    "native": profile.native_pdf_count,
                    "scanned": profile.scanned_pdf_count,
                    "mixed": profile.mixed_pdf_count,
                },
            },
            "processing": {
                "text_extracted": len(list((self.bronze_dir / "extracted_text").rglob("*.txt"))) if (self.bronze_dir / "extracted_text").exists() else 0,
                "pages_with_text": profile.pages_with_text,
                "pages_needing_ocr": profile.pages_needing_ocr,
            },
            "quality": {
                "average_score": results.get("quality_scoring", {}).get("average_score", 0),
                "needs_ocr": results.get("quality_scoring", {}).get("needs_ocr", 0),
                "duplicates": profile.duplicate_files,
            },
            "languages": profile.by_language,
            "scripts": profile.by_script,
            "subjects": dict(list(profile.by_subject.items())[:20]),
            "metadata_completeness": profile.metadata_completeness,
            "validation": results.get("metadata_validation", {}),
            "semantic": results.get("semantic_analysis", {}),
            "search_baseline": results.get("search_baseline", {}),
        }
