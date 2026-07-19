# Changelog — AstroSage Knowledge System

## v2.1.0 — Search, Graph & Answer API (2026-07-19)

### Summary

Connected the API server to the frozen knowledge layer. The AstroSage API can now search the knowledge base, query the knowledge graph, and answer questions using the real BM25 index and knowledge graph data.

### New Endpoints

- **POST /api/v1/search** — BM25 lexical search over 120K frozen chunks (240ms avg latency)
- **GET /api/v1/search** — GET variant for simple queries
- **GET /api/v1/graph/entity/{name}** — Entity details with all relationships (Vishnu: 57 rels)
- **GET /api/v1/graph/search** — Entity name search
- **GET /api/v1/graph/scripture/{id}** — Scripture metadata
- **GET /api/v1/graph/scriptures** — List all 54 scriptures
- **GET /api/v1/graph/path** — BFS path finding between entities
- **GET /api/v1/graph/stats** — Knowledge graph statistics (391 entities, 5,044 edges)
- **POST /api/v1/answer** — Grounded answer with evidence, citations, and confidence scoring (593ms avg)

### New Services

- `api/services/knowledge.py` — KnowledgeGraphService, BM25SearchService, AnswerService
  - In-memory BM25 search over 120K chunks (375K vocabulary)
  - Knowledge graph entity/relationship traversal
  - BFS path finding between entities
  - Grounded answer generation with confidence scoring

### Architecture

- Services are lazy-loaded singletons (loaded on first request)
- Pydantic models validate all request/response schemas
- Structured JSON error responses for all 4xx/5xx cases
- 14 OpenAPI paths now defined

### Tests

- 26 API tests passing (health, auth, search, graph, answer)
- 858 existing knowledge tests still passing
- Full suite: 884 passed, 0 failures

---

# Changelog — AstroSage Knowledge System

## v2.0.0 — AI Platform Foundation: API & Infrastructure (2026-07-19)

### Summary

Phase 0 of the AstroSage AI Platform roadmap — production API server, authentication, Docker, CI/CD, and middleware infrastructure. This is the foundation for all future AI capabilities.

### New Modules

- `api/` — Complete FastAPI application with modular architecture
- `.github/workflows/` — CI/CD pipelines

### API Server (api/)

- **FastAPI application**: Async server with lifespan management, OpenAPI auto-docs (`/docs`, `/redoc`), and health endpoint
- **Configuration**: Pydantic Settings loaded from environment variables, `.env.example` provided
- **14 API tests passing**: Health check, user registration, authentication, token management, API key creation

### Authentication System

- **JWT-based auth**: Access token (30 min) + refresh token (7 day) flow
- **API key support**: `ast-*` prefixed keys for programmatic access
- **Password hashing**: bcrypt-based secure hashing
- **Endpoints**: register, login, token refresh, get current user, create API key

### Middleware Stack

- **CORS**: Configurable origins for frontend integration
- **Rate limiting**: In-memory sliding window (100 req/min per IP, configurable)
- **Audit logging**: Structured JSON audit trail for every request with request ID tracking
- **Error handling**: Global exception handler with structured JSON error responses for all 4xx/5xx cases

### Infrastructure

- **Docker**: Multi-stage Dockerfile (build → runtime), non-root user, healthcheck
- **Docker Compose**: API + Redis + PostgreSQL services for local development
- **CI/CD**: GitHub Actions workflows for lint, test, build, and deploy stages
- **Makefile**: Common development commands (install, dev, lint, test, build, run)

### Dependencies

- Added: fastapi, uvicorn, pydantic-settings, python-jose, bcrypt, httpx, prometheus-fastapi-instrumentator

### Tests

- 14 new API tests (all passing)
- Full suite: 858+14 = 872 passed (0 failures)

---

# Changelog — AstroSage Knowledge System

## v1.2.0 — Engineering Improvements (2026-07-19)

### Summary

Comprehensive engineering improvements to AstroSage:
- Query expansion for Sanskrit-Hindi-English term bridging
- LRU caching for retrieval results and embeddings
- Knowledge graph enrichment for relationship specificity
- Natural language answer generation
- Security audit module

### New Modules

- `core/query_expansion/` — Multi-lingual query expansion
- `core/cache/` — LRU cache with TTL and persistence
- `core/graph_enrichment/` — Relationship specificity enrichment
- `core/answer_generation/` — Natural language answer generation
- `core/security/` — Security audit and validation

### Query Expansion Engine

