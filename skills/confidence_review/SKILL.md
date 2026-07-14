# Confidence Review Skill

## Purpose
Calculate deterministic weighted confidence scores.

## Core Module
`core/confidence/engine.py`

## Weight Factors
OCR Quality, Source Agreement, Edition Agreement,
Metadata Agreement, Checksum Consistency,
Recovery Consistency, Citation Completeness

## Usage
```python
from core.confidence import ConfidenceEngine
engine = ConfidenceEngine()
engine.add_signal(uuid, "ocr_quality", 0.85)
result = engine.calculate(uuid)
```
