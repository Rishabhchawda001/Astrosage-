# AstroSage Knowledge Engine — System Architecture

**Last Updated:** 2026-07-12
**Architecture Version:** Document Intelligence v1.0 (Frozen via ADR-008)

---

## 1. Repository Structure

```
Astrosage-/
├── ARCHITECTURE.md                  # Canonical architecture (frozen)
├── pyproject.toml                   # Project metadata, dependencies
├── adrs/                            # Architecture Decision Records
│   ├── ADR-001-document-extraction.md
│   ├── ADR-002-embedding-model.md
│   ├── ADR-003-vector-database.md
│   ├── ADR-004-retrieval-strategy.md
│   ├── ADR-005-grounding-policy.md
│   ├── ADR-006-document-pipeline.md
│   ├── ADR-007-forensic-validation.md
│   ├── ADR-008-production-pipeline-lock.md
│   └── ADR-009-research-stack.md
├── config/
│   └── processing_tiers.json        # Language tier configuration
├── docs/
│   ├── project/                     # Permanent agent memory (this directory)
│   │   ├── AGENT_CONSTITUTION.md
│   │   ├── PROJECT_MEMORY.md
│   │   ├── ENGINEERING_PLAYBOOK.md
│   │   ├── PROJECT_ROADMAP.md
│   │   ├── ADR_INDEX.md
│   │   ├── DECISION_LOG.md
│   │   ├── PROJECT_GLOSSARY.md
│   │   └── SYSTEM_ARCHITECTURE.md   # This file
│   ├── KNOWLEDGE_LAKE.md
│   ├── KNOWLEDGE_REGISTRY.md
│   ├── PIPELINE_VERSIONING.md
│   ├── PROVENANCE_MODEL.md
│   └── TECHNOLOGY_RESEARCH.md
├── src/astrosage/                   # Core source code
│   ├── pipeline.py                  # Core pipeline orchestration
│   ├── models.py                    # Data models
│   ├── benchmark/                   # Benchmarking
│   │   ├── ocr_benchmark.py
│   │   ├── parser_benchmark.py
│   │   └── sample_selector.py
│   ├── classifier/                  # Document classification
│   │   └── classifier.py
│   ├── forensics/                   # PDF forensics
│   │   ├── page_classifier.py       # Multi-signal page classifier
│   │   ├── pdf_analyzer.py
│   │   ├── pipeline.py
│   │   └── visual_validator.py
│   ├── language/                    # Language detection
│   │   └── detector.py
│   ├── ocr_router/                  # OCR routing
│   │   └── router.py
│   ├── ingestion/                   # Document ingestion
│   │   └── extractor.py
│   ├── metadata/                    # Metadata extraction
│   │   └── extractor.py
│   ├── production/                  # Production pipeline
│   │   ├── pipeline.py              # Production pipeline v1.0
│   │   ├── parallel_corpus.py       # Parallel processor (6 workers)
│   │   ├── run_corpus.py            # Sequential processor
│   │   ├── sampler.py               # Representative sampling
│   │   ├── tier_router.py           # Tier-based routing
│   │   └── validation.py            # Output validation
│   ├── knowledge_lake/              # Knowledge Lake
│   │   └── pipeline.py
│   ├── registry/                    # Knowledge Registry
│   │   └── registry.py
│   ├── provenance/                  # Provenance tracking
│   │   └── graph.py
│   ├── versioning/                  # Pipeline versioning
│   │   └── versions.py
│   ├── mcp/                         # MCP server
│   │   └── server.py
│   ├── research/                    # Technology research
│   │   ├── scoring.py
│   │   ├── plugin_arch.py
│   │   ├── benchmark.py
│   │   └── stack.py
│   ├── chunking/                    # Semantic chunking (scaffold)
│   │   └── chunker.py
│   ├── embedding/                   # Embedding generation (scaffold)
│   │   └── embedder.py
│   ├── recovery/                    # Knowledge Recovery Infrastructure
│   │   ├── source_registry/        # External source catalog
│   │   ├── trust_engine/           # Configurable trust scoring
│   │   ├── knowledge_passport/     # Provenance for recovered knowledge
│   │   ├── recovery_queue/         # Priority recovery queue
│   │   ├── review_queue/           # Human review queue
│   │   ├── edition_registry/       # Edition tracking
│   │   ├── verification/           # Verification interface
│   │   ├── conflict_engine/        # Edition disagreement management
│   │   ├── confidence_engine/      # Confidence aggregation
│   │   └── provenance_ledger/      # Transformation tracking
│   ├── retrieval/                   # Retrieval engine (scaffold)
│   │   └── search.py
│   ├── storage/                     # Vector storage (scaffold)
│   │   └── vector_store.py
│   └── ... (other modules)
├── plugins/                         # Plugin architecture
│   ├── mcp/
│   │   ├── github/                  # GitHub MCP server
│   │   ├── filesystem/              # Filesystem MCP server
│   │   ├── browser/                 # Browser MCP server
│   │   └── memory/                  # Memory MCP server
│   ├── research/
│   │   └── web_search.py            # AgentReach adapter
│   ├── search/                      # Full-text search
│   ├── evaluation/                  # RAG evaluation
│   ├── agents/                      # Agent frameworks
│   ├── ocr/                         # OCR engines
│   ├── parser/                      # Document parsers
│   ├── embedding/                   # Embedding models
│   ├── reranker/                    # Reranking models
│   └── knowledge_graph/             # Graph databases
├── research/                        # Research infrastructure
│   ├── catalog/
│   │   ├── TECHNOLOGY_CATALOG.md
│   │   └── technology_catalog.json  # 26 scored technologies
│   └── reports/
│       └── GITHUB_ECOSYSTEM_DISCOVERY.md
├── tests/                           # Test suite (134 tests)
│   ├── test_phase2.py
│   ├── test_phase25.py
│   ├── test_phase3.py
│   ├── test_phase31.py
│   ├── test_phase35.py
│   ├── test_phase_r1.py
│   ├── test_chunker.py
│   ├── test_extractor.py
│   └── test_models.py
└── knowledge/                       # Knowledge Lake (data)
    ├── raw/source_library/          # 751 source files (15.3 GB)
    ├── bronze/extracted_text/       # 920 text files (484 MB)
    ├── silver/
    │   ├── structured_documents/    # 920 markdown files (481 MB)
    │   └── markdown/                # 329 markdown files (from sequential run)
    ├── gold/                        # Empty — future phases
    ├── quarantine/                  # 55 quarantined items
    ├── reports/                     # Processing reports, manifests
    ├── checkpoints/                 # Pipeline resume state
    ├── benchmarks/                  # Benchmark results
    └── logs/                        # Processing logs
```

