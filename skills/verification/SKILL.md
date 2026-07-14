# Verification Skill

## Purpose
Multi-stage verification of recovered knowledge.

## Core Module
`core/verification/engine.py`

## Stages
- Source verification
- Evidence verification
- Cross-edition verification
- Structure verification
- Metadata verification
- Citation verification
- Confidence verification
- Human approval

## Usage
```python
from core.verification import VerificationEngine
engine = VerificationEngine()
results = engine.verify_all(knowledge_uuid, data)
overall = engine.overall_result(results)
```
