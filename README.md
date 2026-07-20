# AstroSage — Evidence-First Hindu Knowledge System

**API Version**: 2.3.0
**Knowledge Layer**: v1.0.0 (Frozen — immutable)
**Quality Gates**: ✅ 8/8 PASS
**Repository**: [github.com/Rishabhchawda001/Astrosage-](https://github.com/Rishabhchawda001/Astrosage-)

---

## Vision

AstroSage is a permanent, AI-native Knowledge Operating System for Hindu scriptures.
It preserves, reconstructs, validates, connects, retrieves, and reasons over knowledge
while maintaining **complete provenance** and **verifiable evidence** for every claim.

Every answer is explainable. Every claim is traceable to original canonical evidence.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE FREEZE v1.0.0                    │
│         120K semantic chunks, 391 entities, 5K edges         │
└──────────┬───────────────────────────────────────────────────┘
           │
┌──────────▼───────────────────────────────────────────────────┐
│                    API SERVER (FastAPI)                       │
│  ┌─────────────┐ ┌──────────┐ ┌─────────┐ ┌──────────────┐  │
│  │  Search API  │ │   Chat   │ │   MCP   │ │   Web UI     │  │
│  │ BM25+Expand  │ │ LiteLLM  │ │ 7 tools │ │ Vanilla SPA  │  │
│  └─────────────┘ └──────────┘ └─────────┘ └──────────────┘  │
│  ┌─────────────┐ ┌──────────┐ ┌─────────┐                   │
│  │  Auth/JWT   │ │  Cache   │ │Convers. │                   │
│  │ + API Keys  │ │ LRU+TTL  │ │ SQLite  │                   │
│  └─────────────┘ └──────────┘ └─────────┘                   │
└──────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites
- Python 3.10+
- 4GB+ RAM (for knowledge base loading)

### Install & Run

```bash
git clone https://github.com/Rishabhchawda001/Astrosage-.git
cd Astrosage-

pip install fastapi uvicorn pydantic-settings python-jose passlib bcrypt httpx \
            pytest pytest-asyncio rank-bm25 numpy litellm

# Start the API server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker

```bash
docker-compose up --build
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/health` | Health check |
| `POST` | `/api/v1/auth/register` | Register user |
| `POST` | `/api/v1/auth/token` | Get JWT token |
| `POST` | `/api/v1/search` | BM25 lexical search |
| `GET` | `/api/v1/search?q=` | Quick search |
| `POST` | `/api/v1/answer` | Grounded answer with evidence |
| `GET` | `/api/v1/graph/entity/{name}` | Entity lookup |
| `GET` | `/api/v1/graph/search?q=` | Entity name search |
| `GET` | `/api/v1/graph/scriptures` | List all scriptures |
| `GET` | `/api/v1/graph/scripture/{id}` | Scripture metadata |
| `GET` | `/api/v1/graph/path?source=&target=` | BFS path finding |
| `GET` | `/api/v1/graph/stats` | Graph statistics |
| `POST` | `/api/v1/chat/completions` | OpenAI-compatible chat |
| `POST` | `/api/v1/conversations` | Create conversation |
| `GET` | `/api/v1/conversations` | List conversations |
| `GET` | `/api/v1/conversations/{id}` | Get conversation |
| `POST` | `/api/v1/conversations/{id}/messages` | Add message |
| `GET` | `/api/v1/cache/stats` | Cache statistics |
| `POST` | `/api/v1/cache/clear` | Clear cache |
| `GET` | `/` | Web UI |

### Example: Answer a question

```bash
curl -X POST http://localhost:8000/api/v1/answer \
  -H "Content-Type: application/json" \
  -d '{"question": "Who is Krishna?", "top_k": 5}'
```

### Example: Search

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Bhagavad Gita", "top_k": 10}'
```

---

## MCP Server (Claude Desktop Integration)

```bash
# Stdio mode (Claude Desktop)
python3 mcp_server.py

# SSE mode (web clients)
python3 mcp_server.py --sse --port 8001
```

### Available Tools

| Tool | Description |
|------|-------------|
| `search_knowledge` | BM25 search over 120K chunks |
| `get_entity` | Entity lookup with relationships |
| `get_entity_relationships` | Relationship exploration |
| `list_scriptures` | List all 54 indexed scriptures |
| `get_scripture` | Scripture metadata |
| `answer_question` | Grounded QA with citations |
| `knowledge_stats` | Knowledge base statistics |

---

## Quality Metrics (Real Pipeline Evaluation)

**Dataset**: 155 Q&A pairs across 6 categories
**Pipeline**: Real BM25 + Query Expansion + Entity Pre-filtering

| Gate | Threshold | Actual | Status |
|------|-----------|--------|--------|
| Retrieval Latency P95 | < 100ms | **1.4ms** | ✅ |
| Entity Recall@5 | ≥ 30% | **71.4%** | ✅ |
| NDCG@5 | ≥ 0.3 | **0.778** | ✅ |
| Hallucination Rejection | ≥ 80% | **100%** | ✅ |
| Max Adversarial Confidence | < 0.6 | **0.50** | ✅ |
| Regression Rate | < 10% | **0%** | ✅ |
| Graph Integrity | 100% | **100%** | ✅ |
| Test Pass Rate | ≥ 95% | **100%** | ✅ |

**Overall**: ✅ **8/8 QUALITY GATES PASS**

### Key Technical Improvements

- **Entity-guided BM25**: Pre-filters chunks by entity match (260x latency improvement)
- **Query Expansion**: Sanskrit/Hindi/English term bridging (4.5x precision improvement)
- **Adversarial Detection**: Blocks non-Hindu texts, out-of-domain topics
- **Punctuation-aware Tokenization**: Strips punctuation for correct term matching

---

## Knowledge Layer (Frozen v1.0.0)

| Artifact | Count |
|----------|-------|
| Scriptures | 54 |
| Entities | 391 |
| Relationships | 5,044 |
| Semantic Chunks | 120,548 |
| Embeddings | 120,548 (384d, MiniLM-L6-v2) |
| Relationship Types | 68 |
| Graph Integrity | 100% |

---

## Core Capabilities

| Capability | Description |
|-----------|-------------|
| **Entity-Guided BM25 Search** | < 2ms P95, query expansion, cache |
| **Knowledge Graph** | 391 entities, 54 scriptures, 5K edges |
| **Grounded Answers** | Provenance-traced, confidence-scored |
| **Chat Completions** | OpenAI-compatible, LiteLLM routing, SSE streaming |
| **Conversation Management** | Persisted to SQLite, auto-title generation |
| **Cache Layer** | LRU cache with TTL (search: 5min, answer: 10min) |
| **MCP Server** | Claude Desktop compatible, 7 tools |
| **Web UI** | Vanilla JS SPA, chat + search + login |
| **Adversarial Detection** | Blocks non-Hindu content, 100% rejection |
| **Quality Evaluation** | 155 Q&A golden dataset, 8 quality gates |
| **Authentication** | JWT + API key, bcrypt password hashing |
| **Docker Support** | Multi-stage build, docker-compose |

---

## Development

```bash
# Install dev dependencies
pip install pytest pytest-asyncio mypy ruff

# Run all API tests
APP_ENVIRONMENT=development python3 -m pytest api/tests/ -v

# Run real pipeline evaluation
APP_ENVIRONMENT=development python3 -m evaluation.real_pipeline_eval

# Run knowledge system tests
APP_ENVIRONMENT=development python3 -m pytest tests/ -q --tb=short \
  --ignore=tests/test_phase31.py --ignore=tests/test_phase35.py

# Start with hot reload
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Test Suite

| Suite | Tests | Status |
|-------|-------|--------|
| API Tests | 59 | ✅ Passing |
| Knowledge Core Tests | 858 | ✅ Passing |
| Evaluation Framework | 31 | ✅ Passing |
| Query Expansion | 26 | ✅ Passing |
| Cache | 12 | ✅ Passing |
| Answer Generation | 14 | ✅ Passing |
| **Total** | **~1000** | ✅ **All Passing** |

---

## License

Proprietary — AstroSage Knowledge System

---

## Project Structure

```
Astrosage-/
├── api/                   # FastAPI server
│   ├── main.py            # Application entry point
│   ├── config.py          # Pydantic settings
│   ├── services/          # Knowledge, chat, auth, cache, conversation
│   ├── routes/            # API route handlers
│   ├── models/            # Pydantic request/response models
│   ├── middleware/         # Auth, CORS, rate limiting
│   ├── static/            # Web UI (index.html)
│   └── tests/             # API tests
├── evaluation/            # Quality evaluation framework
│   ├── real_pipeline_eval.py  # Real BM25 evaluation
│   ├── golden_dataset.json    # 155 Q&A pairs
│   ├── quality_gates.py       # 8 quality gates
│   └── ...
├── core/                  # Knowledge core modules
│   ├── query_expansion/   # Sanskrit/Hindi/English bridging
│   ├── cache/             # LRU cache
│   └── ...
├── knowledge/             # Frozen knowledge release
│   └── releases/v1.0.0/   # 120K chunks, 391 entities, 5K edges
├── mcp_server.py          # MCP server (Claude Desktop)
├── docker-compose.yml     # API + Redis + PostgreSQL
└── Dockerfile             # Multi-stage build
```
