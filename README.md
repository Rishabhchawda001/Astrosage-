# AstroSage — Evidence-First Hindu Knowledge System

**Version**: 2.5.0
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

## Quick Start

### Docker (Recommended)

```bash
git clone https://github.com/Rishabhchawda001/Astrosage-.git
cd Astrosage-
docker compose up --build
```

- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Manual Setup

```bash
# API
pip install fastapi uvicorn pydantic-settings python-jose passlib bcrypt httpx
uvicorn api.main:app --reload --port 8000

# Frontend
cd frontend && npm install && npm run dev
```

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
│  │  Search API  │ │   Chat   │ │   MCP   │ │   Frontend   │  │
│  │ BM25+Expand  │ │ LiteLLM  │ │ 7 tools │ │  Next.js SSR │  │
│  └─────────────┘ └──────────┘ └─────────┘ └──────────────┘  │
│  ┌─────────────┐ ┌──────────┐ ┌─────────┐                   │
│  │  Auth/JWT   │ │  Cache   │ │Convers. │                   │
│  │ + API Keys  │ │ LRU+TTL  │ │ SQLite  │                   │
│  └─────────────┘ └──────────┘ └─────────┘                   │
└──────────────────────────────────────────────────────────────┘
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/health` | Health check with component status |
| `POST` | `/api/v1/auth/register` | Register user |
| `POST` | `/api/v1/auth/token` | Get JWT token |
| `POST` | `/api/v1/search` | BM25 lexical search with query expansion |
| `POST` | `/api/v1/answer` | Grounded answer with evidence + provenance |
| `GET` | `/api/v1/graph/entity/{name}` | Entity lookup with relationships |
| `GET` | `/api/v1/graph/search?q=` | Entity name search |
| `GET` | `/api/v1/graph/stats` | Knowledge graph statistics |
| `POST` | `/api/v1/chat/completions` | Chat completions (SSE streaming) |
| `GET` | `/api/v1/conversations` | List conversations |
| `POST` | `/api/v1/conversations` | Create conversation |
| `POST` | `/api/v1/cache/clear` | Clear caches |

---

## Frontend Pages

| Page | Route | Description |
|------|-------|-------------|
| Landing | `/` | Cinematic landing with sacred atmosphere |
| Chat | `/chat` | AI conversation with evidence-backed answers |
| Search | `/search` | Knowledge search across 120K+ chunks |
| Explore | `/explore` | Interactive knowledge graph explorer |

---

## Quality Metrics

| Metric | Value |
|--------|-------|
| Quality Gates | 8/8 PASS |
| API Tests | 59 passing |
| Golden Dataset | 155 Q&A pairs |
| Adversarial Rejection | 100% |
| BM25 P95 Latency | 1.5ms |
| Knowledge Freeze | v1.0.0 (immutable) |

---

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for full production deployment guide.

**Production stack**: Nginx → FastAPI + Next.js → Redis + PostgreSQL

**Docker Compose (Production)**:
```bash
cp .env.production .env
# Edit .env with production values
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## Development

```bash
make dev          # Start API + Frontend
make test         # Run API tests
make build        # Build frontend
make lint         # Lint all code
```

---

## License

Open source. See repository for details.
