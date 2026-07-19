# Project State — AstroSage

**Last Updated**: 2026-07-19T12:00:00+00:00
**Git Commit**: HEAD
**Knowledge Version**: 1.0.0
**Current Phase**: Version 1.1 — Evaluation Framework
**Status**: ✅ EVALUATION FRAMEWORK COMPLETE

## Repository State

- Knowledge Graph: 391 entities, 54 scriptures, 5,044 edges
- Knowledge Layer: FROZEN at v1.0.0
- Semantic Chunks: 120,548 chunks
- Embeddings: 120,548 vectors (MiniLM-L6-v2, 384d)
- FAISS Index: 120,548 vectors
- Hybrid Retrieval: BM25 (375K vocab) + FAISS
- Reasoning Engine: Entity + Question reasoning
- Answer Generation: Provenance-traced, high confidence
- Evaluation Framework: v1.1 complete
- Tests: 815 passed (784 existing + 31 evaluation)

## Quick Navigation

| Need | Location |
|------|----------|
| Frozen knowledge | `knowledge/releases/v1.0.0/` |
| Embeddings | `knowledge/releases/v1.0.0/embeddings/` |
| Retrieval | `knowledge/releases/v1.0.0/retrieval/` |
| Reasoning | `knowledge/releases/v1.0.0/reasoning/` |
| Answers | `knowledge/releases/v1.0.0/answers/` |
| Evaluation | `evaluation/` |
| Golden dataset | `evaluation/golden_dataset.json` |
| Eval report | `evaluation/evaluation_report.json` |
| AI Contract | `AI_KNOWLEDGE_CONTRACT.md` |
| Certification | `FINAL_KNOWLEDGE_CERTIFICATION.md` |
| Acceptance Audit | `VERSION_1_ACCEPTANCE_REPORT.md` |
| Scorecard | `VERSION_1_SCORECARD.md` |
| Benchmarks | `FINAL_BENCHMARK_RESULTS.md` |
| Known Limitations | `KNOWN_LIMITATIONS.md` |
