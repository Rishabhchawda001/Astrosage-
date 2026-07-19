# TODO — Next Actions

## Version 1.1 — Evaluation Framework (COMPLETE)

All evaluation modules built and tested:
- Golden dataset: 62 questions
- Retrieval, hallucination, regression, explainability evaluators
- Quality gates with 8 release criteria
- 31 tests passing

## Version 1.1 Remaining Work

1. Wire evaluation to real pipeline (replace mock search_fn/answer_fn)
2. Expand golden dataset to 150+ questions
3. Add CI/CD integration for continuous evaluation
4. Add A/B testing framework for pipeline changes
5. Add cross-lingual evaluation (Devanagari ↔ IAST)

## Future Work (Post v1.1)

1. Web API (FastAPI) for search and QA
2. Multi-turn conversation support
3. Cross-lingual query support (Devanagari ↔ IAST)
4. Real-time corpus updates via migrations
5. Production deployment with monitoring
6. Mobile app interface
