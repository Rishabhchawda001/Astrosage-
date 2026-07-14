# Pipeline Versioning

## Principle

Every pipeline component has an independent version.
Changing one component must NOT require rebuilding unrelated stages.

## Current Versions

| Component | Version | Description |
|-----------|---------|-------------|
| classifier | 0.1.0 | Document type classification |
| language_detector | 0.1.0 | Language and script detection |
| ocr_router | 0.1.0 | OCR routing decisions |
| text_extractor | 0.1.0 | PyMuPDF text extraction |
| metadata_extractor | 0.1.0 | Document metadata extraction |
| chunker | 0.1.0 | Semantic chunking |
| duplicate_detector | 0.1.0 | SHA256 + SimHash detection |
| provenance_graph | 0.1.0 | Data provenance tracking |
| knowledge_registry | 0.1.0 | Permanent ID system |
| manifest | 0.1.0 | Knowledge manifest generation |

## Version Format

MAJOR.MINOR.PATCH
- **MAJOR:** Breaking changes to output format
- **MINOR:** New features, backward-compatible
- **PATCH:** Bug fixes, no output change
