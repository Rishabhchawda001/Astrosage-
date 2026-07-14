# Knowledge Lake Architecture

## Why Each Layer Exists

### `raw/` — Immutable Source Archive
**Purpose:** Exact mirror of the Google Drive source library. Never modified.
**Contains:** Original files with original names, original folder structure.
**Rule:** Nothing in later layers reads directly from raw except through the pipeline.

### `bronze/` — Extracted Content
**Purpose:** First transformation of raw documents into machine-readable text.
**Contains:**
- `extracted_text/` — PDF text extracted via PyMuPDF (native PDFs only)
- `ocr_output/` — Text from OCR processing (scanned PDFs, images)
- `language_detection/` — Language detection results per document
- `page_images/` — Individual page images (for OCR pipeline)

**Rule:** Bronze preserves the raw content structure. No semantic processing.

### `silver/` — Structured Knowledge
**Purpose:** Clean, structured, version-controlled content ready for indexing.
**Contains:**
- `markdown/` — Clean markdown generated from extracted text
- `structured_documents/` — Documents with preserved heading hierarchy
- `metadata/` — Complete metadata per document (JSON)
- `document_graph/` — Document relationship graph

**Rule:** Silver content is what downstream pipelines consume.

### `gold/` — Indexed Knowledge
**Purpose:** Ready-for-query knowledge artifacts.
**Contains:**
- `chunks/` — Semantically chunked text
- `embeddings/` — Vector embeddings
- `indexes/` — Vector database index
- `retrieval/` — Pre-computed retrieval artifacts

**Rule:** Gold is the final output of the processing pipeline.

## Data Flow

```
raw/source_library/  →  bronze/extracted_text/  →  silver/markdown/  →  gold/chunks/
     ↓                        ↓                          ↓                    ↓
  Original PDFs         PyMuPDF text              Clean markdown      Semantic chunks
  751 files             329 text files            329 markdown         With provenance
```

## Layer Sizes (Current)

| Layer | Files | Description |
|-------|-------|-------------|
| raw | 751 | Original source files (15.3 GB) |
| bronze | 329 | Extracted text from native PDFs |
| silver | 329 | Markdown with structure |
| gold | 0 | Not yet built (Phase 3) |
