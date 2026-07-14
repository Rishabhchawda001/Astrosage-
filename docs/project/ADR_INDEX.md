# AstroSage Knowledge Engine — ADR Index

**Last Updated:** 2026-07-12

---

## All Architecture Decision Records

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| ADR-001 | Document Extraction Strategy | ✅ Accepted | 2026-07-11 |
| ADR-002 | Embedding Model Selection | ✅ Accepted | 2026-07-11 |
| ADR-003 | Vector Database Selection | ✅ Accepted | 2026-07-11 |
| ADR-004 | Retrieval Strategy | ✅ Accepted | 2026-07-11 |
| ADR-005 | Grounding and Anti-Hallucination Policy | ✅ Accepted | 2026-07-11 |
| ADR-006 | Document Processing Pipeline | ✅ Accepted | 2026-07-11 |
| ADR-007 | Forensic Validation of Document Classification | ✅ Accepted | 2026-07-11 |
| ADR-008 | Production Pipeline Architecture Lock | ✅ Accepted | 2026-07-12 |
| ADR-009 | Research Stack & MCP Ecosystem | ✅ Accepted | 2026-07-12 |
| ADR-010 | Knowledge Recovery Infrastructure | ✅ Accepted | 2026-07-12 |

---

## Summary by Topic

### Extraction & Processing
- **ADR-001:** Adaptive extraction pipeline (PyMuPDF for native, PaddleOCR for scanned)
- **ADR-006:** Document processing pipeline design (classifier → routing → extraction → validation)
- **ADR-008:** Production pipeline frozen as Document Intelligence v1.0

### Embeddings & Vectors
- **ADR-002:** BGE-M3 selected for multilingual embedding (Hindi/Sanskrit/English)
- **ADR-003:** Qdrant (production) + Chroma (dev) for vector storage

### Retrieval & Grounding
- **ADR-004:** Hybrid search (BM25 + Vector + Cross-Encoder Reranker)
- **ADR-005:** Anti-hallucination policy (RAGAS + DeepEval, sentence-level evidence)

### Recovery & Verification
- **ADR-010:** Knowledge Recovery Infrastructure — Source Registry, Trust Engine, Provenance Ledger, Conflict Engine

### Architecture & Research
- **ADR-007:** Multi-signal page classifier validated (disproved "zero scanned PDFs")
- **ADR-009:** Plugin architecture, technology scoring, MCP servers

---

## Superseded ADRs
None currently.

## Deprecated ADRs
None currently.

## Pending ADRs
None currently.

---

*All ADRs are in the `adrs/` directory at the repository root.*
