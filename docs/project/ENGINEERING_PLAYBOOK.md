# AstroSage Knowledge Engine — Engineering Playbook

**Last Updated:** 2026-07-12
**Status:** ✅ ACTIVE — How we do engineering

---

## 1. How to Start Work

1. Read `AGENT_CONSTITUTION.md` for governing rules
2. Read `PROJECT_MEMORY.md` for project history and decisions
3. Read `PROJECT_ROADMAP.md` for what comes next
4. Read `SYSTEM_ARCHITECTURE.md` for current architecture
5. Sync with GitHub:
   ```bash
   git fetch origin
   git rebase origin/main
   ```
6. Verify clean working tree: `git status`
7. Read the phase specification before any implementation

---

## 2. How to Benchmark

### Running Existing Benchmarks
```bash
PYTHONPATH=src python3 -m pytest tests/ -v
```

### Creating a New Benchmark
1. Add benchmark module to `src/astrosage/benchmark/`
2. Use representative corpus samples (not random PDFs)
3. Measure all relevant metrics (accuracy, speed, memory, quality)
4. Store results in `knowledge/benchmarks/`
5. Update Technology Catalog in `research/catalog/technology_catalog.json`
6. Write results to `research/benchmarks/`
7. Document in an ADR if the benchmark leads to a technology decision

### Technology Scoring (10 Criteria)
Score 0–10, weighted:
1. Engineering Quality
2. Performance
3. Documentation
4. Testing
5. Security
6. Community
7. Offline Capability
8. Maintainability
9. Integration Effort
10. Future Outlook

**Decision thresholds:**
- ≥7.0 → Integrate
- 5.0–6.9 → Evaluate further
- 3.0–4.9 → Catalog for future
- <3.0 → Reject

---

## 3. How to Build Plugins

### Plugin Directory Structure
```
plugins/
  <category>/
    __init__.py
    <plugin_name>/
      __init__.py
      plugin.py
      manifest.json  (optional)
```

### Plugin Categories
- `mcp/` — MCP servers (GitHub, Filesystem, Browser, Memory)
- `research/` — Web search, AgentReach adapters
- `search/` — Full-text search
- `evaluation/` — RAG evaluation
- `agents/` — Agent frameworks
- `ocr/` — OCR engines
- `parser/` — Document parsers
- `embedding/` — Embedding models
- `reranker/` — Reranking models
- `knowledge_graph/` — Graph databases

### Plugin Rules
- Every plugin must use ABC-based interface
- Must be independently testable
- Must be independently replaceable
- Must not hard-code external dependencies in core code
- Must have a manifest or __init__.py that declares capabilities

---

## 4. How to Update Architecture

1. Write an ADR in `adrs/` explaining the change
2. Benchmark against representative corpus
3. Run full regression test suite (134+ tests)
4. Obtain approval
5. Update `ARCHITECTURE.md`
6. Update this playbook if the process changes
7. Commit with explicit message

**Never silently change frozen components.**

---

## 5. How to Process the Corpus

### Running the Full Pipeline
```bash
PYTHONPATH=src python3 -u -c "
from src.astrosage.production.parallel_corpus import ParallelCorpusProcessor
p = ParallelCorpusProcessor('.')
metrics = p.run()
"
```

### Resume After Interruption
The pipeline reads from `knowledge/checkpoints/corpus_checkpoint.json`. To resume:
```bash
PYTHONPATH=src python3 -u -c "
from src.astrosage.production.parallel_corpus import ParallelCorpusProcessor
p = ParallelCorpusProcessor('.')
metrics = p.run()  # Automatically skips already-processed files
"
```

### Checkpoint File Format
```json
{
  "processed": ["file1.pdf", "file2.pdf", ...],
  "quarantined": ["file3.pdf", ...],
  "failed": ["file4.pdf", ...]
}
```

---

## 6. How to Run OCR

### Native PDFs (no OCR needed)
PyMuPDF extracts text directly. The classifier identifies these automatically.

### Scanned PDFs
```bash
# Tesseract with language support
tesseract input.pdf output -l eng
tesseract input.pdf output -l hin
tesseract input.pdf output -l san

# For mixed scripts, use PaddleOCR
python3 -c "
from paddleocr import PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang='en')
result = ocr.ocr('page_image.png')
"
```

### OCR Configuration
- DPI: 150 (optimized for speed)
- Max OCR pages per doc: 100
- Max doc time: 600s
- Languages: eng, hin, san
- Timeout per page: 5s

---

## 7. How to Update the Knowledge Lake

### Adding New Documents
1. Place source files in `knowledge/raw/source_library/`
2. Update `knowledge/reports/manifest.csv`
3. Run pipeline: `ParallelCorpusProcessor` handles bronze/silver
4. Verify with: `find knowledge/bronze -type f | wc -l`

### Promoting a Language (Tier 2 → Tier 1)
1. Edit `config/processing_tiers.json`
2. Add language to `tier1.languages`
3. Remove from `tier2.languages`
4. Increment version in the config
5. Re-run incremental processing

---

## 8. How to Use Recovery Infrastructure

