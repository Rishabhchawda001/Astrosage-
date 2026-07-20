# Changelog — AstroSage Knowledge System

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
  - Non-Hindu text detection (quran, bible, torah, etc.)
  - Out-of-domain keyword blocking (crypto, sports, Norse mythology, etc.)
  - Entity-less query detection
  - 100% rejection rate on adversarial queries
- **Query Expansion**: Integrated QueryExpansionEngine into BM25 search
  - Sanskrit-English synonym bridging (30+ terms: dharma, karma, moksha, etc.)
  - Hindi-English synonym bridging (10+ terms: bhagwan, paramatma, etc.)
  - Semantic variant generation for entity queries
- **Entity-Guided BM25 Pre-filtering**: 260x latency improvement (380ms → 1.5ms P95)
  - Entity-to-chunks index built during service load
  - Mini BM25 on pre-filtered chunks for entity-focused queries
  - Graceful fallback to full BM25 for non-entity queries
- **Expanded Golden Dataset**: 155 Q&A pairs (+55 new)
  - 20 entity_factual, 10 relationship, 10 conceptual
  - 10 adversarial, 5 reasoning
  - All with difficulty levels and source provenance

### Performance Improvements
- `numpy.argsort` for top-k selection (6% faster BM25 scoring)
- Entity-guided search reduces evaluation time from 33s to 0.6s
- Optimized query expansion token selection (max 5 extra terms)

### CI/CD
- Added evaluation benchmark job to CI workflow
- Runs real pipeline evaluation on every push/PR
- Reports 8 quality gate results as GitHub step summary
- Uploads evaluation report as build artifact

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

# Changelog — AstroSage Knowledge System

## v2.3.0 — MCP Server with Live Knowledge Data (2026-07-19)

### Summary

Production MCP server with 7 tools wired to the real knowledge base. Compatible with Claude Desktop, VS Code MCP, and any MCP client.

### MCP Server

- `mcp_server.py` — MCP server with stdio (Claude Desktop) and SSE modes
- 7 tools wired to live data:

| Tool | Description | Data Source |
|------|-------------|-------------|
| `search_knowledge` | BM25 lexical search | 120K chunks, 375K vocab |
| `get_entity` | Entity lookup with relationships | 391 entities, 57 max rels |
| `get_entity_relationships` | Grouped relationship exploration | 42 types, full graph |
| `list_scriptures` | List all indexed scriptures | 54 scriptures |
| `get_scripture` | Scripture metadata | BG: 8372 verses, 100% |
| `answer_question` | Grounded QA with citations | Search + graph fusion |
| `knowledge_stats` | Knowledge base statistics | 391 entities, 5044 edges |

### Architecture

- Standard MCP JSON-RPC protocol (list_tools, call_tool, ping, initialize)
- Stdio mode: `python3 mcp_server.py` (Claude Desktop)
- SSE mode: `python3 mcp_server.py --sse` (web clients)
- Pre-loads knowledge services on startup
- Error handling per tool (entity not found, invalid args)

### Tests

- 12 MCP tool tests (all tool definitions, handlers, protocol compliance)
- 43 API tests total
- 858 existing knowledge tests still passing
- Full suite: 901 passing

---

# Changelog — AstroSage Knowledge System

## v2.2.0 — Chat Completions API & LiteLLM Integration (2026-07-19)

### Summary

Added an OpenAI-compatible chat completions API with LiteLLM model routing, SSE streaming, knowledge base context augmentation, and graceful fallback to the knowledge engine.

### New Endpoint

- **POST /api/v1/chat/completions** — OpenAI-compatible chat completions
  - Supports streaming via Server-Sent Events
  - LiteLLM routing: routes to any model (local vLLM, OpenAI, Claude, Gemini)
  - Knowledge base context augmentation for relevant queries
  - Graceful fallback to knowledge engine when model API is unavailable
  - Full parameter support (temperature, max_tokens, top_p, frequency/penalty)

### New Services

- `api/services/chat.py` — ChatService with LiteLLM integration
  - `acompletion()` — async completion with model routing
  - `acompletion_stream()` — async SSE streaming
  - `_build_context()` — knowledge base context augmentation
  - `_fallback_answer()` — graceful degradation to knowledge engine

### Architecture

- OpenAI-compatible request/response format for easy frontend integration
- SSE streaming with proper headers (Cache-Control, Connection, X-Accel-Buffering)
- Automatic context injection from knowledge base
- Falls back to grounded answer generation when no cloud API key is configured

### Dependencies

- Added: litellm (model routing across 100+ providers)

### Tests

- 5 new chat tests (basic completion, streaming, validation, fallback, system messages)
- 31 API tests total, all passing
- 858 existing knowledge tests still passing

---

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
