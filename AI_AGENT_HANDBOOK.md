# AstroSage AI Agent Handbook

**Version**: 1.0.0
**Last Updated**: 2026-07-19

---

## Purpose

This handbook describes how future AI agents should operate within the AstroSage repository.

---

## 1. Before Writing Code

Every AI agent MUST:

1. Read `.agent/PROJECT_STATE.md` — current repository state
2. Read `.agent/CURRENT_PHASE.md` — active phase status
3. Read `.ai/KNOWLEDGE_VERSION.md` — knowledge version rules
4. Read `AI_KNOWLEDGE_CONTRACT.md` — consumption contract
5. Read `KNOWLEDGE_FREEZE.md` — immutability policy
6. Read `docs/architecture/architecture_book.md` — system architecture

---

## 2. Repository Rules

### Never Do

- Never overwrite `knowledge/releases/v1.0.0/`
- Never modify graph node GUIDs
- Never modify graph edge GUIDs
- Never modify canonical unit IDs
- Never modify frozen SHA256 hashes
- Never delete committed knowledge artifacts

### Always Do

- Always verify before writing
- Always check for existing implementations
- Always preserve provenance
- Always document changes
- Always run validation after changes
- Always commit atomic changes
- Always push after verification

---

## 3. Continuing Development

### Step 1: Read State

```bash
cat .agent/PROJECT_STATE.md
cat .agent/CURRENT_PHASE.md
cat .agent/TODO_NEXT.md
```

### Step 2: Determine Current Phase

The roadmap is in `docs/project/PROJECT_ROADMAP.md`.
Current state: All 15 phases COMPLETE.

### Step 3: Identify Unfinished Work

Check:
- `TODO_NEXT.md` for explicit tasks
- `KNOWN_LIMITATIONS.md` for known gaps
- `docs/project/PROJECT_ROADMAP.md` for future phases

### Step 4: Implement

Follow `docs/developer/developer_guide.md`.

---

## 4. Performing Migrations

### Migration Policy

All knowledge changes go through `knowledge/migrations/`.

### Steps

1. Read `knowledge/migrations/migration_policy.md`
2. Review `knowledge/migrations/MIGRATION_LOG.md`
3. Create migration manifest
4. Generate new frozen release
5. Update `knowledge_manifest.json`
6. Update `MIGRATION_LOG.md`
7. Commit and push

---

## 5. Validating Work

### After Every Change

```bash
# Graph integrity
python3 -c "
import json
with open('knowledge/releases/v1.0.0/graph/graph.json') as f:
    g = json.load(f)
print(f'Nodes: {len(g[\"nodes\"])}, Edges: {len(g[\"edges\"])}')
"

# Search validation
python3 scripts/phase13_hybrid_retrieval.py --validate

# Reasoning validation
python3 scripts/phase14_reasoning_engine.py --validate

# Answer validation
python3 scripts/phase15_answer_generation.py --validate
```

### Artifact Verification

```bash
python3 -c "
import hashlib, os
v1 = 'knowledge/releases/v1.0.0'
for root, dirs, files in os.walk(v1):
    for f in files:
        path = os.path.join(root, f)
        h = hashlib.sha256(open(path, 'rb').read()).hexdigest()[:16]
        print(f'{os.path.relpath(path, v1)}: {h}')
"
```

---

## 6. Avoiding Regressions

### Pre-Commit Checklist

- [ ] All JSON files valid
- [ ] No orphan nodes
- [ ] No duplicate GUIDs
- [ ] No broken references
- [ ] All counts match manifest
- [ ] Scripts pass validation
- [ ] Documentation updated

### Post-Commit Verification

```bash
git log --oneline -5
git status
```

---

## 7. Communication Protocol

AI agents communicate through:

1. **Git commits** — atomic, descriptive messages
2. **Documentation** — updated with every change
3. **`.agent/` files** — current state for next agent
4. **Reports** — validation and audit results

### Commit Message Format

```
Phase X.Y: <description>
Documentation: <description>
```

---

## 8. Emergency Procedures

### If Graph Is Corrupted

1. Check `knowledge/migrations/` for last known good state
2. Restore from git history
3. Verify with integrity check
4. Document the issue

### If Embeddings Are Missing

```bash
python3 scripts/phase12_embeddings.py
```

### If Search Is Broken

```bash
python3 scripts/phase13_hybrid_retrieval.py --validate
```
