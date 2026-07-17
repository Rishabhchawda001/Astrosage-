# Benchmark Report — Phase 9.7

Generated: 2026-07-17T16:36:47.267763

## Before vs After

| Metric | Phase 9.6 | Phase 9.7 | Change |
|--------|-----------|-----------|--------|
| Entities | 498 | 387 | -111 |
| Total Edges | 5084 | 4987 | -97 |
| Edge Types | 61 | 68 | +7 |
| Dialogues | 62 | 170 | +108 |
| Events | 29 | 29 | +0 |
| Genealogy Edges | 84 | 84 | +0 |
| Concept Edges | 70 | 70 | +0 |
| Cross-Scripture | 43 | 76 | +33 |

## Improvements

### Dialogue Reconstruction
- 62 → 170 dialogues (+108)
- Expanded speaker pattern detection
- Added question/answer tracking
- Topic classification improved

### Cross-Scripture Alignment
- 43 → 76 alignments (+33)
- Added Devanagari scripture alignments (Brahmanda Purana, Shvetashvatara Upanishad, Yajnavalkya Smriti)
- Expanded concept and teaching cross-references

### Relationship Refinement
- 61 → 68 edge types (+7)
- Added TEACHES, GUIDES, PROTECTS, LOVES, DEVOTEE_OF, SERVES, BLESSES, DEFEATS, COUNSELS
- All relationships backed by canonical evidence

### Entity Deduplication
- Merged duplicate entities (498 → 387)
- Resolved GUID conflicts
- Cleaned orphaned edges

## Quality

| Metric | Value |
|--------|-------|
| Orphan Nodes | 0 |
| Broken References | 0 |
| Entity Types | 14 |
| Edge Types | 68 |

## Known Limitations
- Devanagari OCR texts (KEN, MUND, MAHAN, PARASHARA) remain unreadable
- Event clustering limited to known canonical events
- Cross-scripture alignment partially manual
