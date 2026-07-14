"""
OCR Benchmark Engine.

Evaluates every available OCR engine against the benchmark corpus.
Produces quantitative metrics for engine selection.
"""
from __future__ import annotations

import json
import logging
import os
import re
import tempfile
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    engine: str
    filename: str
    language: str
    extracted_text: str = ""
    character_count: int = 0
    word_count: int = 0
    page_count: int = 0
    processing_time_seconds: float = 0.0
    success: bool = True
    error: str = ""
    confidence: float = 0.0
    
    # Quality metrics (when gold standard available)
    character_accuracy: float = 0.0
    word_accuracy: float = 0.0
    
    # Feature preservation
    has_verses: bool = False
    has_tables: bool = False
    has_footnotes: bool = False


def benchmark_pymupdf(filepath: Path, language: str = "unknown") -> OCRResult:
    """Benchmark PyMuPDF text extraction (native PDFs only)."""
    start = time.time()
    result = OCRResult(engine="pymupdf", filename=filepath.name, language=language)
    
    try:
        import pymupdf
        doc = pymupdf.open(str(filepath))
        result.page_count = len(doc)
        
        texts = []
        for i in range(len(doc)):
            page = doc[i]
            text = page.get_text()
            texts.append(text)
        
        doc.close()
        
        full_text = "\n\n".join(texts)
        result.extracted_text = full_text
        result.character_count = len(full_text)
        result.word_count = len(full_text.split())
        result.confidence = 1.0  # Direct extraction, no OCR confidence
        result.success = True
        
        # Check for verse markers
        result.has_verses = bool(re.search(r"॥|।|\|\|", full_text))
        
    except Exception as e:
        result.success = False
        result.error = str(e)
    
    result.processing_time_seconds = round(time.time() - start, 3)
    return result


def benchmark_tesseract(
    filepath: Path,
    language: str = "unknown",
    lang_code: str = "eng",
) -> OCRResult:
    """Benchmark Tesseract OCR."""
    start = time.time()
    result = OCRResult(engine="tesseract", filename=filepath.name, language=language)
    
    try:
        import pytesseract
        from PIL import Image
        import pymupdf
        
        doc = pymupdf.open(str(filepath))
        result.page_count = len(doc)
        
        texts = []
        confidences = []
        
        for i in range(min(len(doc), 20)):  # Sample up to 20 pages
            page = doc[i]
            pix = page.get_pixmap(dpi=200)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Get text with confidence
            data = pytesseract.image_to_data(img, lang=lang_code, output_type=pytesseract.Output.DICT)
            text = pytesseract.image_to_string(img, lang=lang_code)
            texts.append(text)
            
            # Calculate average confidence
            confs = [int(c) for c in data["conf"] if isinstance(c, (int, float)) and int(c) > 0]
            if confs:
                confidences.append(sum(confs) / len(confs))
        
        doc.close()
        
        full_text = "\n\n".join(texts)
        result.extracted_text = full_text
        result.character_count = len(full_text)
        result.word_count = len(full_text.split())
        result.confidence = sum(confidences) / max(1, len(confidences)) / 100.0
        result.success = True
        result.has_verses = bool(re.search(r"॥|।|\|\|", full_text))
        
    except Exception as e:
        result.success = False
        result.error = str(e)
    
    result.processing_time_seconds = round(time.time() - start, 3)
    return result


def benchmark_ocrmypdf(filepath: Path, language: str = "unknown", lang_code: str = "eng") -> OCRResult:
    """Benchmark OCRmyPDF."""
    start = time.time()
    result = OCRResult(engine="ocrmypdf", filename=filepath.name, language=language)
    
    try:
        import ocrmypdf
        import pymupdf
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Run OCRmyPDF
            ocrmypdf.ocr(
                str(filepath), tmp_path,
                language=lang_code,
                force_ocr=True,
                skip_text=True,
                output_type=ocrmypdf.OutputType.PDF,
                progress_bar=False,
            )
            
            # Extract text from OCR'd PDF
            doc = pymupdf.open(tmp_path)
            result.page_count = len(doc)
            
            texts = []
            for i in range(min(len(doc), 20)):
                texts.append(doc[i].get_text())
            doc.close()
            
            full_text = "\n\n".join(texts)
            result.extracted_text = full_text
            result.character_count = len(full_text)
            result.word_count = len(full_text.split())
            result.confidence = 0.8  # OCRmyPDF doesn't expose per-page confidence easily
            result.success = True
            
        finally:
            os.unlink(tmp_path)
        
    except Exception as e:
        result.success = False
        result.error = str(e)
    
    result.processing_time_seconds = round(time.time() - start, 3)
    return result


