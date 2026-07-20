# Changelog — AstroSage Knowledge System

## v2.5.0 — Production Deployment & Frontend Completion (2026-07-20)

### Summary

Production-ready deployment infrastructure and frontend polish for public beta readiness.

### New Features

- **Production Docker Compose** with Nginx reverse proxy, SSL termination, and resource limits
- **Standalone Next.js output** for optimized Docker builds
- **Nginx configuration** with SSE streaming support, rate limiting, gzip, and security headers
- **Frontend error boundaries** with graceful error recovery
- **404 page** with themed design
- **Global loading state** for initial page loads
- **SEO files**: robots.txt, sitemap.xml, enhanced OpenGraph metadata
- **Production environment template** with security guidance
- **Deployment documentation** with full production setup guide

### Infrastructure

- **Nginx reverse proxy** with JSON structured logging
- **Resource limits** for API (2GB), Frontend (512MB), Redis (256MB), PostgreSQL (512MB)
- **Health checks** on all Docker services
- **Non-root containers** for security
- **Production CORS** restricted to astrosage.ai domain

### Improvements

- Next.js `output: "standalone"` for minimal Docker images
- `reactStrictMode: true` for better development warnings
- `optimizePackageImports` for lucide-react and framer-motion
- `poweredByHeader: false` for security
- Enhanced Dockerfile with multi-stage build optimization

### Documentation

- Complete `DEPLOYMENT.md` with production setup guide
- Updated `README.md` with architecture diagram and quick start
- Production environment variable template

## v2.4.0 — Backend Production Readiness & Evaluation Framework (2026-07-19)

### Summary

Backend production readiness verified with scientific measurement. All 8 quality gates pass.
Major improvements to BM25 search, adversarial detection, and evaluation infrastructure.

### Critical Fixes

- Fixed BM25 `get_top_index` → `get_scores` + `numpy.argsort` (rank-bm25 API compliance)
- Fixed punctuation handling in tokenization (3x precision/recall improvement)
- Fixed `RegressionEvaluator.check()` → `evaluate()` in real pipeline eval
- Fixed HallucinationEvaluator to handle both nested and flat answer formats
- Fixed evaluation test for expanded dataset difficulty levels

### New Features

- **Adversarial Detection**: Ported from mock to real AnswerService
- **Query Expansion**: Integrated QueryExpansionEngine into BM25 search
- **Entity-Guided BM25 Pre-filtering**: 260x latency improvement (380ms → 1.5ms P95)
- **Expanded Golden Dataset**: 155 Q&A pairs (+55 new)

### Performance Improvements

- `numpy.argsort` for top-k selection (6% faster BM25 scoring)
- Entity-guided search reduces evaluation time from 33s to 0.6s
- Optimized query expansion token selection (max 5 extra terms)

### CI/CD

- Added evaluation benchmark job to CI workflow
- Runs real pipeline evaluation on every push/PR
- Reports 8 quality gate results as GitHub step summary

### Quality Metrics (155 Q&A dataset)

| Metric | Before | After |
|--------|--------|-------|
| Precision@5 | 4.47% | 23.92% |
| Recall@5 | 14.90% | 71.41% |
| NDCG@5 | 0.1245 | 0.7779 |
| Latency P95 | 380ms | 1.5ms |
| Eval Time | 31s | 0.6s |
| Quality Gates | 5/8 PASS | 8/8 PASS |

### Tests

- 59 API tests — all passing
- 31 evaluation framework tests — all passing
- 52 query expansion/cache/answer generation tests — all passing
- 858 knowledge core tests — all passing (from earlier phases)
- Total: ~1000 passing

