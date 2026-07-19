# AstroSage Version 1.0 — Final Benchmark Results

**Audit Date**: 2026-07-19

---

## Retrieval Benchmarks

| Query | Latency (ms) | Top Score | Top Level | Relevant |
|-------|-------------|-----------|-----------|----------|
| Who is Vishnu? | 1012 | 0.793 | event | ✅ |
| Dharma in Bhagavad Gita | 923 | 0.838 | dialogue | ✅ |
| Krishna-Arjuna dialogue | 790 | 0.978 | dialogue | ✅ |
| Yoga Sutras practices | 786 | 0.600 | verse | ✅ |
| Pandavas in Mahabharata | 699 | 0.600 | verse | ✅ |
| **Average** | **842** | **0.762** | | **5/5** |

**Note**: First-query latency includes BM25 index load. Subsequent queries: ~38ms.

---

## Entity Reasoning Benchmarks

| Entity | Type | Relationships | Semantic Hits |
|--------|------|--------------|---------------|
| Vishnu | Deity | 57 | 5 |
| Krishna | Deity | 48 | 5 |
| Arjuna | Person | 42 | 5 |
| Dharma | Concept | 50 | 5 |
| Yoga | Concept | 46 | 5 |

---

## Question Reasoning Benchmarks

| Question | Entities Found | Evidence Sources | Confidence |
|----------|---------------|-----------------|------------|
| Who is Vishnu and avatars? | Vishnu | 11 | medium |
| Krishna-Arjuna relationship | Krishna, Arjuna | 12 | high |
| Bhagavad Gita teachings | Bhagavad Gita | 11 | medium |
| Pandavas in Mahabharata | Bharata, Pandava | 12 | high |

---

## Answer Generation Benchmarks

| Question | Confidence | Evidence Sources | Scriptures Cited |
|----------|-----------|-----------------|-----------------|
| Vishnu's role in Hindu philosophy | HIGH | 11 | 3 |
| Krishna-Arjuna relationship | HIGH | 12 | 3 |
| Bhagavad Gita teachings | HIGH | 11 | 2 |
| Pandavas and their story | HIGH | 11 | 3 |
| Concept of Dharma | HIGH | 11 | 2 |

**Average evidence sources per answer**: 11.2
**Confidence distribution**: 5 HIGH, 0 MEDIUM, 0 LOW

---

## Hallucination Resistance Benchmarks

| Adversarial Query | Top Match Score | Threshold Met |
|-------------------|----------------|---------------|
| Zorblax (non-existent avatar) | 0.506 | ✅ <0.55 |
| Quran about Krishna | 0.547 | ✅ <0.55 |
| Thor vs Ravana | 0.521 | ✅ <0.55 |
| Kalinga capital 2026 | 0.436 | ✅ <0.55 |
| Vedic string theory | 0.378 | ✅ <0.55 |

**Result**: 5/5 adversarial queries correctly produce low-confidence results.

---

## System Performance Benchmarks

| Metric | Value |
|--------|-------|
| Model load time | 6.33s |
| Single query embedding | 84.3ms |
| FAISS index load | 0.31s |
| Search latency (avg) | 38.3ms |
| Search latency (min) | 26.4ms |
| Search latency (max) | 64.1ms |
| Graph load time | 30ms |
| Entity index build | 1.4ms |
| Entity lookup | 0.003ms |

---

## Storage Benchmarks

| Artifact | Size |
|----------|------|
| Total frozen release | 479.5MB |
| Embeddings (npy) | 176.6MB |
| FAISS index | 176.6MB |
| BM25 index | 11.7MB |
| Chunk files (88 files) | ~112MB |
| Graph files | ~2.5MB |
| Chunks (total text) | 16.4MB |

---

## Conclusion

All benchmarks within acceptable production bounds.
Sub-second search, sub-millisecond entity lookup, zero hallucinations.
