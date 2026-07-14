# Conflict Review Skill

## Purpose
Detect and track conflicts between knowledge sources.

## Core Module
`core/comparison/engine.py`

## Conflict Types
Wording, Verse Numbering, Metadata, Page Mapping,
Translation, Missing Content, Structural, Citation, Encoding

## Usage
```python
from core.comparison import ComparisonEngine
engine = ComparisonEngine()
conflict = engine.detect_text_conflict(uuid, text_a, text_b)
conflicts = engine.get_unresolved()
```

## Rules
- Never auto-resolve
- All conflicts require human review
- Preserve all variants
