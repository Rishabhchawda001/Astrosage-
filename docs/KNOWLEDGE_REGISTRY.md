# Knowledge Registry — Permanent ID System

## ID Hierarchy

```
BOOK-XXXXXXXX  →  PAGE-XXXXXXXX  →  SECTION-XXXXXXXX  →  CHUNK-XXXXXXXX  →  EMBEDDING-XXXXXXXX
```

## Design Principles

1. **Deterministic:** Same content always produces the same ID (SHA256-based)
2. **Immutable:** Once assigned, IDs never change
3. **Traceable:** Every artifact traces to its source BOOK
4. **Reproducible:** Registry can be rebuilt from raw data alone

## ID Generation

```
BOOK-{sha256(sha256)[:8]}     — One per unique document
PAGE-{sha256(book_id:page)[:8]}  — One per page
SECTION-{sha256(book_id:path)[:8]}  — One per section
CHUNK-{sha256(book_id:index:text)[:8]}  — One per chunk
EMBED-{sha256(chunk_id)[:8]}  — One per embedding
```

## Current Statistics

- **620 unique BOOKs** (after SHA256 deduplication from 751 files)
- **68 duplicate groups** (131 duplicate files)
