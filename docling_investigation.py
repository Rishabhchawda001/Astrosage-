"""Docling Investigation Report and Marker Benchmark Plan."""
import json, sys
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(line_buffering=True)

BASE = Path(".")
REPORTS_DIR = BASE / "knowledge" / "reports"
FORENSICS_DIR = BASE / "knowledge" / "benchmarks" / "forensics"

# ══════════════════════════════════════════════════════════════════
# 1. DOCLING INVESTIGATION REPORT
# ══════════════════════════════════════════════════════════════════

report = f"""# Docling Investigation Report

## Status: PARTIALLY INVESTIGATED

## Date
{datetime.now().strftime('%Y-%m-%d')}

## Current State

- **docling-core** v2.87.0 is installed (data model and document types)
- **docling** (full package) is NOT installed
- Previous Phase 3 benchmarks reported Docling at 0% success

## Investigation

### Why Docling Failed in Phase 3

Docling was benchmarked using only `docling-core`, which provides data model types
(DoclingDocument, PageItem, etc.) but NOT the actual document conversion pipeline.
The full `docling` package includes:

1. **Document converters** — PDF, DOCX, HTML, etc.
2. **OCR engines** — Tesseract integration, EasyOCR
3. **Table extraction** — TableFormer model
4. **Pipeline orchestration** — Model loading, processing

The Phase 3 benchmark was fundamentally flawed for Docling because only the
data model library was available, not the converter.

### Full Docling Installation

Full `docling` installation was attempted but encountered issues:

1. **Dependency conflict** — `externally-managed-environment` (PEP 668)
2. **Large download** — Requires `docling-serve`, model weights (~1GB+)
3. **GPU models** — TableFormer and layout models may need GPU
4. **Time** — Installation exceeds 5 minutes due to model downloads

### What Docling Would Provide

If fully installed, Docling offers:

| Feature | Description |
|---------|-------------|
| TableFormer | State-of-the-art table extraction |
| Layout detection | Page layout analysis |
| Figure extraction | Image and figure detection |
| Multi-format | PDF, DOCX, HTML, PPTX |
| OCR integration | Tesseract, EasyOCR |
| Markdown export | Structured markdown output |
| Document model | Rich document graph |

### Recommendation

**Docling should be installed in a dedicated virtual environment** to avoid system
package conflicts. It should be benchmarked against the AstroSage corpus before
final pipeline selection.

**Estimated effort:** 2-4 hours for installation and benchmarking
**Risk:** May not support Devanagari/Sanskrit OCR natively
**Dependency:** Requires GPU for optimal TableFormer performance

## Conclusion

Docling's Phase 3 failure was caused by incomplete installation, not fundamental
incompatibility. The full package should be installed and benchmarked before
dismissing it as an option.

---
*Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}*
"""

with open(REPORTS_DIR / "DOCLING_INVESTIGATION_REPORT.md", "w") as f:
    f.write(report)
print("Written: DOCLING_INVESTIGATION_REPORT.md", flush=True)

# ══════════════════════════════════════════════════════════════════
# 2. MARKER BENCHMARK PLAN
# ══════════════════════════════════════════════════════════════════

marker_plan = f"""# Marker Benchmark Plan

## Date
{datetime.now().strftime('%Y-%m-%d')}

## Status: PLANNED (Installation in progress)

## Overview

Marker is a markdown conversion pipeline that uses deep learning models for:

- Layout detection
- OCR
- Table extraction
- Formula detection
- Page header/footer removal
- Semantic block detection

## Benchmark Criteria

### Documents to Test

Select from the AstroSage benchmark corpus:

1. **English native PDF** — `Prakashika-10 Abhigyan Shankuntal.pdf` (262 pages)
2. **Hindi native PDF** — `गीता साधक संजीवनी.pdf` (1299 pages)
3. **English scanned PDF** — `Gita-Sadhale.pdf` (1495 pages)
4. **Sanskrit+English mixed** — `Four-Vedas-English-Translation.pdf` (1446 pages)
5. **Hindi scanned** — `test_download.pdf` (1538 pages)

### Metrics to Measure

| Metric | Method |
|--------|--------|
| Heading detection | Compare detected headings vs ground truth |
| Chapter detection | Verify chapter boundaries |
| Table extraction | Count extracted tables |
| Verse preservation | Hindi/Sanskrit verse structure |
| Figure extraction | Image detection and captioning |
| Footnote extraction | Footnote detection and linking |
| Markdown quality | Human-readable output assessment |
| Processing speed | Pages per second |
| Memory usage | Peak RAM during processing |
| Failure rate | % of documents that fail |

### Comparison Targets

Compare against:

1. **PyMuPDF** — Current baseline (100% success, 87.5% structure)
2. **Docling** — Pending installation
3. **Marker** — Being installed

## Expected Outcomes

- Determine if Marker provides better structure preservation than PyMuPDF
- Identify any Markdown quality improvements
- Assess processing overhead vs quality gain
- Document any failure modes

---
*Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}*
"""

