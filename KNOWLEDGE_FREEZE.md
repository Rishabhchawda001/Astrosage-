# Knowledge Freeze Policy — AstroSage v1.0.0

**Effective**: 2026-07-18T20:00:50.146197+00:00
**Commit**: 646d3eb80bf9aa9a7602836f16de1dacdca01e96

## Purpose

The Knowledge Freeze establishes an immutable, reproducible snapshot of every
verified knowledge artifact in the AstroSage repository. All downstream AI
pipelines — chunking, embeddings, retrieval, reasoning — must consume ONLY
frozen releases.

## Freeze Philosophy

Knowledge construction is iterative and exploratory.
Knowledge consumption must be deterministic and reproducible.
The freeze boundary separates these two modes of operation.

## What Is Immutable

Once frozen in a release, the following may NOT be modified:

- `knowledge/releases/v1.0.0/` — entire directory
- `knowledge_manifest.json` — the manifest for this version
- Any SHA256 hash published in a freeze manifest

## What Can Evolve

- **New releases**: `knowledge/releases/v1.1.0/`, `v2.0.0/`, etc.
- **Migrations**: `knowledge/migrations/` — additive changes only
- **Scripts**: `scripts/` — may be updated to produce new releases
- **AI Operating Layer**: `.agent/`, `.ai/`, `.astrosage/` — metadata updates

## Migration Rules

1. Every new knowledge artifact must be added through a numbered migration.
2. Migrations are append-only. They may add new entities, edges, scriptures, or sub-graphs.
3. Migrations may NOT modify or delete existing frozen artifacts.
4. Migrations must produce a new release version.
5. Every migration must include:
   - Migration ID (monotonically increasing)
   - Description of changes
   - Added/modified artifact lists
   - Validation report
   - Backward compatibility confirmation
   - Updated statistics

## Versioning Rules

Follows semantic versioning:

- **Major** (v2.0.0): Breaking schema changes, entity ID changes, edge type changes
- **Minor** (v1.1.0): New scriptures, new entities, new edges, new sub-graphs
- **Patch** (v1.0.1): Documentation corrections, metadata updates, bug fixes

## Deprecation Policy

- Deprecated artifacts are marked with `deprecated: true` in metadata.
- Deprecated artifacts remain in frozen releases for backward compatibility.
- Deprecation is announced one release before removal.

## Compatibility Policy

- v1.x releases are backward compatible with all v1.y releases (y > x).
- v2.0.0 may break v1.x compatibility with a migration guide.

## Rollback Policy

- Rollback to a previous release by pointing pipelines at that release directory.
- No release may be deleted from the repository.

## Recovery Policy

- If a frozen release is corrupted, rebuild from source using the same commit.
- Verify SHA256 hashes match before replacing.
- Document the incident in the migration log.

## Graph Evolution Rules

- New entity types must be registered in `graph_schema.json`.
- New edge types must be registered in `graph_schema.json`.
- Entity GUIDs are immutable once assigned.
- Relationship GUIDs are immutable once assigned.
- Duplicate detection must run before adding new entities.

## Entity Evolution Rules

- Entity names may gain aliases (additive).
- Entity types may not change after freeze.
- Entity GUIDs are permanent.
- Entity sources list may grow (additive).

## Relationship Evolution Rules

- New relationship types require schema update.
- Existing relationship types may gain new edges (additive).
- Relationship confidence may be updated with evidence.
- Relationship GUIDs are permanent.

## Corpus Evolution Rules

- New scriptures may be added via migrations.
- Existing scripture definitions may not change.
- Scripture canonical unit counts may increase (new verses discovered).
- Corpus source files are NOT frozen (they are inputs, not outputs).
