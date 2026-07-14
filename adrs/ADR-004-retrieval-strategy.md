# ADR-004: Retrieval Strategy

## Status
Accepted

## Date
2026-07-11

## Problem
Our knowledge base spans Vedic scriptures, Ayurveda, astrology, mathematics, philosophy, and more. Queries may be exact term matches ("Bhagavad Gita Chapter 2"), semantic concepts ("healing through herbs"), or cross-references ("similar verses in Rigveda and Atharvaveda").

## Alternatives Considered
1. **Vector-only** — Good semantic search. Misses exact terms.
2. **BM25-only** — Fast keyword matching. Misses synonyms and concepts.
3. **Hybrid (BM25 + Vector)** — Combines both. Score fusion needed.
4. **Hybrid + Reranking** — Adds cross-encoder for precision.
5. **GraphRAG** — Adds knowledge graph. Complex to build.

## Decision
**Hybrid search (BM25 + Vector) with cross-encoder reranking.**

## Rationale
- BM25 catches exact Sanskrit terms, verse numbers, author names
- Vector search handles conceptual queries and paraphrases
- BGE-M3 provides both sparse (BM25-like) and dense embeddings natively
- Cross-encoder reranking significantly improves precision on top results
- Evidence from benchmarks shows hybrid consistently outperforms either approach alone

## Tradeoffs
- Score fusion requires tuning (alpha parameter)
- Reranking adds ~50-200ms latency on top-20 results
- More complex than single-method retrieval

## Future Migration Path
- Add query routing (intent classification to choose retrieval strategy)
- GraphRAG for relationship queries (Phase 2)
- Learned fusion weights from evaluation feedback
