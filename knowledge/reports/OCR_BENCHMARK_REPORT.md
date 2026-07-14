# OCR Benchmark Report

## Results Summary

| Engine | Tests | Success Rate | Avg Time | Avg Chars | Avg Confidence |
|--------|-------|-------------|----------|-----------|----------------|
| pymupdf | 23 | 100.0% | 1.934s | 491577 | 1.0 |
| tesseract | 3 | 100.0% | 75.622s | 25579 | 0.766 |

## Recommendation

**Best engine: pymupdf**

Pipeline: PyMuPDF (native) + pymupdf (scanned) + pymupdf (parsing)
