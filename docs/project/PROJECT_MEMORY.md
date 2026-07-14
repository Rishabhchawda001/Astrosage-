# AstroSage Knowledge Engine — Project Memory

**Last Updated:** 2026-07-12
**Status:** ✅ ACTIVE — Living memory of the project

---

## 1. Why AstroSage Exists

AstroSage is a self-hosted Knowledge Operating System built to index, structure, and query a massive collection of Vedic texts, Ayurveda books, astrology manuscripts, research papers, and general books. The corpus was downloaded from Google Drive (15.3 GB, 751 files, 602 PDFs, 194,577 PDF pages). The goal is to build a system that can answer questions grounded in these documents with zero hallucination.

**Key constraint:** Everything must run locally. No paid APIs. No cloud dependency.

---

## 2. Completed Phases

### Phase 0–3: Foundation
- Repository setup, codebase architecture, initial pipeline design

### Phase 1: Knowledge Acquisition ✅
- Downloaded 751 files (15.3 GB) from Google Drive
- 750 of 751 files successfully downloaded (1 was a Google Sheet link, not accessible)
- Production downloader built at `scripts/download_production.py`
- Root cause of original download failures: `gdown` library's broken confirmation token handling (NOT authentication)
- All files mirrored into `knowledge/source_library/`

### Phase 2: Knowledge Normalization ✅
- Knowledge Lake architecture: raw → bronze → silver → gold
- Knowledge Registry: 620 unique books after SHA256 deduplication from 751 files
- Manifest: `knowledge/reports/manifest.csv` + `manifest.parquet` (751 records)
- Provenance graph: 658 nodes, 329 edges
- Pipeline versioning: 16 components, independent versioning
- 41 tests passing

### Phase 2.5: Corpus Intelligence ✅
- **194,577 total PDF pages** across 602 PDFs
- Languages: Hindi 273, English 243, Sanskrit 97, Telugu 18, Gujarati 6, Kannada 6
- 118 named entities detected, 122,110 unique terms
- 1,000 golden evaluation questions generated
- Document quality average: 56.6/100 (metadata completeness is low)
- 55 tests passing

### Phase 3: Document Intelligence Lab ✅
- **OCR Benchmark (26 tests):**
  - PyMuPDF: 100% success, 1.9s avg
  - Tesseract: 100% success, 75.6s avg, 76.6% confidence
  - PaddleOCR: installed, benchmarked
- **Parser Benchmark (16 tests):**
  - PyMuPDF: 100% success, 87.5% structure preservation
  - Docling: 0% (needs full library, not just docling-core)
  - Marker: installed, benchmarked
- **Initial finding (later DISPROVED):** "Zero fully scanned PDFs"
- 66 tests passing

### Phase 3.1: Document Forensics ✅ (CRITICAL FINDING)
- Built multi-signal page classifier with 11+ signals per page
- Analyzed all 599 PDFs (79,078 sampled pages)
- **DISPROVED Phase 3 claim: Corpus contains 51.4% scanned pages**
- 259 fully scanned documents, 226 native, 39 OCR overlay, 20 hybrid
- Visual validation on 28 samples confirmed accuracy
- Unicode quality: 0 encoding errors
- 91 tests passing

### Phase 3.5: Production Pipeline Validation ✅
- Validated on 40 documents (4,721 pages)
- 0% document failure rate
- 100% Knowledge Lake integrity (40/40 bronze, 40/40 silver)
- 100% Unicode integrity (0 broken characters)
- **GO decision** — Pipeline certified for full-corpus execution
- Architecture frozen as Document Intelligence v1.0 (ADR-008)
- 108 tests passing

### Phase R1: Research Stack & MCP Ecosystem ✅
- Technology Scoring Framework (weighted 10-criteria, 0-10 scale)
- Technology Catalog: 26 projects scored across 13 categories
- Plugin Architecture (ABC-based, independently replaceable)
- 4 MCP server plugins: GitHub, Filesystem, Browser, Memory
- AgentReach adapter for web search
- Benchmark Framework (repeatable, versioned)
- 134 tests passing


### Phase 4.5: Knowledge Recovery Infrastructure ✅
- 12 core subsystems built: Source Registry, Trust Engine, Knowledge Passport, Recovery Queue, Review Queue, Edition Registry, Verification Interface, Conflict Engine, Confidence Engine, Source Connectors, Provenance Ledger
- 5 default knowledge sources registered (Internet Archive, Open Library, Crossref, OpenAlex, Wikidata)
- 11 entry types in Provenance Ledger (character → OCR → recovery → verification → edition alignment → knowledge object → chunk → embedding → retrieval → answer → conflict → human review)
- 8 edition types (original, translation, publisher, critical, commentary, roman transliteration, regional, digital reprint)
- 4 conflict severity levels (minor, moderate, major, critical)
- Confidence engine with 6 configurable component weights
- ABC-based plugin interfaces for recovery, verification, and source connectors
- 59 new tests, 193 total tests passing
- ADR-010 written

