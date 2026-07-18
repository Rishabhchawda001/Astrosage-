# AI Knowledge Contract — AstroSage v1.0.0

**Effective**: 2026-07-18T20:00:50.146197+00:00
**Frozen Release**: `knowledge/releases/v1.0.0/`

## Purpose

This contract defines the rules every AI pipeline must follow when consuming
the AstroSage frozen knowledge layer.

## Rules

### 1. Load Only Frozen Releases

Every AI pipeline MUST load knowledge exclusively from `knowledge/releases/v1.0.0/`.
Never load from `knowledge/graph/` (working directory) for production inference.

### 2. No Modification

No AI agent may modify, overwrite, or delete any file in `knowledge/releases/`.
All knowledge changes must go through `knowledge/migrations/`.

### 3. Provenance Required

Every answer produced by AstroSage MUST reference:
- Source scripture
- Canonical unit (verse/sutra number)
- Graph node GUID(s)
- Relationship GUID(s)
- Confidence level
- Evidence description

### 4. Reproducibility Required

Every answer must be reproducible. Given the same input and frozen release,
two independent runs must produce equivalent outputs.

### 5. No Hallucination

If the frozen knowledge layer does not contain information to answer a question,
the AI MUST say so. Never generate knowledge not present in the frozen release.

### 6. Pipeline Consumption Order

```
Frozen Release (v1.0.0)
  ↓ Semantic Chunking (Phase 11)
  ↓ Embeddings (Phase 12)
  ↓ Hybrid Retrieval (Phase 13)
  ↓ Knowledge Graph Traversal
  ↓ Reasoning Engine
  ↓ Citation Engine
  ↓ Grounded Answer Generation
```

Every stage reads from frozen data. No stage writes to frozen data.

### 7. Version Pinning

Pipelines must pin to a specific release version.
`v1.0.0` is the current and only release.

### 8. Schema Compliance

All graph traversals must comply with `graph_schema.json` v1.0.
Node types and edge types are defined and frozen.

### 9. Entity Resolution

When the same real-world entity appears in multiple scriptures,
use the canonical entity node from the frozen graph.
Do not create duplicate entities.

### 10. Evidence Hierarchy

When sources conflict:
1. Use the entity with higher mention count
2. Use the relationship with higher confidence
3. Use the cross-scripture alignment with "Confirmed" status
4. If unresolved, present both views with provenance

## Frozen Artifacts Available

| Artifact | Path | Description |
|----------|------|-------------|
| Full Graph | `graph/graph.json` | Complete knowledge graph |
| Entity Registry | `graph/nodes/entity_nodes.json` | All 391 entities |
| Scripture Registry | `graph/nodes/scripture_nodes.json` | All 54 scriptures |
| Relationship Registry | `graph/edges/relationship_edges.json` | All 5044 edges |
| Schema | `graph/schemas/graph_schema.json` | Node/edge type definitions |
| Entity Index | `graph/indexes/entity_index.json` | Entity lookup index |
| Dialogue Graph | `graph/dialogue_graph.json` | 170 dialogues |
| Event Graph | `graph/event_graph.json` | 29 events |
| Genealogy Graph | `graph/genealogy_graph.json` | Family trees |
| Concept Graph | `graph/concept_graph.json` | Philosophical concepts |
| Ritual Graph | `graph/ritual_graph.json` | Ritual practices |
| Cross-Scripture | `graph/cross_scripture_alignment.json` | 76 cross-references |

## Violations

Any AI pipeline that:
- Reads from non-frozen paths
- Modifies frozen artifacts
- Produces answers without provenance
- Generates knowledge not in the frozen layer

is in violation of this contract and must be corrected before deployment.