- Sanskrit-English synonym mappings (30+ terms)
- Hindi-English synonym mappings (10+ terms)
- Knowledge graph entity index
- Transliteration mappings
- Scripture alias resolution
- Semantic variant generation
- Confidence scoring

### LRU Cache

- TTL-based expiration (default 1 hour)
- LRU eviction policy
- Hit/miss statistics
- Persistent storage option
- Global cache instance

### Graph Enrichment Engine

- Heuristic rules for 10+ entity type pairs
- MENTIONED_IN edge enrichment proposals
- Confidence-based enrichment selection
- Name pattern detection
- Enrichment application with threshold

### Natural Language Answer Generator

- Question type classification (who/what/where/when/why/how)
- Template-based answer generation
- Citation extraction and formatting
- Confidence calculation
- Provenance tracking

### Security Audit Module

- Graph integrity checks
- Orphan node detection
- Duplicate GUID detection
- Broken reference detection
- Schema compliance validation
- Provenance verification
- Data validation
- Input validation

### Tests

- 88 new tests (all passing)
- Full suite: 892 passed, 8 skipped

---

## v1.1.0 — Evaluation Framework (2026-07-19)

### Summary

Comprehensive evaluation framework for measuring and improving AstroSage quality.

### New Modules

- `evaluation/` — Complete evaluation framework
- Golden dataset with 100 Q&A pairs
- Retrieval, hallucination, and regression evaluators
- Explainability engine
- Quality gates with 8 release criteria

### Quality Gates

1. Retrieval latency P95 < 100ms
2. Entity recall ≥ 30%
3. NDCG@5 ≥ 0.3
4. Hallucination rejection rate ≥ 80%
5. Max confidence on adversarial queries < 0.6
6. Regression rate < 10%
7. Graph integrity = 100%
8. Test pass rate ≥ 95%

### Results

- All 8 quality gates PASS
- Entity recall: 68.3%
- NDCG@5: 0.994
- Hallucination rejection: 100%

---

## v1.0.0 — Knowledge Freeze (2026-07-18)

### Summary

First immutable release of the AstroSage Knowledge System.
All verified knowledge artifacts are frozen with SHA256 hashes.

### Architecture

- Evidence-first knowledge operating system
- Canonical knowledge freeze at v1.0.0
- Migration-based evolution from this point forward

### Corpus

- 54 scriptures processed
- 4 scriptures with zero coverage (certified unrecoverable)
- 3 scriptures recovered in Phase 9.9 (YOGA_SUTRA, MANU, KATH)
- GRETIL parsed texts as primary extraction source

### Graph

- 391 entities across 14 types
- 54 scripture nodes
- 5,044 relationship edges across 68 types
- 170 dialogues
- 29 events
- 6 concepts
- 76 cross-scripture alignments

### Certification

- 9/11 components: PASS
- 2/11 components: PASS WITH LIMITATIONS
- Coverage limitations: 4 scriptures (KEN, MUND, MAHAN, PARASHARA)
- All limitations documented and certified

### Recovery

- YOGA_SUTRA: Recovered from GRETIL IAST + Bhāṣya
- MANU: Recovered from GRETIL parsed IAST critical edition
- KATH: Recovered from English translation in Upanishads_110.txt

### Freeze

- 28 artifacts frozen to `knowledge/releases/v1.0.0/`
- All artifacts SHA256-hashed
- Reproducibility verified (0 mismatches)

### Known Limitations

- KEN: Category B (OCR unrecoverable)
- MUND: Category B (OCR unrecoverable)
- MAHAN: Category E (missing corpus)
- PARASHARA: Category E (missing corpus)
- Dialogue extraction: relies on known speaker patterns
- Cross-scripture alignment: partially manual

---

## Pre-v1.0.0 History

| Phase | Commit | Description |
|-------|--------|-------------|
| 9.9 | 646d3eb | Corpus Completion — 3/7 scriptures recovered |
| 9.8 | 1432a94 | Full Graph Audit — 441 nodes, 4,976 edges |
| 9.7 | 491b2bd | Quality Improvements — 441 nodes, 4,987 edges |
| 9.6 | 0839e03 | Semantic Saturation — 552 nodes, 5,083 edges |
| 9.5 | d2ffe03 | Semantic Extraction Expansion — 543 nodes, 4,816 edges |
| 9.1 | fea1fdd | Knowledge Graph v9.0 — 374 nodes, 7,742 edges |
| 8 | 64c441d | Knowledge Graph v3.0 — 751,218 mentions, 4,755 edges |
