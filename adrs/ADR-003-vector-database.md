# ADR-003: Vector Database Selection

## Status
Accepted

## Date
2026-07-11

## Problem
We need a vector database that supports metadata filtering, runs locally (no cloud dependency), handles our document scale (estimated 50k-500k chunks), and provides production reliability.

## Alternatives Considered
1. **Chroma** — Simple, embedded mode. Limited to single-node, less production-hardened.
2. **Qdrant** — Rust-based, excellent filtering, snapshots. Requires server process.
3. **LanceDB** — Embedded mode, versioning. Newer, less proven.
4. **Milvus** — High scale. Overkill dependencies (etcd, MinIO).
5. **Weaviate** — GraphQL API. Heavier deployment.

## Decision
**Primary: Qdrant** for production, **Chroma** for development/testing.

## Rationale
- Qdrant's metadata filtering enables precise queries (by document, language, chapter, etc.)
- Rust performance handles large-scale search with low latency
- Snapshot capability supports backup/restore requirements
- Simple Docker deployment with minimal configuration
- Chroma's embedded mode enables zero-dependency testing

## Tradeoffs
- Qdrant requires separate server process (slight deployment complexity)
- Two databases to maintain (dev vs. prod)
- Qdrant's REST API adds thin HTTP layer

## Future Migration Path
- Evaluate LanceDB for embedded production mode
- Consider SQLite + sqlite-vss for ultra-lightweight deployment
- Qdrant clustering for multi-node if scale demands
