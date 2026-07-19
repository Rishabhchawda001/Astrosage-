# AstroSage Version 1.0 — Known Limitations

**Audit Date**: 2026-07-19

---

## 1. Corpus Limitations

| Scripture ID | Name | Classification | Reason |
|-------------|------|---------------|--------|
| KEN | Kena Upanishad | B (OCR unrecoverable) | OCR quality prevents reliable extraction |
| MUND | Mundaka Upanishad | B (OCR unrecoverable) | OCR quality prevents reliable extraction |
| MAHAN | Mahanarayana Upanishad | E (Missing corpus) | No authoritative corpus in repository |
| PARASHARA | Parashara Smriti | E (Missing corpus) | No authoritative corpus in repository |

**Impact**: 4 out of 54 scriptures (7.4%) have zero coverage.
**Resolution**: Requires future corpus discovery and verification pipeline.

---

## 2. Graph Limitations

| Limitation | Description | Priority |
|------------|-------------|----------|
| MENTIONED_IN dominance | 94.4% of edges (4,763/5,044) are generic MENTIONED_IN relationships | Medium |
| Limited genealogical depth | 84 genealogy edges — some dynasties incomplete | Low |
| Event count (29) | May undercount due to conservative extraction | Low |
| No astronomy entries | 0 entries in astronomy graph — schema exists but data missing | Low |
| Limited geography | 0 entries in geography graph — schema exists but data missing | Low |

---

## 3. Chunking Limitations

| Limitation | Description | Priority |
|------------|-------------|----------|
| Verse granularity | 119,904 verse chunks (99.5%) — very fine granularity | Low |
| Short text chunks | Average 135 characters per chunk | Medium |
| No multi-verse spans | Each verse is a separate chunk (except dialogue/event) | Low |
| OCR artifacts | Some verse text includes OCR noise | Medium |

---

## 4. Retrieval Limitations

| Limitation | Description | Priority |
|------------|-------------|----------|
| CPU-only inference | 84ms per query embedding, 6s model load | Low |
| BM25 type ambiguity | 6 tokens indexed as single types — vocab may be structured differently | Medium |
| No query expansion | No synonym/thesaurus expansion for Sanskrit terms | Low |
| No cross-lingual search | No Devanagari-IAST bridging | Medium |

---

## 5. Reasoning Limitations

| Limitation | Description | Priority |
|------------|-------------|----------|
| Rule-based only | No LLM/neural reasoning augmenting | Medium |
| Confidence binary | medium/high only — no continuous confidence scores | Low |
| No temporal reasoning | Event ordering/timelines not implemented | Low |
| No causal reasoning | Cause-effect chains not extracted | Low |

---

## 6. Answer Generation Limitations

| Limitation | Description | Priority |
|------------|-------------|----------|
| No natural language generation | Answers are evidence-structure dumps, not prose | Medium |
| No multi-turn context | Each query independent | Low |
| No formatting | Evidence in raw JSON/structured format | Low |

---

## 7. Infrastructure Limitations

| Limitation | Description | Priority |
|------------|-------------|----------|
| No API server | No REST/gRPC interface | Low |
| No async processing | Synchronous only | Low |
| No caching | Every query re-encodes and re-searches | Medium |
| No monitoring | No metrics, logging, or alerts | Low |
| No CI/CD | Manual deployment | Low |

---

## 8. Documentation Limitations

| Limitation | Description | Priority |
|------------|-------------|----------|
| README.md missing | No entry point for new users | High |
| Self-index stale | References old commit hashes | Medium |
| Architecture docs | Partial — not all subsystems documented | Low |

---

## 9. Certification Status

| Subsystem | Status |
|-----------|--------|
| Graph Structure | ✅ PASS |
| Entity Registry | ✅ PASS |
| Relationship Registry | ✅ PASS |
| Dialogue Graph | ✅ PASS |
| Event Graph | ✅ PASS |
| Genealogy Graph | ✅ PASS |
| Concept Graph | ✅ PASS (with schema gaps) |
| Cross-Scripture Alignment | ✅ PASS |
| Corpus Completion | ⚠️ PASS WITH LIMITATIONS |
| Coverage | ⚠️ PASS WITH LIMITATIONS |
| Knowledge Freeze | ✅ PASS |
| Reproducibility | ✅ PASS |

---

**Note**: All limitations are documented, categorized, and have clear resolution paths.
No limitation prevents Version 1.0 certification. Limitations are tracked for
future version planning and are not blockers for the knowledge freeze.
