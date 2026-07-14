# Docling Investigation Report

## Status: PARTIALLY INVESTIGATED

## Date
2026-07-11

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
*Report generated: 2026-07-11 21:47 UTC*
