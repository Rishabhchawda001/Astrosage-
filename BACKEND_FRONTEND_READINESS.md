# Backend Frontend Readiness Report

**Audit Date:** 2026-07-19

---

## Summary

**The backend CANNOT support frontend development in its current state.**

A frontend requires an HTTP API. The backend has no API server.

---

## Frontend Feature Support Matrix

| Frontend Feature | Backend Capability | API Endpoint | Status |
|-----------------|-------------------|--------------|--------|
| Search UI | BM25 + FAISS hybrid search | `/api/v1/search` | ❌ No API |
| Knowledge Explorer | Graph traversal | `/api/v1/graph` | ❌ No API |
| Graph Visualization | Entity + edge data | `/api/v1/graph/entity/{name}` | ❌ No API |
| Scripture Reader | Chunk retrieval | `/api/v1/chunks` | ❌ No API |
| Compare View | Multi-scripture comparison | `/api/v1/compare` | ❌ No API |
| Timeline | Event ordering | `/api/v1/events` | ❌ No API |
| Answer QA | Reasoning + answer gen | `/api/v1/answer` | ❌ No API |
| Evidence Panel | Citation retrieval | `/api/v1/evidence` | ❌ No API |
| Analytics Dashboard | Metrics aggregation | `/api/v1/metrics` | ❌ No API |
| Real-time Search | WebSocket/SSE | `/ws/search` | ❌ No API |
| User Authentication | User management | `/api/v1/auth` | ❌ No system |
| Caching | LRU cache | `/api/v1/cache` | ❌ No API |

---

## What the Backend CAN Provide (via scripts)

| Capability | How | Limitation |
|-----------|-----|-----------|
| Knowledge graph data | Read JSON files | Manual file access |
| Search results | Run phase13 script | No real-time API |
| Reasoning results | Run phase14 script | Pre-computed only |
| Answers | Run phase15 script | Pre-computed only |
| Evaluation metrics | Run evaluation/runner.py | Mock search only |

---

## Minimum Viable API (MVP)

For a frontend to work, the backend needs at minimum:

```python
# Minimum FastAPI server (conceptual)
from fastapi import FastAPI
app = FastAPI()

@app.get("/api/v1/health")
async def health(): ...

@app.post("/api/v1/search")
async def search(query: str, top_k: int = 10): ...

@app.post("/api/v1/answer")
async def answer(question: str): ...

@app.get("/api/v1/graph/entity/{name}")
async def entity(name: str): ...

@app.get("/api/v1/graph/scripture/{id}")
async def scripture(id: str): ...
```

**Estimated effort to build MVP API:** 2-4 days

---

## Recommended Frontend Stack

| Component | Recommendation | Reason |
|-----------|---------------|--------|
| Framework | Next.js 14+ | SSR, API routes, TypeScript |
| State | Zustand or React Query | Server state management |
| Styling | Tailwind CSS | Rapid development |
| Search | Algolia-style search UI | Familiar UX |
| Graph | D3.js or React Flow | Interactive visualization |
| Charts | Recharts | Analytics dashboard |

---

## Frontend Readiness Score: 0/10

No API exists. Frontend development is blocked.
