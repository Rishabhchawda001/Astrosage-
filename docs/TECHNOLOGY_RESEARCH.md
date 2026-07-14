# AstroSage Knowledge Engine — Technology Research Report

## 1. OCR Engines

### 1.1 Tesseract OCR
- **Repository**: https://github.com/tesseract-ocr/tesseract
- **Stars**: ~65k
- **License**: Apache 2.0
- **Languages**: 100+ (Hindi, Sanskrit, English supported)
- **Last Release**: 5.5.0 (2024)
- **Pros**: Mature, widely used, good Hindi/Sanskrit support, free, runs locally
- **Cons**: Struggles with complex layouts, no GPU acceleration, poor table/figure extraction
- **Verdict**: **Baseline OCR engine** — good for initial text extraction but insufficient for complex documents

### 1.2 OCRmyPDF
- **Repository**: https://github.com/ocrmypdf/OCRmyPDF
- **Stars**: ~14k
- **License**: MIT
- **Last Release**: 16.6.0 (2024)
- **Pros**: Wraps Tesseract with PDF-aware workflow, produces searchable PDFs, preserves original layout, handles multi-page
- **Cons**: Depends on Tesseract quality, no native deep learning models
- **Verdict**: **Best PDF-specific OCR wrapper** — use for scanned PDFs after language detection

### 1.3 PaddleOCR
- **Repository**: https://github.com/PaddlePaddle/PaddleOCR
- **Stars**: ~44k
- **License**: Apache 2.0
- **Languages**: 80+
- **Last Release**: 3.0.0 (2024)
- **Pros**: Deep learning-based, excellent layout analysis, good multilingual support, table extraction
- **Cons**: Heavy dependencies (PaddlePaddle framework), larger model sizes
- **Verdict**: **Best accuracy for complex layouts** — recommend for Hindi/Sanskrit documents with tables and mixed content

### 1.4 Marker
- **Repository**: https://github.com/VikParuchuri/marker
- **Stars**: ~19k
- **License**: GPL-3.0
- **Pros**: Converts PDF to Markdown with LLM-based enhancement, handles tables/figures well, semantic structure preservation
- **Cons**: Requires LLM calls (adds latency/cost), GPL license restricts commercial use
- **Verdict**: **Best for converting to clean Markdown** — use as primary parser for native PDFs and simple layouts

### 1.5 Docling
- **Repository**: https://github.com/DS4SD/docling
- **Stars**: ~19k
- **License**: MIT
- **Pros**: IBM-backed, excellent document understanding, multi-format support, table extraction, clean API
- **Cons**: Newer project, less battle-tested
- **Verdict**: **Strong alternative to Marker** — MIT license makes it more suitable for production

### 1.6 olmOCR
- **Repository**: https://github.com/allenai/olmOCR
- **Stars**: ~5k
- **License**: Apache 2.0
- **Pros**: AI2's vision-language model approach, handles degraded/scanned docs well
- **Cons**: Requires GPU, newer, limited language support for Devanagari
- **Verdict**: **Worth benchmarking for scanned documents** — may not beat PaddleOCR for Hindi/Sanskrit

### 1.7 PyMuPDF (fitz)
- **Repository**: https://github.com/pymupdf/PyMuPDF
- **Stars**: ~5k
- **License**: AGPL-3.0
- **Pros**: Fast PDF text extraction, image extraction, metadata access, no OCR needed for native PDFs
- **Cons**: AGPL license, no OCR capability (text extraction only)
- **Verdict**: **Essential for native PDF text extraction** — use first before any OCR

### 1.8 Unstructured
- **Repository**: https://github.com/Unstructured-IO/unstructured
- **Stars**: ~9k
- **License**: Apache 2.0
- **Pros**: Multi-format support, chunking built-in, cloud/local modes
- **Cons**: Heavy, many dependencies, some features require cloud API
- **Verdict**: **Not recommended** — too heavy for our specific use case; better to use focused tools

### OCR Pipeline Recommendation
1. **Native PDFs**: Extract text directly with PyMuPDF (no OCR)
2. **Scanned PDFs**: Use PaddleOCR with language-specific models
3. **Fallback**: OCRmyPDF + Tesseract for simple documents
4. **Complex layouts**: Marker/Docling for semantic structure

---

## 2. Embedding Models

