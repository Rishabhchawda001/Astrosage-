# AstroSage Backend Architecture Report

**Audit Date:** 2026-07-19
**Auditor:** Independent Production Readiness Review Board
**Repository:** main @ ed1e5b6

---

## Executive Summary

AstroSage's backend is a **script-based knowledge pipeline** — not a production API server. It consists of frozen knowledge artifacts, batch processing scripts, and evaluation infrastructure. There is **no HTTP/REST/WebSocket API**, **no containerization**, and **no deployment configuration**.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                 FROZEN KNOWLEDGE LAYER v1.0.0                │
│  knowledge/releases/v1.0.0/                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐  │
│  │  Graph   │ │  Chunks  │ │Retrieval │ │   Reasoning   │  │
│  │ 445 nodes│ │ 120,548  │ │ BM25     │ │ 5 entities    │  │
│  │ 5,044    │ │  chunks  │ │ (no FAISS│ │ 4 questions   │  │
│  │ edges    │ │          │ │  in repo)│ │               │  │
│  └──────────┘ └──────────┘ └──────────┘ └───────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                   BATCH PIPELINE SCRIPTS                     │
│  phase10 → phase11 → phase12 → phase13 → phase14 → phase15 │
│  (freeze)  (chunk)  (embed)  (retrieval)(reason)(answer)    │
└──────────────────────────┬──────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    CORE MODULES (v1.2)                       │
│  ┌──────────┐ ┌──────┐ ┌──────────┐ ┌──────────┐ ┌──────┐ │
│  │  Query   │ │Cache │ │  Graph   │ │  Answer  │ │Secur-│ │
│  │Expansion │ │ (LRU)│ │Enrichment│ │  Gen     │ │ity   │ │
│  └──────────┘ └──────┘ └──────────┘ └──────────┘ └──────┘ │
└──────────────────────────┬──────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                EVALUATION FRAMEWORK (v1.1)                   │
│  Golden Dataset (100 Q&A) → Retrieval Eval → Quality Gates  │
│  Hallucination Eval → Regression Eval → Explainability      │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Layers

### Layer 1: Frozen Knowledge (v1.0.0)

| Artifact | Location | Size | Status |
|----------|----------|------|--------|
| Knowledge Graph | `graph/graph.json` | 445 nodes, 5,044 edges | ✅ Verified |
| Entity Nodes | `graph/nodes/entity_nodes.json` | 391 entities, 14 types | ✅ Verified |
| Scripture Nodes | `graph/nodes/scripture_nodes.json` | 54 scriptures | ✅ Verified |
| Relationship Edges | `graph/edges/relationship_edges.json` | 5,044 edges, 68 types | ✅ Verified |
| Scripture Chunks | `chunks/scripture_chunks.json` | 9,307 chunks | ✅ Verified |
| Entity Chunks | `chunks/entity_chunks.json` | 41,884 chunks | ✅ Verified |
| Dialogue Chunks | `chunks/dialogue_chunks.json` | 6,631 chunks | ✅ Verified |
| Event Chunks | `chunks/event_chunks.json` | 1,273 chunks | ✅ Verified |
| Verse Chunks | `chunks/verses/` | 61,453 chunks (82 files) | ✅ Verified |
| BM25 Index | `retrieval/bm25_index.json` | 375K vocab | ✅ Verified |
| FAISS Index | `embeddings/faiss_index.bin` | 120K vectors, 384d | ❌ NOT IN REPO |
| Embeddings NPY | `embeddings/embeddings.npy` | 185MB | ❌ NOT IN REPO |
| Chunk Mapping | `embeddings/chunk_id_mapping.json` | 120K mappings | ✅ Verified |
| Reasoning Results | `reasoning/entity_reasoning.json` | 5 entities | ✅ Verified |
| Answer Results | `answers/grounded_answers.json` | 5 answers | ✅ Verified |

### Layer 2: Batch Pipeline Scripts

