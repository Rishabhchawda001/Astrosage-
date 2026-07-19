# AstroSage Operations Manual

**Version**: 1.0.0
**Last Updated**: 2026-07-19

---

## 1. Deployment

### Prerequisites

- Python 3.10+
- 4GB+ RAM (8GB+ for embedding generation)
- 500MB+ disk for frozen release
- Network access (for initial dependency installation only)

### Deployment Steps

```bash
# 1. Clone repository
git clone https://github.com/Rishabhchawda001/Astrosage-.git
cd Astrosage-

# 2. Install dependencies
pip install torch sentence-transformers faiss-cpu numpy

# 3. Verify frozen release
python3 -c "
import json
with open('knowledge/releases/v1.0.0/graph/graph.json') as f:
    g = json.load(f)
print(f'OK: {len(g[\"nodes\"])} nodes, {len(g[\"edges\"])} edges')
"

# 4. Run validation
python3 scripts/phase13_hybrid_retrieval.py --validate
python3 scripts/phase14_reasoning_engine.py --validate
python3 scripts/phase15_answer_generation.py --validate
```

---

## 2. Updating

### Updating Code Only

```bash
git pull origin main
# Verify scripts still work
python3 scripts/phase13_hybrid_retrieval.py --validate
```

### Updating Knowledge Layer

Knowledge changes require versioned migrations:

```bash
# 1. Check migration policy
cat knowledge/migrations/migration_policy.md

# 2. Review applied migrations
cat knowledge/migrations/MIGRATION_LOG.md

# 3. Apply new migration (if any)
# Follow the migration framework in docs/developer/developer_guide.md
```

---

## 3. Backups

### What to Back Up

| Path | Priority | Size | Description |
|------|----------|------|-------------|
| `knowledge/releases/v1.0.0/` | Critical | 479.5MB | Frozen knowledge layer |
| `knowledge/graph/` | High | ~15MB | Working knowledge graph |
| `scripts/` | High | ~50KB | Pipeline implementations |
| `.agent/` | Medium | ~3KB | AI operating layer |
| `docs/` | Medium | ~20KB | Documentation |

### Backup Commands

```bash
# Full backup
tar -czf astrosage-backup-$(date +%Y%m%d).tar.gz \
  knowledge/releases/ \
  knowledge/graph/ \
  scripts/ \
  .agent/ \
  .ai/ \
  .astrosage/

# Verify backup
tar -tzf astrosage-backup-*.tar.gz | head -20
```

---

## 4. Embedding Regeneration

If embeddings need to be regenerated (e.g., after model update):

```bash
# WARNING: This takes ~57 minutes on CPU
python3 scripts/phase12_embeddings.py

# Verify
python3 -c "
import numpy as np, faiss
emb = np.load('knowledge/releases/v1.0.0/embeddings/embeddings.npy', mmap_mode='r')
index = faiss.read_index('knowledge/releases/v1.0.0/embeddings/faiss_index.bin')
print(f'Embeddings: {emb.shape}')
print(f'FAISS: {index.ntotal} vectors')
"
```

---

## 5. Index Rebuilding

### BM25 Index

```bash
python3 scripts/phase13_hybrid_retrieval.py --validate
# This rebuilds the BM25 index from chunks
```

### FAISS Index

The FAISS index is built during embedding generation (`phase12_embeddings.py`).
To rebuild:

```bash
python3 scripts/phase12_embeddings.py
```

---

## 6. Monitoring

### Health Check

```bash
python3 -c "
import json, os

# Check frozen release exists
release_path = 'knowledge/releases/v1.0.0'
assert os.path.exists(release_path), 'Release missing!'

# Check graph integrity
with open(f'{release_path}/graph/graph.json') as f:
    g = json.load(f)
print(f'Nodes: {len(g[\"nodes\"])}')
print(f'Edges: {len(g[\"edges\"])}')

# Check embeddings exist
assert os.path.exists(f'{release_path}/embeddings/embeddings.npy'), 'Embeddings missing!'
assert os.path.exists(f'{release_path}/embeddings/faiss_index.bin'), 'FAISS index missing!'

# Check chunk count
with open(f'{release_path}/chunks/chunk_manifest.json') as f:
    cm = json.load(f)
print(f'Chunks: {cm[\"total_chunks\"]}')

print('Health check: OK')
"
```

### Performance Check

```bash
python3 -c "
import time, numpy as np, faiss
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
index = faiss.read_index('knowledge/releases/v1.0.0/embeddings/faiss_index.bin')

emb = model.encode(['test query'], normalize_embeddings=True).astype('float32')
t0 = time.time()
D, I = index.search(emb, 5)
latency = (time.time() - t0) * 1000
print(f'Search latency: {latency:.1f}ms')
assert latency < 1000, f'Latency too high: {latency}ms'
print('Performance check: OK')
"
```

---

## 7. Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'torch'"

```bash
pip install torch
# or
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### Issue: "ModuleNotFoundError: No module named 'faiss'"

```bash
pip install faiss-cpu
# or for GPU
pip install faiss-gpu
```

### Issue: "FileNotFoundError: embeddings.npy not found"

The embedding files are large and may not be tracked in git.
Regenerate them:

```bash
python3 scripts/phase12_embeddings.py
```

### Issue: "Graph validation failed"

Check for orphan nodes or broken references:

```bash
python3 -c "
import json
with open('knowledge/releases/v1.0.0/graph/graph.json') as f:
    g = json.load(f)
node_guids = set(n['GUID'] for n in g['nodes'])
for e in g['edges']:
    if e['source_GUID'] not in node_guids:
        print(f'Orphan source: {e[\"source_GUID\"]}')
    if e['target_GUID'] not in node_guids:
        print(f'Orphan target: {e[\"target_GUID\"]}')
print('Validation complete')
"
```

### Issue: "Search returns no results"

Ensure the FAISS index is loaded correctly:

```bash
python3 -c "
import faiss
index = faiss.read_index('knowledge/releases/v1.0.0/embeddings/faiss_index.bin')
print(f'Index loaded: {index.ntotal} vectors')
"
```

---

## 8. Disaster Recovery

### Scenario: Corrupted Knowledge Release

1. Restore from backup:
   ```bash
   tar -xzf astrosage-backup-YYYYMMDD.tar.gz
   ```

2. Verify integrity:
   ```bash
   python3 -c "
   import json
   with open('knowledge/releases/v1.0.0/graph/graph.json') as f:
       g = json.load(f)
   print(f'Restored: {len(g[\"nodes\"])} nodes, {len(g[\"edges\"])} edges')
   "
   ```

### Scenario: Missing Embeddings

Regenerate from frozen release:

```bash
python3 scripts/phase12_embeddings.py
```

### Scenario: Git History Corruption

Re-clone from GitHub:

```bash
rm -rf Astrosage-
git clone https://github.com/Rishabhchawda001/Astrosage-.git
```
