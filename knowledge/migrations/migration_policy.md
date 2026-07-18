# Migration Policy — AstroSage Knowledge System

**Effective**: 2026-07-18T20:00:50.146197+00:00

## Purpose

Migrations are the ONLY mechanism for modifying the knowledge layer after a freeze.
Every migration is a numbered, validated, traceable change to the knowledge base.

## Migration Structure

```
knowledge/migrations/
  applied/          — Completed migrations (immutable after execution)
  migration_policy.md
  MIGRATION_LOG.md
```

## Migration Format

Each migration must produce a manifest:

```json
{
  "migration_id": "MIG-001",
  "version_from": "1.0.0",
  "version_to": "1.1.0",
  "created": "ISO-8601",
  "author": "string",
  "description": "string",
  "changes": {
    "added_scriptures": [],
    "added_entities": [],
    "added_edges": [],
    "added_subgraphs": [],
    "modified_artifacts": [],
    "removed_artifacts": []
  },
  "statistics_delta": {},
  "validation": {
    "orphan_nodes": 0,
    "orphan_edges": 0,
    "broken_references": 0,
    "status": "PASS"
  },
  "backward_compatible": true,
  "release_dir": "knowledge/releases/v1.1.0/"
}
```

## Rules

1. Migration IDs are monotonically increasing (MIG-001, MIG-002, ...).
2. Existing IDs are never reused.
3. Each migration produces a new release.
4. Migrations are append-only (no deletions of frozen data).
5. Every migration must pass validation before being marked applied.
6. The MIGRATION_LOG.md tracks all applied migrations.
