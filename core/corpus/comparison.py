"""Corpus Comparison — Compares editions for gap analysis."""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

class CorpusComparisonType(str, Enum):
    OCR_VS_RECOVERED = "ocr_vs_recovered"
    EDITION_A_VS_B = "edition_a_vs_b"
    PARALLEL_EDITIONS = "parallel_editions"

class CorpusDifferenceType(str, Enum):
    IDENTICAL = "identical"
    WORDING = "wording"
    MISSING_CONTENT = "missing_content"
    EXTRA_CONTENT = "extra_content"
    COMPLETELY_DIFFERENT = "completely_different"

@dataclass
class CorpusComparisonResult:
    comparison_id: str = ""
    comparison_type: CorpusComparisonType = CorpusComparisonType.EDITION_A_VS_B
    source_a_id: str = ""
    source_b_id: str = ""
    similarity: float = 0.0
    difference_type: CorpusDifferenceType = CorpusDifferenceType.IDENTICAL
    source_a_text: str = ""
    source_b_text: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    compared_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    def __post_init__(self):
        if not self.comparison_id: self.comparison_id = f"CR-{uuid.uuid4().hex[:12]}"

class CorpusComparisonEngine:
    def __init__(self):
        self._results: dict[str, CorpusComparisonResult] = {}
    def compare_texts(self, text_a: str, text_b: str, **kwargs) -> CorpusComparisonResult:
        words_a = set(text_a.lower().split()) if text_a else set()
        words_b = set(text_b.lower().split()) if text_b else set()
        union = words_a | words_b
        intersection = words_a & words_b
        similarity = len(intersection) / len(union) if union else 0.0
        if similarity > 0.95: diff_type = CorpusDifferenceType.IDENTICAL
        elif similarity > 0.5: diff_type = CorpusDifferenceType.WORDING
        else: diff_type = CorpusDifferenceType.COMPLETELY_DIFFERENT
        result = CorpusComparisonResult(similarity=round(similarity, 4), difference_type=diff_type, source_a_text=text_a[:500], source_b_text=text_b[:500], **kwargs)
        self._results[result.comparison_id] = result
        return result
    def count(self) -> int:
        return len(self._results)
    def summary(self) -> dict:
        return {"total_comparisons": self.count()}
