# Backend Component Inventory

**Audit Date:** 2026-07-19

---

## Component Matrix

| # | Component | Location | Purpose | Implementation | Status | Dependencies | Health |
|---|-----------|----------|---------|----------------|--------|-------------|--------|
| 1 | Knowledge Graph | `knowledge/releases/v1.0.0/graph/` | Entity + relationship storage | JSON files | ✅ Complete | None | Healthy |
| 2 | Semantic Chunks | `knowledge/releases/v1.0.0/chunks/` | 120K text chunks at 5 levels | JSON files | ✅ Complete | None | Healthy |
| 3 | BM25 Index | `knowledge/releases/v1.0.0/retrieval/bm25_index.json` | Lexical search | JSON serialized | ✅ Complete | None | Healthy |
| 4 | FAISS Index | `knowledge/releases/v1.0.0/embeddings/faiss_index.bin` | Semantic search | Binary (gitignored) | ⚠️ Missing | faiss-cpu | Not available |
| 5 | Embeddings | `knowledge/releases/v1.0.0/embeddings/embeddings.npy` | Vector representations | Numpy (gitignored) | ⚠️ Missing | numpy | Not available |
| 6 | Chunk Mapping | `knowledge/releases/v1.0.0/embeddings/chunk_id_mapping.json` | ID ↔ index mapping | JSON | ✅ Complete | None | Healthy |
| 7 | Reasoning Engine | `scripts/phase14_reasoning_engine.py` | Entity + question reasoning | Python script | ✅ Complete | graph, chunks, FAISS | Partially (no FAISS) |
| 8 | Answer Generator | `scripts/phase15_answer_generation.py` | Grounded answer generation | Python script | ✅ Complete | graph, chunks, FAISS | Partially (no FAISS) |
| 9 | Query Expansion | `core/query_expansion/engine.py` | Multi-lingual query expansion | Python module | ✅ Complete | graph | Healthy |
| 10 | LRU Cache | `core/cache/lru_cache.py` | Retrieval result caching | Python module | ✅ Complete | None | Healthy |
| 11 | Graph Enrichment | `core/graph_enrichment/enrichment.py` | MENTIONED_IN → specific types | Python module | ✅ Complete | graph | Healthy |
| 12 | Answer Generation (NL) | `core/answer_generation/generator.py` | Template-based NL answers | Python module | ✅ Complete | None | Healthy |
| 13 | Security Auditor | `core/security/audit.py` | Graph integrity + provenance | Python module | ✅ Complete | graph | Healthy |
| 14 | Evaluation Runner | `evaluation/runner.py` | Full evaluation orchestration | Python script | ✅ Complete | graph, mock search | Healthy |
| 15 | Golden Dataset | `evaluation/golden_dataset.json` | 100 Q&A evaluation pairs | JSON | ✅ Complete | None | Healthy |
| 16 | Quality Gates | `evaluation/quality_gates.py` | Release pass/fail criteria | Python module | ✅ Complete | None | Healthy |
| 17 | Retrieval Evaluator | `evaluation/retrieval_eval.py` | P@k, R@k, NDCG@k | Python module | ✅ Complete | None | Healthy |
| 18 | Hallucination Evaluator | `evaluation/hallucination_eval.py` | Adversarial query detection | Python module | ✅ Complete | None | Healthy |
| 19 | Regression Evaluator | `evaluation/regression_eval.py` | Baseline comparison | Python module | ✅ Complete | None | Healthy |
| 20 | Explainability Engine | `evaluation/explainability.py` | Reasoning trace generation | Python module | ✅ Complete | None | Healthy |

---

## Missing Components (Required for Production)

| # | Component | Purpose | Priority | Impact |
|---|-----------|---------|----------|--------|
| 1 | **API Server** (FastAPI) | HTTP/REST endpoints for frontend | CRITICAL | Cannot serve frontend |
| 2 | **Authentication** | User management, API keys, JWT | CRITICAL | No access control |
| 3 | **Docker** | Containerized deployment | HIGH | No reproducible deployment |
| 4 | **CI/CD Pipeline** | Automated testing + deployment | HIGH | No deployment automation |
| 5 | **Rate Limiting** | API abuse prevention | HIGH | No DoS protection |
| 6 | **Monitoring** | Metrics, logging, alerting | MEDIUM | No observability |
| 7 | **Real Pipeline Integration** | Connect core modules to API | HIGH | Modules exist but unused |
| 8 | **Streaming Responses** | Server-sent events for answers | MEDIUM | No real-time answers |
| 9 | **WebSocket** | Real-time search updates | LOW | No live updates |
| 10 | **Background Workers** | Async embedding/reasoning | LOW | Batch-only currently |

---

## Dependency Matrix

```
API Server (MISSING)
  ├── Authentication (MISSING)
  ├── Rate Limiting (MISSING)
  ├── Streaming (MISSING)
  └── Query Pipeline
       ├── Query Expansion ✅
       ├── LRU Cache ✅
       ├── BM25 Search ✅
       ├── FAISS Search ⚠️ (index missing from repo)
       ├── Hybrid Fusion (embedded in phase13)
       ├── Reasoning Engine ✅
       ├── Answer Generator (NL) ✅
       └── Security Auditor ✅
```
