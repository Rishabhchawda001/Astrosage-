# AstroSage Knowledge Engine — Agent Constitution

**Version:** 1.0.0
**Last Updated:** 2026-07-12
**Status:** ✅ ACTIVE — Permanent engineering constitution

---

## Preamble

This document is the supreme governing charter of the AstroSage Knowledge Engine engineering effort. It defines the mission, principles, rules, and frozen architecture that every agent and human contributor must follow. No phase, task, or implementation may violate this constitution without a formal amendment process.

---

## Article I — Mission

**We build a permanent, self-hosted, fully reproducible Knowledge Operating System for Vedic texts, Ayurveda, astrology, research papers, and books.**

### Core Commitments
1. **Zero data loss** — Every source document is preserved forever.
2. **Zero fabricated citations** — Every answer must trace to source material.
3. **Fully reproducible indexing** — A clean clone of this repository must be sufficient to rebuild the entire system.
4. **Local execution** — No dependency on paid APIs or cloud services.
5. **Offline capability** — The system must function with no internet access.
6. **Complete traceability** — Every artifact must trace to its originating source document.
7. **Modular architecture** — Every component must be independently replaceable.
8. **Long-term maintainability** — The system must be auditable and extensible for the next decade.

---

## Article II — Engineering Principles

### 2.1 Research Before Implementation
No technology may be selected without:
- Benchmarking against the AstroSage corpus
- Scoring via the Technology Scoring Framework (10 weighted criteria)
- Documenting in an Architecture Decision Record (ADR)

### 2.2 Measure Before Optimizing
- Profile before optimizing
- Benchmark before selecting
- Never trust assumptions about performance

### 2.3 Verify Before Trusting
- Every conclusion must be independently verifiable
- Never accept previous results without revalidation
- Scientific evidence takes priority over prior conclusions

### 2.4 Evidence Over Opinion
- Every engineering decision must cite measured evidence
- "It's popular" is not a valid reason
- "It benchmarks better on our corpus" is the only valid reason

### 2.5 Preserve Everything
- Never delete archived files automatically
- Never rename source files
- Move unknown files to `_quarantine`, never delete
- Preserve directory structure from source

### 2.6 Modularity Over Cleverness
- ABC-based plugin interfaces for all major components
- No hard-coded dependencies on specific technologies
- Every plugin must be independently replaceable

### 2.7 Maintainability Over Convenience
- Code must be readable by a future engineer years from now
- Prefer explicit over implicit
- Document why, not just what

### 2.8 Reproducibility Over Convenience
- One command should rebuild the entire system from archived sources
- Every processing stage must be versioned independently
- Pipeline configuration must be in files, not code

---

## Article III — Architecture Principles

### 3.1 Knowledge Lake — 4-Layer Architecture
```
raw/     → Immutable source archive (never modified)
bronze/  → Extracted text (first transformation)
silver/  → Structured markdown with preserved hierarchy
gold/    → Chunked, embedded, indexed knowledge
```

### 3.2 Provenance — Every Artifact Traceable
```
Source Document (BOOK-xxx)
  → Page (PAGE-xxx)
    → Section (SECTION-xxx)
      → Chunk (CHUNK-xxx)
        → Embedding (EMBED-xxx)
          → Retrieved Context
            → Answer (ANSWER-xxx)
```

### 3.3 Tier-Based Processing — Language-Aware Routing
```
Document → Classification → Language Detection → Tier Assignment
  Tier 1 (eng/hin/san): Complete pipeline (OCR, parse, metadata, knowledge lake)
  Tier 2 (deferred languages): Register + basic metadata only
  Tier 3 (media): Register only
```
Language tiers are configured in `config/processing_tiers.json`. No code changes needed.

### 3.4 Page-Level Routing — Adaptive per Page
Each page is independently classified. No book is processed as a single unit.

### 3.5 Pipeline Stages (Document Intelligence v1.0)
1. Document Registry (SHA256, UUID)
2. Multi-Signal Page Classifier (11+ signals)
3. Language Detection
4. Page-Level Routing
5. Text Extraction (PyMuPDF / Tesseract)
6. Quality Validation
7. Metadata Extraction
8. Knowledge Lake Ingestion (bronze → silver)

---

## Article IV — Coding Rules

### 4.1 Python Standards
- Target: Python 3.11+
- Follow existing codebase style (ruff-compatible)
- One class per file when possible
- Type hints required for all functions
- Docstrings for all public APIs

### 4.2 Plugin Architecture
- All major components use ABC-based plugin interfaces
- Plugin directory: `plugins/`
- Each plugin must be independently testable
- No hard-coded external dependencies in core code

### 4.3 Knowledge Lake Rules
- Nothing reads from `raw/` except the pipeline
- Everything flows through manifest → bronze → silver → gold
- Never write directly to gold/ (future phases)
- All generated files must include pipeline version metadata

### 4.4 Provenance Rules
- Every artifact gets a permanent UUID
- Every artifact traces to its source document
- Provenance graph maintained in `knowledge/reports/`
- No orphaned artifacts allowed

### 4.5 Testing Rules
- All tests must be automated (pytest)
- Unit tests for core logic
- Integration tests for pipeline stages
- Regression tests for fixed bugs
- Performance benchmarks for critical paths
- Minimum 134 tests passing before any commit