### Source Registry
```python
from astrosage.recovery.source_registry.registry import KnowledgeSourceRegistry
reg = KnowledgeSourceRegistry()
sources = reg.list_sources()
ia = reg.get_source("src_internet_archive")
```

### Trust Engine
```python
from astrosage.recovery.trust_engine.engine import TrustEngine
engine = TrustEngine()
score = engine.score_ocr({"character_confidence": 0.85})
action = engine.recommend_action(score)  # auto_accept, manual_review, reject
```

### Knowledge Passport
```python
from astrosage.recovery.knowledge_passport.passport import KnowledgePassportRegistry
reg = KnowledgePassportRegistry()
passport = reg.create_passport("knowledge-uuid", "book-uuid")
passport.add_evidence(source)
passport.compute_overall_confidence()
```

### Recovery Queue
```python
from astrosage.recovery.recovery_queue.queue import RecoveryQueue, Priority
q = RecoveryQueue()
jid = q.enqueue("doc-1", priority=Priority.HIGH, reason="Low OCR confidence")
job = q.dequeue()
q.complete_job(jid)
```

### Edition Registry
```python
from astrosage.recovery.edition_registry.registry import EditionRegistry, Edition, EditionType
reg = EditionRegistry()
eid = reg.register_edition(Edition(title="Book", edition_type=EditionType.ORIGINAL))
```

### Provenance Ledger
```python
from astrosage.recovery.provenance_ledger.ledger import KnowledgeProvenanceLedger, LedgerEntryType
ledger = KnowledgeProvenanceLedger()
eid = ledger.record(entry_type=LedgerEntryType.OCR, object_id="doc-1", transformation="OCR")
chain = ledger.get_chain(eid)  # Trace to origin
trail = ledger.audit_trail("doc-1")  # Human-readable audit
```

---

## 8. How to Create Embeddings (Future Phase)

1. Ensure bronze/silver layers are populated
2. Run chunker: `src/astrosage/chunking/chunker.py`
3. Run embedder: `src/astrosage/embedding/embedder.py` (BGE-M3)
4. Store in `knowledge/gold/embeddings/`
5. Index in Qdrant (production) or Chroma (dev)

---

## 9. How to Benchmark Retrieval (Future Phase)

1. Run hybrid retrieval (BM25 + Vector + Reranker)
2. Evaluate against golden evaluation dataset (1,000 questions)
3. Measure: precision@k, recall@k, MRR, nDCG
4. Compare across pipeline versions
5. Store results in `knowledge/benchmarks/`

---

## 10. How to Evaluate Hallucinations

1. Use RAGAS faithfulness metric
2. Use DeepEval hallucination detection
3. Every answer must have sentence-level evidence mapping
4. Unsupported sentences must be removed
5. If no evidence exists: return "The indexed knowledge base does not contain sufficient evidence to answer this question."

---

## 11. How to Write ADRs

### Template
```markdown
# ADR-XXX: Title

## Status
Accepted | Superseded | Deprecated

## Date
YYYY-MM-DD

## Problem
What problem are we solving?

## Alternatives Considered
1. Alternative A — pros/cons
2. Alternative B — pros/cons

## Decision
What did we choose and why?

## Rationale
Evidence-based reasoning.

## Tradeoffs
What are we giving up?

## Future Migration Path
How could this be changed later?
```

### Naming
- `adrs/ADR-NNN-lowercase-hyphenated-title.md`
- Sequential numbering: ADR-001, ADR-002, ...

---

## 12. How to Push to GitHub

### Standard Flow
```bash
git add -A
git commit -m "Phase N: Description"
git push origin main
```

### Verify Push
```bash
git log --oneline -3
git status  # Should show "up to date with origin/main"
```

### If Push Fails
1. Check: `git remote -v`
2. Check: `git log --oneline origin/main` (has remote changed?)
3. If changed: `git fetch origin && git rebase origin/main`
4. Resolve conflicts
5. Try push again
6. **NEVER force push main**

---

## 13. How to Recover

### Pipeline Crash
The pipeline resumes from the last checkpoint. Simply re-run the pipeline command. It reads `corpus_checkpoint.json` and skips already-processed files.

### Corrupted Bronze/Silver File
Delete the corrupted file and re-run the pipeline. It will reprocess only that document.

### Git State Issues
```bash
git stash          # Save local changes
git fetch origin
git rebase origin/main
git stash pop      # Restore local changes
```

---

## 14. How to Debug

### Pipeline Issues
- Check `knowledge/logs/` for processing logs
- Check `knowledge/checkpoints/corpus_checkpoint.json` for state
- Check `knowledge/quarantine/` for quarantined files

### Test Failures
```bash
PYTHONPATH=src python3 -m pytest tests/ -v --tb=short
```

### Module Import Issues
```bash
PYTHONPATH=src python3 -c "from astrosage.<module> import <class>"
```

### Unicode Issues
All bronze/silver files are UTF-8. Check with:
```bash
file --mime-encoding knowledge/bronze/extracted_text/*.txt | head -5
```

---

*This document is part of the AstroSage Knowledge Engine project and lives at `docs/project/ENGINEERING_PLAYBOOK.md`.*
