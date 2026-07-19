# NEXT GENERATION ROADMAP

**Date:** 2026-07-19
**Current Version:** 1.2.0

---

## Vision

Transform AstroSage from a rule-based knowledge system into a neural-augmented, production-ready platform for Hindu scripture understanding.

---

## Version 1.3 — Production Readiness

**Timeline:** 2-4 weeks
**Goal:** Wire evaluation to real pipeline and add CI/CD

### Milestones
1. Wire evaluation to real BM25+FAISS pipeline
2. Expand golden dataset to 200+ questions
3. Add CI/CD integration (GitHub Actions)
4. Implement cross-lingual evaluation (Devanagari ↔ IAST)
5. Add A/B testing framework

### Success Criteria
- Evaluation runs on real pipeline
- 200+ golden Q&A pairs
- CI/CD pipeline passing
- Cross-lingual evaluation working

---

## Version 1.4 — API & Interface

**Timeline:** 4-6 weeks
**Goal:** Expose AstroSage as a web service

### Milestones
1. FastAPI web server for search and QA
2. Multi-turn conversation support
3. Cross-lingual query support
4. Real-time corpus updates via migrations
5. Production deployment with monitoring

### Success Criteria
- FastAPI server running
- Multi-turn conversation working
- Cross-lingual search functional
- Monitoring and alerting in place

---

## Version 2.0 — Next Generation

**Timeline:** 8-12 weeks
**Goal:** LLM-augmented reasoning and neural answer generation

### Milestones
1. LLM-augmented reasoning (neural + rule-based)
2. Neural answer generation
3. Production deployment with scaling
4. Mobile app interface
5. Community contribution framework

### Success Criteria
- LLM reasoning working
- Neural answers generating
- Production deployment running
- Mobile app available
- Community contributing

---

## Technical Roadmap

### Query Expansion (v1.3)
- Add contextual embeddings
- Implement query reformulation
- Add cross-lingual expansion

### Retrieval (v1.4)
- Add cross-encoder reranking
- Implement hybrid search with dense+lexical
- Add metadata filtering

### Reasoning (v2.0)
- Implement chain-of-thought reasoning
- Add multi-hop reasoning
- Implement causal reasoning

### Answer Generation (v2.0)
- Implement neural text generation
- Add citation grounding
- Implement answer verification

---

## Success Metrics

| Metric | v1.3 Target | v1.4 Target | v2.0 Target |
|--------|-------------|-------------|-------------|
| Entity Recall | 75% | 80% | 85% |
| NDCG@5 | 0.995 | 0.997 | 0.999 |
| Hallucination Rejection | 100% | 100% | 100% |
| P95 Latency | <50ms | <30ms | <20ms |
| Golden Dataset | 200+ | 300+ | 500+ |
| Test Count | 950+ | 1000+ | 1100+ |

---

## Dependencies

### v1.3
- FAISS installation
- sentence-transformers installation
- GitHub Actions setup

### v1.4
- FastAPI installation
- WebSocket support
- Docker setup

### v2.0
- LLM API access
- GPU infrastructure
- Mobile development tools

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| FAISS installation issues | Medium | High | Use CPU-only FAISS |
| LLM API costs | High | Medium | Use local models |
| Mobile development complexity | Medium | Low | Start with web app |
| Performance degradation | Low | High | Continuous monitoring

---

## Next Steps

1. Complete v1.3 milestones
2. Begin v1.4 planning
3. Research LLM integration options
4. Set up CI/CD pipeline
5. Expand golden dataset
