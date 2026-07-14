# AstroSage Recovery Audit — Phase 21

**Date:** 2026-07-14
**Commit:** 27ad111
**Tests:** 792 passed (0 failed)

## Repository Health

| Metric | Value | Status |
|--------|-------|--------|
| Bronze files | 635 | ✓ |
| Silver files | 635 | ✓ |
| Bronze/Silver match | 635/635 | ✓ |
| Orphaned files | 0 | ✓ |
| Downloads | 119 txt | ✓ |
| CKU registry | 29 files | ✓ |
| Authority graphs | 8 | ✓ |
| Tests passing | 792/792 | ✓ |

## Knowledge Metrics (Recomputed)

| Metric | Value |
|--------|-------|
| Total silver files | 635 |
| Total CKUs (paragraphs) | 1,114,925 |
| Total verses | 897,019 |
| Total words | 79,034,327 |
| Total characters | 296,476,768 |
| Total Devanagari chars | 119,923,511 |
| Authoritative CKUs | 63,360 |
| Coverage | 1759.7% (Silver contains commentary, metadata, multiple editions) |

## Silver Quality

| Grade | Files | Percentage |
|-------|-------|------------|
| A (90-100) | 588 | 92.6% |
| B (70-89) | 47 | 7.4% |
| C (50-69) | 0 | 0% |
| D (30-49) | 0 | 0% |
| F (<30) | 0 | 0% |

**Average quality score:** 98.5/100

## Search Connectors

| Connector | Health | Search | Latency |
|-----------|--------|--------|---------|
| Internet Archive | ✓ | ✓ (633 results) | 0.5s |
| Open Library | ✓ | ✓ (193 results) | 0.7s |
| Crossref | ✓ | ✓ (25,326 results) | 0.5s |
| OpenAlex | ✓ | ✓ (2,522 results) | 1.0s |
| Wikidata | ✓ | ✓ (0 results*) | 0.4s |
| GitHub | ✓ | ✓ (68 results) | 0.6s |
| arXiv | ✓ | ✓ (3 results) | 0.6s |
| Google Books | ✗ degraded | ✗ (rate limited) | 1.2s |

*Wikidata returns 0 for "Bhagavad Gita Sanskrit" but works for other queries.

## OCR Languages (13)

eng, hin, san, guj, mar, ben, tel, pan, ori, tam, kan, mal, osd

## Disk Usage

| Component | Size |
|-----------|------|
| Silver | 853 MB |
| Bronze | 709 MB |
| Downloads | 451 MB |
| External Bronze | 391 MB |
| Source Library | 8.7 GB |
| Git objects | 2.1 GB |
| **Total repo** | **14 GB** |
| **Free disk** | **25 GB** |

## Security

- No hardcoded API keys or secrets
- No .env files committed
- No AWS/live credentials found
- API key references are configuration placeholders only

## Duplicate Analysis

- **Bronze duplicate groups:** 46 (mostly "Copy of" files)
- **Cross-file paragraph duplicates:** 118,559 (19.2%)
- **Multi-edition scriptures:** 7 (Harivansh, Linga, Kurma, Raghav, Matsya, Vaman, Skand)

## Authority Graphs (8 scriptures)

1. Bhagavat Purana: 5 editions, scores 30-63
2. Valmiki Ramayana: 3 editions, scores 55-65
3. Rigveda: 4 editions, scores 40-70
4. Atharvaveda: 3 editions, scores 45-75
5. Samaveda: 2 editions, scores 40-50
6. Yajurveda: 2 editions, scores 35-50
7. Vidur Niti: 3 editions, scores 45-60
8. Vishnu Sahasranama: 3 editions, scores 50-80

## Recovery Session Summary

**Commits this session:** 5
**New editions downloaded:** 9
**New silver files created:** 9
**Atomic fragments recovered:** 155,637
**Characters recovered:** 50,713,512
**Capability improvements:** 8 search connectors, 13 OCR languages, download manager
