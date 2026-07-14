# ADR-007: Forensic Validation of Document Classification

## Status
**Accepted** — Phase 3 claim of "zero scanned PDFs" is **DISPROVED**

## Date
2026-07-11

## Context

Phase 3 concluded that "the corpus contains zero fully scanned PDFs" based on a single-signal
classifier using `page.get_text()`. Phase 3.1 independently validated this using 11+ signals
per page across all 599 PDFs (79,078 sampled pages).

## Decision

**The Phase 3 conclusion is DISPROVED.**

The corpus contains significant scanned content that requires OCR processing.

### Evidence

| Metric | Value |
|--------|-------|
| Total PDFs analyzed | 589 |
| Total pages sampled | 79,078 |
| Scanned image pages | 40,678 (51.4%) |
| OCR overlay pages | 9,290 (11.8%) |
| Native text pages | 28,520 (36.1%) |
| Fully scanned documents | 259 |
| OCR overlay documents | 39 |
| Hybrid documents | 20 |

### Classification Accuracy

The single-signal classifier from Phase 3 detected text via `page.get_text()` and
concluded all pages were native text. The multi-signal classifier reveals this was wrong
because:

- OCR-overlaid scans contain invisible text that `get_text()` extracts successfully
- Only image coverage analysis, DPI estimation, and bounding box overlap detection
  can distinguish between native text and OCR-overlaid scans

## Consequences

### Updated Production Pipeline

```
Raw PDF
  ↓
Multi-Signal Document Classifier (Phase 3.1)
  ↓
├── Native PDF (>90% native pages) → PyMuPDF text extraction
├── Scanned PDF (>80% scanned pages) → OCR Router
│   ├── English → Tesseract (eng)
│   ├── Hindi → Tesseract (hin) or PaddleOCR
│   ├── Sanskrit → Tesseract (san) + PaddleOCR
│   └── Mixed → PaddleOCR (multilingual)
├── OCR Overlay → Extract existing OCR text + validate + fallback OCR
├── Hybrid → Page-level routing (native + OCR per page)
└── Unknown → Manual review queue
```

### Required Infrastructure

1. **Multi-signal page classifier** — Production deployment of the Phase 3.1 classifier
2. **OCR engine** — Tesseract 5.x + PaddleOCR for Hindi/Sanskrit
3. **Page-level routing** — Each page independently classified and processed
4. **Quality validation** — OCR confidence scoring before knowledge lake ingestion
5. **Visual validation** — Random sample inspection for quality assurance

## Alternatives Considered

| Alternative | Decision | Rationale |
|-------------|----------|-----------|
| PyMuPDF only | **Rejected** | Cannot handle scanned/OCR-overlay pages |
| Single-signal classifier | **Rejected** | Proven incorrect by Phase 3.1 |
| OCR everything | **Rejected** | Unnecessary for native PDFs, wastes resources |
| Multi-signal adaptive pipeline | **Selected** | Handles all document types correctly |

## Follow-up Actions

1. Complete OCR benchmark (Phase 3) with corrected understanding
2. Select OCR engine based on benchmarks
3. Implement adaptive production pipeline
4. Deploy visual validation infrastructure

---
*This ADR supersedes any implicit assumptions from Phase 3 about zero scanned PDFs.*
