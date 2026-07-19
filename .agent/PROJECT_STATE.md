# Project State — AstroSage

**Last Updated**: 2026-07-19T23:30:00+00:00
**Git Commit**: 24ded48
**Knowledge Version**: 1.0.0
**Current Phase**: Phase 5 — Web UI Frontend
**Status**: ✅ API Production-Ready (8/8 Quality Gates PASS)

## Repository State

- Knowledge Graph: 391 entities, 54 scriptures, 5,044 edges
- Knowledge Layer: FROZEN at v1.0.0
- Semantic Chunks: 120,548 chunks
- Embeddings: 120,548 vectors (MiniLM-L6-v2, 384d)
- BM25 Search: rank-bm25 with entity-guided pre-filtering (1.5ms P95)
- Query Expansion: Sanskrit/Hindi/English term bridging
- Adversarial Detection: Non-Hindu texts, out-of-domain topics, entity-less queries
- Hallucination Rejection: 100% on adversarial queries
- API: FastAPI with 16+ endpoints, JWT auth, streaming, caching
- Web UI: Vanilla JS SPA with chat, search, conversation management
- MCP Server: 7 tools, stdio + SSE modes
- Tests: 59 API + 858 knowledge = 917 passing

## Quick Navigation

| Need | Location |
|------|----------|
| Frozen knowledge | `knowledge/releases/v1.0.0/` |
| API server | `api/main.py` |
| Knowledge services | `api/services/knowledge.py` |
| Evaluation | `evaluation/` |
| Real pipeline eval | `evaluation/real_pipeline_eval.py` |
| Golden dataset | `evaluation/golden_dataset.json` |
| Query expansion | `core/query_expansion/engine.py` |
| MCP server | `mcp_server.py` |
| Web UI | `api/static/index.html` |
| AI Contract | `AI_KNOWLEDGE_CONTRACT.md` |
| Certification | `FINAL_KNOWLEDGE_CERTIFICATION.md` |

## Remaining Roadmap Items

| Phase | What | Status |
|-------|------|--------|
| 2.4 | Meilisearch full-text search | Not started |
| 2.5 | Unified search service | Not started |
| 3.1 | Mem0 user memory | Not started |
| 6 | Quality (golden dataset expansion, CI benchmarks) | Partially done |
| 7 | Security hardening | Not started |
| 8 | Release & launch | Not started |