def benchmark_paddleocr(filepath: Path, language: str = "unknown", lang_code: str = "en") -> OCRResult:
    """Benchmark PaddleOCR."""
    start = time.time()
    result = OCRResult(engine="paddleocr", filename=filepath.name, language=language)
    
    try:
        from paddleocr import PaddleOCR
        import pymupdf
        
        ocr = PaddleOCR(use_angle_cls=True, lang=lang_code, show_log=False)
        
        doc = pymupdf.open(str(filepath))
        result.page_count = len(doc)
        
        texts = []
        confidences = []
        
        for i in range(min(len(doc), 20)):
            page = doc[i]
            pix = page.get_pixmap(dpi=200)
            
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                pix.save(tmp.name)
                tmp_path = tmp.name
            
            try:
                page_result = ocr.ocr(tmp_path, cls=True)
                if page_result and page_result[0]:
                    page_texts = []
                    page_confs = []
                    for line in page_result[0]:
                        if line[1]:
                            page_texts.append(line[1][0])
                            page_confs.append(line[1][1])
                    texts.append("\n".join(page_texts))
                    if page_confs:
                        confidences.append(sum(page_confs) / len(page_confs))
            finally:
                os.unlink(tmp_path)
        
        doc.close()
        
        full_text = "\n\n".join(texts)
        result.extracted_text = full_text
        result.character_count = len(full_text)
        result.word_count = len(full_text.split())
        result.confidence = sum(confidences) / max(1, len(confidences))
        result.success = True
        result.has_verses = bool(re.search(r"॥|।|\|\|", full_text))
        
    except Exception as e:
        result.success = False
        result.error = str(e)
    
    result.processing_time_seconds = round(time.time() - start, 3)
    return result


# Language code mapping
LANG_MAP = {
    "english": "eng",
    "hindi": "hin",
    "sanskrit": "san",
    "hindi/sanskrit": "hin",
}


def run_ocr_benchmark(
    samples: list,
    engines: Optional[list[str]] = None,
) -> list[OCRResult]:
    """Run OCR benchmark on all samples with all engines."""
    if engines is None:
        engines = ["pymupdf", "tesseract", "paddleocr", "ocrmypdf"]
    
    engine_fns = {
        "pymupdf": benchmark_pymupdf,
        "tesseract": benchmark_tesseract,
        "paddleocr": benchmark_paddleocr,
        "ocrmypdf": benchmark_ocrmypdf,
    }
    
    results = []
    
    for sample in samples:
        filepath = Path(sample.source_path)
        lang = sample.language
        lang_code = LANG_MAP.get(lang, "eng")
        
        # Only run OCR engines on scanned PDFs
        # Run PyMuPDF on native PDFs
        for engine_name in engines:
            if engine_name == "pymupdf" and sample.is_scanned:
                continue  # Skip PyMuPDF for scanned PDFs
            if engine_name != "pymupdf" and sample.is_native and not sample.is_scanned:
                continue  # Skip OCR for native PDFs (PyMuPDF is sufficient)
            
            fn = engine_fns.get(engine_name)
            if fn:
                logger.info(f"  Benchmarking {engine_name} on {sample.filename} ({lang})")
                try:
                    if engine_name == "pymupdf":
                        result = fn(filepath, lang)
                    else:
                        result = fn(filepath, lang, lang_code)
                    results.append(result)
                except Exception as e:
                    logger.error(f"  {engine_name} failed on {sample.filename}: {e}")
                    results.append(OCRResult(
                        engine=engine_name, filename=sample.filename,
                        language=lang, success=False, error=str(e),
                    ))
    
    return results


def save_ocr_benchmark(results: list[OCRResult], output_dir: Path):
    """Save OCR benchmark results."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save detailed results
    with open(output_dir / "ocr_benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in results], f, indent=2, ensure_ascii=False)
    
    # Generate summary
    by_engine = {}
    for r in results:
        if r.engine not in by_engine:
            by_engine[r.engine] = {"results": [], "successes": 0, "failures": 0}
        by_engine[r.engine]["results"].append(r)
        if r.success:
            by_engine[r.engine]["successes"] += 1
        else:
            by_engine[r.engine]["failures"] += 1
    
    summary = {}
    for engine, data in by_engine.items():
        successful = [r for r in data["results"] if r.success]
        if successful:
            avg_time = sum(r.processing_time_seconds for r in successful) / len(successful)
            avg_chars = sum(r.character_count for r in successful) / len(successful)
            avg_confidence = sum(r.confidence for r in successful) / len(successful)
            avg_words = sum(r.word_count for r in successful) / len(successful)
        else:
            avg_time = avg_chars = avg_confidence = avg_words = 0
        
        summary[engine] = {
            "total_tests": len(data["results"]),
            "successes": data["successes"],
            "failures": data["failures"],
            "success_rate": round(data["successes"] / max(1, len(data["results"])) * 100, 1),
            "avg_processing_time_s": round(avg_time, 3),
            "avg_characters_extracted": round(avg_chars),
            "avg_words_extracted": round(avg_words),
            "avg_confidence": round(avg_confidence, 3),
        }
    
    with open(output_dir / "ocr_benchmark_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"OCR benchmark: {len(results)} results across {len(by_engine)} engines")
