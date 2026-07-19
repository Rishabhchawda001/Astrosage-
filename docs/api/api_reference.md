# AstroSage API Reference

**Version**: 1.0.0
**Last Updated**: 2026-07-19

---

## Overview

AstroSage currently operates as a **script-based system** rather than a REST API.
This document describes the programmatic interfaces available through Python.

---

## 1. Hybrid Search

### Purpose

Search across 120,548 semantic chunks using BM25 + FAISS.

### Usage

```python
import json, numpy as np, faiss
from sentence_transformers import SentenceTransformer

# Load model and index
model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
index = faiss.read_index('knowledge/releases/v1.0.0/embeddings/faiss_index.bin')

# Search
query = "Who is Vishnu?"
embedding = model.encode([query], normalize_embeddings=True).astype('float32')
scores, indices = index.search(embedding, k=5)

# Load chunk mapping
with open('knowledge/releases/v1.0.0/chunks/chunk_manifest.json') as f:
    manifest = json.load(f)

# Results
for score, idx in zip(scores[0], indices[0]):
    print(f"Score: {score:.4f}, Index: {idx}")
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| query | str | required | Search query text |
| k | int | 5 | Number of results to return |
| alpha | float | 0.6 | Semantic vs lexical weight |

### Output

Returns a list of (score, chunk_index) tuples ranked by relevance.

---

## 2. Entity Reasoning

### Purpose

Get detailed reasoning about an entity from the knowledge graph.

### Usage

```python
import json

# Load graph
with open('knowledge/releases/v1.0.0/graph/graph.json') as f:
    graph = json.load(f)

# Find entity
entities = {n['GUID']: n for n in graph['nodes']}
entity = next(n for n in graph['nodes'] if n['name'] == 'Vishnu')

# Get relationships
edges = [e for e in graph['edges'] if e['source_GUID'] == entity['GUID']]

print(f"Entity: {entity['name']}")
print(f"Type: {entity['entity_type']}")
print(f"Mentions: {entity['total_mentions']}")
print(f"Sources: {entity['sources']}")
print(f"Relationships: {len(edges)}")
for e in edges:
    target = entities.get(e['target_GUID'], {})
    print(f"  {e['type']}: {target.get('name', 'unknown')}")
```

### Output

Returns entity metadata, mentions, sources, and relationship chain.

---

## 3. Question Reasoning

### Purpose

Answer a natural language question using graph + semantic evidence.

### Usage

```python
import json, numpy as np, faiss
from sentence_transformers import SentenceTransformer

# Load all components
model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
index = faiss.read_index('knowledge/releases/v1.0.0/embeddings/faiss_index.bin')
with open('knowledge/releases/v1.0.0/graph/graph.json') as f:
    graph = json.load(f)

# Search for evidence
query = "What is the relationship between Krishna and Arjuna?"
embedding = model.encode([query], normalize_embeddings=True).astype('float32')
scores, indices = index.search(embedding, k=5)

# Combine with graph reasoning
entities = [n for n in graph['nodes'] if n['name'] in ['Krishna', 'Arjuna']]
# ... (evidence chain construction)
```

### Output

Returns evidence chain with confidence score and source references.

---

## 4. Grounded Answer Generation

### Purpose

Generate a provenance-traced answer with full evidence attribution.

### Usage

```python
# Run the full pipeline
import subprocess
result = subprocess.run(
    ['python3', 'scripts/phase15_answer_generation.py', '--validate'],
    capture_output=True, text=True
)
print(result.stdout)
```

### Output

Returns structured answer with:
- Entity information
- Key relationships
- Scripture references
- Evidence sources (avg 11+)
- Confidence level

---

## 5. Graph Traversal

### Purpose

Navigate the knowledge graph programmatically.

### Usage

```python
import json

with open('knowledge/releases/v1.0.0/graph/graph.json') as f:
    graph = json.load(f)

# Build adjacency list
adj = {}
for e in graph['edges']:
    src = e['source_GUID']
    if src not in adj:
        adj[src] = []
    adj[src].append(e)

# Traverse from entity
entity = next(n for n in graph['nodes'] if n['name'] == 'Krishna')
neighbors = adj.get(entity['GUID'], [])
print(f"Krishna has {len(neighbors)} outgoing relationships")
```

---

## 6. Chunk Access

### Purpose

Access individual semantic chunks.

### Usage

```python
import json

# Load chunk manifest
with open('knowledge/releases/v1.0.0/chunks/chunk_manifest.json') as f:
    manifest = json.load(f)

# Load verse chunks for a specific scripture
with open('knowledge/releases/v1.0.0/chunks/verses/Bhagavadgītā with the commentary ascribed to Śaṃkara (Adhyāyas 1-17).json') as f:
    chunks = json.load(f)

print(f"Chunks: {len(chunks)}")
for chunk in chunks[:3]:
    print(f"  {chunk['canonical_ref']}: {chunk['text'][:50]}...")
```

---

## 7. Cross-Scripture Alignment

### Purpose

Find equivalent entities, events, or concepts across scriptures.

### Usage

```python
import json

with open('knowledge/releases/v1.0.0/graph/cross_scripture_alignment.json') as f:
    alignments = json.load(f)

# Check alignments
edges = alignments.get('edges', [])
print(f"Total alignments: {len(edges)}")
for a in edges[:5]:
    print(f"  {a.get('type', 'unknown')}: {a.get('source_ref', '')} -> {a.get('target_ref', '')}")
```

---

## 8. Performance Characteristics

| Operation | Latency | Notes |
|-----------|---------|-------|
| FAISS search | 38ms avg | Single query, 5 results |
| Entity lookup | <1ms | By GUID |
| Graph load | 30ms | Full graph into memory |
| Embedding generation | 84ms | Single query on CPU |
| Full pipeline | ~2s | Query → search → reason → answer |

---

## 9. Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| `FileNotFoundError` | Missing frozen release | Verify `knowledge/releases/v1.0.0/` exists |
| `ModuleNotFoundError` | Missing dependency | `pip install torch sentence-transformers faiss-cpu` |
| `MemoryError` | Insufficient RAM | Use machine with 8GB+ RAM |
| `IndexError` | FAISS index out of bounds | Verify embedding count matches chunk count |

---

## 10. Authentication

Currently, AstroSage operates locally without authentication.
Future API versions will include token-based authentication.
