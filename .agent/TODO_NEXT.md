# TODO — Next Actions (Priority Order)

## Just Completed
- ✅ Fixed BM25 `get_top_index` → `get_scores` + numpy argsort
- ✅ Fixed punctuation handling in tokenization (4.5x precision gain)
- ✅ Fixed RegressionEvaluator.check() → evaluate() in real pipeline eval
- ✅ Ported adversarial detection to AnswerService
- ✅ Integrated QueryExpansionEngine for Sanskrit/Hindi/English bridging
- ✅ Added entity-guided BM25 pre-filtering (260x latency improvement)
- ✅ 8/8 Quality Gates PASS
- ✅ 59 API + 858 knowledge tests passing

## Priority 1: Expand Golden Dataset
- Current: 100 Q&A pairs (62 non-adversarial + 15 adversarial in dataset, 100 total)
- Target: 150+ Q&A pairs across all categories
- Add more entity_factual, relationship, cross_scripture questions
- Add more adversarial variations

## Priority 2: Fix HallucinationEvaluator Compatibility
- `hallucination_eval.py` expects flat `confidence` key but AnswerService returns nested `answer.confidence`
- Update `evaluate_question()` to handle both formats
- This only affects standalone use of HallucinationEvaluator

## Priority 3: CI/CD Integration for Evaluation
- Add GitHub Actions workflow to run `real_pipeline_eval.py` on PRs
- Track benchmark history
- Block changes that regress quality gates

## Future Roadmap
| Phase | What | Priority |
|-------|------|----------|
| 2.4 | Meilisearch full-text search | Medium |
| 2.5 | Unified search service (BM25 + Meilisearch + FAISS) | Medium |
| 3.1 | Mem0 user memory (Qdrant or SQLite) | Low |
| 6 | Quality (golden dataset expansion, CI benchmarks) | High |
| 7 | Security hardening | Medium |
| 8 | Release & launch | Low |
