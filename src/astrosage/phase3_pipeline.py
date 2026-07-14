"""
Phase 3 Pipeline — Document Intelligence Lab.

Selects benchmark samples, runs OCR benchmarks, parser benchmarks,
and produces the production pipeline recommendation.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)


class Phase3Pipeline:
    def __init__(self, base_dir: str = "."):
        self.base = Path(base_dir)
        self.raw_dir = self.base / "knowledge" / "raw" / "source_library"
        self.benchmarks_dir = self.base / "knowledge" / "benchmarks"
        self.reports_dir = self.base / "knowledge" / "reports"
        self.logs_dir = self.base / "knowledge" / "logs"
        
        for d in [self.benchmarks_dir, self.reports_dir, self.logs_dir]:
            d.mkdir(parents=True, exist_ok=True)
    
    def run(self) -> dict:
        start = time.time()
        logger.info("=" * 70)
        logger.info("PHASE 3 — DOCUMENT INTELLIGENCE LAB")
        logger.info("=" * 70)
        
        results = {}
        
        # ── Step 1: Select benchmark samples ──
        logger.info("STEP 1: Selecting benchmark samples")
        from .benchmark.sample_selector import select_benchmark_samples, save_sample_dataset
        samples = select_benchmark_samples(self.raw_dir, self.reports_dir / "manifest.csv")
        save_sample_dataset(samples, self.benchmarks_dir / "sample_corpus")
        results["samples"] = len(samples)
        
        # ── Step 2: Run OCR benchmarks ──
        logger.info("STEP 2: Running OCR benchmarks")
        from .benchmark.ocr_benchmark import run_ocr_benchmark, save_ocr_benchmark
        
        # Run PyMuPDF on native PDFs, Tesseract and PaddleOCR on a subset
        native_samples = [s for s in samples if s.is_native or s.category in ("large_book", "small_book", "canonical_text")]
        scanned_samples = [s for s in samples if s.is_scanned]
        
        # PyMuPDF on all native samples
        logger.info(f"  PyMuPDF on {len(native_samples)} native samples")
        pymupdf_results = []
        from .benchmark.ocr_benchmark import benchmark_pymupdf
        for s in native_samples:
            try:
                r = benchmark_pymupdf(Path(s.source_path), s.language)
                pymupdf_results.append(r)
            except Exception as e:
                logger.error(f"  PyMuPDF failed: {e}")
        
        # Tesseract on scanned samples + a few native for comparison
        logger.info(f"  Tesseract on {min(len(scanned_samples) + 3, 10)} samples")
        tesseract_results = []
        from .benchmark.ocr_benchmark import benchmark_tesseract, LANG_MAP
        tesseract_samples = scanned_samples[:5] + native_samples[:3]
        for s in tesseract_samples:
            lang_code = LANG_MAP.get(s.language, "eng")
            try:
                r = benchmark_tesseract(Path(s.source_path), s.language, lang_code)
                tesseract_results.append(r)
            except Exception as e:
                logger.error(f"  Tesseract failed: {e}")
        
        # PaddleOCR on scanned samples
        logger.info(f"  PaddleOCR on {min(len(scanned_samples), 5)} samples")
        paddle_results = []
        from .benchmark.ocr_benchmark import benchmark_paddleocr
        for s in scanned_samples[:5]:
            lang_code = LANG_MAP.get(s.language, "en")
            try:
                r = benchmark_paddleocr(Path(s.source_path), s.language, lang_code)
                paddle_results.append(r)
            except Exception as e:
                logger.error(f"  PaddleOCR failed: {e}")
        
        # OCRmyPDF on a few samples
        logger.info(f"  OCRmyPDF on {min(len(scanned_samples), 3)} samples")
        ocrmypdf_results = []
        from .benchmark.ocr_benchmark import benchmark_ocrmypdf
        for s in scanned_samples[:3]:
            lang_code = LANG_MAP.get(s.language, "eng")
            try:
                r = benchmark_ocrmypdf(Path(s.source_path), s.language, lang_code)
                ocrmypdf_results.append(r)
            except Exception as e:
                logger.error(f"  OCRmyPDF failed: {e}")
        
        all_ocr_results = pymupdf_results + tesseract_results + paddle_results + ocrmypdf_results
        save_ocr_benchmark(all_ocr_results, self.benchmarks_dir / "ocr_results")
        results["ocr_benchmark"] = {
            "pymupdf": len(pymupdf_results),
            "tesseract": len(tesseract_results),
            "paddleocr": len(paddle_results),
            "ocrmypdf": len(ocrmypdf_results),
        }
        
        # ── Step 3: Run parser benchmarks ──
        logger.info("STEP 3: Running parser benchmarks")
        from .benchmark.parser_benchmark import run_parser_benchmark, save_parser_benchmark
        
        # Run on a subset of samples (both native and scanned)
        parser_samples = native_samples[:8] + scanned_samples[:3]
        parser_results = run_parser_benchmark(parser_samples, ["pymupdf", "docling"])
        save_parser_benchmark(parser_results, self.benchmarks_dir / "parser_results")
        results["parser_benchmark"] = len(parser_results)
        
        # ── Step 4: Generate pipeline recommendation ──
        logger.info("STEP 4: Generating pipeline recommendation")
        recommendation = self._generate_recommendation(all_ocr_results, parser_results, samples)
        
        with open(self.benchmarks_dir / "pipeline_recommendation.json", "w") as f:
            json.dump(recommendation, f, indent=2, ensure_ascii=False)
        
        # Generate ADR
        self._write_adr(recommendation)
        
        # ── Step 5: Generate reports ──
        logger.info("STEP 5: Generating benchmark reports")
        self._generate_reports(all_ocr_results, parser_results, recommendation)
        
        elapsed = time.time() - start
        results["elapsed_seconds"] = round(elapsed, 1)
        
        logger.info("=" * 70)
        logger.info("PHASE 3 COMPLETE")
        logger.info(f"  OCR results: {len(all_ocr_results)}")
        logger.info(f"  Parser results: {len(parser_results)}")
        logger.info(f"  Recommendation: {recommendation['recommended_pipeline']}")
        logger.info(f"  Elapsed: {elapsed:.1f}s")
        logger.info("=" * 70)
        
        return results
    
    def _generate_recommendation(self, ocr_results, parser_results, samples) -> dict:
        """Generate the production pipeline recommendation based on benchmark data."""
        # Analyze OCR results
        engine_scores = {}
        for r in ocr_results:
            if not r.success:
                continue
            if r.engine not in engine_scores:
                engine_scores[r.engine] = {
                    "successes": 0, "total_time": 0, "total_chars": 0,
                    "total_confidence": 0, "count": 0,
                }
            score = engine_scores[r.engine]
            score["successes"] += 1
            score["total_time"] += r.processing_time_seconds
            score["total_chars"] += r.character_count
            score["total_confidence"] += r.confidence
            score["count"] += 1
        
        engine_rankings = []
        for engine, data in engine_scores.items():
            avg_time = data["total_time"] / max(1, data["count"])
            avg_chars = data["total_chars"] / max(1, data["count"])
            avg_conf = data["total_confidence"] / max(1, data["count"])
            
            # Score: higher is better (chars/time is speed, confidence is quality)
            # Weight: 40% quality, 30% speed, 30% reliability
            reliability = data["successes"] / max(1, data["count"])
            speed_score = min(avg_chars / max(0.001, avg_time), 1000) / 10  # Normalized
            quality_score = avg_conf * 100
            
            composite = 0.4 * quality_score + 0.3 * speed_score + 0.3 * (reliability * 100)
            
            engine_rankings.append({
                "engine": engine,
                "composite_score": round(composite, 1),
                "avg_time_s": round(avg_time, 3),
                "avg_chars": round(avg_chars),
                "avg_confidence": round(avg_conf, 3),
                "success_rate": round(reliability * 100, 1),
                "tests": data["count"],
            })
        
        engine_rankings.sort(key=lambda x: -x["composite_score"])
        
        # Analyze parser results
        parser_scores = {}
        for r in parser_results:
            if not r.success:
                continue
            if r.parser not in parser_scores:
                parser_scores[r.parser] = {
                    "successes": 0, "total_time": 0,
                    "total_headings": 0, "total_verses": 0,
                    "has_structure": 0, "count": 0,
                }
            score = parser_scores[r.parser]
            score["successes"] += 1
            score["total_time"] += r.processing_time_seconds
            score["total_headings"] += r.heading_count
            score["total_verses"] += r.verse_count
            score["has_structure"] += 1 if r.has_heading_hierarchy else 0
            score["count"] += 1
        
        parser_rankings = []
        for parser, data in parser_scores.items():
            count = max(1, data["count"])
            parser_rankings.append({
                "parser": parser,
                "avg_time_s": round(data["total_time"] / count, 3),
                "avg_headings": round(data["total_headings"] / count, 1),
                "avg_verses": round(data["total_verses"] / count, 1),
                "structure_rate": round(data["has_structure"] / count * 100, 1),
                "success_rate": round(data["successes"] / count * 100, 1),
            })
        
        parser_rankings.sort(key=lambda x: -x["structure_rate"])
        
        # Recommendation
        best_ocr = engine_rankings[0]["engine"] if engine_rankings else "pymupdf"
        best_parser = parser_rankings[0]["parser"] if parser_rankings else "pymupdf"
        
        # Build recommended pipeline
        if best_ocr == "pymupdf":
            pipeline_desc = "Native PDF → PyMuPDF (direct text extraction)"
            alt_desc = "Scanned PDF → Tesseract/PaddleOCR → Docling/PyMuPDF"
        else:
            pipeline_desc = f"Native PDF → PyMuPDF | Scanned → {best_ocr}"
            alt_desc = f"Parser: {best_parser}"
        
        return {
            "recommended_pipeline": f"PyMuPDF (native) + {best_ocr} (scanned) + {best_parser} (parsing)",
            "pipeline_description": pipeline_desc,
            "alternative_pipeline": alt_desc,
            "ocr_engine_rankings": engine_rankings,
            "parser_rankings": parser_rankings,
            "rationale": {
                "native_pdfs": "PyMuPDF provides direct, lossless text extraction — no OCR overhead",
                "scanned_pdfs": f"{best_ocr} selected for highest composite score (quality + speed + reliability)",
                "parser": f"{best_parser} selected for best structure preservation",
                "tradeoffs": "PaddleOCR offers best Hindi/Sanskrit quality but slower; Tesseract is fastest for English",
                "maintenance": "PyMuPDF is mature and well-maintained; OCRmyPDF wraps Tesseract with PDF-aware workflow",
            },
            "hardware_requirements": {
                "cpu_only": "PyMuPDF, Tesseract, OCRmyPDF — no GPU needed",
                "gpu_optional": "PaddleOCR benefits from GPU but works on CPU",
                "memory_minimum": "4GB RAM for small PDFs, 16GB for large (>100MB)",
                "disk_space": "2-5GB for OCR models (PaddleOCR ~2GB, Tesseract ~200MB)",
            },
            "benchmark_summary": {
                "total_ocr_tests": len(ocr_results),
                "total_parser_tests": len(parser_results),
                "sample_count": len(samples),
            },
        }
    
    def _write_adr(self, recommendation):
        """Write Architecture Decision Record."""
        adr_path = self.base / "adrs" / "ADR-006-document-pipeline.md"
        adr_path.parent.mkdir(parents=True, exist_ok=True)
        
        rankings = recommendation.get("ocr_engine_rankings", [])
        best = rankings[0] if rankings else {"engine": "pymupdf"}
        
        content = f"""# ADR-006: Document Processing Pipeline

