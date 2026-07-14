# AstroSage Knowledge Engine — Project Roadmap

**Last Updated:** 2026-07-12
**Status:** ✅ ACTIVE

---

## Phase Status

| Phase | Name | Status | Tests |
|-------|------|--------|-------|
| Phase 0–3 | Foundation | ✅ Complete | — |
| Phase 1 | Knowledge Acquisition | ✅ Complete | — |
| Phase 2 | Knowledge Normalization | ✅ Complete | 41 |
| Phase 2.5 | Corpus Intelligence | ✅ Complete | 55 |
| Phase 3 | Document Intelligence Lab | ✅ Complete | 66 |
| Phase 3.1 | Document Forensics | ✅ Complete | 91 |
| Phase 3.5 | Production Pipeline Validation | ✅ Complete | 108 |
| Phase R1 | Research Stack & MCP | ✅ Complete | 134 |
| Phase 4 | Production Document Processing | ✅ Complete | 134 |
| Phase M1 | Permanent Agent Memory | ✅ Complete | 134 |
| Phase 4.5 | Knowledge Recovery Infrastructure | ✅ Complete | 193 |
| Phase 5 | Semantic Chunking | ⏳ Pending | — |
| Phase 6 | Embeddings | ⏳ Pending | — |
| Phase 7 | Vector Indexing | ⏳ Pending | — |
| Phase 8 | Retrieval Pipeline | ⏳ Pending | — |
| Phase 9 | Grounding & Anti-Hallucination | ⏳ Pending | — |
| Phase 10 | MCP Integration | ⏳ Pending | — |
| Phase 11 | Knowledge Graph | ⏳ Pending | — |
| Phase 12 | User Interface | ⏳ Pending | — |

---

## Current Status (Post Phase 4)

### What's Complete
- ✅ 751 source files downloaded and archived
- ✅ 601/602 PDFs processed (99.8%)
- ✅ 920 bronze files (extracted text)
- ✅ 920 silver files (structured markdown)
- ✅ Document Intelligence v1.0 frozen and locked
- ✅ Production pipeline certified (GO decision)
- ✅ 26 technologies cataloged and scored
- ✅ Plugin architecture implemented
- ✅ 4 MCP server plugins
- ✅ 134 tests passing
- ✅ GitHub synchronized

### What's Not Started
- ❌ Semantic chunking (gold layer)
- ❌ Embedding generation
- ❌ Vector indexing
- ❌ Retrieval pipeline
- ❌ Grounding/anti-hallucination
- ❌ Knowledge graph
- ❌ User interface

---

## Phase 5: Semantic Chunking (Next Major Phase)

### Objective
Convert silver-layer structured documents into semantically meaningful chunks for embedding and retrieval.

### Key Decisions
- Chunking strategy: Semantic boundaries (not fixed token windows)
- Preserve: page references, chapter structure, verse boundaries
- Preserve: citations, footnotes, references
- Never split mid-verse or mid-citation

### Dependencies
- Phase 4 complete (Knowledge Lake populated)
- Bronze/silver layers stable

---

## Phase 6: Embeddings

### Objective
Generate vector embeddings for all chunks using BGE-M3.

### Key Decisions
- Model: BGE-M3 (multilingual, supports Hindi/Sanskrit/English)
- Dense + sparse embeddings for hybrid search
- Store embeddings in gold layer
- Qdrant for production, Chroma for development

### Dependencies
- Phase 5 (chunks available)
- BGE-M3 model downloaded and tested

---

## Phase 7–8: Vector Indexing & Retrieval

### Objective
Build hybrid retrieval (BM25 + Vector + Cross-Encoder Reranker).

### Key Decisions
- Hybrid search: BM25 + dense vector + reranker
- Metadata filtering: by document, language, chapter, etc.
- Top-20 retrieval → cross-encoder rerank → top-5

### Dependencies
- Phase 6 (embeddings generated)
- Qdrant/Chroma configured

---

## Phase 9: Grounding & Anti-Hallucination

### Objective
Every answer must be evidence-backed with sentence-level citations.

### Key Decisions
- Use RAGAS faithfulness metric
- Use DeepEval hallucination detection
- Every sentence maps to retrieved source material
- Unsupported sentences removed
- Fallback: "The indexed knowledge base does not contain sufficient evidence to answer this question."

### Dependencies
- Phase 8 (retrieval working)

---

## Phase 10: MCP Integration

### Objective
Expose the knowledge engine through MCP tools for AI assistants.

### Tools to Expose
- search_books, search_pages, list_books
- compare_sources, verify_answer
- sync_library, reindex
- pipeline_status, audit_status
- ocr_statistics, index_statistics
- knowledge_graph

### Dependencies
- Phase 9 (grounded retrieval working)

---

## Phase 11: Knowledge Graph

### Objective
Build a knowledge graph connecting books, chapters, verses, people, places, concepts, scriptures.

### Dependencies
- Phase 5 (structured chunks)
- Entity extraction capabilities

---

## Phase 12: User Interface

### Objective
Build a web interface for interacting with the Knowledge Engine.

### Dependencies
- Phase 10 (MCP working)

---

## Critical Path
```
Phase 4.5 (recovery infra) → Phase 5 (chunking) → Phase 6 (embeddings) → Phase 7–8 (vector/retrieval) → Phase 9 (grounding) → Phase 10 (MCP)
```

---


## Phase 4.5: Knowledge Recovery Infrastructure (Complete)

### Objective
Build the complete Knowledge Recovery Infrastructure — frameworks, interfaces, registries, queues, schemas, plugin contracts, confidence models, verification models, and provenance ledger.

### Key Components
- Knowledge Source Registry (5 default sources: Internet Archive, Open Library, Crossref, OpenAlex, Wikidata)
- Trust Engine (configurable weights for source, edition, OCR, recovery, verification trust)
- Knowledge Passport (complete provenance for recovered knowledge objects)
- Recovery Queue (priority-based with retry and checkpointing)
- Human Review Queue (5 states: pending, approved, rejected, deferred, needs_more_evidence)
- Edition Registry (8 edition types, 7 relationship types)
- Verification Interface (ABC-based, DefaultVerification with character/word similarity)
- Conflict Engine (4 severity levels, stores all variants)
- Confidence Engine (6 component types, configurable weights)
- Source Connectors (4 stub connectors, ABC-based plugin interfaces)
- Knowledge Provenance Ledger (11 entry types, append-only, chain tracing)
- Plugin interfaces for recovery, verification, and source connectors

### Tests
59 new tests added, all passing. Total: 193 tests.

### Dependencies
- Phase 4 complete (Knowledge Lake populated)

### What's Next
- Phase 5: Semantic Chunking (now unblocked)

## Blocked Work
- Phase 5+ blocked until Phase 4.5 complete
- Full corpus processing for Tier 2 languages blocked until OCR support added
- Knowledge graph blocked on entity extraction model selection

---

## Repository Status
- **Branch:** main (trunk-based)
- **Latest commit:** `bb3343e` (Phase 4 fixup)
- **Tests:** 134 passing
- **Working tree:** Clean (after stash)
- **Remote:** `https://github.com/Rishabhchawda001/Astrosage-.git`

---

*This document is part of the AstroSage Knowledge Engine project and lives at `docs/project/PROJECT_ROADMAP.md`.*
