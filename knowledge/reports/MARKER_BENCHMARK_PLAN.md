# Marker Benchmark Plan

## Date
2026-07-11

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
*Report generated: 2026-07-11 21:47 UTC*
