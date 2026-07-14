# ADR-009: Research Stack & MCP Ecosystem

## Status
**Accepted**

## Date
2026-07-12

## Problem
Build permanent research capability for discovering, evaluating, and integrating open-source technologies.

## Decision

### Architecture
```
research/catalog/     # Technology scores and evaluations
research/benchmarks/  # Reusable benchmark results
research/plugins/     # Plugin prototypes
research/reports/     # Research reports

plugins/mcp/          # MCP servers (GitHub, Filesystem, Browser, Memory)
plugins/research/     # Web search, AgentReach adapters
plugins/search/       # Full-text search
plugins/evaluation/   # RAG evaluation
plugins/agents/       # Agent frameworks
```

### Core Components
1. Technology Scoring (weighted 10-criteria, 0-10 scale)
2. Plugin Architecture (ABC-based, independently replaceable)
3. Technology Catalog (26 projects scored)
4. MCP Servers (4 server plugins)
5. Benchmark Framework (repeatable, versioned)

### 26 Technologies Cataloged
- **OCR:** Tesseract, PaddleOCR, OCRmyPDF, Marker, Docling
- **Parsing:** PyMuPDF, Unstructured
- **MCP:** GitHub, Filesystem, Browser, Memory
- **RAG:** LlamaIndex, DSPy
- **Vector DB:** Chroma, Qdrant, LanceDB
- **Embeddings:** BGE-M3
- **Rerankers:** BGE Reranker
- **Search:** Meilisearch
- **Evaluation:** RAGAS, DeepEval
- **Knowledge Graph:** RDFLib
- **Agents:** LangGraph, PydanticAI, Aider

## Change Policy
- New tech requires catalog scoring
- Score >= 7.0 = integrate | 5.0-7.0 = evaluate | 3.0-5.0 = catalog | < 3.0 = reject