### Phase 4: Production Document Processing ✅
- **601 of 602 PDFs processed** (99.8%) — 1 genuinely corrupted (`panini_kashika.pdf`)
- **920 bronze files** (extracted text) generated
- **920 silver files** (structured markdown) generated
- **56 quarantined** (large scanned PDFs, edge cases)
- **149 non-PDF files** registered (66 mp4, 63 jpeg, 12 mp3, etc.)
- Parallel processor: 6 workers, 239.8 pages/min, 0.6 books/min
- Checkpoint system operational for resume
- 134 tests passing

---

## 3. Major Discoveries

### The "Zero Scanned PDFs" Fallacy
Phase 3 concluded "zero fully scanned PDFs." This was **WRONG.** Phase 3.1 proved the opposite with a multi-signal classifier:
- 51.4% of all pages are scanned images
- 259 of 599 PDFs are fully scanned
- 36.1% of pages have native text
- 11.7% have OCR overlay

**Lesson:** Never trust a classifier that uses only `page.get_text()` as its signal. Multi-signal analysis is mandatory.

### Download Failures Were NOT Auth Issues
Original downloader failures were caused by `gdown` library's broken confirmation token handling, not Google Drive authentication. Root cause analysis before writing code saved weeks of wrong solutions.

### PyMuPDF is the Right Parser
Despite testing Docling and Marker, PyMuPDF won for production because:
- 100% success rate on the corpus
- Fastest extraction (1.9s per document)
- Best for native PDF text extraction
- Docling failed entirely (needed full library, not just core)
- Marker needed GPU for full functionality

### Tesseract Works for Sanskrit
Tesseract handles Sanskrit with the `san` language model at 76.6% confidence. Combined with PaddleOCR for Hindi, the pipeline covers all Tier 1 languages.

---

## 4. Corpus Statistics

| Metric | Value |
|--------|-------|
| Total source files | 751 |
| Total PDFs | 602 |
| Total non-PDF files | 149 |
| Total PDF pages | 194,577 |
| PDFs processed (bronze) | 601 (99.8%) |
| Bronze files | 920 |
| Silver files | 920 |
| Quarantined | 55 |
| Failed | 1 (corrupted PDF) |
| Source library size | ~15.3 GB |
| Bronze size | ~484 MB |
| Silver size | ~481 MB |

### File Type Distribution
| Type | Count |
|------|-------|
| PDF | 602 |
| MP4 | 66 |
| JPEG | 63 |
| MP3 | 12 |
| JPG | 5 |
| DOCX | 1 |
| ZIP | 1 |
| PNG | 1 |

### Language Distribution
| Language | PDF Count |
|----------|-----------|
| Hindi | 273 |
| English | 243 |
| Sanskrit | 97 |
| Telugu | 18 |
| Gujarati | 6 |
| Kannada | 6 |
| Other | ~56 |

### Page Classification Results
| Class | % of Pages |
|-------|-----------|
| Scanned Image | 51.4% |
| Native Text | 36.1% |
| OCR Overlay | 11.7% |
| Hybrid/Other | ~0.8% |

---

## 5. Approved Technologies

| Technology | Version | Purpose | Status |
|-----------|---------|---------|--------|
| Python | 3.11+ | Runtime | ✅ Active |
| PyMuPDF | 1.28.0 | PDF extraction, page classification | ✅ Frozen |
| Tesseract | 5.3.4 | OCR (eng/hin/san) | ✅ Frozen |
| PaddleOCR | 3.7.0 | Multilingual OCR fallback | ✅ Installed |
| BGE-M3 | 570M | Multilingual embeddings | ✅ Selected (ADR-002) |
| Qdrant | latest | Production vector DB | ✅ Selected (ADR-003) |
| Chroma | latest | Development vector DB | ✅ Selected (ADR-003) |
| BM25 | 0.2.2 | Sparse retrieval | ✅ Selected (ADR-004) |
| cross-encoder/ms-marco-MiniLM | L-6-v2 | Reranking | ✅ Selected (ADR-004) |
| RAGAS | 0.2.0+ | RAG evaluation | ✅ Selected (ADR-005) |
| DeepEval | 2.0+ | Hallucination detection | ✅ Selected (ADR-005) |
| MCP (Python) | 1.0+ | Tool server | ✅ Active |

---

## 6. Rejected Technologies

| Technology | Reason |
|-----------|--------|
| Docling (full) | 0% success rate on parser benchmark; dependency issues |
| Marker | Needs GPU models for full functionality; dependency conflicts |
| Chroma (production) | Limited filtering, single-node only — used for dev only |
| Milvus | Overkill dependencies (etcd, MinIO) |
| Weaviate | Heavier deployment than necessary |
| Stella | English-only, insufficient multilingual support |
| E5 | Limited multilingual support |
| nomic-embed-text | English-focused |

---

## 7. Critical Git History