### 2.1 BGE-M3
- **Repository**: https://github.com/BAAI/BGEM3
- **Stars**: ~5k
- **License**: MIT
- **Pros**: Multi-granularity (dense + sparse + ColBERT), multilingual (100+ languages including Hindi/Sanskrit), 8192 token context
- **Cons**: Requires 2GB VRAM, ~570M parameters
- **Verdict**: **Best multilingual embedding model** — top recommendation for Sanskrit/Hindi/English

### 2.2 nomic-embed-text
- **Repository**: https://github.com/nomic-ai/nomic-embed-text-v1.5
- **Stars**: ~3k
- **License**: Apache 2.0
- **Pros**: 137M params, efficient, supports Ollama, good English performance
- **Cons**: Primarily English-focused, limited Devanagari support
- **Verdict**: **Good for English-only queries** — not sufficient for multilingual needs

### 2.3 E5 (Microsoft)
- **Repository**: https://github.com/microsoft/unilm/tree/master/e5
- **Stars**: ~8k
- **License**: MIT
- **Pros**: Strong retrieval performance, instruction-aware
- **Cons**: Primarily English, smaller language coverage
- **Verdict**: **Strong English option** — not primary choice for multilingual

### 2.4 Jina Embeddings
- **Repository**: https://github.com/jina-ai/jina-embeddings-v3
- **Stars**: ~3k
- **License**: Apache 2.0
- **Pros**: Multilingual, late interaction model, good multilingual performance
- **Cons**: API-based for full features, open model smaller
- **Verdict**: **Strong alternative to BGE-M3** — worth benchmarking

### 2.5 Stella
- **Repository**: https://github.com/Mennyt/STELLA
- **Stars**: ~1k
- **License**: Various (model-dependent)
- **Pros**: High retrieval performance on MTEB
- **Cons**: Primarily English, less multilingual coverage
- **Verdict**: **Not recommended** for our multilingual use case

### Embedding Recommendation
**Primary: BGE-M3** — multilingual, supports Hindi/Sanskrit, dense+sparse+ColBERT modes enable hybrid search natively. No paid APIs required.

---

## 3. Vector Databases

### 3.1 Chroma
- **Repository**: https://github.com/chroma-core/chroma
- **Stars**: ~17k
- **License**: Apache 2.0
- **Pros**: Simple API, embedded mode, metadata filtering, Python-native
- **Cons**: Single-node only, limited scale, less mature for production
- **Verdict**: **Best for single-machine deployment** — ideal for our self-hosted requirement

### 3.2 Qdrant
- **Repository**: https://github.com/qdrant/qdrant
- **Stars**: ~23k
- **License**: Apache 2.0
- **Pros**: High performance, Rust-based, advanced filtering, payload support, snapshots
- **Cons**: Requires separate server process, slightly more complex setup
- **Verdict**: **Best production vector DB** — excellent filtering, good for metadata-aware queries

### 3.3 LanceDB
- **Repository**: https://github.com/lancedb/lancedb
- **Stars**: ~11k
- **License**: Apache 2.0
- **Pros**: Embedded mode, columnar storage, multi-modal, versioning, zero-copy
- **Cons**: Newer, smaller ecosystem
- **Verdict**: **Interesting for future** — embedded mode is compelling but less proven

### 3.4 Milvus
- **Repository**: https://github.com/milvus-io/milvus
- **Stars**: ~33k
- **License**: Apache 2.0
- **Pros**: High scale, GPU acceleration, distributed mode
- **Cons**: Heavy dependencies (etcd, MinIO), overkill for single-node
- **Verdict**: **Overkill for our use case**

### 3.5 Weaviate
- **Repository**: https://github.com/weaviate/weaviate
- **Stars**: ~13k
- **License**: BSD-3
- **Pros**: GraphQL API, vectorization modules, hybrid search built-in
- **Cons**: Go-based, heavier deployment, some features require cloud
- **Verdict**: **Not recommended** — Chroma or Qdrant are better fits

### Vector DB Recommendation
**Primary: Qdrant** — production-grade, excellent metadata filtering, Rust performance, simple Docker deployment.  
**Fallback: Chroma** — simpler for development, embedded mode for zero-dependency operation.

---

## 4. Retrieval Approaches

### 4.1 BM25 (Sparse Retrieval)
- **Implementation**: rank_bm25, Elasticsearch
- **Pros**: Fast, interpretable, no model needed, good for keyword matching
- **Cons**: No semantic understanding, limited for synonyms
- **Verdict**: **Essential component** of hybrid search