| Script | Purpose | Status |
|--------|---------|--------|
| `phase10_knowledge_freeze.py` | Freeze knowledge artifacts | ✅ Complete |
| `phase11_semantic_chunker.py` | Generate semantic chunks | ✅ Complete |
| `phase12_embeddings.py` | Generate embeddings + FAISS index | ✅ Complete (but output gitignored) |
| `phase13_hybrid_retrieval.py` | Build BM25 + FAISS hybrid search | ✅ Complete |
| `phase14_reasoning_engine.py` | Entity + question reasoning | ✅ Complete |
| `phase15_answer_generation.py` | Grounded answer generation | ✅ Complete |

### Layer 3: Core Modules (v1.2)

| Module | Purpose | Status |
|--------|---------|--------|
| `core/query_expansion/` | Sanskrit-Hindi-English query expansion | ✅ Working |
| `core/cache/` | LRU cache with TTL + persistence | ✅ Working |
| `core/graph_enrichment/` | MENTIONED_IN → specific relationship enrichment | ✅ Working |
| `core/answer_generation/` | Template-based NL answer generation | ✅ Working |
| `core/security/` | Security audit (graph integrity, provenance) | ✅ Working (2 medium/high findings) |

### Layer 4: Evaluation Framework (v1.1)

| Module | Purpose | Status |
|--------|---------|--------|
| `evaluation/golden_dataset.json` | 100 Q&A pairs across 6 categories | ✅ Complete |
| `evaluation/runner.py` | Orchestrates evaluation (uses **mock search**) | ✅ Working |
| `evaluation/retrieval_eval.py` | Precision@k, Recall@k, NDCG@k | ✅ Working |
| `evaluation/hallucination_eval.py` | Adversarial query detection | ✅ Working |
| `evaluation/regression_eval.py` | Baseline comparison | ✅ Working |
| `evaluation/explainability.py` | Reasoning traces | ✅ Working |
| `evaluation/quality_gates.py` | 8 release criteria | ✅ All 8 PASS |

---

## Critical Architectural Findings

### 1. No Production API Server

**Impact:** CRITICAL

There is **no HTTP server** in the backend. No FastAPI, no Flask, no Django, no WebSocket. The system is entirely script-based:

- `python3 scripts/phase13_hybrid_retrieval.py` → builds indices
- `python3 scripts/phase14_reasoning_engine.py` → runs reasoning
- `python3 scripts/phase15_answer_generation.py` → generates answers

A frontend **cannot** query this backend without an API layer.

### 2. FAISS Index Not in Repository

**Impact:** HIGH

The FAISS binary index (`faiss_index.bin`, ~185MB) and embeddings numpy file (`embeddings.npy`, ~185MB) are gitignored and not committed. A fresh clone cannot run the real hybrid retrieval pipeline without regenerating these (~57 minutes of compute).

### 3. Evaluation Uses Mock Search

**Impact:** MEDIUM

The evaluation runner (`evaluation/runner.py`) uses `_mock_search()` which queries the knowledge graph directly — not the real BM25+FAISS pipeline. Quality gate metrics are based on mock search, not production retrieval.

### 4. No Containerization

**Impact:** HIGH

No Dockerfile, no docker-compose.yml, no Kubernetes manifests. No deployment automation exists.

### 5. No Authentication/Authorization

**Impact:** HIGH

No user system, no API keys, no JWT, no session management.

### 6. No Caching in Real Pipeline

**Impact:** MEDIUM

The `core/cache/` module exists but is not integrated into the retrieval pipeline. The mock search has no caching.

---

## Architecture Score

| Dimension | Score | Notes |
|-----------|-------|-------|
| Knowledge Layer | 9/10 | Well-structured, frozen, reproducible |
| Pipeline Design | 7/10 | Clean phases, but batch-only |
| Core Modules | 6/10 | Good implementations, not integrated |
| Evaluation | 7/10 | Comprehensive but uses mock search |
| API Layer | 0/10 | Does not exist |
| Deployment | 0/10 | No Docker, no CI/CD |
| Security | 3/10 | Basic audit only, no auth |
| Documentation | 6/10 | Good README, missing API docs |
| **Overall** | **4.8/10** | **Not production-ready** |
