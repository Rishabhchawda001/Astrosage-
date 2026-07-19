# AstroSage — Evidence-First Knowledge Operating System

**Version**: 1.0.0
**Status**: ✅ Certified (PASS WITH LIMITATIONS)
**Knowledge Layer**: Frozen — immutable at `knowledge/releases/v1.0.0/`
**Repository**: [github.com/Rishabhchawda001/Astrosage-](https://github.com/Rishabhchawda001/Astrosage-)

---

## Vision

AstroSage is a permanent, AI-native Knowledge Operating System for Hindu scriptures.
It preserves, reconstructs, validates, connects, retrieves, and reasons over knowledge
while maintaining **complete provenance** and **verifiable evidence** for every claim.

Every answer produced by AstroSage is explainable. Every claim is traceable to
original canonical evidence.

---

## Core Capabilities

| Capability | Description |
|-----------|-------------|
| **Knowledge Graph** | 391 entities, 54 scriptures, 5,044 relationships across 68 types |
| **Semantic Chunking** | 120,548 deterministic chunks at 5 levels (scripture → verse → dialogue → event → entity) |
| **Hybrid Retrieval** | BM25 lexical search + FAISS semantic search fused via alpha-weighted scoring |
| **Reasoning Engine** | Rule-based entity and question reasoning with evidence chain construction |
| **Grounded Answers** | Provenance-traced answers with high-confidence evidence attribution |
| **Hallucination Resistance** | All adversarial queries produce appropriately low confidence scores |
| **Knowledge Freeze** | Immutable v1.0.0 release with SHA256 hashes and migration framework |
| **Migration System** | Versioned, append-only knowledge evolution without modifying frozen artifacts |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CANONICAL CORPUS (54 scriptures)          │
│         GRETIL, Upanishads, Puranas, Vedas, Smritis         │
└──────────────────────────┬──────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE FREEZE v1.0.0                   │
│              Immutable release at knowledge/releases/        │
└──────────┬──────────┬──────────┬──────────┬─────────────────┘
           ↓          ↓          ↓          ↓
┌──────────────┐ ┌──────────┐ ┌─────────┐ ┌───────────────┐
│  Knowledge   │ │ Semantic │ │ Hybrid  │ │   Reasoning   │
│    Graph     │ │ Chunking │ │Retrieval│ │    Engine     │
│ 391 entities │ │120,548   │ │BM25 +   │ │ Entity + QA   │
│ 5,044 edges  │ │ chunks   │ │FAISS    │ │ EvidenceChain │
└──────────────┘ └──────────┘ └─────────┘ └───────┬───────┘
                                                   ↓
┌──────────────────────────────────────────────────────────────┐
│                  GROUNDED ANSWER GENERATION                   │
│        Provenance-traced, evidence-backed, high confidence   │
└──────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- PyTorch (CPU-only is sufficient for inference)
- 4GB+ RAM (8GB+ recommended for embedding generation)
- 500MB+ disk for frozen release

### Installation

```bash
# Clone the repository
git clone https://github.com/Rishabhchawda001/Astrosage-.git
cd Astrosage-

# Install dependencies
pip install -r requirements.txt  # or poetry install

# Verify the frozen knowledge layer loads
python3 -c "
import json
with open('knowledge/releases/v1.0.0/graph/graph.json') as f:
    g = json.load(f)
print(f'Knowledge graph loaded: {len(g[\"nodes\"])} nodes, {len(g[\"edges\"])} edges')
"
```

### Run a Search

```bash
python3 scripts/phase13_hybrid_retrieval.py --validate
```

### Run the Reasoning Engine

```bash
python3 scripts/phase14_reasoning_engine.py --validate
```

### Generate Grounded Answers

```bash
python3 scripts/phase15_answer_generation.py --validate
```

---

## Repository Layout

```
Astrosage-/
├── README.md                          # This file
├── CHANGELOG.md                       # Version history
├── KNOWLEDGE_FREEZE.md                # Immutability policy
├── AI_KNOWLEDGE_CONTRACT.md           # AI consumption contract
├── FINAL_KNOWLEDGE_CERTIFICATION.md   # Component certification
├── PROJECT_COMPLETION.md              # Roadmap completion summary
│
├── .agent/                            # AI operating layer
│   ├── PROJECT_STATE.md               #    Current repository state
│   ├── CURRENT_PHASE.md               #    Active phase
│   └── TODO_NEXT.md                   #    Next actions
├── .ai/                               # AI knowledge version
│   └── KNOWLEDGE_VERSION.md
├── .astrosage/                        # Configuration
│   └── CONFIG.md
│
├── knowledge/
│   ├── releases/v1.0.0/               # FROZEN KNOWLEDGE LAYER
│   │   ├── graph/                     #    Knowledge graph (nodes + edges)
│   │   ├── chunks/                    #    120,548 semantic chunks
│   │   ├── embeddings/                #    Vector embeddings + FAISS index
│   │   ├── retrieval/                 #    BM25 index + search validation
│   │   ├── reasoning/                 #    Entity + question reasoning
│   │   └── answers/                   #    Grounded answers with provenance
│   ├── migrations/                    #    Versioned knowledge evolution
│   └── cku_registry/                  #    Canonical unit registry
│
├── scripts/                           # Pipeline scripts
│   ├── phase10_knowledge_freeze.py    #    Knowledge freeze pipeline
│   ├── phase11_semantic_chunker.py    #    Semantic chunking pipeline
│   ├── phase12_embeddings.py          #    Embedding generation pipeline
│   ├── phase13_hybrid_retrieval.py    #    Hybrid retrieval pipeline
│   ├── phase14_reasoning_engine.py    #    Reasoning engine pipeline
│   └── phase15_answer_generation.py   #    Answer generation pipeline
│
├── docs/                              # Documentation
│   ├── architecture/                  #    Architecture documentation
│   ├── developer/                     #    Developer guide
│   ├── user/                          #    User guide
│   ├── operations/                    #    Operations manual
│   └── api/                           #    API reference
│
├── VERSION_1_ACCEPTANCE_REPORT.md     # Independent audit report
├── VERSION_1_SCORECARD.md             # Audit scorecard
├── SYSTEM_VERIFICATION_REPORT.md      # System verification
├── FINAL_BENCHMARK_RESULTS.md         # Performance benchmarks
├── PRODUCTION_READINESS_REPORT.md     # Production readiness
└── KNOWN_LIMITATIONS.md               # Documented limitations
```

---

## Pipeline Documentation

| Pipeline | Script | Description | Output |
|----------|--------|-------------|--------|
| Knowledge Freeze | `phase10_knowledge_freeze.py` | Freezes verified knowledge into immutable release | SHA256-hashed artifacts |
| Semantic Chunking | `phase11_semantic_chunker.py` | Chunks knowledge at 5 semantic levels | 120,548 deterministic chunks |
| Embeddings | `phase12_embeddings.py` | Generates vector embeddings | 120,548 × 384 vectors + FAISS index |
| Hybrid Retrieval | `phase13_hybrid_retrieval.py` | BM25 + FAISS search engine | Search index + validation |
| Reasoning | `phase14_reasoning_engine.py` | Entity and question reasoning | Evidence chains + relationships |
| Answer Generation | `phase15_answer_generation.py` | Grounded answers with provenance | Traced, high-confidence responses |

---

## Knowledge Graph Statistics

| Metric | Value |
|--------|-------|
| Total Nodes | 445 |
| Entity Nodes | 391 (14 types) |
| Scripture Nodes | 54 |
| Total Edges | 5,044 (68 types) |
| Dialogues | 170 |
| Events | 29 |
| Cross-Scripture Alignments | 76 |
| Orphan Nodes | 0 |
| Broken References | 0 |
| Duplicate GUIDs | 0 |

### Entity Type Distribution

| Type | Count | Examples |
|------|-------|----------|
| Person | 124 | Arjuna, Yudhishthira, Vyasa |
| Concept | 51 | Dharma, Karma, Moksha, Atman |
| Place | 48 | Kurukshetra, Ayodhya, Vrindavan |
| Deity | 46 | Vishnu, Shiva, Krishna, Devi |
| Animal | 33 | Garuda, Nandi, Sesha |
| Weapon | 23 | Sudarshana Chakra, Pashupatastra |
| Text | 19 | Bhagavad Gita, Yoga Sutras |
| Ritual | 14 | Ashvamedha, Yajna |
| Dynasty | 11 | Pandava, Solar, Lunar |
| Avatar | 7 | Rama, Krishna, Narasimha |
| Nakshatra | 5 | Ashvini, Rohini |
| Loka | 3 | Vaikuntha, Kailasa |
| Graha | 5 | Surya, Chandra, Mangala |
| School | 2 | Advaita, Yoga |

---

## Performance Benchmarks

| Metric | Value |
|--------|-------|
| Search Latency (avg) | 38ms |
| Search Latency (max) | 64ms |
| Entity Lookup | <1ms |
| Graph Load Time | 30ms |
| FAISS Index Load | 310ms |
| Query Embedding | 84ms |
| Frozen Release Size | 479.5MB |

---

## Known Limitations

- **4 scriptures unrecoverable**: KEN, MUND, MAHAN, PARASHARA (documented in `KNOWN_LIMITATIONS.md`)
- **94.4% of edges** are generic MENTIONED_IN relationships
- **Rule-based reasoning only** — no neural reasoning augmentation
- **No natural language generation** — answers are evidence-structure formatted
- **No API server** — currently script-driven
- **No cross-lingual search** — Devanagari-IAST bridging not implemented

---

## Certification

| Component | Status |
|-----------|--------|
| Graph Structure | ✅ PASS |
| Entity Registry | ✅ PASS |
| Relationship Registry | ✅ PASS |
| Dialogue Graph | ✅ PASS |
| Event Graph | ✅ PASS |
| Genealogy Graph | ✅ PASS |
| Concept Graph | ✅ PASS |
| Cross-Scripture Alignment | ✅ PASS |
| Corpus Completion | ⚠️ PASS WITH LIMITATIONS |
| Coverage | ⚠️ PASS WITH LIMITATIONS |
| Knowledge Freeze | ✅ PASS |
| Reproducibility | ✅ PASS |

**Overall**: CERTIFIED WITH LIMITATIONS (see `VERSION_1_ACCEPTANCE_REPORT.md`)

---

## License

This repository is distributed under the MIT License.
Copyrighted source texts are excluded from the repository (see commit policy).

---

## Contributing

See `docs/developer/developer_guide.md` for contribution guidelines.
All knowledge changes must go through the migration framework at `knowledge/migrations/`.
