# Provenance Model

## Traceability Chain

```
Source Document (BOOK-xxx)
  → Extracted Text (bronze/)
    → Structured Markdown (silver/)
      → Semantic Chunks (gold/)
        → Vector Embeddings (gold/)
          → Retrieved Context
            → Generated Answer
```

## Every Object Must Be Traceable

The provenance graph records:
- **Input** → **Transformation** → **Output**
- Pipeline name and version
- Timestamp and duration
- Success/failure status
- Error messages

## Current State

- **658 provenance nodes** (329 source + 329 extraction)
- **329 provenance edges**
- Full graph saved to `knowledge/reports/provenance_graph.json`
