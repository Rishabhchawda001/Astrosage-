# ADR-008: Production Pipeline Architecture Lock

## Status
**Accepted** — GO

## Date
2026-07-12

## Problem
Certify the production document pipeline is stable enough for full-corpus (194,577 page) processing.

## Evidence

- Validated on 40 documents (4,721 pages)
- Representative corpus covering: scanned, native, OCR overlay, hybrid, mixed content
- Languages: Hindi, English, Sanskrit, Telugu, Malayalam, Kannada
- 0% document failure rate
- 100% Knowledge Lake integrity (40/40 bronze, 40/40 silver)
- 100% Unicode integrity (0 broken characters)
- Graceful failure on difficult cases
- Provenance maintained for all artifacts

## Architecture Lock

The following components are frozen as **Document Intelligence v1.0**:

| Component | Version | Status |
|-----------|---------|--------|
| Multi-Signal Page Classifier | v1.0 | LOCKED |
| Document Classification | v1.0 | LOCKED |
| OCR Routing | v1.0 | LOCKED |
| Text Extraction (PyMuPDF) | v1.0 | LOCKED |
| OCR Engine (Tesseract 5.3.4) | v1.0 | LOCKED |
| Language Detection | v1.0 | LOCKED |
| Metadata Extraction | v1.0 | LOCKED |
| Quality Validation | v1.0 | LOCKED |
| Knowledge Lake Schema | v1.0 | LOCKED |
| Provenance Model | v1.0 | LOCKED |

## Change Policy

Future changes to any locked component require:
1. Updated benchmarks on representative corpus
2. Regression testing
3. Updated ADR
4. Explicit approval

## Tradeoffs

- Locked architecture may miss newer/better tools
- Mitigated by modular design — components can be swapped behind interfaces
- Architecture version tracked for reproducibility
