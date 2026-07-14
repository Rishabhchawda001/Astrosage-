# ADR-001: Document Extraction Strategy

## Status
Accepted

## Date
2026-07-11

## Problem
The knowledge library contains 755 files across PDFs (603), images (70), DOCX (1), and unknown types (80). We need a reliable extraction pipeline that preserves content quality across native PDFs, scanned PDFs, and multilingual content (English, Hindi, Sanskrit in Devanagari script).

## Alternatives Considered
1. **PyMuPDF only** — Fast text extraction, no OCR. Cannot handle scanned PDFs.
2. **OCRmyPDF + Tesseract** — PDF-aware OCR. Good but struggles with complex layouts.
3. **PaddleOCR standalone** — Best accuracy. No PDF workflow integration.
4. **Docling/Marker** — Best document understanding but heavier dependencies.
5. **Adaptive pipeline** — Route documents through appropriate extraction method based on type.

## Decision
Implement an adaptive extraction pipeline:
1. **Native PDFs**: Extract text directly with PyMuPDF (zero OCR overhead)
2. **Scanned/mixed PDFs**: Route to PaddleOCR with language-specific models
3. **Complex layouts**: Use Docling for semantic structure preservation
4. **Non-PDF**: Use format-specific handlers (python-docx for DOCX, etc.)

## Rationale
- Native PDF extraction is 100x faster than OCR and lossless for text-based PDFs
- PaddleOCR provides state-of-the-art accuracy for Hindi/Sanskrit
- Docling preserves semantic structure (chapters, sections, tables)
- Adaptive routing minimizes processing time while maximizing quality

## Tradeoffs
- More complex pipeline logic vs. single-tool approach
- Multiple dependencies to maintain
- Detection step adds small overhead but saves large amounts of unnecessary OCR work

## Future Migration Path
- Replace PaddleOCR with olmOCR when it supports Devanagari
- Add GPU-accelerated extraction when available
- Evaluate Docling v2+ for production readiness
