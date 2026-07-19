# Backend Performance Report

**Audit Date:** 2026-07-19

---

## Component Load Times

| Component | Load Time | Memory | Notes |
|-----------|-----------|--------|-------|
| Knowledge Graph (JSON) | 82ms | ~15 MB | 445 nodes, 5,044 edges |
| Chunks (JSON) | 1,150ms | ~80 MB | 120,548 chunks from 86 files |
| BM25 Index (JSON) | 350ms | ~30 MB | 375,327 vocab tokens |
| Reasoning Results | 10ms | <1 MB | 5 entity + 4 question results |
| Answer Results | 3ms | <1 MB | 5 pre-computed answers |
| **Total (JSON only)** | **1,595ms** | **~126 MB** | No FAISS, no model |
| FAISS Index | ~2,000ms (est.) | ~500 MB (est.) | 120K × 384d vectors |
| MiniLM Model | ~3,000ms (est.) | ~900 MB (est.) | all-MiniLM-L6-v2 |
| **Total (full pipeline)** | **~5.6s (est.)** | **~1.5 GB (est.)** | Complete system |

---

## Search Latency (from quality gates)

| Metric | Measured | Threshold | Status |
|--------|----------|-----------|--------|
| Retrieval P95 Latency | 16.5ms | <100ms | ✅ PASS |
| BM25 Tokenization | 0.01ms/query | N/A | Excellent |
| BM25 Search (full) | ~5-15ms (est.) | N/A | Fast (in-memory) |
| FAISS Search (full) | ~1-5ms (est.) | N/A | Fast (in-memory) |
| Hybrid Fusion | <1ms | N/A | Trivial |

**Note:** Search latency is measured on the evaluation runner's mock search, not the real BM25+FAISS pipeline.

---

## Throughput Estimates

| Operation | Estimated Throughput | Notes |
|-----------|---------------------|-------|
| BM25 search only | ~200 queries/sec | In-memory, no FAISS |
| FAISS search only | ~500 queries/sec | Vector index |
| Hybrid search | ~100 queries/sec | Combined |
| Full pipeline (search + reasoning) | ~20 queries/sec | With evidence assembly |
| Concurrent requests (estimated) | ~10-20 | Single-process Python |

---

## Memory Profile

| Component | RSS (current) | Notes |
|-----------|---------------|-------|
| Python process (basic) | 403 MB | After loading graph + chunks + BM25 |
| + FAISS index | ~900 MB (est.) | 120K × 384d × 4 bytes |
| + SentenceTransformer | ~1.3 GB (est.) | Model weights |
| **Total estimated** | **~1.5 GB** | For full pipeline |

---

## Performance Bottlenecks

1. **Chunk loading (1.15s):** 120K chunks loaded from 86 JSON files. Could be optimized with a single binary format.
2. **BM25 loading (350ms):** 375K vocab loaded from JSON. Could use msgpack or binary format.
3. **Model loading (~3s):** SentenceTransformer cold start. Could use ONNX Runtime for faster loading.
4. **No caching in real pipeline:** The LRU cache module exists but is not integrated.
5. **Single-process architecture:** No async, no worker pool, no connection pooling.

---

## Scalability Assessment

| Dimension | Current | Required for Production |
|-----------|---------|------------------------|
| Concurrent users | 1 (script) | 100+ |
| Queries per second | ~20 (est.) | 100+ |
| Memory per request | ~1.5 GB (shared) | ~100 MB per connection |
| Horizontal scaling | Not possible | Multiple workers/pods |
| Load balancing | N/A | Required |
| Database connection pooling | N/A | Required |

---

## Performance Score: 4/10

Strengths:
- Fast BM25 search (in-memory)
- Fast FAISS search (in-memory)
- All quality gate latency thresholds met

Weaknesses:
- No API server to measure real throughput
- No concurrent request handling
- No caching integration
- Large memory footprint for single process
- No binary serialization for fast loading
