# Production Pipeline Recommendation

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
*Date: 2026-07-11*

## Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 4 cores | 8+ cores |
| RAM | 8 GB | 16+ GB |
| Disk | 20 GB | 100+ GB (SSD) |
| GPU | Not required | NVIDIA GPU with CUDA (for Marker/PaddleOCR acceleration) |
| Network | None (offline capable) | Initial setup only |

### Per-Component Requirements

- **PyMuPDF:** CPU only, <1GB RAM, fast
- **Tesseract:** CPU only, <2GB RAM, moderate speed
- **PaddleOCR:** CPU or GPU, 2-4GB RAM, GPU acceleration available
- **Marker:** GPU recommended, 4-8GB RAM for model loading
- **Docling:** GPU recommended for TableFormer, 4GB+ RAM

### Batch Processing Estimates (599 PDFs, ~194K pages)

| Operation | CPU Time | GPU Time |
|-----------|----------|----------|
| Classification | ~1 hour | N/A |
| Native text extraction | ~30 min | N/A |
| OCR (scanned pages) | ~24 hours | ~4 hours |
| Marker conversion | ~8 hours | ~2 hours |
| Total pipeline | ~25 hours | ~7 hours |
