# Passport Management Skill

## Purpose
Manage permanent knowledge passports throughout their lifecycle.

## Core Module
`core/passports/passport.py`

## Usage
```python
from core.passports import PassportManager, KnowledgePassport
manager = PassportManager()
passport = manager.create(language="sanskrit", book_uuid="BK-xxx")
passport.add_version(content, source="ocr_engine_v2")
passport.add_conflict("wording", variant_a, variant_b)
passport.approve()
```

## Lifecycle
Created → Evidence Collected → Recovery Attempted → Verified → Approved
Any stage may result in Conflicted, Rejected, or Under Review.
