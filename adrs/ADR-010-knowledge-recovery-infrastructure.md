# ADR-010: Knowledge Recovery Infrastructure

## Status
Accepted

## Date
2026-07-12

## Problem
OCR is not perfect. Some documents contain missing characters, words, lines, verses, poor OCR quality, damaged pages, broken metadata, and incorrect structure. If we continue building on incomplete OCR, embeddings, retrieval, knowledge graph, and reasoning will all inherit OCR mistakes. Recovery MUST happen BEFORE knowledge enrichment, chunking, and embeddings.

## Alternatives Considered
1. **Skip recovery, build on raw OCR** — Rejected: propagates errors through entire pipeline
2. **Single-source recovery** — Rejected: insufficient evidence from one source
3. **Multi-source recovery with trust scoring** — Selected: provides verifiable, auditable recovery

## Decision
Build a complete Knowledge Recovery Infrastructure with:
- Knowledge Source Registry (Internet Archive, Open Library, Crossref, OpenAlex, Wikidata)
- Trust Engine (configurable weights for source, edition, OCR, recovery, verification trust)
- Knowledge Passport (complete provenance for recovered knowledge)
- Recovery Queue (priority-based, with retry and checkpointing)
- Human Review Queue (pending/approved/rejected/deferred states)
- Edition Registry (tracking original, translation, commentary, transliteration editions)
- Verification Interface (ABC-based, pluggable)
- Conflict Engine (storing all variants, never discarding)
- Confidence Engine (aggregating scores from all stages)
- Source Connectors (ABC-based plugin interfaces)
- Knowledge Provenance Ledger (tracking every transformation)

## Rationale
- Original OCR always survives (never overwritten)
- Recovered text stored separately with full evidence chain
- Every recovered character has: evidence, source, confidence, agreement, timestamp, pipeline version
- Nothing becomes permanent without traceability
- Plugin architecture allows swapping implementations

## Tradeoffs
- Infrastructure-first approach delays actual recovery
- More complex than single-source recovery
- Requires human review for low-confidence cases

## Future Migration Path
- Phase 5+ will implement actual recovery using this infrastructure
- Source connectors will be populated with API integrations
- Confidence models will be tuned based on real recovery results
