# Backend Execution Report

**Audit Date:** 2026-07-19

---

## Execution Verification Results

Every backend component was actually executed (not just code-reviewed).

### ✅ PASSED

| Component | Test | Result | Latency |
|-----------|------|--------|---------|
| Knowledge Graph Load | Load graph.json, count nodes/edges | 445 nodes, 5,044 edges | 82ms |
| Entity Nodes | Load entity_nodes.json | 391 entities, 14 types | 15ms |
| Scripture Nodes | Load scripture_nodes.json | 54 scriptures | 2ms |
| Relationship Edges | Load relationship_edges.json | 5,044 edges, 68 types | 20ms |
| Chunks Load | Load all 4 chunk files + 82 verse files | 120,548 chunks | 1,150ms |
| BM25 Index Load | Load bm25_index.json | 375,327 vocab, 120,548 docs | 350ms |
| BM25 Tokenization | Tokenize 100 queries | ~0.01ms/query | <1ms |
| Reasoning Results | Load entity + question reasoning | 5 entities, 4 questions | 10ms |
| Grounded Answers | Load grounded_answers.json | 5 answers | 3ms |
| Query Expansion | Expand "Who is Krishna?" | 3 expanded terms, confidence=0.3 | 5ms |
| LRU Cache | Set/Get/Stats | Working, 100% hit rate | <1ms |
| Graph Enrichment | Analyze 5,044 edges | 3,779 enrichment proposals | 15ms |
| Security Audit | 8 checks on graph | 6 passed, 2 failed | 50ms |
| All Tests | pytest tests/ | 892 passed, 8 skipped | 66.7s |

### ❌ FAILED / NOT AVAILABLE

| Component | Issue | Impact |
|-----------|-------|--------|
| FAISS Index | `faiss_index.bin` not in repository (gitignored) | Cannot run real semantic search |
| Embeddings NPY | `embeddings.npy` not in repository (gitignored) | Cannot load precomputed embeddings |
| Real Hybrid Search | Requires FAISS index | Cannot execute end-to-end |
| API Server | Does not exist | Cannot serve any HTTP requests |
| Docker | Does not exist | Cannot containerize |
| Authentication | Does not exist | No access control |

### ⚠️ PARTIAL

| Component | Status | Notes |
|-----------|--------|-------|
| Reasoning Engine | Pre-computed results only | Real-time reasoning requires FAISS |
| Answer Generation | Pre-computed results only | Real-time answers require FAISS |
| Evaluation Runner | Uses mock search | Not testing real retrieval pipeline |

---

## Cold Start Timing

| Phase | Time | Notes |
|-------|------|-------|
| Graph load | 82ms | JSON parse |
| Chunks load | 1,150ms | 120K chunks from JSON |
| BM25 index load | 350ms | 375K vocab |
| Reasoning results | 10ms | Pre-computed |
| **Subtotal (JSON only)** | **1,592ms** | No FAISS |
| FAISS index load | ~2,000ms | Estimated (not in repo) |
| Model load (MiniLM) | ~3,000ms | Estimated |
| **Total (full pipeline)** | **~5.6s** | Estimated |

---

## Memory Profile

| Metric | Value |
|--------|-------|
| RSS (current process) | 403 MB |
| Graph JSON in memory | ~15 MB |
| Chunks JSON in memory | ~80 MB |
| BM25 data in memory | ~30 MB |
| **Estimated full pipeline** | **~1.5 GB** |

---

## Test Suite Results

```
Platform: linux | Python 3.12.3 | pytest 9.1.1
892 passed, 8 skipped in 66.68s

Skipped tests (expected):
- 5 tests: No PDFs found (test_phase31.py)
- 2 tests: No raw source library found (test_phase35.py)
- 1 test: Skipped (test_phase35.py)
```

---

## Quality Gate Results (from evaluation/evaluation_report.json)

| Gate | Threshold | Actual | Status |
|------|-----------|--------|--------|
| Retrieval P95 Latency | <100ms | 16.5ms | ✅ PASS |
| Entity Recall | ≥30% | 68.3% | ✅ PASS |
| NDCG@5 | ≥0.3 | 0.994 | ✅ PASS |
| Hallucination Rejection | ≥80% | 100% | ✅ PASS |
| Max Adversarial Confidence | <0.6 | 0.25 | ✅ PASS |
| Regression Rate | <10% | 0% | ✅ PASS |
| Graph Integrity | 100% | 100% | ✅ PASS |
| Test Pass Rate | ≥95% | 100% | ✅ PASS |

**Note:** These metrics are based on the evaluation runner's mock search, not the real BM25+FAISS pipeline.
