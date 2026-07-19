# Backend Blockers

**Audit Date:** 2026-07-19
**Decision:** ❌ NOT READY

---

## Blocker #1: No API Server (CRITICAL)

**Problem:** There is no HTTP server anywhere in the repository. No FastAPI, no Flask, no Django, no WebSocket server. The backend is entirely script-based.

**Evidence:**
- `grep -r "FastAPI\|Flask\|Django\|uvicorn" --include="*.py" .` returns zero results
- No `main.py` or `app.py` entry point exists
- OpenAPI specs in `openapi/` are design documents only — no implementation

**Impact:** Frontend cannot send requests to the backend. This is a complete blocker for any frontend integration.

**Required Action:** Implement a FastAPI server with endpoints for search, answer, graph queries, health, and metrics.

**Estimated Effort:** 2-4 days

---

## Blocker #2: FAISS Index Not in Repository (HIGH)

**Problem:** The FAISS binary index (`faiss_index.bin`, ~185MB) and embeddings numpy file (`embeddings.npy`, ~185MB) are gitignored and not committed to the repository.

**Evidence:**
- `.gitignore` contains `knowledge/embeddings/`
- `knowledge/releases/v1.0.0/embeddings/` contains only `chunk_id_mapping.json` and `embedding_manifest.json`
- `find . -name "faiss_index*"` returns nothing
- `phase13_hybrid_retrieval.py` and `phase14_reasoning_engine.py` both require `faiss_index.bin`

**Impact:** A fresh clone cannot run the real hybrid retrieval or reasoning pipelines. Only pre-computed results are available.

**Required Action:** Either commit the FAISS index to the repository (using Git LFS) or implement a regeneration script that is automatically triggered on first run.

**Estimated Effort:** 1 day

---

## Blocker #3: No Authentication (HIGH)

**Problem:** There is no user authentication or authorization system.

**Evidence:**
- No user model, no JWT, no API keys, no session management
- No login/signup endpoints
- No middleware for auth checking

**Impact:** Any user can access all data without restriction. No access control whatsoever.

**Required Action:** Implement JWT-based authentication with API key support for programmatic access.

**Estimated Effort:** 1-2 days

---

## Blocker #4: No Docker/Deployment Configuration (HIGH)

**Problem:** There is no Dockerfile, docker-compose.yml, or any deployment configuration.

**Evidence:**
- `find . -name "Dockerfile"` returns nothing
- `find . -name "docker-compose*"` returns nothing
- No Kubernetes manifests, no Terraform, no Ansible

**Impact:** Cannot deploy the backend in any standard way. No reproducible deployment.

**Required Action:** Create Dockerfile, docker-compose.yml, and basic deployment documentation.

**Estimated Effort:** 1 day

---

## Blocker #5: Evaluation Uses Mock Search (MEDIUM)

**Problem:** The evaluation runner (`evaluation/runner.py`) uses `_mock_search()` which queries the knowledge graph directly, not the real BM25+FAISS pipeline.

**Evidence:**
- `_mock_search()` method in `runner.py` performs graph traversal, not vector search
- Quality gate metrics are based on mock search results
- No evaluation exists for the real hybrid retrieval pipeline

**Impact:** Quality metrics do not reflect real-world retrieval performance. The 68.3% entity recall and 0.994 NDCG@5 are measured on graph lookup, not semantic search.

**Required Action:** Create a separate evaluation path that uses the real BM25+FAISS pipeline.

**Estimated Effort:** 1 day

---

## Blocker #6: Missing Release Manifest (MEDIUM)

**Problem:** The master release manifest (`knowledge/releases/v1.0.0/manifest.json`) does not exist.

**Evidence:**
- Security audit reports: "Release manifest not found"
- Individual artifact manifests exist but no master manifest
- SHA256 verification cannot be done end-to-end

**Impact:** Provenance chain is incomplete. Cannot verify entire release integrity.

**Required Action:** Generate master release manifest with SHA256 hashes of all artifacts.

**Estimated Effort:** 0.5 day

---

## Priority Order

| # | Blocker | Priority | Effort | Blocks |
|---|---------|----------|--------|--------|
| 1 | No API Server | CRITICAL | 2-4 days | Everything |
| 2 | FAISS Index Missing | HIGH | 1 day | Real search |
| 3 | No Authentication | HIGH | 1-2 days | Secure access |
| 4 | No Docker | HIGH | 1 day | Deployment |
| 5 | Mock Search Evaluation | MEDIUM | 1 day | Accurate metrics |
| 6 | Missing Manifest | MEDIUM | 0.5 day | Provenance |

**Total estimated effort to clear all blockers: 6.5-9.5 days**
