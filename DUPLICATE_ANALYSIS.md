# Duplicate Analysis — Phase 21

**Date:** 2026-07-14

## Bronze File Duplicates

| Metric | Value |
|--------|-------|
| Total bronze files | 586 |
| Unique hashes | 540 |
| Duplicate groups | 46 |

Most duplicates are "Copy of" files (e.g., "Copy of आर्यभट्ट.txt" == "आर्यभट्ट.txt").

## Cross-File Paragraph Duplicates

| Metric | Value |
|--------|-------|
| Total paragraphs | 792,097 |
| Unique paragraphs | 616,906 |
| Cross-file duplicates | 118,559 |
| Duplicate rate | 19.2% |

This is expected behavior — scriptures share verses, mantras, and common passages across multiple texts.

## Multi-Edition Scriptures

| Scripture | Editions |
|-----------|----------|
| Harivansh Puran | 2 |
| Linga Puran | 2 |
| Kurma Puran | 2 |
| Raghav-Yadviyam | 2 |
| Matsya Puran | 2 |
| Vaman Puran | 2 |
| Skand Puran | 2 |

## Recommendations

1. Consider deduplicating "Copy of" bronze files
2. Cross-file paragraph duplicates are legitimate (shared verses across scriptures)
3. Multi-edition scriptures should have authority graphs built
