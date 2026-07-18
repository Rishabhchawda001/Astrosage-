# Changelog — AstroSage Knowledge System

## v1.0.0 — Knowledge Freeze (2026-07-18)

### Summary

First immutable release of the AstroSage Knowledge System.
All verified knowledge artifacts are frozen with SHA256 hashes.

### Architecture

- Evidence-first knowledge operating system
- Canonical knowledge freeze at v1.0.0
- Migration-based evolution from this point forward

### Corpus

- 54 scriptures processed
- 4 scriptures with zero coverage (certified unrecoverable)
- 3 scriptures recovered in Phase 9.9 (YOGA_SUTRA, MANU, KATH)
- GRETIL parsed texts as primary extraction source

### Graph

- 391 entities across 14 types
- 54 scripture nodes
- 5,044 relationship edges across 68 types
- 170 dialogues
- 29 events
- 6 concepts
- 76 cross-scripture alignments

### Certification

- 9/11 components: PASS
- 2/11 components: PASS WITH LIMITATIONS
- Coverage limitations: 4 scriptures (KEN, MUND, MAHAN, PARASHARA)
- All limitations documented and certified

### Recovery

- YOGA_SUTRA: Recovered from GRETIL IAST + Bhāṣya
- MANU: Recovered from GRETIL parsed IAST critical edition
- KATH: Recovered from English translation in Upanishads_110.txt

### Freeze

- 28 artifacts frozen to `knowledge/releases/v1.0.0/`
- All artifacts SHA256-hashed
- Reproducibility verified (0 mismatches)

### Known Limitations

- KEN: Category B (OCR unrecoverable)
- MUND: Category B (OCR unrecoverable)
- MAHAN: Category E (missing corpus)
- PARASHARA: Category E (missing corpus)
- Dialogue extraction: relies on known speaker patterns
- Cross-scripture alignment: partially manual

### Future Roadmap

11. Semantic Chunking
12. Embeddings
13. Hybrid Retrieval
14. Reasoning Engine
15. Grounded Answer Generation

---

## Pre-v1.0.0 History

| Phase | Commit | Description |
|-------|--------|-------------|
| 9.9 | 646d3eb | Corpus Completion — 3/7 scriptures recovered |
| 9.8 | 1432a94 | Full Graph Audit — 441 nodes, 4,976 edges |
| 9.7 | 491b2bd | Quality Improvements — 441 nodes, 4,987 edges |
| 9.6 | 0839e03 | Semantic Saturation — 552 nodes, 5,083 edges |
| 9.5 | d2ffe03 | Semantic Extraction Expansion — 543 nodes, 4,816 edges |
| 9.1 | fea1fdd | Knowledge Graph v9.0 — 374 nodes, 7,742 edges |
| 8 | 64c441d | Knowledge Graph v3.0 — 751,218 mentions, 4,755 edges |
