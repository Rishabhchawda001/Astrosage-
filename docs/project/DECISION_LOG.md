# AstroSage Knowledge Engine — Decision Log

**Last Updated:** 2026-07-12
**Purpose:** Chronological record of all major engineering decisions

---

## 2026-07-11

### Decision: Document Extraction Pipeline
- **ADR:** ADR-001
- **Decision:** Adaptive pipeline — PyMuPDF for native, PaddleOCR for scanned
- **Why:** Native extraction is 100x faster than OCR; PaddleOCR handles Hindi/Sanskrit
- **Alternatives:** PyMuPDF-only (rejected: can't OCR), single OCR (rejected: wasteful)
- **Outcome:** Implemented in Phase 3 pipeline

### Decision: Embedding Model
- **ADR:** ADR-002
- **Decision:** BGE-M3 for all languages
- **Why:** Only model natively handling Hindi and Sanskrit with strong English
- **Alternatives:** nomic-embed (English only), E5 (limited multilingual), Jina (API-dependent)
- **Outcome:** Selected, pending Phase 6 implementation

### Decision: Vector Database
- **ADR:** ADR-003
- **Decision:** Qdrant (production) + Chroma (development)
- **Why:** Qdrant: metadata filtering, Rust performance, snapshots; Chroma: embedded mode
- **Alternatives:** Milvus (overkill), Weaviate (heavier)
- **Outcome:** Selected, pending Phase 7 implementation

### Decision: Retrieval Strategy
- **ADR:** ADR-004
- **Decision:** Hybrid search (BM25 + Vector + Cross-Encoder Reranker)
- **Why:** Strongest evidence-based approach; handles exact + semantic matching
- **Alternatives:** BM25-only (no semantics), vector-only (misses exact terms)
- **Outcome:** Selected, pending Phase 8 implementation

### Decision: Anti-Hallucination Policy
- **ADR:** ADR-005
- **Decision:** RAGAS + DeepEval, sentence-level evidence mapping
- **Why:** Zero fabrication commitment; every answer must trace to source
- **Alternatives:** No grounding (unacceptable), simple keyword matching (insufficient)
- **Outcome:** Policy defined, pending Phase 9 implementation

### Decision: Document Pipeline Design
- **ADR:** ADR-006
- **Decision:** Multi-stage adaptive pipeline with page-level routing
- **Why:** Each page independently classified; native PDFs fast, scanned get OCR
- **Alternatives:** Book-level routing (wrong: pages vary), single extractor (wrong: can't handle all types)
- **Outcome:** Implemented in Phase 3.5, frozen as v1.0

### Decision: Page Classifier Architecture
- **ADR:** ADR-007
- **Decision:** Multi-signal classifier (11+ signals per page)
- **Why:** Single-signal classifier (page.get_text()) was proven wrong in Phase 3.1
- **Lesson:** The initial Phase 3 conclusion of "zero scanned PDFs" was **disproved**
- **Outcome:** Implemented, validated on full corpus

### Decision: Production Pipeline Lock
- **ADR:** ADR-008
- **Decision:** Freeze Document Intelligence v1.0
- **Why:** Validated on 4,721 pages; 0% failure; 100% integrity
- **Impact:** All 10 components frozen; changes require benchmark + ADR + approval
- **Outcome:** Architecture locked, Phase 4 executed

### Decision: Technology Stack
- **ADR:** ADR-009
- **Decision:** Plugin architecture, 26 technologies cataloged, 4 MCP servers
- **Why:** Permanent research capability; evidence-based technology selection
- **Outcome:** Implemented in Phase R1

---

## 2026-07-12

### Decision: Language-Based Processing Tiers
- **ADR:** Config-driven in `config/processing_tiers.json`
- **Decision:** Three tiers — Tier 1 (eng/hin/san full), Tier 2 (other langs register only), Tier 3 (media register only)
- **Why:** Avoid wasting resources on non-English OCR; future promotion via config
- **Alternatives:** Process all languages equally (wasteful), skip non-English entirely (data loss)
- **Outcome:** Implemented, Tier 1 processed through Phase 4

### Decision: Parallel Processing
- **ADR:** Operational decision
- **Decision:** 6-worker parallel processor with checkpoint system
- **Why:** Sequential processing too slow (1 book/5 min); need 5-10x throughput
- **Outcome:** 240 pages/min achieved, checkpoint system operational

### Decision: Quarantine Policy
- **ADR:** Operational decision
- **Decision:** Quarantine with reason, never delete automatically
- **Why:** Preserve all data; allow future re-processing with better tools
- **Outcome:** 55 files quarantined, all preserved

### Decision: Golden Evaluation Dataset
- **ADR:** Phase 2.5 deliverable
- **Decision:** 1,000 representative questions with expected answers
- **Why:** Reproducible evaluation of retrieval quality
- **Outcome:** Generated, stored in knowledge/benchmarks/

---


### Decision: Knowledge Recovery Infrastructure
- **ADR:** ADR-010
- **Decision:** Build complete recovery infrastructure before executing recovery
- **Why:** OCR errors propagate through entire pipeline; recovery must happen before chunking/embeddings
- **Components:** Source Registry, Trust Engine, Knowledge Passport, Recovery Queue, Review Queue, Edition Registry, Verification Interface, Conflict Engine, Confidence Engine, Source Connectors, Provenance Ledger
- **Alternatives:** Skip recovery (rejected: propagates errors), single-source recovery (rejected: insufficient evidence)
- **Outcome:** Infrastructure built, 59 tests passing, ready for actual recovery in future phases

## Key Rejected Ideas

| Idea | Why Rejected |
|------|-------------|
| Process all 751 files identically | Tier 2 languages don't have OCR support; waste resources |
| OCR all pages | Native PDFs extract perfectly; OCR unnecessary |
| Use single OCR engine | No single engine handles all scripts well |
| Trust Phase 3 "zero scanned PDFs" | Disproved by Phase 3.1 multi-signal classifier |
| Delete duplicates | Preserve for provenance; flag as duplicates in registry |

---

*This document is part of the AstroSage Knowledge Engine project and lives at `docs/project/DECISION_LOG.md`.*