---

## 2. Pipeline Architecture (Document Intelligence v1.0)

### Processing Flow
```
Raw PDF (knowledge/raw/source_library/)
  │
  ├── Stage 1: Document Registry
  │   ├── SHA256 hash computation
  │   ├── UUID assignment (BOOK-{sha256[:8]})
  │   └── Manifest update
  │
  ├── Stage 2: Multi-Signal Page Classifier
  │   ├── 11+ independent signals per page
  │   ├── Text layer analysis
  │   ├── Image coverage analysis
  │   ├── Font analysis
  │   ├── OCR overlay detection
  │   └── Page class assignment (native_text | scanned_image | ocr_overlay | mixed_content | blank)
  │
  ├── Stage 3: Language Detection
  │   ├── Script analysis (Devanagari, Latin, etc.)
  │   ├── Filename heuristics
  │   ├── Content sampling
  │   └── Per-page language assignment
  │
  ├── Stage 4: Tier Assignment
  │   ├── Check config/processing_tiers.json
  │   ├── Tier 1 (eng/hin/san): Full pipeline
  │   ├── Tier 2 (other langs): Register only
  │   └── Tier 3 (media): Register only
  │
  ├── Stage 5: Page-Level Routing
  │   ├── Native Text → PyMuPDF text extraction
  │   ├── Scanned → Tesseract OCR (eng/hin/san)
  │   ├── OCR Overlay → Verify existing + fallback OCR
  │   ├── Hybrid → Per-page routing (native + OCR mix)
  │   └── Blank → Skip
  │
  ├── Stage 6: Quality Validation
  │   ├── OCR confidence scoring
  │   ├── Unicode integrity check
  │   ├── Content completeness
  │   └── Quality score assignment
  │
  ├── Stage 7: Metadata Extraction
  │   ├── Title, author, publisher, edition
  │   ├── Language, script
  │   ├── Page count, document class
  │   └── Processing metadata (pipeline version, timestamp)
  │
  └── Stage 8: Knowledge Lake Ingestion
      ├── Bronze: extracted_text/{filename}.txt
      ├── Silver: structured_documents/{filename}.md
      └── Provenance graph update
```

### Parallel Execution
- 6 worker processes (adaptive to CPU count)
- Checkpoint every 3 completed books
- Resume from last checkpoint on restart
- Safety timeout: 900s per book
- Max OCR pages: 100 per document
- DPI: 150 (optimized for speed)

---

## 3. Knowledge Lake

### Layer Design
```
raw/           Immutable source archive. Never modified.
  │
  ↓ Pipeline
  │
bronze/        Extracted text. First transformation.
  │
  ↓ Pipeline
  │
silver/        Structured markdown. Clean, hierarchical content.
  │
  ↓ Pipeline (future)
  │
gold/          Chunks, embeddings, indexes. Ready for retrieval.
```

### Current State
| Layer | Files | Size | Status |
|-------|-------|------|--------|
| raw | 751 | ~15.3 GB | ✅ Populated |
| bronze | 920 | ~484 MB | ✅ Populated |
| silver | 920 | ~481 MB | ✅ Populated |
| gold | 0 | 0 | ⏳ Pending Phase 5+ |

---

## 4. Knowledge Registry

### ID Hierarchy
```
BOOK-{sha256(sha256)[:8]}
  → PAGE-{sha256(book_id:page)[:8]}
    → SECTION-{sha256(book_id:path)[:8]}
      → CHUNK-{sha256(book_id:index:text)[:8]}
        → EMBED-{sha256(chunk_id)[:8]}
```

