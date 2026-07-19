# AstroSage Developer Guide

**Version**: 1.0.0
**Last Updated**: 2026-07-19

---

## 1. Environment Setup

### Prerequisites

```bash
# Python 3.10+ required
python3 --version

# pip or poetry
pip install --upgrade pip
# or
pip install poetry
```

### Installation

```bash
git clone https://github.com/Rishabhchawda001/Astrosage-.git
cd Astrosage-

# Install dependencies
pip install torch sentence-transformers faiss-cpu numpy

# Verify installation
python3 -c "
import torch, faiss, sentence_transformers
print('PyTorch:', torch.__version__)
print('FAISS: OK')
print('Sentence Transformers:', sentence_transformers.__version__)
"
```

---

## 2. Repository Structure

```
Astrosage-/
├── knowledge/releases/v1.0.0/   # Frozen release (DO NOT MODIFY)
├── scripts/                      # Pipeline implementations
├── docs/                         # Documentation
├── .agent/                       # AI operating layer
├── .ai/                          # AI knowledge metadata
└── .astrosage/                   # Configuration
```

### Key Conventions

- **Frozen files** in `knowledge/releases/v1.0.0/` are immutable
- **Working graph** in `knowledge/graph/` is for development only
- **Scripts** in `scripts/` implement pipelines
- **Migrations** in `knowledge/migrations/` handle versioned updates

---

## 3. Coding Standards

### Python Style

- Follow PEP 8
- Use type hints where practical
- Write docstrings for public functions
- Keep functions focused and under 50 lines where possible

### Commit Messages

Use the format:

```
Phase X.Y: <description>
```

Examples:
```
Phase 15: Answer generation with provenance tracing
Documentation: Repository README
```

---

## 4. Testing

### Run Pipeline Validation

```bash
# Search validation
python3 scripts/phase13_hybrid_retrieval.py --validate

# Reasoning validation
python3 scripts/phase14_reasoning_engine.py --validate

# Answer validation
python3 scripts/phase15_answer_generation.py --validate
```

### Run Graph Integrity Check

```bash
python3 -c "
import json
with open('knowledge/releases/v1.0.0/graph/graph.json') as f:
    g = json.load(f)
print(f'Nodes: {len(g[\"nodes\"])}')
print(f'Edges: {len(g[\"edges\"])}')
orphan = [n for n in g['nodes'] if n['GUID'] not in
          set(e['source_GUID'] for e in g['edges']) |
          set(e['target_GUID'] for e in g['edges'])]
print(f'Orphans: {len(orphan)}')
"
```

### Run Artifact Verification

```bash
python3 -c "
import hashlib, os
v1 = 'knowledge/releases/v1.0.0'
for root, dirs, files in os.walk(v1):
    for f in files:
        path = os.path.join(root, f)
        h = hashlib.sha256(open(path, 'rb').read()).hexdigest()[:16]
        print(f'  {os.path.relpath(path, v1)}: {h}')
"
```

---

## 5. Extending the Knowledge Graph

### Adding New Entities

1. Identify the entity in the canonical corpus
2. Determine entity type (Person, Deity, Place, Concept, etc.)
3. Create a new node in `knowledge/graph/graph.json`:
   ```json
   {
     "GUID": "<generated-uuid>",
     "name": "Entity Name",
     "type": "Deity",
     "entity_type": "Deity",
     "total_mentions": 0,
     "sources": [],
     "provenance": {},
     "mentions": []
   }
   ```
4. Add edges connecting to other entities
5. Re-run validation
6. Create a migration (see below)

### Adding New Relationships

1. Identify source and target entity GUIDs
2. Determine relationship type (one of 68 established types)
3. Create a new edge:
   ```json
   {
     "GUID": "<generated-uuid>",
     "type": "TEACHER_OF",
     "source_GUID": "<source-guid>",
     "target_GUID": "<target-guid>",
     "evidence": "canonical_scripture",
     "confidence": 0.95,
     "phase": "10"
   }
   ```
4. Add evidence (scripture, chapter, verse)
5. Re-run validation

---

## 6. Creating Migrations

### Migration Structure

```
knowledge/migrations/
├── migration_policy.md        # Migration rules
├── MIGRATION_LOG.md           # Applied migrations
└── applied/
    └── v1.0.0_initial.json    # Initial freeze manifest
```

### Creating a New Migration

1. Create a migration manifest:
   ```json
   {
     "id": "MIGRATION_V1_1_0",
     "version": "1.1.0",
     "description": "Add new entities from recovered corpus",
     "scriptures_added": ["KEN"],
     "artifacts_modified": [],
     "artifacts_added": ["knowledge/releases/v1.1.0/graph/new_entities.json"],
     "backwards_compatible": true
   }
   ```

2. Update `MIGRATION_LOG.md`

3. Generate new frozen release at `knowledge/releases/v1.1.0/`

4. Update `knowledge_manifest.json`

---

## 7. Running Benchmarks

### Search Latency

```bash
python3 -c "
import time, json, numpy as np, faiss
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
index = faiss.read_index('knowledge/releases/v1.0.0/embeddings/faiss_index.bin')

queries = ['Who is Vishnu?', 'What is dharma?']
for q in queries:
    emb = model.encode([q], normalize_embeddings=True).astype('float32')
    t0 = time.time()
    D, I = index.search(emb, 5)
    print(f'{q}: {(time.time()-t0)*1000:.1f}ms, score={D[0][0]:.3f}')
"
```

### Graph Load Time

```bash
python3 -c "
import json, time
t0 = time.time()
with open('knowledge/releases/v1.0.0/graph/graph.json') as f:
    g = json.load(f)
print(f'Graph load: {(time.time()-t0)*1000:.1f}ms')
print(f'Nodes: {len(g[\"nodes\"])}, Edges: {len(g[\"edges\"])}')
"
```

---

## 8. Release Workflow

1. Complete all pipeline validation
2. Verify artifact integrity (SHA256 hashes match)
3. Run benchmarks
4. Update documentation
5. Commit with descriptive message
6. Push to main
7. Verify on GitHub

### Release Checklist

- [ ] All scripts pass validation
- [ ] Graph integrity verified
- [ ] Artifact hashes match manifest
- [ ] Benchmarks within acceptable range
- [ ] Documentation updated
- [ ] No breaking changes without migration
