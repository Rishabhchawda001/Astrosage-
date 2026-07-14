# AstroSage Knowledge Engine — Architecture

## Version
**Document Intelligence v1.0** (Locked via ADR-008)

## Frozen Components

| Component | Version | ADR |
|-----------|---------|-----|
| Document Classifier | v1.0 | ADR-007, ADR-008 |
| OCR Engine | Tesseract 5.3.4 + PaddleOCR 3.7.0 | ADR-006 |
| Parser | PyMuPDF 1.28.0 | ADR-008 |
| Routing Strategy | Page-level multi-signal | ADR-007, ADR-008 |
| Metadata Pipeline | PyMuPDF + heuristic extraction | ADR-008 |
| Provenance Model | UUID chain (DOC→PAGE→CHUNK) | ADR-002 |
| Knowledge Lake | Bronze/Silver/Gold layers | ADR-001 |
| Plugin Architecture | ABC-based, independently replaceable | ADR-009 |
| Research Stack | Technology Scoring + Catalog | ADR-009 |

## Pipeline Architecture

```
Raw PDF (knowledge/raw/source_library/)
  ↓ Stage 1: Document Registry (SHA256, UUID assignment)
  ↓ Stage 2: Document Classification (multi-signal page classifier)
  ↓ Stage 3: Language Detection (per-page, Hindi/English/Sanskrit/Mixed)
  ↓ Stage 4: Page Routing
  │   ├── Native Text → PyMuPDF text extraction
  │   ├── Scanned → Tesseract OCR (eng/hin/san)
  │   ├── OCR Overlay → Verify existing + fallback OCR
  │   ├── Hybrid → Per-page routing
  │   └── Blank → Skip
  ↓ Stage 5: Quality Validation (confidence, Unicode, completeness)
  ↓ Stage 6: Metadata Extraction (title, author, language, script, etc.)
  ↓ Stage 7: Knowledge Lake Ingestion
  │   ├── Bronze: extracted_text/ (raw text per document)
  │   └── Silver: structured_documents/ (Markdown per document)
  ↓ Stage 8: Provenance Validation (traceability check)
```

## Knowledge Lake Layout

```
knowledge/
  raw/source_library/     # Original documents (symlink to archive)
  bronze/extracted_text/  # Raw extracted text per document
  silver/structured_documents/  # Structured Markdown per document
  reports/                # Processing reports, manifests, metrics
  benchmarks/             # Benchmark results and forensic data
  quarantine/             # Rejected low-quality outputs
  logs/                   # Processing logs
```

## Technology Stack

| Technology | Version | Purpose |
|-----------|---------|---------|
| Python | 3.12.3 | Runtime |
| PyMuPDF | 1.28.0 | PDF text extraction |
| Tesseract | 5.3.4 | OCR (eng/hin/san) |
| PaddleOCR | 3.7.0 | Multilingual OCR fallback |
| Pydantic | 2.13.4 | Data validation |
| pandas | 3.0.3 | Data manipulation |
| pyarrow | 25.0.0 | Parquet support |
| pytest | 9.1.1 | Testing |
| rich | 15.0.0 | CLI formatting |

## Page Classification Signals

1. Text layer exists
2. Text character density
3. Font count and types
4. Image count and coverage percentage
5. Raster DPI estimation
6. Vector object count
7. Text/image bounding box overlap
8. OCR overlay detection
9. Whitespace ratio
10. Content stream analysis
11. Rendering complexity

## Change Policy

Architecture changes require:
1. Benchmark on representative corpus
2. Updated ADR
3. Regression testing
4. Explicit approval

No silent changes.

## ADR References

- ADR-001: Document Extraction
- ADR-002: Embedding Model
- ADR-003: Vector Database
- ADR-004: Retrieval Strategy
- ADR-005: Grounding Policy
- ADR-006: Document Pipeline
- ADR-007: Forensic Validation
- ADR-008: Production Pipeline Lock
- ADR-009: Research Stack & MCP Ecosystem

## Language-Based Processing Tiers

### Configuration
Defined in `config/processing_tiers.json`. No source code changes needed to promote/demote languages.

### Tier 1 — Full Processing
**Languages:** English, Hindi, Sanskrit
**Processing:** OCR (when required), parsing, metadata extraction, Knowledge Lake (bronze/silver)
**Future:** Chunking, embeddings, retrieval

### Tier 2 — Deferred Processing
**Languages:** Telugu, Kannada, Tamil, Malayalam, Gujarati, Bengali, Punjabi, Odia, Marathi
**Processing:** Register in Knowledge Registry, preserve provenance, extract basic metadata
**Deferred:** OCR, parsing, chunking, embeddings
**Promotion:** Add language to tier1.languages in config/processing_tiers.json

### Tier 3 — Media (Deferred)
**Extensions:** MP3, MP4, images, ZIP
**Processing:** Register and preserve metadata
**Future:** Dedicated media pipelines

### Routing Order
```
Document → Classification → Language Detection → Tier Assignment → Appropriate Pipeline
```

### Promotion Policy
To promote a language from Tier 2 to Tier 1:
1. Edit `config/processing_tiers.json`
2. Add language to `tier1.languages` array
3. Remove from `tier2.languages` array
4. Increment version
5. Re-run incremental processing for affected documents

### Policy: Preserve All Documents
No document is ever deleted. Every document is registered in the Knowledge Registry
regardless of tier. Processing depth changes, not preservation.

---

## Knowledge Recovery Infrastructure (Phase 4.5)

**Status:** Infrastructure built. No frozen components changed.

### New Subsystems
- `src/astrosage/recovery/` — Recovery infrastructure modules
- `plugins/recovery/` — Recovery plugin interfaces
- `plugins/verification/` — Verification plugin interfaces
- `plugins/source_connectors/` — Source connector plugin interfaces
- `knowledge/recovery/` — Recovery data directory

### Components
- Knowledge Source Registry
- Trust Engine
- Knowledge Passport
- Recovery Queue
- Review Queue
- Edition Registry
- Verification Interface
- Conflict Engine
- Confidence Engine
- Source Connectors
- Knowledge Provenance Ledger

### ADR
- ADR-010: Knowledge Recovery Infrastructure