with open(REPORTS_DIR / "MARKER_BENCHMARK_PLAN.md", "w") as f:
    f.write(marker_plan)
print("Written: MARKER_BENCHMARK_PLAN.md", flush=True)

# ══════════════════════════════════════════════════════════════════
# 3. PRODUCTION PIPELINE RECOMMENDATION
# ══════════════════════════════════════════════════════════════════

pipeline_rec = f"""# Production Pipeline Recommendation

## Based on Phase 3.1 Forensic Investigation

### Current Understanding

| Metric | Value |
|--------|-------|
| Total PDFs | 599 |
| Total pages | ~194,577 |
| Native text pages | 36.1% |
| Scanned image pages | 51.4% |
| OCR overlay pages | 11.7% |
| Fully scanned docs | 259 |
| Native docs | 226 |
| OCR overlay docs | 39 |
| Hybrid docs | 20 |

### Recommended Pipeline

```
Raw PDF
  ↓
[Stage 1] Multi-Signal Page Classifier
  Analyzes every page using 11+ signals
  ↓
[Stage 2] Document Classification
  ├── Native (>90% native pages)
  ├── Scanned (>80% scanned pages)
  ├── OCR Overlay (scanned + invisible text)
  ├── Hybrid (mixed native + scanned)
  └── Unknown (< 50% pages classified)
  ↓
[Stage 3] Routing
  ├── Native → PyMuPDF text extraction
  ├── Scanned → OCR Engine (Tesseract/PaddleOCR)
  ├── OCR Overlay → Extract OCR text + validate + fallback OCR
  ├── Hybrid → Page-level routing
  └── Unknown → Manual review queue
  ↓
[Stage 4] Language Detection
  Detect language per page for OCR engine selection
  ├── English → Tesseract (eng)
  ├── Hindi → Tesseract (hin) or PaddleOCR
  ├── Sanskrit → Tesseract (san) + PaddleOCR
  ├── Mixed → PaddleOCR (multilingual)
  └── Other → PaddleOCR (auto)
  ↓
[Stage 5] Quality Validation
  OCR confidence scoring
  Text quality assessment
  Unicode validation
  ↓
[Stage 6] Knowledge Lake Ingestion
  Bronze layer: extracted text
  Silver layer: structured markdown
  Gold layer: chunks and embeddings
```

### Key Decisions

1. **PyMuPDF is the primary extractor** for native PDFs (fast, reliable)
2. **Tesseract + PaddleOCR** are needed as fallback for scanned content
3. **Page-level routing** is essential — many documents are hybrid
4. **Multi-signal classification** replaces the flawed single-signal approach
5. **OCR overlay detection** prevents misclassification of OCR'd scans

### Why PyMuPDF Alone Is Insufficient

- 51.4% of pages are scanned images
- PyMuPDF extracts only the OCR text overlay (if present)
- OCR text quality varies significantly
- Native text extraction on scans returns empty or garbage

### Why Full-Page OCR Is Not the Answer

- 36.1% of pages are native text — OCR would degrade quality
- Native text is already high quality (fonts, structure)
- OCR is slower and introduces errors
- Adaptive routing preserves native text quality

---
*Pipeline designed based on Phase 3.1 forensic evidence.*
*Date: {datetime.now().strftime('%Y-%m-%d')}*
"""

with open(REPORTS_DIR / "PRODUCTION_PIPELINE_RECOMMENDATION.md", "w") as f:
    f.write(pipeline_rec)
print("Written: PRODUCTION_PIPELINE_RECOMMENDATION.md", flush=True)

print("\nAll reports generated.", flush=True)
