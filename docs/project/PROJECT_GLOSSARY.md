# AstroSage Knowledge Engine — Glossary

**Last Updated:** 2026-07-12

---

## Core Architecture Terms

### Knowledge Lake
The four-layer data architecture that organizes all knowledge artifacts:
- **raw/** — Immutable source archive (original files, never modified)
- **bronze/** — First transformation: extracted text from documents
- **silver/** — Structured knowledge: clean markdown with preserved hierarchy
- **gold/** — Final indexed knowledge: chunks, embeddings, indexes (future)

### Raw Layer
The top-level tier of the Knowledge Lake. Contains exact mirrors of Google Drive source files with original names and directory structure. Nothing in later layers reads directly from raw except through the pipeline.

### Bronze Layer
Second tier of the Knowledge Lake. Contains extracted text from PDFs (via PyMuPDF or OCR). Also holds OCR output, language detection results, and page images. Bronze preserves raw content structure — no semantic processing.

### Silver Layer
Third tier of the Knowledge Lake. Contains clean, structured Markdown with preserved heading hierarchy, and document metadata. Silver content is what downstream pipelines consume.

### Gold Layer
Fourth tier (future). Contains semantically chunked text, vector embeddings, vector indexes, and pre-computed retrieval artifacts.

### Manifest
The canonical registry of every document in the knowledge base. Exported as `manifest.csv` and `manifest.parquet`. Each record includes UUID, SHA256, filename, path, metadata, processing status, and pipeline version.

### Provenance
The complete traceability chain from source document to final answer:
```
Source Document → Page → Section → Chunk → Embedding → Retrieved Context → Answer
```
Every artifact must be traceable to its originating source. No orphaned artifacts.

### Provenance Graph
A directed acyclic graph (DAG) tracking input → transformation → output for every pipeline run. Currently 658 nodes and 329 edges.

### Knowledge Registry
The permanent ID assignment system:
```
BOOK-{sha256[:8]} → PAGE-{sha256[:8]} → SECTION-{sha256[:8]} → CHUNK-{sha256[:8]} → EMBED-{sha256[:8]}
```
620 unique books registered from 751 files (after SHA256 deduplication).

### Pipeline
The document processing pipeline. Currently frozen as **Document Intelligence v1.0** with 8 stages:
1. Document Registry (SHA256, UUID)
2. Multi-Signal Page Classifier
3. Language Detection
4. Page-Level Routing
5. Text Extraction (PyMuPDF / Tesseract)
6. Quality Validation
7. Metadata Extraction
8. Knowledge Lake Ingestion

### Pipeline Versioning
Each pipeline component has an independent version (MAJOR.MINOR.PATCH). Changing one component does not require rebuilding unrelated stages.

### Plugin Architecture
ABC-based, independently replaceable components. Plugin directory: `plugins/`. Categories: mcp, research, search, evaluation, agents, ocr, parser, embedding, reranker, knowledge_graph.

---

## Document Classification Terms

### Native PDF
A PDF where the majority of pages contain extractable text. Typically born-digital documents. Can be extracted directly with PyMuPDF without OCR.

### Scanned PDF
A PDF where pages are images (scans of physical documents). Requires OCR for text extraction. Currently 51.4% of all pages.

### OCR Overlay
A scanned PDF where an OCR text layer has been added (invisible text over images). Can be extracted directly but may need verification.

### Hybrid PDF
A PDF containing a mix of native text pages and scanned image pages. Requires page-level routing.

### Multi-Signal Page Classifier
A page classification system using 11+ independent signals to determine page type:
1. Text layer existence
2. Text character density
3. Font count and types
4. Image count and coverage
5. Raster DPI estimation
6. Vector object count
7. Text/image bounding box overlap
8. OCR overlay detection
9. Whitespace ratio
10. Content stream analysis
11. Rendering complexity

---

## Processing Terms

### Tier (Language Processing Tier)
Config-driven classification determining processing depth:
- **Tier 1:** Full processing (OCR, parsing, metadata, knowledge lake) — English, Hindi, Sanskrit
- **Tier 2:** Register + basic metadata only — Telugu, Kannada, Tamil, Malayalam, Gujarati, Bengali, Punjabi, Odia, Marathi
- **Tier 3:** Register only — MP3, MP4, images, ZIP

### OCR
Optical Character Recognition. Converting scanned document images to text. Currently using Tesseract 5.3.4 (eng/hin/san) with PaddleOCR 3.7.0 as fallback.

### Page-Level Routing
Each page is independently classified and routed to the appropriate extractor. No book is processed as a single unit.

### Quality Validation
Post-extraction validation checking OCR confidence, Unicode integrity, completeness, and content quality. Low-quality outputs are quarantined.

### Quarantine
Directory (`knowledge/quarantine/`) for documents that failed processing. Files are preserved with exact failure reason. Never automatically deleted.

---

## Technology Terms

### BGE-M3
Multilingual embedding model (570M params) supporting 100+ languages including Hindi and Sanskrit. Selected for production embeddings (ADR-002). Produces dense + sparse + ColBERT embeddings.

### Qdrant
Rust-based vector database selected for production. Features: metadata filtering, snapshots, Docker deployment. Selected in ADR-003.

### Chroma
Embedded vector database selected for development/testing. Zero-dependency operation. Selected in ADR-003.

### BM25
Best Matching 25 — a sparse retrieval algorithm based on term frequency. Part of hybrid search strategy (ADR-004).

### Cross-Encoder Reranker
A model that scores query-document relevance pairs. Used to rerank top-20 results to top-5. Currently using `cross-encoder/ms-marco-MiniLM-L-6-v2` (ADR-004).

### MCP (Model Context Protocol)
Standard protocol for AI tool servers. AstroSage exposes tools (search_books, list_books, etc.) through MCP for Claude integration.

### RAGAS
Retrieval-Augmented Generation Assessment — framework for evaluating RAG quality: faithfulness, answer relevance, context precision/recall (ADR-005).

### DeepEval
LLM evaluation framework for hallucination detection, bias detection (ADR-005).

---

## Evaluation Terms

### Golden Evaluation Dataset
1,000 representative questions with expected answers, supporting documents, and difficulty ratings. Used for reproducible retrieval quality evaluation.

### Search Baseline
Performance metrics for non-semantic search methods (filename search, metadata search, BM25 keyword search). Used as baseline for comparing future hybrid retrieval.

### Precision@k
The fraction of top-k retrieved results that are relevant. Higher is better.

### Recall@k
The fraction of all relevant results that appear in top-k. Higher is better.

### MRR (Mean Reciprocal Rank)
Average of 1/rank for the first relevant result. Higher is better.

---


---

## Recovery & Verification Terms

### Knowledge Source Registry
Catalog of all external knowledge sources AstroSage may use for recovery. Each source has UUID, trust level, rate limits, supported recovery modes, and health status. Default sources: Internet Archive, Open Library, Crossref, OpenAlex, Wikidata.

### Trust Engine
Configurable scoring system for evaluating trust across six dimensions: source trust, edition trust, metadata trust, OCR trust, recovery trust, and verification trust. All weights loaded from configuration — no hardcoded thresholds.

### Knowledge Passport
Complete provenance and verification record for a recovered knowledge object. Contains original OCR, recovered candidate, evidence sources, agreement metrics, verification history, edition links, and checksums.

### Recovery Queue
Priority queue for recovery jobs. Supports critical/high/medium/low priorities, retry with exponential backoff, checkpointing, and failure categorization (recoverable, retryable, fatal).

### Human Review Queue
Queue for items requiring human judgment. Supports states: pending, approved, rejected, deferred, needs_more_evidence. Every review includes reviewer, timestamp, and notes.

### Edition Registry
Tracks different editions of the same work: original, translation, publisher edition, critical edition, commentary, roman transliteration, regional edition, digital reprint. Every edition receives UUID. Nothing merged. Everything linked.

### Verification Interface
ABC-based contract for verification implementations. Input: OCR text, candidate recovery, evidence. Output: verified/rejected/conflict/manual_review, confidence, reason. DefaultVerification uses character-level Jaccard similarity.

### Conflict Engine
Manages disagreements between editions and sources. Stores all variants (never discards). Supports four severity levels: minor, moderate, major, critical. Resolved by selecting preferred variant with evidence.

### Confidence Engine
Aggregates confidence scores from all pipeline stages: OCR, parser, metadata, recovery, edition agreement, verification. All weights configurable. Supports adding components dynamically.

### Source Connectors
ABC-based plugin interfaces for external source integration. Four default connectors: InternetArchiveConnector, OpenLibraryConnector, CrossrefConnector, OpenAlexConnector. All stub implementations (interfaces only).

### Knowledge Provenance Ledger
Append-only ledger tracking every transformation: character → OCR → recovery → verification → edition alignment → knowledge object → chunk → embedding → retrieval → answer. Every step logged. Nothing may disappear.

### Recovery Mode
Types of recovery supported by a source: metadata_only, text_recovery, ocr_recovery, edition_comparison, full_recovery.

### Edition Relationship
Links between editions: translation_of, edition_of, commentary_on, transliteration_of, reprint_of, derived_from, related_to.

## Repository Terms

### ADR (Architecture Decision Record)
Formal document recording an architectural decision: problem, alternatives, decision, rationale, tradeoffs. Stored in `adrs/` directory.

### Checkpoint
JSON file (`knowledge/checkpoints/corpus_checkpoint.json`) recording which documents have been processed. Enables resume after pipeline interruption.

### Phase
A gated work unit with defined objectives, tasks, deliverables, and acceptance criteria. Phases execute sequentially.

### Phase M1
The current phase: Permanent Agent Memory. Creating the engineering memory documents that future agents read before beginning work.

---

*This document is part of the AstroSage Knowledge Engine project and lives at `docs/project/PROJECT_GLOSSARY.md`.*
