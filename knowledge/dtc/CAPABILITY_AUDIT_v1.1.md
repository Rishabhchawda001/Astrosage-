# AstroSage Capability Audit v1.1
**Generated:** 2026-07-16T18:40:00Z

## Corpus Status
| Metric | Value |
|--------|-------|
| Scriptures | 54 |
| Certified | 49 |
| Provisional | 5 |
| Unverified | 0 |
| Total verses/units | 1,322,481 |

## Installed Capabilities
| Category | Count |
|----------|-------|
| OCR Engines | 7 |
| Document Parsers | 6 |
| Sanskrit NLP Libraries | 5 |
| Textual Criticism Tools | 3 |
| AI/ML Frameworks | 2 |
| Image Processing | 3 |

## OCR Engines
- Tesseract 5.3.4 (13 languages including Sanskrit)
- PaddleOCR 3.7.0
- EasyOCR 1.7.2
- Surya OCR 0.17.1
- Kraken 7.0.2
- OCRmyPDF 17.8.0
- Pytesseract 0.3.13

## Document Parsers
- PyMuPDF 1.28.0
- pdfplumber 0.11.10
- pdfminer (installed)
- Marker (installed)
- lxml 6.1.1
- BeautifulSoup4 4.15.0

## Sanskrit NLP
- indic-transliteration 2.3.82 (26.75 μs/word)
- sanskrit-parser 0.2.6
- sanskrit-util 0.1.2
- sentencepiece (installed)
- Unidecode 1.4.0

## Textual Criticism
- CollateX 2.3 (0.96 ms/collation)
- Levenshtein (installed)
- regex 2024.11.6

## Data Sources
| Source | Files | Size |
|--------|-------|------|
| GRETIL XML | 126 | Authoritative |
| Archive.org | 537 total | 1.85 GB |
| Bronze tier | 525+ files | OCR from original corpus |

## Benchmarks
| Operation | Speed |
|-----------|-------|
| Sanskrit transliteration | 26.75 μs/word |
| CollateX collation | 0.96 ms |
| Unicode NFC | 0.19 μs/op |

## Session Improvements
- VYU: CERTIFIED via GRETIL TEI XML (7,609 verses, 232 adhyayas)
- KATH: Fixed extraction (369 verses, CERTIFIED)
- VAISHESHIKA_SUTRA: UNVERIFIED -> PROVISIONALLY_CERTIFIED (247 sutras)
- VYASA_SM: UNVERIFIED -> PROVISIONALLY_CERTIFIED (211 verses)
- SV: 66 -> 1,833 verse-ending lines
- KALI: Added 2 Archive.org OCR sources
- MBH: Added 8,584 GRETIL IAST verses as second witness
- Installed: kraken 7.0.2, sentencepiece, levenshtein, pdfminer
- Built: benchmark lab, capability matrix, dashboard

## Remaining Gaps
### High Priority
- MBH: 69.0% coverage — needs better OCR sources or copyrighted BORI edition
- KALI: 15.4% coverage — only 1,384/9,000 verses from OCR

### Medium Priority
- VAISHESHIKA_SUTRA: 66.8% — 247/370 sutras from DLI OCR
- VYASA_SM: 84.4% — 211/250 verses from Archive.org

### Structural
- No public-domain full Mahabharata Sanskrit text available
- No public-domain Kalika Purana full Sanskrit text available
- GRETIL returns 404 for direct downloads — limited to existing files
- BORI critical editions are copyrighted — cannot be redistributed

## Evidence Quality
- **Authoritative sources:** GRETIL TEI XML (CC BY-NC-SA 4.0)
- **OCR sources:** Archive.org DjVu text (DLI, BORI, Gita Press)
- **Witness independence:** Multiple publishers/editors for key texts
- **Unicode validation:** NFC normalization verified for all GRETIL texts
- **Provenance:** Complete for all downloaded sources