### Current Statistics
- 620 unique BOOKs (after SHA256 dedup from 751 files)
- 68 duplicate groups (131 duplicate files)
- 751 files in manifest
- Full manifest: `knowledge/reports/manifest.csv`

---

## 5. Provenance Model

### Traceability Chain
```
Source Document (BOOK-xxx)
  → Page (PAGE-xxx)
    → Section (SECTION-xxx)
      → Chunk (CHUNK-xxx)
        → Embedding (EMBED-xxx)
          → Retrieved Context
            → Generated Answer (ANSWER-xxx)
```

### Current State
- 658 provenance nodes (329 source + 329 extraction)
- 329 provenance edges
- Full graph: `knowledge/reports/provenance_graph.json`

---

## 6. Plugin Architecture

### Categories
```
plugins/
  mcp/          # MCP servers (GitHub, Filesystem, Browser, Memory)
  research/     # Web search, AgentReach adapters
  search/       # Full-text search
  evaluation/   # RAG evaluation (RAGAS, DeepEval)
  agents/       # Agent frameworks
  ocr/          # OCR engines (Tesseract, PaddleOCR)
  parser/       # Document parsers (PyMuPDF, Docling)
  embedding/    # Embedding models (BGE-M3)
  reranker/     # Reranking models
  knowledge_graph/  # Graph databases
```

### Design Principles
- ABC-based interfaces
- Independently testable
- Independently replaceable
- No hard-coded dependencies in core code

---

## 7. Research Stack

### Technology Scoring Framework
- 10 weighted criteria, 0-10 scale
- Thresholds: ≥7.0 integrate, 5.0-6.9 evaluate, 3.0-4.9 catalog, <3.0 reject
- 26 technologies cataloged across 13 categories

### Technology Catalog
- `research/catalog/technology_catalog.json`
- `research/catalog/TECHNOLOGY_CATALOG.md`

---

## 8. MCP (Model Context Protocol)

### Tools Exposed
1. `search_books` — Search across entire knowledge base
2. `search_pages` — Page-level retrieval with OCR text
3. `list_books` — Enumerate indexed documents
4. `compare_sources` — Compare information across documents
5. `verify_answer` — Check if answer is grounded in sources
6. `sync_library` — Trigger re-sync from source
7. `reindex` — Re-index a specific document or all
8. `pipeline_status` — Check ingestion pipeline status
9. `audit_status` — System health and integrity
10. `ocr_statistics` — OCR processing metrics
11. `index_statistics` — Index size and coverage
12. `knowledge_graph` — Query concept relationships

---

## 9. Future: Retrieval Architecture

### Hybrid Search (ADR-004)
```
User Query
  │
  ├── BM25 Sparse Retrieval (keyword matching)
  │   └── Top-20 candidates
  │
  ├── Vector Dense Retrieval (semantic matching via BGE-M3)
  │   └── Top-20 candidates
  │
  ├── Reciprocal Rank Fusion (RRF)
  │   └── Merged Top-20
  │
  └── Cross-Encoder Reranker
      └── Final Top-5 (grounded, cited)
```

### Grounding (ADR-005)
```
Answer Generation
  │
  ├── RAGAS Faithfulness Check
  │   └── Every sentence mapped to retrieved source
  │
  ├── DeepEval Hallucination Detection
  │   └── Unsupported sentences flagged
  │
  └── Final Output
      ├── Grounded sentences with citations
      └── Fallback: "Insufficient evidence in knowledge base"
```

---

## 12. Deployment & Monitoring

### Deployment
- Self-hosted (no cloud dependency)
- Docker support for Qdrant
- Python 3.11+ runtime
- Pinned dependency versions

### Monitoring (Planned)
- Library growth tracking
- Processing status dashboard
- Metadata completeness metrics
- OCR readiness monitoring
- Quality score distribution
- Pipeline version history
- Storage utilization
- Processing failures

---

## 13. Technology Versions

| Technology | Version | Purpose |
|-----------|---------|---------|
| Python | 3.11+ | Runtime |
| PyMuPDF | 1.28.0 | PDF extraction |
| Tesseract | 5.3.4 | OCR (eng/hin/san) |
| PaddleOCR | 3.7.0 | Multilingual OCR |
| BGE-M3 | 570M | Embeddings |
| Qdrant | latest | Vector DB (prod) |
| Chroma | latest | Vector DB (dev) |
| rank-bm25 | 0.2.2 | Sparse retrieval |
| cross-encoder | ms-marco-MiniLM-L-6-v2 | Reranking |
| RAGAS | 0.2.0+ | RAG evaluation |
| DeepEval | 2.0+ | Hallucination detection |
| MCP | 1.0+ | Tool server |
| pytest | 9.1.1 | Testing |
| pydantic | 2.13.4 | Data validation |

---

*This document is part of the AstroSage Knowledge Engine project and lives at `docs/project/SYSTEM_ARCHITECTURE.md`.*
