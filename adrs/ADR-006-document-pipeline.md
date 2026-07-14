# ADR-006: Document Processing Pipeline

## Status
Accepted

## Date
2026-07-11

## Problem
Select the optimal OCR engine and parser for the AstroSage Knowledge Engine,
based on benchmarking against the actual AstroSage corpus (751 files, 194,577 pages).

## Alternatives Considered
1. **pymupdf** — composite score 100.0, 100.0% success, 1.934s avg time
2. **tesseract** — composite score 70.8, 100.0% success, 75.622s avg time

## Decision
**PyMuPDF (native) + pymupdf (scanned) + pymupdf (parsing)**

## Rationale
- **native_pdfs:** PyMuPDF provides direct, lossless text extraction — no OCR overhead
- **scanned_pdfs:** pymupdf selected for highest composite score (quality + speed + reliability)
- **parser:** pymupdf selected for best structure preservation
- **tradeoffs:** PaddleOCR offers best Hindi/Sanskrit quality but slower; Tesseract is fastest for English
- **maintenance:** PyMuPDF is mature and well-maintained; OCRmyPDF wraps Tesseract with PDF-aware workflow

## Tradeoffs
- Native PDFs: PyMuPDF is fastest and most reliable (no OCR needed)
- Scanned PDFs: pymupdf provides best balance of quality/speed
- PaddleOCR: Best Hindi/Sanskrit quality but requires more memory
- Tesseract: Fastest for English but lower Devanagari quality

## Hardware Requirements
- **cpu_only:** PyMuPDF, Tesseract, OCRmyPDF — no GPU needed
- **gpu_optional:** PaddleOCR benefits from GPU but works on CPU
- **memory_minimum:** 4GB RAM for small PDFs, 16GB for large (>100MB)
- **disk_space:** 2-5GB for OCR models (PaddleOCR ~2GB, Tesseract ~200MB)

## Future Migration Path
- Monitor PaddleOCR v4 for improved Devanagari support
- Evaluate olmOCR when it supports more Indian languages
- Consider GPU acceleration for large-batch OCR processing