### 4.6 Git Rules
- Single branch: `main` (trunk-based development)
- Commit messages follow: "Phase N: Description"
- Working tree must be clean before phase transitions
- Push after every phase milestone
- GitHub is the single source of truth
- No local-only work may remain

### 4.7 Security Rules
- No hardcoded credentials
- No secrets in source code or client bundles
- Environment variables for all credentials
- Pinned dependency versions for all installed packages

### 4.8 Documentation Rules
- Every phase produces deliverables documented in the phase specification
- ARCHITECTURE.md reflects current frozen architecture
- ADRs document every major decision
- README kept concise and current

---

## Article V — Frozen Components (Document Intelligence v1.0)

The following components are FROZEN. Changes require: benchmark, ADR, regression testing, approval.

| Component | Version | ADR | Status |
|-----------|---------|-----|--------|
| Multi-Signal Page Classifier | v1.0 | ADR-007, ADR-008 | 🔒 LOCKED |
| Document Classification | v1.0 | ADR-007, ADR-008 | 🔒 LOCKED |
| OCR Routing | v1.0 | ADR-007, ADR-008 | 🔒 LOCKED |
| Text Extraction (PyMuPDF) | v1.0 | ADR-008 | 🔒 LOCKED |
| OCR Engine (Tesseract 5.3.4) | v1.0 | ADR-008 | 🔒 LOCKED |
| Language Detection | v1.0 | ADR-008 | 🔒 LOCKED |
| Metadata Extraction | v1.0 | ADR-008 | 🔒 LOCKED |
| Quality Validation | v1.0 | ADR-008 | 🔒 LOCKED |
| Knowledge Lake Schema | v1.0 | ADR-001, ADR-008 | 🔒 LOCKED |
| Provenance Model | v1.0 | ADR-002, ADR-008 | 🔒 LOCKED |

### Change Policy
1. Benchmark against representative corpus
2. Write updated ADR
3. Run full regression test suite (134+ tests)
4. Obtain explicit approval
5. No silent changes — ever

---

## Article VI — Versioning Policy

### Pipeline Components
- Format: `MAJOR.MINOR.PATCH`
- MAJOR: Breaking output format changes
- MINOR: New features, backward-compatible
- PATCH: Bug fixes, no output change
- Each component versioned independently

### Architecture Versions
- Frozen as `Document Intelligence v1.0`
- Future architectures will be `Document Intelligence v2.0`, etc.
- Architecture upgrades require full re-validation

### Dataset Versions
- `DATASET_VERSION` in `versioning/versions.py`
- Increment when the corpus changes
- Schema changes tracked separately in `SCHEMA_VERSION`

---

## Article VII — Engineering Process

### Phase Execution Policy
1. Read this constitution and PROJECT_MEMORY.md before starting
2. Sync with GitHub (fetch, rebase)
3. Execute phase deliverables under **APEE v1** parallel execution model (see `docs/project/APEE_V1.md`)
   - Divide work into independent packages
   - Run 10 implementation workers + 5 validation workers
   - Never leave a worker idle
   - Checkpoint every 5-10 minutes or at logical milestones
   - All 5 validators must approve before merge
4. Run tests
5. Commit and push
6. Verify push succeeded

### Failure Recovery
- Pipeline has checkpoint system: resume from last completed book
- Three failure categories: Recoverable, Retryable, Fatal
- Recoverable: retry automatically with exponential backoff
- Retryable: retry up to 3 times
- Fatal (corrupted, encrypted): quarantine with exact reason

### Benchmark Rules
- Every benchmark must be repeatable
- Store historical results for comparison
- Support version tracking
- Automatic regression detection

---

## Article VIII — Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| PDFs processed | 601/602 (99.8%) | 100% |
| Tests passing | 193 | 193+ |
| Knowledge Lake integrity | 100% | 100% |
| Unicode integrity | 100% | 100% |
| Provenance coverage | 100% | 100% |
| Phases completed | Phase 4.5 | All phases |
| Processing throughput | 240 pages/min | TBD |
| Retrieval precision | N/A | ≥90% |

---

## Amendment Process

1. Write a new ADR explaining the change
2. Provide benchmark evidence
3. Run full regression test suite
4. Update this constitution with a new version
5. Obtain approval before implementation

**No agent, human, or process may override this constitution without following the amendment process.**

---

*This constitution is part of the AstroSage Knowledge Engine project and lives at `docs/project/AGENT_CONSTITUTION.md`.*

---

## Appendix A — Auto-Context Protocol

**Every future phase MUST read these documents before making any implementation decisions:**

1. `docs/project/AGENT_CONSTITUTION.md` — This file (governing rules)
2. `docs/project/PROJECT_MEMORY.md` — Everything learned so far
3. `docs/project/ENGINEERING_PLAYBOOK.md` — How we do engineering
4. `docs/project/PROJECT_ROADMAP.md` — What comes next and current status

**Reading order:** Constitution → Memory → Playbook → Roadmap

**Conflict resolution:** If a phase prompt conflicts with these documents, **STOP** and explain the conflict. Never silently override the constitution.

**Self-check:** Before beginning any implementation, verify that your understanding of the project matches what's documented here. If the documents are stale, flag it.

**These documents are the project's long-term memory. The agent is stateless. These documents are not.**
