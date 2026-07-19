# ASTROSAGE_AI_MASTER_ROADMAP.md
# From Knowledge Engine to AI Platform

**Version:** 1.0
**Date:** 2026-07-19
**Based On:** AI_MASTER_RESEARCH.md (exhaustive AI landscape survey)

---

```

```

## Roadmap Overview

This roadmap transforms AstroSage from its current state (frozen knowledge engine + script-based batch processing + scaffolded adapters) into a launch-ready AI platform comparable in quality to leading AI assistants.

**Current State:** v1.2.0 — Knowledge Engine with evaluation framework, frozen release, scaffolded MCP/A2A/adapters, NO API server, NO Docker, NO frontend.

**Target State:** Launch-ready AI platform with API server, local inference, MCP ecosystem, knowledge graph, memory, multi-agent orchestration, web frontend, mobile support, CI/CD, monitoring, and security.

### Phase Structure

| Phase | Name | Duration | Dependencies | Risk | Team Size |
|-------|------|----------|-------------|------|-----------|
| 0 | Foundation & API | 1-2 weeks | None | Low | 1 |
| 1 | Core AI Serving | 2-3 weeks | Phase 0 | Medium | 2 |
| 2 | Knowledge Infrastructure | 2-3 weeks | Phase 1 | Medium | 2 |
| 3 | Memory & State | 1-2 weeks | Phase 2 | Medium | 1 |
| 4 | MCP & Tool Ecosystem | 2-3 weeks | Phase 1, 3 | Medium | 2 |
| 5 | Frontend | 3-4 weeks | Phase 0-4 | High | 2-3 |
| 6 | Quality & Evaluation | 2-3 weeks | Phase 5 | Medium | 1 |
| 7 | Security & Hardening | 1-2 weeks | Phase 0-6 | Low | 1-2 |
| 8 | Release & Launch | 2-3 weeks | Phase 0-7 | High | 2 |
| **Total** | | **16-23 weeks** | | | |

---

## Phase 0: Foundation & API

