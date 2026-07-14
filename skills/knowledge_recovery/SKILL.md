# Knowledge Recovery Skill

## Purpose
Detect and recover OCR errors in the knowledge corpus.

## Core Module
`core/recovery/engine.py`

## Usage
```python
from core.recovery import RecoveryEngine
engine = RecoveryEngine()
issues = engine.detect(text, document_uuid, page)
candidate = engine.add_candidate(issue_id, recovered_text, source, confidence)
```

## Capabilities
- Empty page detection
- Truncated line detection
- Encoding failure detection
- Broken OCR detection
- Low confidence detection
- Structural anomaly detection
- Recovery candidate management
- Status tracking

## Output
Recovery issues and candidates stored in recovery layer.
Original OCR never modified.