| Commit | Phase | Description |
|--------|-------|-------------|
| `00314f6` | Phase 0–3 | Foundation: initial codebase, forensics, pipeline design |
| `83b70b7` | Phase 3.5 | Pipeline validation, architecture lock (GO decision) |
| `a95d904` | Phase R1 | Research stack, MCP ecosystem, plugin architecture |
| `00a5055` | Phase 4 | Production processing, Knowledge Lake population |
| `bb3343e` | Phase 4 | Fixup: post-commit processing update |

---

## 8. Lessons Learned

1. **Multi-signal classifiers beat single-signal classifiers.** Always use multiple independent signals for page classification.
2. **Root cause analysis before writing code.** Understanding the actual problem (gdown token handling) saved weeks of wrong solutions.
3. **Benchmark before selecting.** PyMuPDF won because it actually works on our corpus, not because it's the most popular.
4. **Checkpoint everything.** Parallel processing with checkpointing saved days when the sequential pipeline hit timeouts.
5. **Tier-based processing scales.** Language-aware routing avoids wasting resources on non-English OCR.
6. **Quarantine, never delete.** 56 quarantined files are preserved for future re-processing.
7. **Test continuously.** Going from 41 tests (Phase 2) to 134 tests (Phase 4) caught regressions early.
8. **GitHub is source of truth.** Every phase ends with a commit and push. No local-only work.

---

## 9. Known Issues

1. **1 corrupted PDF** (`panini_kashika.pdf`) — PyMuPDF reports invalid page count
2. **11 PDFs without bronze** — partially processed or quarantined
3. **Docling** — full library not installed, only docling-core
4. **Marker** — dependency conflicts (Pillow downgrade)
5. **No chunking, embedding, retrieval yet** — planned for Phase 5+
6. **Recovery infrastructure built but not executed** — actual recovery in Phase 5+

---

*This document is part of the AstroSage Knowledge Engine project and lives at `docs/project/PROJECT_MEMORY.md`.*

---

## 10. Phase A1 — Foundation Installation (2026-07-12)

**Commit:** `8ef52df`

Built production-ready infrastructure:
- `core/` — Plugin system, service registry, config loader, versioning, logging, DI container
- `adapters/` — ABC interfaces for document processing, search, vector, memory, guardrails, browser, research
- `schemas/` — MCP tools (12), A2A schemas, prompt templates, OpenAPI specs (10 services)
- `services/` — MCP server scaffold, A2A server scaffold
- `commands/` — Command registry with 14 known commands
- `contracts/` — Service interface contracts (10 services)
- `registries/` — Technology, skill, benchmark, research registries
- `skills/` — SKILL.md loader and registry
- **62 new tests**

## 11. Phase A2 — Knowledge Recovery & Evidence Engine (2026-07-12)

**Commit:** `009955a`

Built evidence-first knowledge infrastructure:
- `core/recovery/engine.py` — OCR error detection and recovery
- `core/evidence/engine.py` — Multi-source evidence collection with provenance
- `core/verification/engine.py` — 8-stage verification pipeline
- `core/provenance/ledger.py` — Immutable provenance ledger
- `core/passports/passport.py` — Knowledge passports with lifecycle
- `core/confidence/engine.py` — Weighted deterministic confidence scoring
- `core/alignment/engine.py` — Cross-edition alignment (never auto-merges)
- `core/comparison/engine.py` — Conflict detection and tracking
- `core/trust/engine.py` — Configurable trust scoring
- `adapters/sources/` — 7 source connector stubs (Internet Archive, Open Library, Crossref, OpenAlex, GitHub, ArXiv, Google Drive)
- **78 new tests** (140 total)

## 12. Phase 10 — Semantic Chunking Engine (2026-07-12)

**Commit:** `b29c4a2`

Built production semantic chunking:
- `core/chunking/engine.py` — 18 chunk types, hierarchical chunking, verse splitting
- `core/chunks/models.py` — Chunk metadata, embedding & search interfaces
- `core/hierarchy/engine.py` — Parent-child hierarchy graph
- `core/semantic/engine.py` — Semantic boundary detection
- `core/deduplication/engine.py` — Exact, near, parallel translation duplicate detection
- `core/chunk_registry/registry.py` — Permanent chunk registry with versioning
- `core/chunk_validation/validator.py` — Chunk validation and integrity checks
- `core/chunk_quality/quality.py` — 9-dimension quality scoring (A-F grades)
- **57 new tests** (197 total)

## 13. APEE v1 — Parallel Execution Engine (2026-07-12)

**Status:** PERMANENT EXECUTION POLICY

Global execution directive stored at `docs/project/APEE_V1.md`.

Establishes:
- 10 implementation workers + 5 validation workers model
- Dynamic task scheduler
- Quality gates (all 5 validators must approve)
- Checkpoint policy (5-10 min or logical milestone)
- Self-review protocol
- Correctness-over-speed policy
- Failure isolation policy

All future phases execute under APEE v1 unless technically impossible.

---

*This document is part of the AstroSage Knowledge Engine project and lives at `docs/project/PROJECT_MEMORY.md`.*