### 4.2 Vector Retrieval (Dense)
- **Implementation**: Via embedding model + vector DB
- **Pros**: Semantic understanding, handles paraphrases
- **Cons**: May miss exact terms, requires embedding model
- **Verdict**: **Core component**

### 4.3 Hybrid Search (BM25 + Vector)
- **Implementation**: Combining sparse and dense scores
- **Pros**: Best of both worlds — exact matching + semantic understanding
- **Cons**: Score fusion requires tuning
- **Verdict**: **Strongest approach** for our diverse knowledge base

### 4.4 Cross-Encoder Reranking
- **Models**: cross-encoder/ms-marco-MiniLM-L-6-v2, BGE-reranker-v2-m3
- **Pros**: Significantly improves precision, understands query-document relevance deeply
- **Cons**: Slower (requires inference per pair), adds latency
- **Verdict**: **Strong recommendation** — rerank top-20 results for final top-5

### 4.5 Knowledge Graphs (GraphRAG)
- **Implementation**: Neo4j, NetworkX
- **Pros**: Captures relationships between concepts, enables graph traversal queries
- **Cons**: Complex to build, requires entity extraction
- **Verdict**: **Phase 2+ feature** — too complex for initial implementation

### Retrieval Recommendation
**Hybrid search (BM25 + vector) with cross-encoder reranking** — this is the strongest evidence-based approach.

---

## 5. MCP Server

### Architecture
- **Protocol**: Model Context Protocol (MCP) via stdio transport
- **Implementation**: Python with `mcp` library
- **Exposure**: Local process, connects to Claude Desktop / Claude Code
- **Design**: Stateless tool handlers over shared database connections

### Tools to Expose
1. `search_books` — search across entire knowledge base
2. `search_pages` — page-level retrieval with OCR text
3. `list_books` — enumerate indexed documents
4. `compare_sources` — compare information across documents
5. `verify_answer` — check if answer is grounded in sources
6. `sync_library` — trigger re-sync from source
7. `reindex` — re-index a specific document or all
8. `pipeline_status` — check ingestion pipeline status
9. `audit_status` — system health and integrity
10. `ocr_statistics` — OCR processing metrics
11. `index_statistics` — index size and coverage
12. `knowledge_graph` — query concept relationships

---

## 6. Evaluation

### RAGAS
- **Repository**: https://github.com/explodinggradients/ragas
- **Stars**: ~9k
- **License**: Apache 2.0
- **Pros**: RAG-specific metrics (faithfulness, answer relevance, context precision/recall)
- **Cons**: Requires reference data for full evaluation
- **Verdict**: **Best RAG evaluation framework** — use for benchmarking retrieval quality

### DeepEval
- **Repository**: https://github.com/confident-ai/deepeval
- **Stars**: ~4k
- **License**: Apache 2.0
- **Pros**: LLM evaluation metrics, hallucination detection, bias detection
- **Cons**: Newer
- **Verdict**: **Good complement to RAGAS**

### TruLens
- **Repository**: https://github.com/truera/trulens
- **Stars**: ~3k
- **License**: Apache 2.0
- **Pros**: Feedback functions, ground-truth evaluation, dashboard
- **Cons**: Heavier integration
- **Verdict**: **Not primary** — RAGAS is simpler and more focused

### Evaluation Recommendation
**RAGAS** for RAG quality metrics, **DeepEval** for hallucination detection.

---

## 7. Additional Research

### Ollama (Local LLM)
- **Purpose**: Local LLM for document summarization, entity extraction, query expansion
- **Pros**: Runs locally, good model library, simple API
- **Cons**: Requires 8GB+ RAM for useful models
- **Verdict**: **Recommended for Phase 2** — document understanding, not core requirement

---

## Summary: Recommended Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Native PDF extraction | PyMuPDF | Fast, no OCR needed |
| OCR (scanned) | PaddleOCR | Best accuracy, multilingual |
| OCR (fallback) | OCRmyPDF + Tesseract | PDF-aware, mature |
| Document parsing | Docling (primary), Marker (fallback) | MIT license, excellent structure |
| Embeddings | BGE-M3 | Multilingual (Hindi/Sanskrit/English) |
| Vector DB | Qdrant | Production-grade, metadata filtering |
| Search | Hybrid (BM25 + Vector + Reranker) | Strongest retrieval |
| Evaluation | RAGAS + DeepEval | RAG-specific metrics |
| MCP | Python + mcp library | Claude integration |
| Local LLM | Ollama (Phase 2) | Entity extraction, summarization |
