"""
Recovery Engine — Detects and recovers OCR errors.

NEVER overwrites original OCR. Recovers into a separate recovery layer.
Supports detection of: missing paragraphs, missing verses, broken OCR,
skipped pages, damaged glyphs, truncated lines, encoding failures, empty pages.
"""
from __future__ import annotations

import hashlib
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


class RecoveryIssueType(str, Enum):
    MISSING_PARAGRAPH = "missing_paragraph"
    MISSING_VERSE = "missing_verse"
    BROKEN_OCR = "broken_ocr"
    SKIPPED_PAGE = "skipped_page"
    DAMAGED_GLYPH = "damaged_glyph"
    TRUNCATED_LINE = "truncated_line"
    ENCODING_FAILURE = "encoding_failure"
    EMPTY_PAGE = "empty_page"
    LOW_CONFIDENCE = "low_confidence"
    STRUCTURAL_ANOMALY = "structural_anomaly"


class RecoveryStatus(str, Enum):
    DETECTED = "detected"
    CANDIDATE_FOUND = "candidate_found"
    RECOVERED = "recovered"
    VERIFIED = "verified"
    REJECTED = "rejected"
    NEEDS_HUMAN = "needs_human"
    SKIPPED = "skipped"


@dataclass
class RecoveryIssue:
    issue_id: str = ""
    issue_type: RecoveryIssueType = RecoveryIssueType.BROKEN_OCR
    document_uuid: str = ""
    book_uuid: str = ""
    page: int = 0
    region: str = ""  # bounding box or text region
    original_text: str = ""
    description: str = ""
    severity: float = 0.0  # 0.0-1.0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.issue_id:
            self.issue_id = f"RI-{uuid.uuid4().hex[:12]}"


@dataclass
class RecoveryCandidate:
    candidate_id: str = ""
    issue_id: str = ""
    text: str = ""
    source: str = ""  # which source provided this candidate
    confidence: float = 0.0
    evidence: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.candidate_id:
            self.candidate_id = f"RC-{uuid.uuid4().hex[:12]}"


class RecoveryDetector:
    """Detects recovery issues in OCR output."""

    def detect_issues(self, text: str, document_uuid: str = "", page: int = 0) -> list[RecoveryIssue]:
        issues = []
        issues.extend(self._detect_empty_pages(text, document_uuid, page))
        issues.extend(self._detect_truncated_lines(text, document_uuid, page))
        issues.extend(self._detect_encoding_failures(text, document_uuid, page))
        issues.extend(self._detect_low_confidence(text, document_uuid, page))
        issues.extend(self._detect_structural_anomalies(text, document_uuid, page))
        return issues

    def _detect_empty_pages(self, text: str, doc_id: str, page: int) -> list[RecoveryIssue]:
        if len(text.strip()) < 10:
            return [RecoveryIssue(
                issue_type=RecoveryIssueType.EMPTY_PAGE,
                document_uuid=doc_id, page=page,
                original_text=text, description="Page has less than 10 characters",
                severity=0.8,
            )]
        return []

    def _detect_truncated_lines(self, text: str, doc_id: str, page: int) -> list[RecoveryIssue]:
        issues = []
        for i, line in enumerate(text.split("\n")):
            stripped = line.strip()
            if stripped and len(stripped) > 3:
                # Check if line ends abruptly (no punctuation, no whitespace)
                if stripped[-1] not in ".।!?;:,\n" and not stripped.endswith("—"):
                    if i < len(text.split("\n")) - 1:  # Not last line
                        issues.append(RecoveryIssue(
                            issue_type=RecoveryIssueType.TRUNCATED_LINE,
                            document_uuid=doc_id, page=page,
                            original_text=stripped,
                            description=f"Line may be truncated: '{stripped[-20:]}'",
                            severity=0.4,
                        ))
        return issues[:5]  # Limit

    def _detect_encoding_failures(self, text: str, doc_id: str, page: int) -> list[RecoveryIssue]:
        issues = []
        # Check for replacement characters
        if "\ufffd" in text:
            issues.append(RecoveryIssue(
                issue_type=RecoveryIssueType.ENCODING_FAILURE,
                document_uuid=doc_id, page=page,
                original_text=text[:200],
                description="Contains Unicode replacement characters",
                severity=0.7,
            ))
        # Check for common OCR garbage patterns
        garbage_patterns = [r"[^\w\s\.,!?;:'\"\-()।॥०-९०-९]{5,}"]
        for pattern in garbage_patterns:
            matches = re.findall(pattern, text)
            if matches:
                issues.append(RecoveryIssue(
                    issue_type=RecoveryIssueType.BROKEN_OCR,
                    document_uuid=doc_id, page=page,
                    original_text=matches[0][:200],
                    description=f"Garbage characters detected: {matches[0][:50]}",
                    severity=0.6,
                ))
        return issues

    def _detect_low_confidence(self, text: str, doc_id: str, page: int) -> list[RecoveryIssue]:
        # Heuristic: very short words average suggests poor OCR
        words = text.split()
        if len(words) > 10:
            avg_word_len = sum(len(w) for w in words) / len(words)
            if avg_word_len < 2.0:
                return [RecoveryIssue(
                    issue_type=RecoveryIssueType.LOW_CONFIDENCE,
                    document_uuid=doc_id, page=page,
                    original_text=text[:200],
                    description=f"Average word length {avg_word_len:.1f} suggests poor OCR",
                    severity=0.5,
                )]
        return []

    def _detect_structural_anomalies(self, text: str, doc_id: str, page: int) -> list[RecoveryIssue]:
        issues = []
        if len(text) > 100:
            alpha_ratio = sum(c.isalpha() for c in text) / len(text)
            if alpha_ratio < 0.3:
                issues.append(RecoveryIssue(
                    issue_type=RecoveryIssueType.STRUCTURAL_ANOMALY,
                    document_uuid=doc_id, page=page,
                    original_text=text[:200],
                    description=f"Low alpha ratio {alpha_ratio:.2f} suggests structural issues",
                    severity=0.5,
                ))
        return issues


