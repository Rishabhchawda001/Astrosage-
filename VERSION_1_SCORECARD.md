# AstroSage Version 1.0 — Scorecard

**Audit Date**: 2026-07-19
**Auditor**: Independent Verification Board

---

## Scores (0–100)

| Category | Score | Justification |
|----------|-------|---------------|
| Knowledge Quality | 78 | 391 entities, 68 relationship types, 170 dialogues, 29 events across 54 scriptures. 4 scriptures with zero coverage (certified unrecoverable). Cross-scripture alignment covers 76 alignments. Solid coverage for core texts; limited by corpus availability. |
| Corpus Quality | 72 | 54 scriptures processed. 3 recovered in Phase 9.9. 4 certified unrecoverable (KEN, MUND, MAHAN, PARASHARA). GRETIL IAST as primary source — high quality for available texts. OCR artifacts present in some verse files. |
| Retrieval Quality | 82 | Hybrid BM25+FAISS with 375K vocabulary. Average latency 38ms. Fusion scoring with alpha=0.6. Top results are semantically relevant. Some short verse chunks score high on pure semantic similarity despite low information content. |
| Reasoning Quality | 75 | Entity reasoning traces 57 relationships for Vishnu with evidence chains. Question reasoning combines graph traversal with semantic retrieval. Confidence scoring present. No LLM-based reasoning — rule-based evidence chaining only. |
| Evidence Quality | 85 | Every edge has evidence and confidence fields. Every entity has source scriptures. Graph validation: PASS. Zero orphan nodes, zero broken references, zero duplicate GUIDs. |
| Citation Quality | 72 | Grounded answers reference 11.2 average sources. Scripture attribution present. Canonical unit references present in verse chunks. Some dialogue chunks have limited verse range specificity. |
| Performance | 88 | Search: 38ms avg, 64ms max. Graph load: 30ms. Entity lookup: 0.003ms. Embedding: 84ms/query. All within acceptable production bounds. CPU-only (no GPU). |
| Reliability | 80 | All pipeline scripts run successfully. Artifacts reproducible. FAISS index loads correctly. BM25 index loads correctly. Graceful handling of missing files. No crashes during testing. |
| Maintainability | 70 | Migration framework exists. Versioned releases. AI operating layer. Self-indexing. However, some metadata references stale commits. Documentation gaps (README.md). |
| Documentation | 55 | Missing README.md. Stale self-index references. Good freeze policy, AI contract, changelog, certification. Scripts well-documented with usage. Architecture docs exist but not all referenced. |
| Reproducibility | 85 | Deterministic chunk IDs via SHA256. All artifacts SHA256-hashed. Frozen release immutable. Embeddings reproducible from model + chunks. FAISS index reproducible. Knowledge manifest captures all metadata. |
| Overall Readiness | 75 | Functionally complete for v1.0.0 scope. Documentation and self-indexing need updates. No hallucinations detected. Provenance tracing working. Ready for knowledge freeze with documentation fixes. |

---

## Grade: B+

AstroSage v1.0.0 delivers a verified, evidence-first knowledge system for Hindu scriptures.
The core technical stack is solid. Documentation and self-indexing need attention.
The knowledge layer is frozen and reproducible. The system is ready for production use
with the understanding that 4 scriptures remain unrecoverable (documented).