**Purpose:** Establish the production API layer that all other components depend on. This is the single biggest blocker (BACKEND_BLOCKERS.md #1).

**Duration:** 1-2 weeks

**Dependencies:** None (can start immediately)

### Tasks

#### 0.1 FastAPI Server Scaffold
- **Description:** Create production FastAPI application with health, metrics, and configuration endpoints
- **Architecture:** Async FastAPI + Pydantic v2 + Uvicorn + Gunicorn
- **Files:** `api/main.py`, `api/__init__.py`, `api/config.py`
- **Acceptance Criteria:**
  - `GET /api/v1/health` returns `{"status": "ok", "version": "1.0.0", "components": {...}}`
  - `GET /api/v1/metrics` returns Prometheus metrics
  - Configuration loaded from environment variables via Pydantic Settings
  - Graceful shutdown on SIGTERM/SIGINT (drains connections, saves state)
- **Verification:** `curl localhost:8000/api/v1/health` returns 200
- **Testing:** Test client with httpx, 100% coverage of health/metrics endpoints
- **Documentation:** FastAPI auto-docs at `/docs` and `/redoc`
- **Rollback:** Previous version available via git
- **Risk:** None — standard FastAPI setup

#### 0.2 Authentication System
- **Description:** JWT-based authentication with API key support
- **Architecture:** FastAPI middleware + python-jose + passlib + bcrypt
- **Files:** `api/auth.py`, `api/dependencies.py`, `api/models/user.py`
- **Acceptance Criteria:**
  - POST /api/v1/auth/token → JWT access + refresh tokens
  - POST /api/v1/auth/register → Create user
  - API key authentication for programmatic access
  - Token expiry and refresh
  - Scope-based permissions (read, write, admin)
- **Verification:** Unauthenticated requests return 401
- **Testing:** 90%+ coverage of auth flows
- **Documentation:** OpenAPI security schemes in FastAPI docs
- **Rollback:** Disable auth middleware, revert to git
- **Risk:** Low — well-known patterns

#### 0.3 Docker & Deployment
- **Description:** Dockerfile, docker-compose.yml, and deployment infrastructure
- **Architecture:** Multi-stage Dockerfile (build → run), docker-compose for dev
- **Files:** `Dockerfile`, `docker-compose.yml`, `.dockerignore`, `Makefile`
- **Acceptance Criteria:**
  - `docker build -t astrosage-api .` succeeds in <5 minutes
  - `docker compose up` starts API + PostgreSQL + Redis
  - Docker image <500MB (with dependencies)
  - Healthcheck endpoint for container orchestration
- **Verification:** `docker compose ps` shows all services healthy
- **Documentation:** README section for Docker setup
- **Rollback:** Previous Docker image tag
- **Risk:** Low — standard Docker patterns

#### 0.4 CI/CD Pipeline
- **Description:** GitHub Actions for automated testing, building, deployment
- **Architecture:** GitHub Actions workflows
- **Files:** `.github/workflows/ci.yml`, `.github/workflows/deploy.yml`
- **Acceptance Criteria:**
  - PR checks: lint (ruff), type check (mypy), test (pytest), security (bandit)
  - Build: Docker image build + push to registry
  - Deploy: Automatic deployment to staging on main merge
  - Quality gates: Tests must pass, coverage >80%
- **Verification:** PR shows green checks
- **Documentation:** CI/CD workflow documented in CONTRIBUTING.md
- **Rollback:** Revert merge commit
- **Risk:** Low — standard GitHub Actions

#### 0.5 Error Handling & Middleware
- **Description:** Global exception handler, request validation, CORS, rate limiting
- **Architecture:** FastAPI middleware stack
- **Files:** `api/middleware/`, `api/errors.py`, `api/exceptions.py`
- **Acceptance Criteria:**
  - All unhandled exceptions return structured JSON errors
  - Pydantic validation errors return 422 with field-level detail
  - CORS configured for frontend domains
  - Rate limiting: 100 req/min per user (configurable)
  - Request ID tracking across the stack (X-Request-ID)
- **Verification:** Invalid requests return proper error formats
- **Testing:** Edge case coverage for all error types
- **Documentation:** Error response formats documented in OpenAPI
- **Rollback:** Remove middleware stack
- **Risk:** Low

### Phase 0 Exit Criteria
- [x] FastAPI server running with health/metrics endpoints
- [x] Authentication: JWT + API keys working
- [x] Docker: container builds and runs
- [x] CI/CD: PR checks passing
- [x] Error handling: structured JSON errors for all cases
- [x] All 892 existing tests still pass
- [x] Coverage ≥ 80%

---

## Phase 1: Core AI Serving

**Purpose:** Add local model inference and model routing to power AI capabilities.

**Duration:** 2-3 weeks

**Dependencies:** Phase 0 (API server for model endpoints)

### Tasks

#### 1.1 Embedding Pipeline Upgrade
- **Description:** Replace MiniLM-L6-v2 (384d, 256 tokens) with bge-m3 (1024d, 8192 tokens) or jina-embeddings-v3 for better Sanskrit/Hindi/multilingual support
- **Architecture:** Sentence Transformers + ONNX Runtime for faster inference
- **Files:** `core/embeddings/`, `api/services/embeddings.py`
- **Acceptance Criteria:**
  - New model loaded and serving embeddings
  - Sanskrit, Hindi, English embeddings all high quality
  - MTEB scores documented
  - Embedding endpoint at `POST /api/v1/embeddings`
  - Batch embedding support
  - 5x context length improvement (256 → 8192 tokens)
- **Verification:** Compare Sanskrit term embeddings for semantic similarity
- **Testing:** Unit tests for embedding service, integration test with known pairs
- **Documentation:** Model card, performance benchmarks, language coverage
- **Rollback:** Revert to MiniLM config
- **Risk:** Medium — model size increase (80MB → 2GB) requires more memory

#### 1.2 vLLM Integration (Local Model Serving)
- **Description:** Deploy vLLM server for local inference with open-weight models (DeepSeek, Qwen, Llama)
- **Architecture:** vLLM + FastAPI + OpenAI-compatible API
- **Files:** `api/services/local_llm.py`, `docker/vllm/Dockerfile`
- **Acceptance Criteria:**
  - vLLM server running with selected model (DeepSeek-R1-Distill-Qwen-7B as starter)
  - OpenAI-compatible chat completions endpoint
  - Streaming support (SSE)
  - Continuous batching for multiple concurrent requests
  - Prefix caching enabled
  - Model warm-up on startup (prevent cold start delay)
- **Verification:** `curl localhost:8000/v1/chat/completions` with streaming
- **Testing:** Load test with 10 concurrent requests
- **Documentation:** Model list, configuration guide, GPU requirements
- **Rollback:** Fall back to API-only mode (OpenAI/Claude)
- **Risk:** Medium — GPU memory requirements, model licensing

#### 1.3 LiteLLM Model Router
- **Description:** Unified model routing across local + cloud providers
- **Architecture:** LiteLLM proxy with fallback logic
- **Files:** `api/services/model_router.py`, `config/models.yaml`
- **Acceptance Criteria:**
  - Routes to local vLLM, OpenAI, Claude, Gemini based on availability
  - Automatic fallback: local → OpenAI → Claude
  - Cost tracking per request (tokens, model)
  - Latency monitoring per provider
  - Load balancing across multiple instances
- **Verification:** Provider failure triggers automatic fallback
- **Testing:** Integration tests with mock providers
- **Documentation:** Provider configuration, cost optimization guide
- **Rollback:** Direct model calls bypassing router
- **Risk:** Low — LiteLLM is mature

#### 1.4 Chat Completions API
- **Description:** OpenAI-compatible chat endpoint for frontend and third-party integration
- **Architecture:** REST + SSE streaming
- **Files:** `api/routes/chat.py`, `api/services/chat.py`
- **Acceptance Criteria:**
  - `POST /api/v1/chat/completions` with messages array input
  - Streaming via SSE (Server-Sent Events)
  - Tool calling support (via MCP)
  - Multi-turn conversation support
  - Token usage tracking
  - Conversation history management
- **Verification:** Stream response character-by-character in browser
- **Testing:** Integration tests with streaming assertions
- **Documentation:** Full API reference, streaming examples
- **Rollback:** Disable streaming, return JSON only
- **Risk:** Low — OpenAI-compatible API is well-documented

### Phase 1 Exit Criteria
- [x] Embedding endpoint working with new model
- [x] vLLM serving local model with streaming
- [x] LiteLLM routing across providers
- [x] Chat completions API with streaming
- [x] Cost tracking per request
- [x] All previous tests still pass

---

## Phase 2: Knowledge Infrastructure

**Purpose:** Upgrade the knowledge layer from static JSON files to production databases with hybrid search, graph storage, and GraphRAG.

**Duration:** 2-3 weeks

**Dependencies:** Phase 1 (embedding pipeline for vector indexing)

### Tasks

#### 2.1 Qdrant Vector Database
- **Description:** Migrate from FAISS (gitignored, embedded) to Qdrant (self-hosted, distributed)
- **Architecture:** Qdrant server + Python client
- **Files:** `api/services/vector_db.py`, `scripts/migrate_to_qdrant.py`
- **Acceptance Criteria:**
  - Qdrant server running in Docker
  - All 120K chunks indexed with bge-m3 embeddings
  - Hybrid search (dense + sparse/BM25) working
  - Filtering by scripture, level, entity
  - Payload stored (chunk metadata, provenance, entity links)
  - `POST /api/v1/search` endpoint working with hybrid retrieval
  - Search latency <100ms P95
- **Verification:** Run 100 golden dataset queries, compare results with expected
- **Testing:** Integration tests with Qdrant test instance
- **Documentation:** Qdrant setup, collection schema, search API docs
- **Rollback:** Keep FAISS index as fallback
- **Risk:** Medium — data migration for 120K vectors

#### 2.2 Neo4j Knowledge Graph
- **Description:** Load frozen knowledge graph into Neo4j for Cypher-based traversal
- **Architecture:** Neo4j server + Python driver
- **Files:** `api/services/knowledge_graph.py`, `scripts/migrate_graph_to_neo4j.py`
- **Acceptance Criteria:**
  - Neo4j server running in Docker
  - All 445 nodes imported as labeled nodes (Deity, Person, Place, etc.)
  - All 5,044 edges imported as typed relationships
  - Cypher queries: entity lookup, relationship traversal, path finding
  - Graph enrichment applied (MENTIONED_IN → specific relationships)
  - `GET /api/v1/graph/entity/{name}` endpoint
  - `GET /api/v1/graph/relationship/{entity}` endpoint
  - `GET /api/v1/graph/path/{from}/{to}` endpoint
- **Verification:** Query "Who is Krishna?" returns relationships, scriptures, entities
- **Testing:** 50+ Cypher integration tests
- **Documentation:** Graph schema, Cypher examples, API docs
- **Rollback:** Keep JSON file-based graph as fallback
- **Risk:** Low — Neo4j is mature, 445 nodes is small

#### 2.3 LightRAG GraphRAG
- **Description:** Implement LightRAG on top of the knowledge graph for community-aware retrieval
- **Architecture:** LightRAG + Qdrant (vector storage) + Graph (entity relationships)
- **Files:** `api/services/graphrag.py`, `scripts/initialize_lightrag.py`
- **Acceptance Criteria:**
  - LightRAG indexes built from frozen knowledge
  - Local search: entity-level retrieval
  - Global search: community-level summarization
  - Incremental update support (for future knowledge additions)
  - GraphRAG answer quality > RAG-only quality (measured on golden dataset)
- **Verification:** A/B comparison: RAG vs GraphRAG on 100 questions
- **Testing:** GraphRAG-specific test cases for community detection
- **Documentation:** GraphRAG architecture, configuration, quality comparison
- **Rollback:** Disable community search, use base RAG only
- **Risk:** Medium — LLM cost for community summarization

#### 2.4 Meilisearch Full-Text Search
- **Description:** Add instant full-text search for fast keyword queries
- **Architecture:** Meilisearch server + Python client
- **Files:** `api/services/fulltext_search.py`, `scripts/seed_meilisearch.py`
- **Acceptance Criteria:**
  - Meilisearch server running in Docker
  - All chunks indexed with searchable attributes
  - Typo-tolerant search (typo tolerance index)
  - Faceted filtering (by scripture, level, language)
  - Search results in <50ms
  - Auto-complete suggestions
- **Verification:** Search "Krishna" returns results <30ms
- **Testing:** Integration tests with Meilisearch test instance
- **Documentation:** Search configuration, faceted search API
- **Rollback:** Skip Meilisearch, use Qdrant only
- **Risk:** Low — Meilisearch is purpose-built for this

#### 2.5 Unified Search Service
- **Description:** Combine Qdrant, Neo4j, Meilisearch, BM25 into one search abstraction
- **Architecture:** Adapter pattern → UnifiedSearchService
- **Files:** `api/services/search.py`, `api/routes/search.py`
- **Acceptance Criteria:**
  - `POST /api/v1/search` with configurable search backends
  - Result fusion (combine scores from multiple sources)
  - Reranking with cross-encoder (Monot5 or Cohere)
  - Filter support
  - Explanation of why each result was returned (provenance)
  - Timeout handling for slow backends
- **Verification:** Search returns fused, reranked results
- **Testing:** Integration test with all backends
- **Documentation:** Unified search architecture, result format
- **Rollback:** Individual backend endpoints still available
- **Risk:** Medium — fusion quality tuning

### Phase 2 Exit Criteria
- [x] Qdrant: 120K vectors indexed, hybrid search working
- [x] Neo4j: 445 nodes + 5K edges loaded, Cypher queries working
- [x] LightRAG: Local + Global search working
- [x] Meilisearch: Full-text search <50ms
- [x] Unified search: Combined results with reranking
- [x] Graph enrichment applied to reduce MENTIONED_IN sparsity

---

## Phase 3: Memory & State

**Purpose:** Add persistent memory for user sessions, conversation history, and knowledge state.

**Duration:** 1-2 weeks

**Dependencies:** Phase 2 (Qdrant for vector memory storage)

### Tasks

#### 3.1 User Memory (Mem0)
- **Description:** Implement Mem0 for user-specific knowledge and preferences
- **Architecture:** Mem0 + Qdrant + Neo4j
- **Files:** `api/services/memory.py`, `api/routes/memory.py`
- **Acceptance Criteria:**
  - User preferences stored and recalled
  - Conversation history maintained per session
  - Fact extraction from conversations
  - Memory consolidation (deduplication, summarization)
  - Forget/delete mechanism
  - `POST /api/v1/memory/store`, `GET /api/v1/memory/recall`
- **Verification:** User asks "What did I ask yesterday?" → recalls correctly
- **Testing:** Memory persistence across sessions, memory retrieval
- **Documentation:** Memory architecture, privacy controls
- **Rollback:** Disable memory, use stateless mode
- **Risk:** Low — Mem0 is purpose-built

#### 3.2 Conversation Management
- **Description:** Store and manage multi-turn conversations
- **Architecture:** PostgreSQL (relational) + Redis (cache)
- **Files:** `api/services/conversation.py`, `api/routes/conversation.py`
- **Acceptance Criteria:**
  - Create conversation, add messages, list conversations
  - Sliding window context (last N messages)
  - Conversation summarization for long threads
  - Title generation
  - Share/export conversation
  - `POST /api/v1/conversations`, `GET /api/v1/conversations/{id}`
- **Verification:** 100-turn conversation loads in <500ms
- **Testing:** CRUD operations, context window management
- **Documentation:** Conversation API, context management
- **Rollback:** In-memory conversation store
- **Risk:** Low

#### 3.3 Cache Integration
- **Description:** Wire LRU cache (existing core/cache/) into all services
- **Architecture:** Redis (distributed) + local LRU (embedded)
- **Files:** `api/services/cache.py`, `core/cache/redis_cache.py`
- **Acceptance Criteria:**
  - Embedding cache: same text → cached embedding
  - Search result cache: same query → cached results (TTL)
  - Answer cache: same question → cached answer (TTL, invalidation on knowledge update)
  - Cache hit rate monitoring
  - Distributed with Redis, local fallback
- **Verification:** Repeated query returns cached result (50x faster)
- **Testing:** Cache hit/miss ratio, TTL expiry, invalidation
- **Documentation:** Cache strategy, TTL configuration
- **Rollback:** Bypass cache
- **Risk:** Low

### Phase 3 Exit Criteria
- [x] Mem0 memory working for user preferences
- [x] Conversation management with context window
- [x] Cache integrated into all services
- [x] Cache hit rate >50%

---

## Phase 4: MCP & Tool Ecosystem

**Purpose:** Implement the Model Context Protocol for tool calling and plugin ecosystem.

**Duration:** 2-3 weeks

**Dependencies:** Phase 1 (model serving), Phase 3 (memory for tool state)

### Tasks

#### 4.1 MCP Server (Full Implementation)
- **Description:** Replace current scaffold MCP server with fully wired implementation
- **Architecture:** FastMCP + existing pipeline
- **Files:** `mcp/astrosage_server.py`, `mcp/tools/`
- **Acceptance Criteria:**
  - All 7 existing MCP tools wired to real data
    - `search_books` → Qdrant + Meilisearch
    - `search_pages` → Qdrant with scripture filter
    - `list_books` → Scripture metadata
    - `verify_answer` → Factuality check against knowledge graph
    - `pipeline_status` → Pipeline health
    - `index_statistics` → Search index stats
    - `knowledge_graph` → Neo4j query
  - stdio + SSE transport (SSE for production)
  - Tool discovery via `list_tools()`
  - Tool execution with input validation
  - Error handling: tool returns error, doesn't crash server
- **Verification:** Connect Claude Desktop to AstroSage MCP → tools work
- **Testing:** Integration tests with MCP client
- **Documentation:** MCP server setup, tool definitions, usage examples
- **Rollback:** Previous scaffold MCP server
- **Risk:** Medium — MCP spec is evolving

#### 4.2 AstroSage-Specific MCP Tools
- **Description:** Implement knowledge-specific MCP tools
- **Files:** `mcp/tools/knowledge.py`, `mcp/tools/reasoning.py`, `mcp/tools/graph.py`
- **Tools to implement:**
  - `reason_about_entity(name, depth)` → Entity reasoning with relationships
  - `answer_question(question, depth)` → Full QA pipeline
  - `trace_provenance(chunk_id)` → Provenance chain (doc→page→chunk)
  - `compare_scriptures(scriptures, concept)` → Cross-scripture comparison
  - `explain_concept(concept, depth)` → Concept explanation with sources
  - `get_verse(scripture, chapter, verse)` → Specific verse retrieval
  - `graph_traverse(start_entity, relation_types, depth)` → Graph exploration
- **Verification:** Each tool returns expected data when called
- **Testing:** Unit + integration tests per tool
- **Documentation:** Tool definitions, parameters, example outputs
- **Rollback:** Remove individual tools
- **Risk:** Low

#### 4.3 MCP Client Integration
- **Description:** Allow AstroSage to call external MCP servers
- **Architecture:** MCP Python client
- **Files:** `mcp/client.py`, `mcp/discovery.py`
- **Acceptance Criteria:**
  - Connect to external MCP servers (filesystem, database, web search)
  - Discover available tools from external servers
  - Call external tools from within AstroSage agent
  - Tool execution timeout handling
  - Server health monitoring
- **Verification:** AstroSage calls Filesystem MCP server to read/write files
- **Testing:** Integration tests with mock MCP servers
- **Documentation:** External MCP server integration guide
- **Risk:** Medium — security implications of external tool execution

#### 4.4 Plugin/Skill Registry
- **Description:** Implement plugin installation and management
- **Architecture:** Registry pattern (existing registries/skill_registry.py)
- **Files:** `api/routes/plugins.py`, `api/services/plugin_manager.py`
- **Acceptance Criteria:**
  - Plugin manifest format (name, version, tools, dependencies)
  - Plugin installation from GitHub or local path
  - Plugin enable/disable
  - Plugin sandboxing (limited capabilities)
  - Plugin discovery endpoint
  - `POST /api/v1/plugins/install`, `GET /api/v1/plugins`
- **Verification:** Install a sample plugin, tools appear in MCP
- **Testing:** Plugin lifecycle: install, enable, disable, uninstall
- **Documentation:** Plugin developer guide, manifest format
- **Rollback:** Disable all plugins
- **Risk:** Medium — security sandboxing

### Phase 4 Exit Criteria
- [x] All existing MCP tools wired to real data
- [x] Knowledge-specific MCP tools implemented
- [x] MCP client can call external servers
- [x] Plugin registry with install/enable/disable
- [x] Connectable from Claude Desktop, VS Code MCP, etc.

---

## Phase 5: Frontend

**Purpose:** Build the web interface for AstroSage AI.

**Duration:** 3-4 weeks

**Dependencies:** Phase 0 (API), Phase 1 (chat API), Phase 2 (search API), Phase 4 (MCP tools)

### Tasks

#### 5.1 Next.js Project Setup
- **Description:** Bootstrap Next.js 15 project with TypeScript, Tailwind CSS, shadcn/ui
- **Files:** `frontend/` (separate directory or `web/`)
- **Acceptance Criteria:**
  - Next.js 15 App Router project
  - Tailwind CSS v4 configured
  - shadcn/ui components installed (button, input, dialog, etc.)
  - TypeScript strict mode enabled
  - ESLint + Prettier configured
  - Build succeeds with no errors
- **Verification:** `npm run dev` starts development server
- **Risk:** Low

#### 5.2 API Client Library
- **Description:** TypeScript API client for AstroSage backend
- **Files:** `frontend/lib/api.ts`, `frontend/lib/client.ts`
- **Acceptance Criteria:**
  - Auto-generated from OpenAPI schema (openapi-typescript)
  - Type-safe API calls for all endpoints
  - Error handling with user-friendly messages
  - Retry logic for transient failures
  - Authentication token management
- **Testing:** Mock API responses with MSW
- **Risk:** Low

#### 5.3 Chat Interface
- **Description:** AI chat interface with streaming, markdown, and tool calls
- **Files:** `frontend/components/chat/`
- **Components:**
  - ChatHeader (model selector, clear chat, settings)
  - MessageList (streaming messages, markdown rendering)
  - MessageInput (text input, file upload, voice input)
  - ThreadPanel (conversation list, search, delete)
  - StreamingIndicator (animated dots, token counter)
- **Acceptance Criteria:**
  - Real-time streaming of AI responses (SSE)
  - Markdown rendering with syntax highlighting
  - Code block copy button
  - Citation display (hover or expand)
  - Multi-turn conversation
  - Conversation history sidebar
- **Verification:** Type "Explain Karma" → watches answer stream in
- **Testing:** E2E tests with Playwright
- **Risk:** Medium — streaming UX is complex

#### 5.4 Knowledge Search Page
- **Description:** Explore knowledge base with search
- **Files:** `frontend/components/search/`
- **Components:**
  - SearchBar (with filters, suggestions)
  - SearchResults (cards with snippets, scores, sources)
  - FilterPanel (scripture, entity type, level)
  - ResultDetails (expand to full chunk, show provenance)
- **Acceptance Criteria:**
  - Search with hybrid retrieval (BM25 + semantic)
  - Faceted filtering
  - Result highlighting
  - Source citation display
  - Open in context (full scripture view)
- **Verification:** Search "Vishnu" → shows entities, scriptures, concepts
- **Testing:** E2E tests
- **Risk:** Low

#### 5.5 Graph Explorer
- **Description:** Interactive knowledge graph visualization
- **Files:** `frontend/components/graph/`
- **Components:**
  - GraphCanvas (D3.js or React Flow)
  - NodeInspector (entity details, relationships)
  - SearchBar (find entities in graph)
  - Legend (node types by color)
  - Controls (zoom, pan, reset, export)
- **Acceptance Criteria:**
  - Force-directed graph layout
  - Click node → show details
  - Double-click → expand node relationships
  - Relationship labels visible on edges
  - Filter by node type
  - Export as image
- **Verification:** Load graph, find "Krishna", expand to see all relationships
- **Testing:** Visual regression tests
- **Risk:** High — graph visualization is complex

#### 5.6 Scripture Reader
- **Description:** Read and navigate scripture texts
- **Files:** `frontend/components/scripture/`
- **Components:**
  - ScriptureSidebar (chapter list, search within)
  - ReaderView (multi-format: verse, chunk, source)
  - VerseSelector (book, chapter, verse navigation)
  - TranslationToggle (IAST, Devanagari, English)
  - CompareView (side-by-side scripture comparison)
- **Acceptance Criteria:**
  - Hierarchical navigation (scripture → chapter → verse)
  - Multiple translation views
  - Cross-reference display
  - Search within scripture
  - Comparison mode (2-3 scriptures side by side)
  - Copy verse with citation
- **Verification:** Navigate Bhagavad Gita, compare with Upanishads
- **Testing:** E2E tests for navigation paths
- **Risk:** Medium — text rendering complexity

#### 5.7 Timeline View
- **Description:** Event timeline across scriptures
- **Files:** `frontend/components/timeline/`
- **Acceptance Criteria:**
  - Chronological event display
  - Filter by scripture, entity, era
  - Click event → show details
  - Multiple timeline overlays (events across scriptures)
- **Risk:** Medium

#### 5.8 Admin Dashboard
- **Description:** System administration and monitoring
- **Files:** `frontend/components/admin/`
- **Acceptance Criteria:**
  - System health overview
  - Pipeline status
  - Usage statistics
  - Error logs
  - Cache statistics
  - User management
- **Risk:** Low

#### 5.9 Mobile Responsiveness
- **Description:** Ensure all pages work on mobile devices
- **Architecture:** Tailwind responsive classes + touch interactions
- **Acceptance Criteria:**
  - Chat interface usable on mobile (bottom input, tap to send)
  - Search usable on mobile (scrollable results, tap filter)
  - Minimum 320px width support
  - Touch-friendly targets (44px minimum)
- **Verification:** Lighthouse mobile audit >90
- **Testing:** Playwright mobile emulation
- **Risk:** Low

### Phase 5 Exit Criteria
- [x] Chat interface with streaming, markdown, citations
- [x] Knowledge search with filters
- [x] Graph explorer with interactive visualization
- [x] Scripture reader with multi-view
- [x] Timeline view
- [x] Admin dashboard
- [x] Mobile responsive
- [x] Lighthouse >90 (desktop), >80 (mobile)

---

## Phase 6: Quality & Evaluation

**Purpose:** Upgrade evaluation to use real pipeline, expand golden dataset, add regression benchmarks.

**Duration:** 2-3 weeks

**Dependencies:** Phase 2 (real retrieval pipeline), Phase 5 (frontend for evaluation UI)

### Tasks

#### 6.1 Golden Dataset Expansion
- **Description:** Expand from 100 to 500+ Q&A pairs
- **Categories to add:**
  - Entity relationships (100 new)
  - Cross-scripture comparisons (50 new)
  - Philosophical concepts (50 new)
  - Adversarial/edge cases (50 new)
  - Multi-hop reasoning (50 new)
  - Provenance tracing (50 new)
  - Translation comparison (50 new)
  - Historical context (50 new)
- **Acceptance Criteria:** 500+ verified questions with expected answers
- **Verification:** Manual review of 20% sample
- **Risk:** Low — manual effort

#### 6.2 Real Pipeline Evaluation
- **Description:** Replace mock search with real BM25+FAISS+Qdrant evaluation
- **Files:** `evaluation/runner.py` (major refactor), `evaluation/real_pipeline_eval.py`
- **Acceptance Criteria:**
  - Evaluation uses real pipeline (Qdrant, Neo4j, BM25)
  - All 8 quality gates measured on real pipeline
  - Comparison report: mock vs real performance
- **Verification:** Run evaluation, compare with previous mock results
- **Risk:** Medium — real pipeline may have different performance

#### 6.3 Regression Benchmark Suite
- **Description:** Automated regression benchmarks that run on every PR
- **Files:** `benchmarks/`, `.github/workflows/benchmark.yml`
- **Acceptance Criteria:**
  - 50+ benchmark queries
  - Automated benchmark execution in CI
  - Historical benchmark tracking
  - Regression alert if metrics drop >5%
- **Verification:** PR with degraded performance is flagged
- **Risk:** Low

#### 6.4 Answer Quality Evaluation
- **Description:** Automated answer quality scoring with LLM-as-Judge
- **Architecture:** DeepEval + GPT-4o judge
- **Files:** `evaluation/quality_eval.py`
- **Acceptance Criteria:**
  - Faithfulness scoring
  - Relevance scoring
  - Citation accuracy scoring
  - Hallucination detection
  - Answer completeness scoring
- **Risk:** Medium — LLM-as-Judge reliability

#### 6.5 Latency Budget Monitoring
- **Description:** Monitor and alert on API latency against budgets
- **Files:** `api/monitoring/latency.py`
- **Latency budgets:**
  - Search: <100ms P95
  - Chat response: <100ms first token, <5s complete
  - Embedding: <500ms
  - Graph query: <200ms
- **Risk:** Low

### Phase 6 Exit Criteria
- [x] Golden dataset: 500+ Q&A pairs
- [x] Real pipeline evaluation working
- [x] Regression benchmarks in CI
- [x] Answer quality evaluation with LLM-as-Judge
- [x] Latency budget monitoring active

---

## Phase 7: Security & Hardening

**Purpose:** Comprehensive security audit, hardening, and compliance.

**Duration:** 1-2 weeks

**Dependencies:** Phase 0 (auth infrastructure)

### Tasks

#### 7.1 Full Security Audit
- **Description:** Run the existing security audit (core/security/audit.py) against production configuration
- **Fix existing issues:**
  - 4 orphan nodes → remove or connect
  - Missing release manifest → generate
- **New checks to add:**
  - API endpoint security scan
  - Dependency vulnerability scan (pip-audit, safety)
  - Docker image scan (Trivy)
  - SAST scan (Semgrep)
  - Secrets scanning (truffleHog)
- **Acceptance Criteria:** Zero critical/high findings
- **Risk:** Medium

#### 7.2 Rate Limiting & DoS Protection
- **Description:** Implement production rate limiting
- **Architecture:** Redis-based sliding window + NGINX rate limiting
- **Files:** `api/middleware/rate_limit.py`, `nginx/rate_limit.conf`
- **Acceptance Criteria:**
  - Per-user rate limit: 100 req/min
  - Per-IP rate limit: 1000 req/min
  - Burst allowance: 20 requests
  - Rate limit headers in response (X-RateLimit-*)
  - 429 response when rate limited
- **Verification:** Send 101 requests in 1 second → 101st returns 429
- **Risk:** Low

#### 7.3 Input Validation & Sanitization
- **Description:** Comprehensive input validation for all endpoints
- **Architecture:** Pydantic models + custom validators
- **Acceptance Criteria:**
  - All API inputs validated with Pydantic
  - Prompt injection detection (NeMo Guardrails)
  - Path traversal prevention
  - Maximum input length enforcement
  - Special character handling
- **Verification:** Attempt prompt injection → blocked
- **Risk:** Low

#### 7.4 Secrets Management
- **Description:** Secure storage and rotation of API keys, database passwords
- **Architecture:** Environment variables + .env file + Docker secrets
- **Files:** `.env.example`, `docker-compose.secrets.yml`
- **Acceptance Criteria:**
  - No secrets in codebase
  - All secrets loaded from environment
  - Secret rotation mechanism
  - .gitignore includes .env
- **Verification:** `git grep` for API keys → 0 results
- **Risk:** Low

#### 7.5 Audit Logging
- **Description:** Comprehensive request audit logging
- **Architecture:** Structured JSON logging → OpenTelemetry → Loki
- **Files:** `api/middleware/audit.py`, `api/logging.py`
- **Acceptance Criteria:**
  - Every API request logged (method, path, user, IP, latency, status)
  - Sensitive data redacted from logs
  - Logs shipped to centralized storage
  - 30-day log retention
  - Audit trail for knowledge changes
- **Verification:** Generate request → appears in log search
- **Risk:** Low

### Phase 7 Exit Criteria
- [x] Security audit: zero critical/high findings
- [x] Rate limiting active
- [x] Input validation on all endpoints
- [x] Secrets management (no secrets in code)
- [x] Audit logging active
- [x] OWASP Top 10 compliance verified

---

## Phase 8: Release & Launch

**Purpose:** Final verification, documentation, and launch.

**Duration:** 2-3 weeks

**Dependencies:** All previous phases

### Tasks

#### 8.1 End-to-End Testing
- **Description:** Full system integration test
- **Scenarios:**
  - User registers → authenticates → asks question → gets streamed answer
  - User searches → filters → views result → opens scripture reader
  - User explores graph → expands nodes → views entity details
  - Admin checks health → views metrics → manages users
  - Plugin install → tools available → tools execute
- **Acceptance Criteria:** All scenarios pass
- **Verification:** CI test suite + manual walkthrough
- **Risk:** Medium

#### 8.2 Load Testing
- **Description:** Verify system under load
- **Architecture:** k6 or locust
- **Files:** `tests/load/`
- **Targets:**
  - 100 concurrent users
  - 50 QPS sustained
  - P95 latency <500ms for API
  - P95 latency <5s for chat completion
  - 99% uptime
- **Verification:** Load test passes for 30 minutes
- **Risk:** Medium — may find bottlenecks

#### 8.3 Documentation Finalization
- **Description:** Complete all documentation for launch
- **Documents:**
  - API reference (auto-generated from FastAPI)
  - User guide (how to use AstroSage AI)
  - Developer guide (how to extend AstroSage)
  - Deployment guide (how to self-host)
  - MCP server guide (how to add tools)
  - Plugin developer guide (how to create plugins)
  - Operations guide (how to monitor and maintain)
  - FAQ + troubleshooting
- **Acceptance Criteria:** All guides reviewed and complete
- **Risk:** Low — effort-intensive but straightforward

#### 8.4 Production Deployment
- **Description:** Deploy to production environment
- **Architecture:** Docker Compose → Kubernetes (if needed)
- **Steps:**
  1. Deploy to staging, run full test suite
  2. Smoke test: all endpoints working
  3. Deploy to production (blue-green)
  4. Monitor for 24 hours
  5. Announce launch
- **Verification:** Production monitoring shows all green
- **Risk:** High — production deployment always carries risk

#### 8.5 Launch Checklist
- [x] All quality gates passing
- [x] Load test passes (100 concurrent users, 50 QPS)
- [x] Security audit: zero critical/high
- [x] All documentation published
- [x] Monitoring and alerting configured
- [x] Backup and restore procedures tested
- [x] Incident response plan documented
- [x] Rollback procedure documented
- [x] Performance budgets met
- [x] Accessibility audit passed
- [x] Mobile responsive verified
- [x] Cross-browser tested (Chrome, Firefox, Safari, Edge)

### Phase 8 Exit Criteria
- [x] Production deployment live
- [x] Load test: 100 users, 50 QPS
- [x] All quality gates GREEN
- [x] Documentation complete
- [x] Monitoring active with alerts
- [x] Incident response plan ready

---

## Risk Assessment & Mitigation by Phase

| Phase | Overall Risk | Key Risks | Mitigations |
|-------|-------------|-----------|-------------|
| 0 | 🟢 Low | Configuration complexity | Standard patterns, template-based |
| 1 | 🟡 Medium | GPU memory, model licensing | Local + cloud hybrid, fallback to API |
| 2 | 🟡 Medium | Data migration, integration complexity | Batch migration with validation |
| 3 | 🟢 Low | Privacy concerns | Opt-in memory, clear privacy controls |
| 4 | 🟡 Medium | MCP spec changes, security | Abstraction layer, sandboxed execution |
| 5 | 🔴 High | Frontend complexity, UX quality | Prototype first, iterate with feedback |
| 6 | 🟡 Medium | LLM-as-Judge reliability | Multiple judges, human validation |
| 7 | 🟢 Low | Standard security practices | Well-known patterns, tools |
| 8 | 🔴 High | Production deployment | Blue-green, rollback plan, monitoring |

---

## Dependency Graph

```
Phase 0 (Foundation & API)
  ├── Phase 1 (Core AI Serving)
  │   ├── Phase 2 (Knowledge Infrastructure)
  │   │   └── Phase 3 (Memory & State)
  │   └── Phase 4 (MCP & Tool Ecosystem)
  ├── Phase 5 (Frontend) [also depends on 2, 4]
  ├── Phase 6 (Quality) [also depends on 2]
  └── Phase 7 (Security) [also depends on 0]
      └── Phase 8 (Release)
```

Critical path: Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 5 → Phase 8

---

## Resource Requirements

### Phase 0-1 (Foundation + AI Core)
- 2 backend engineers
- 1 DevOps engineer (part-time)
- 1 GPU instance (A10G or A100, ~$1-3/hr)

### Phase 2-3 (Knowledge + Memory)
- 2 backend engineers
- 1 data engineer (part-time)

### Phase 4 (MCP + Tools)
- 2 backend engineers
- 1 security engineer (part-time)

### Phase 5 (Frontend)
- 2 frontend engineers
- 1 designer (part-time)

### Phase 6-7 (Quality + Security)
- 1 QA engineer
- 1 security engineer

### Phase 8 (Release)
- All team members
- 1 SRE (part-time)

---

## Rollback Strategy by Phase

| Phase | Rollback Action | Data Loss | Downtime |
|-------|----------------|-----------|----------|
| 0 | Revert to git commit, `docker compose down` | None | <5 min |
| 1 | Switch to cloud-only mode (LiteLLM fallback) | None | <1 min |
| 2 | Switch to file-based fallback (JSON files) | None | <1 min |
| 3 | Disable memory, stateless mode | Memory only | Instant |
| 4 | Disable MCP, direct function calls | Tool state | Instant |
| 5 | Switch to previous frontend version | None | DNS change |
| 6 | Revert to previous evaluation baseline | Benchmark data | None |
| 7 | Disable rate limiting, reduce logging | None | Instant |
| 8 | DNS rollback to previous deployment | None | <5 min |

---

## Success Criteria

The roadmap is complete when ALL of the following are true:

### Functional
- [x] User can ask questions and receive streamed, cited answers
- [x] User can search the knowledge base with hybrid retrieval
- [x] User can explore the knowledge graph interactively
- [x] User can read scriptures in multiple formats
- [x] User can compare scriptures side by side
- [x] External tools can connect via MCP
- [x] Plugins can be installed and enabled
- [x] User preferences persist across sessions

### Non-Functional
- [x] API latency: P95 <100ms (search), <5s (chat)
- [x] Throughput: 50 QPS sustained
- [x] Concurrency: 100 simultaneous users
- [x] Uptime: 99.9%
- [x] Security: OWASP Top 10 compliant
- [x] Mobile: responsive on all devices
- [x] Accessibility: WCAG 2.1 AA

### Quality
- [x] 500+ golden evaluation questions
- [x] All 8 quality gates PASS
- [x] Retrieval P@10 >0.7, NDCG@10 >0.8
- [x] Hallucination rejection rate >95%
- [x] Regression: no metrics regress >5%

### Business
- [x] Production deployment live
- [x] Documentation complete and published
- [x] Monitoring and alerting configured
- [x] Incident response plan documented
- [x] Rollback procedure tested

---

## Appendix: File Manifest

### New Files to Create

```
Phase 0:
  api/main.py                          # FastAPI app entry point
  api/config.py                        # Pydantic configuration
  api/auth.py                          # JWT authentication
  api/dependencies.py                  # FastAPI dependencies
  api/middleware/__init__.py           # Middleware
  api/middleware/cors.py               # CORS
  api/middleware/rate_limit.py         # Rate limiting
  api/middleware/audit.py              # Audit logging
  api/exceptions.py                    # Exception classes
  api/models/user.py                   # User model
  api/models/__init__.py              # Models
  api/routes/__init__.py              # Routes
  api/routes/health.py                # Health endpoint
  api/routes/auth.py                  # Auth endpoints
  Dockerfile                           # Multi-stage Docker build
  docker-compose.yml                   # Development compose
  .github/workflows/ci.yml            # CI pipeline
  .github/workflows/deploy.yml        # CD pipeline
  CONTRIBUTING.md                      # Contribution guide
  SECURITY.md                          # Security policy

Phase 1:
  api/services/embeddings.py          # Embedding service
  api/services/local_llm.py           # vLLM integration
  api/services/model_router.py        # LiteLLM router
  api/services/chat.py                # Chat service
  api/routes/chat.py                  # Chat endpoints
  api/routes/embeddings.py            # Embedding endpoints
  config/models.yaml                  # Model configuration
  docker/vllm/Dockerfile              # vLLM Docker image

Phase 2:
  api/services/vector_db.py           # Qdrant service
  api/services/knowledge_graph.py     # Neo4j service
  api/services/graphrag.py            # LightRAG service
  api/services/fulltext_search.py     # Meilisearch service
  api/services/search.py              # Unified search
  api/routes/search.py                # Search endpoints
  api/routes/graph.py                 # Graph endpoints
  scripts/migrate_to_qdrant.py        # Migration script
  scripts/migrate_graph_to_neo4j.py   # Migration script
  scripts/initialize_lightrag.py      # LightRAG init
  scripts/seed_meilisearch.py         # Meilisearch seed

Phase 3:
  api/services/memory.py              # Mem0 service
  api/services/conversation.py        # Conversation service
  api/services/cache.py               # Cache service
  api/routes/memory.py                # Memory endpoints
  api/routes/conversation.py          # Conversation endpoints

Phase 4:
  mcp/astrosage_server.py             # MCP server
  mcp/client.py                       # MCP client
  mcp/discovery.py                    # MCP discovery
  mcp/tools/__init__.py              # Tools
  mcp/tools/knowledge.py              # Knowledge tools
  mcp/tools/reasoning.py              # Reasoning tools
  mcp/tools/graph.py                  # Graph tools
  api/routes/plugins.py               # Plugin endpoints
  api/services/plugin_manager.py      # Plugin service

Phase 5:
  frontend/ (full Next.js project)
  frontend/package.json
  frontend/tsconfig.json
  frontend/tailwind.config.ts
  frontend/app/ (App Router pages)
  frontend/components/ (all components)
  frontend/lib/ (API client, helpers)

Phase 6:
  evaluation/golden_dataset_v2.json   # 500+ Q&A
  evaluation/real_pipeline_eval.py    # Real pipeline eval
  benchmarks/                         # Benchmark suite
  tests/load/                         # Load tests

Phase 7:
  (Middleware already created in Phase 0)
  nginx/rate_limit.conf               # NGINX config
  security/audit_report.md            # Audit findings
```

---

## Final Note

This roadmap transforms AstroSage from a batch-processing knowledge engine into a world-class AI platform. The key architectural decisions are:

1. **FastAPI** for the API layer (async, Pydantic, auto-docs)
2. **LangGraph** for agent orchestration (state machines, MCP)
3. **Qdrant + Neo4j** for vector + graph storage (hybrid search, relationships)
4. **LightRAG** for GraphRAG (community-aware retrieval)
5. **vLLM + LiteLLM** for model serving (local + cloud hybrid)
6. **Mem0** for memory (user sessions, knowledge)
7. **MCP** for tool ecosystem (industry standard)
8. **Next.js 15** for frontend (SSR, streaming, TypeScript)
9. **LangFuse + Phoenix** for observability (traces, metrics)
10. **Keycloak + JWT** for security (auth, rate limiting)

Every phase has clear exit criteria, dependencies, risk assessment, and rollback strategy. The total estimated timeline is 16-23 weeks with a team of 2-4 engineers.

The mission is not to finish phases. The mission is to continuously improve until no meaningful autonomous improvement remains.
