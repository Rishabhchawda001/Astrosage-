# ADR-005: Grounding and Anti-Hallucination Policy

## Status
Accepted

## Date
2026-07-11

## Problem
The Knowledge Engine must never fabricate citations or present unsupported information. Every answer must be traceable to source material. The system serves religious and philosophical texts where accuracy is paramount.

## Alternatives Considered
1. **No grounding** — Standard RAG. Risk of hallucination.
2. **Citation-only** — Force citations but don't verify. Partial protection.
3. **Grounding + verification** — Verify every claim against sources. Strong protection.
4. **Grounding + confidence scoring** — Add confidence levels. More nuanced.

## Decision
**Mandatory grounding with verification and confidence scoring.**

## Implementation
- Every response sentence must map to at least one retrieved chunk
- Each chunk carries source metadata (document, page, chapter, section)
- Unverifiable sentences are removed from responses
- If insufficient evidence: return "The indexed knowledge base does not contain sufficient evidence to answer this question."
- Confidence scoring: high (direct quote match), medium (paraphrase match), low (inference)
- All citations include document title, page number, and chapter/section

## Rationale
- Religious/philosophical texts demand highest accuracy standards
- Users must be able to verify every claim
- Building trust requires zero tolerance for fabrication
- Confidence scoring helps users calibrate trust

## Tradeoffs
- May return "insufficient evidence" more often than users prefer
- Adds processing overhead for verification step
- Requires high-quality chunking to enable accurate citation

## Future Migration Path
- LLM-based fact verification (Phase 2)
- User feedback loop for grounding quality
- Automated citation accuracy testing
