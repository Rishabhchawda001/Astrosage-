# ADR-002: Embedding Model Selection

## Status
Accepted

## Date
2026-07-11

## Problem
We need an embedding model that supports English, Hindi (Devanagari script), and Sanskrit with high retrieval quality, runs locally, and requires no paid APIs.

## Alternatives Considered
1. **nomic-embed-text** — Efficient, Ollama-compatible. English-focused.
2. **E5 (Microsoft)** — Strong English retrieval. Limited multilingual.
3. **BGE-M3** — Multilingual (100+), dense+sparse+ColBERT. 570M params.
4. **Jina Embeddings** — Multilingual, late interaction. API-dependent for full features.
5. **Stella** — High MTEB scores. English-only.

## Decision
**Primary: BGE-M3** for all languages.

## Rationale
- Only model that natively handles Hindi and Sanskrit with strong English performance
- Multi-granularity embeddings (dense + sparse + ColBERT) enable hybrid search without separate BM25
- 8192 token context window handles long passages
- MIT license, no API dependency
- Open-source, fully self-hostable

## Tradeoffs
- 570M parameters requires ~2GB VRAM/RAM
- Slightly slower than lightweight English-only models
- Sparse embedding mode adds storage overhead

## Future Migration Path
- Monitor Jina v3 for improved multilingual support
- Evaluate smaller distilled BGE models for edge deployment
- Consider fine-tuning on domain-specific Vedic texts