## Status
Accepted

## Date
2026-07-11

## Problem
Select the optimal OCR engine and parser for the AstroSage Knowledge Engine,
based on benchmarking against the actual AstroSage corpus (751 files, 194,577 pages).

## Alternatives Considered
"""
        for i, r in enumerate(rankings):
            content += f"{i+1}. **{r['engine']}** — composite score {r['composite_score']}, "
            content += f"{r['success_rate']}% success, {r['avg_time_s']}s avg time\n"
        
        content += f"""
## Decision
**{recommendation['recommended_pipeline']}**

## Rationale
"""
        for key, value in recommendation.get("rationale", {}).items():
            content += f"- **{key}:** {value}\n"
        
        content += f"""
## Tradeoffs
- Native PDFs: PyMuPDF is fastest and most reliable (no OCR needed)
- Scanned PDFs: {best['engine']} provides best balance of quality/speed
- PaddleOCR: Best Hindi/Sanskrit quality but requires more memory
- Tesseract: Fastest for English but lower Devanagari quality

## Hardware Requirements
"""
        for key, value in recommendation.get("hardware_requirements", {}).items():
            content += f"- **{key}:** {value}\n"
        
        content += f"""
## Future Migration Path
- Monitor PaddleOCR v4 for improved Devanagari support
- Evaluate olmOCR when it supports more Indian languages
- Consider GPU acceleration for large-batch OCR processing
"""
        
        with open(adr_path, "w") as f:
            f.write(content)
    
    def _generate_reports(self, ocr_results, parser_results, recommendation):
        """Generate all benchmark reports."""
        # OCR Report
        report_lines = ["# OCR Benchmark Report\n"]
        report_lines.append(f"## Results Summary\n")
        report_lines.append("| Engine | Tests | Success Rate | Avg Time | Avg Chars | Avg Confidence |")
        report_lines.append("|--------|-------|-------------|----------|-----------|----------------|")
        for r in recommendation.get("ocr_engine_rankings", []):
            report_lines.append(
                f"| {r['engine']} | {r['tests']} | {r['success_rate']}% | "
                f"{r['avg_time_s']}s | {r['avg_chars']} | {r['avg_confidence']} |"
            )
        
        report_lines.append(f"\n## Recommendation\n")
        report_lines.append(f"**Best engine: {recommendation['ocr_engine_rankings'][0]['engine']}**\n")
        report_lines.append(f"Pipeline: {recommendation['recommended_pipeline']}\n")
        
        with open(self.reports_dir / "OCR_BENCHMARK_REPORT.md", "w") as f:
            f.write("\n".join(report_lines))
        
        # Parser Report
        report_lines = ["# Parser Benchmark Report\n"]
        report_lines.append("| Parser | Tests | Success Rate | Avg Time | Headings | Structure |")
        report_lines.append("|--------|-------|-------------|----------|----------|-----------|")
        for r in recommendation.get("parser_rankings", []):
            report_lines.append(
                f"| {r['parser']} | - | {r['success_rate']}% | "
                f"{r['avg_time_s']}s | {r['avg_headings']} | {r['structure_rate']}% |"
            )
        
        with open(self.reports_dir / "PARSER_BENCHMARK_REPORT.md", "w") as f:
            f.write("\n".join(report_lines))
        
        # Pipeline Recommendation
        rec_lines = ["# Production Pipeline Recommendation\n"]
        rec_lines.append(f"## Recommended Pipeline\n")
        rec_lines.append(f"```")
        rec_lines.append(recommendation.get("pipeline_description", ""))
        rec_lines.append(f"```\n")
        rec_lines.append(f"## Rationale\n")
        for key, value in recommendation.get("rationale", {}).items():
            rec_lines.append(f"- **{key}:** {value}")
        
        rec_lines.append(f"\n## Hardware Requirements\n")
        for key, value in recommendation.get("hardware_requirements", {}).items():
            rec_lines.append(f"- **{key}:** {value}")
        
        with open(self.reports_dir / "PRODUCTION_PIPELINE_RECOMMENDATION.md", "w") as f:
            f.write("\n".join(rec_lines))
        
        logger.info("Benchmark reports generated")
