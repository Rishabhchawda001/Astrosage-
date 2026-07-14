# AstroSage Technology Catalog

**Total Technologies:** 26
**Recommended for Integration:** 21
**Candidate for Evaluation:** 4
**Cataloged (Future):** 1

---

## Agent (3)

| Technology | Score | Recommendation | Stars | License | Notes |
|-----------|-------|---------------|-------|---------|-------|
| PydanticAI | 8.01 | ✅ integrate | 8,000 | MIT | Built on Pydantic. Type-safe, modular. Excellent fit for Ast |
| LangGraph | 7.11 | ✅ integrate | 12,000 | MIT | Most capable agent framework. Heavy dependency but powerful  |
| Aider | 7.08 | ✅ integrate | 28,000 | Apache-2.0 | CLI-based, hard to embed in pipeline. Use as external tool,  |

## Embedding (1)

| Technology | Score | Recommendation | Stars | License | Notes |
|-----------|-------|---------------|-------|---------|-------|
| BGE-M3 | 7.44 | ✅ integrate | 15,000 | MIT | Best open multilingual embedding model. 8192 token context.  |

## Evaluation (2)

| Technology | Score | Recommendation | Stars | License | Notes |
|-----------|-------|---------------|-------|---------|-------|
| RAGAS | 7.31 | ✅ integrate | 8,000 | Apache-2.0 | Best-in-class RAG evaluation. Needs LLM for metric computati |
| DeepEval | 7.08 | ✅ integrate | 4,500 | Apache-2.0 | Mature evaluation framework. Good for CI/CD integration. |

## Knowledge Graph (1)

| Technology | Score | Recommendation | Stars | License | Notes |
|-----------|-------|---------------|-------|---------|-------|
| RDFLib | 7.13 | ✅ integrate | 2,500 | BSD-3 | Lightweight, pure Python. Fits AstroSage's offline-first phi |

## Mcp (4)

| Technology | Score | Recommendation | Stars | License | Notes |
|-----------|-------|---------------|-------|---------|-------|
| Filesystem MCP Server | 8.17 | ✅ integrate | 28,000 | MIT | Official MCP server. Read/write/search files within allowed  |
| Memory MCP Server | 7.17 | ✅ integrate | 28,000 | MIT | Knowledge graph-based persistent memory. Stores tech evaluat |
| GitHub MCP Server | 6.97 | 🔍 evaluate | 28,000 | MIT | Official MCP server from Anthropic. Supports repo search, co |
| Browser MCP Server | 6.93 | 🔍 evaluate | 28,000 | MIT | Playwright-based. For docs browsing, GitHub reading, Hugging |

## Ocr (5)

| Technology | Score | Recommendation | Stars | License | Notes |
|-----------|-------|---------------|-------|---------|-------|
| Tesseract | 8.14 | ✅ integrate | 64,000 | Apache-2.0 | Already installed. Primary OCR for AstroSage. Supports eng/h |
| PaddleOCR | 7.78 | ✅ integrate | 48,000 | Apache-2.0 | Already installed (v3.7.0). Excellent for Hindi/Sanskrit. GP |
| OCRmyPDF | 7.77 | ✅ integrate | 20,000 | MPL-2.0 | Already installed (v17.8.0). Adds PDF processing around Tess |
| Docling | 7.41 | ✅ integrate | 28,000 | MIT | Needs full installation with model weights. docling-core ava |
| Marker | 6.83 | 🔍 evaluate | 24,000 | GPL-3.0 | Installed (v1.10.2). Needs GPU for practical use. Full bench |

## Parsing (2)

| Technology | Score | Recommendation | Stars | License | Notes |
|-----------|-------|---------------|-------|---------|-------|
| PyMuPDF | 8.61 | ✅ integrate | 6,000 | AGPL-3.0 / Commercial | Already installed (v1.28.0). Primary extraction engine for n |
| Unstructured | 6.36 | 🔍 evaluate | 10,000 | Apache-2.0 | Heavy dependency chain. Cloud dependency for some features.  |

## Rag (2)

| Technology | Score | Recommendation | Stars | License | Notes |
|-----------|-------|---------------|-------|---------|-------|
| DSPy | 7.66 | ✅ integrate | 21,000 | MIT | Programmatic prompt optimization. Interesting for optimizing |
| LlamaIndex | 7.29 | ✅ integrate | 40,000 | MIT | Heavy framework. Overkill for AstroSage's modular architectu |

## Reranker (1)

| Technology | Score | Recommendation | Stars | License | Notes |
|-----------|-------|---------------|-------|---------|-------|
| BGE Reranker | 7.24 | ✅ integrate | 15,000 | MIT | Best open-source reranker. Works with BGE-M3 embeddings. Use |

## Research (1)

| Technology | Score | Recommendation | Stars | License | Notes |
|-----------|-------|---------------|-------|---------|-------|
| AgentReach | 3.83 | 📋 catalog | 0 | MIT | Not a standard open-source project. Build adapter for web/gi |

## Search (1)

| Technology | Score | Recommendation | Stars | License | Notes |
|-----------|-------|---------------|-------|---------|-------|
| Meilisearch | 8.58 | ✅ integrate | 50,000 | MIT | Excellent full-text search. Replace BM25 baseline with Meili |

## Vector Db (3)

| Technology | Score | Recommendation | Stars | License | Notes |
|-----------|-------|---------------|-------|---------|-------|
| Qdrant | 8.51 | ✅ integrate | 24,000 | Apache-2.0 | Best performance among open-source vector DBs. Rust core wit |
| Chroma | 7.19 | ✅ integrate | 18,000 | Apache-2.0 | Simplest integration. Python-native. Good for validation and |
| LanceDB | 7.16 | ✅ integrate | 5,500 | Apache-2.0 | Lance columnar format. Interesting for multi-modal data with |

---

## Scoring Criteria

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Engineering Quality | 15% | Code quality, architecture, maintainability |
| Performance | 15% | Speed, resource efficiency |
| Documentation | 10% | Docs quality, examples, tutorials |
| Testing | 10% | Test coverage, CI/CD |
| Security | 10% | Vulnerability handling, security practices |
| Community | 8% | Contributors, activity, responsiveness |
| Offline Capability | 12% | Works without internet |
| Maintainability | 8% | Long-term maintenance burden |
| Integration Effort | 7% | Ease of integration into AstroSage |
| Future Outlook | 5% | Development trajectory |

---
*Generated by AstroSage Technology Scoring Framework v1.0*