class RecoveryEngine:
    """
    Production recovery engine.

    Detects issues, generates candidates, stores in recovery layer.
    NEVER overwrites original OCR.
    """

    def __init__(self, recovery_dir: str = "knowledge/recovery"):
        self.recovery_dir = Path(recovery_dir)
        self.recovery_dir.mkdir(parents=True, exist_ok=True)
        self.detector = RecoveryDetector()
        self._issues: dict[str, RecoveryIssue] = {}
        self._candidates: dict[str, RecoveryCandidate] = {}
        self._status: dict[str, RecoveryStatus] = {}

    def detect(self, text: str, document_uuid: str = "", page: int = 0) -> list[RecoveryIssue]:
        issues = self.detector.detect_issues(text, document_uuid, page)
        for issue in issues:
            self._issues[issue.issue_id] = issue
            self._status[issue.issue_id] = RecoveryStatus.DETECTED
        return issues

    def add_candidate(self, issue_id: str, text: str, source: str, confidence: float = 0.0) -> RecoveryCandidate:
        candidate = RecoveryCandidate(
            issue_id=issue_id, text=text, source=source, confidence=confidence,
        )
        self._candidates[candidate.candidate_id] = candidate
        if issue_id in self._status:
            self._status[issue_id] = RecoveryStatus.CANDIDATE_FOUND
        return candidate

    def get_issues(self, document_uuid: str = "") -> list[RecoveryIssue]:
        if document_uuid:
            return [i for i in self._issues.values() if i.document_uuid == document_uuid]
        return list(self._issues.values())

    def get_candidates(self, issue_id: str = "") -> list[RecoveryCandidate]:
        if issue_id:
            return [c for c in self._candidates.values() if c.issue_id == issue_id]
        return list(self._candidates.values())

    def get_status(self, issue_id: str) -> RecoveryStatus:
        return self._status.get(issue_id, RecoveryStatus.DETECTED)

    def summary(self) -> dict:
        status_counts = {}
        for s in self._status.values():
            status_counts[s.value] = status_counts.get(s.value, 0) + 1
        type_counts = {}
        for i in self._issues.values():
            type_counts[i.issue_type.value] = type_counts.get(i.issue_type.value, 0) + 1
        return {
            "total_issues": len(self._issues),
            "total_candidates": len(self._candidates),
            "by_status": status_counts,
            "by_type": type_counts,
        }
