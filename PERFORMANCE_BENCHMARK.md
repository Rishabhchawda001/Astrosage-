# Performance Benchmark — Phase 21

**Date:** 2026-07-14

## Pipeline Speed

| Operation | Time |
|-----------|------|
| CKU recomputation (635 files) | ~47s |
| Silver quality inspection | ~15s |
| Test suite (792 tests) | ~44s |
| Connector health check (8 connectors) | ~6s |
| Duplicate detection | ~30s |
| Alignment pipeline (76 editions) | ~281s |

## Connector Latency

| Connector | Latency |
|-----------|---------|
| Internet Archive | 0.5s |
| Open Library | 0.7s |
| Crossref | 0.5s |
| OpenAlex | 1.0s |
| Wikidata | 0.4s |
| GitHub | 0.6s |
| arXiv | 0.6s |
| Google Books | 1.2s |
| **Average** | **0.69s** |

## Resource Usage

| Resource | Usage |
|----------|-------|
| RAM (peak during alignment) | ~8.5 GB |
| Disk (repo total) | 14 GB |
| Disk (free) | 25 GB |
| CPU cores available | 8 |

## Storage Efficiency

| Component | Size | Per File |
|-----------|------|----------|
| Silver | 853 MB | 1.3 MB |
| Bronze | 709 MB | 1.1 MB |
| Downloads | 451 MB | 2.4 MB |
| External Bronze | 391 MB | 3.3 MB |

## Conclusion

Pipeline performs well within resource constraints. Connector latency is acceptable for batch operations. Memory usage is the primary constraint for large-scale alignment.
