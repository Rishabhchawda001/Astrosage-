# Marker Investigation Report

## Date
2026-07-11

## Status: INVESTIGATED — Not benchmarked

## What Is Marker

Marker is a PDF-to-Markdown conversion pipeline that uses deep learning models:
- **Surya OCR** — Multilingual OCR engine
- **Layout detection** — Page layout analysis (headers, paragraphs, tables, figures)
- **Table extraction** — Table structure recognition
- **Recognition model** — Text recognition for non-native text

## Installation

- **marker-pdf v1.10.2** installed successfully
- **Dependencies installed:** surya-ocr 0.17.1, torch 2.13.0, transformers 4.57.6, opencv-python-headless
- **Dependency conflicts noted:** Pillow downgraded to 10.4.0 (ocrmypdf needs ≥11.1.0)

## Why Full Benchmark Was Not Completed

Marker's `PdfConverter` requires pre-loaded model artifacts:
```python
PdfConverter(artifact_dict, processor_list, renderer, llm_service, config)
```

The `artifact_dict` must be created via `create_model_dict()` which downloads and loads:
- Layout model (Surya checkpoint)
- Recognition model (Surya checkpoint)
- Table recognition model
- Detection model
- OCR error model

These models:
1. Require ~2GB disk space for model weights
2. Require GPU for reasonable inference speed
3. Take 30+ seconds to load on CPU
4. Are designed for batch processing, not single-file benchmarking

## What Marker Would Provide

| Feature | Description |
|---------|-------------|
| Surya OCR | Multilingual OCR (100+ languages) |
| Layout detection | Identifies headers, paragraphs, tables, figures, equations |
| Table extraction | Structured table output |
| Markdown export | Clean Markdown with structure preserved |
| Formula detection | Mathematical formula recognition |

## Comparison with Existing Parsers

| Capability | PyMuPDF | Docling | Marker |
|-----------|---------|---------|--------|
| Native text extraction | ✅ Excellent | ✅ Good | ✅ Good |
| OCR | ❌ None | ✅ Tesseract | ✅ Surya (built-in) |
| Layout detection | ❌ Basic | ✅ Good | ✅ Excellent |
| Table extraction | ❌ Basic | ✅ TableFormer | ✅ Surya table_rec |
| Multi-format | PDF only | PDF+DOCX+HTML | PDF only |
| Speed | Fast (C library) | Medium | Slow (GPU models) |
| Installation | Simple | Complex | Complex |
| Devanagari support | Via text layer | Unknown | ✅ Surya supports |
| GPU required | No | No | Recommended |

## Recommendation

**Marker should be benchmarked in a GPU-enabled environment** before production deployment.
It offers superior layout detection and built-in OCR which may be valuable for scanned pages.

However, for the current AstroSage pipeline:
- **PyMuPDF** remains optimal for native PDF text extraction
- **Tesseract/PaddleOCR** are sufficient for scanned content OCR
- Marker could replace both in the future if GPU is available

## Next Steps

1. Benchmark Marker on a GPU machine with 10 representative PDFs
2. Compare layout detection quality against PyMuPDF + manual classification
3. Evaluate Surya OCR quality for Hindi/Sanskrit
4. Assess memory requirements for batch processing

---
*Report generated: 2026-07-11*
