"""
Verification Engine — Multi-stage verification of recovered knowledge.

Supports: source, evidence, cross-edition, structure, metadata, citation,
confidence verification, and human approval.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class VerificationStage(str, Enum):
    SOURCE = "source"
    EVIDENCE = "evidence"
    CROSS_EDITION = "cross_edition"
    STRUCTURE = "structure"
    METADATA = "metadata"
    CITATION = "citation"
    CONFIDENCE = "confidence"
    HUMAN_APPROVAL = "human_approval"


class VerificationResult(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    INCONCLUSIVE = "inconclusive"
    PENDING = "pending"
    CONFLICTED = "conflicted"


class ApprovalStatus(str, Enum):
    UNREVIEWED = "unreviewed"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEFERRED = "deferred"


@dataclass
class VerificationRecord:
    """A single verification record."""
    record_id: str = ""
    knowledge_uuid: str = ""
    stage: VerificationStage = VerificationStage.SOURCE
    result: VerificationResult = VerificationResult.PENDING
    confidence: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)
    verifier: str = "system"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    pipeline_version: str = "1.0.0"

    def __post_init__(self):
        if not self.record_id:
            self.record_id = f"VR-{uuid.uuid4().hex[:12]}"


class SourceVerifier:
    """Verifies the source of knowledge items."""

    def verify(self, knowledge_uuid: str, source_data: dict) -> VerificationRecord:
        has_source = bool(source_data.get("source_file"))
        has_hash = bool(source_data.get("sha256"))
        has_registry = bool(source_data.get("registry_id"))
        passed = has_source and has_hash and has_registry
        return VerificationRecord(
            knowledge_uuid=knowledge_uuid,
            stage=VerificationStage.SOURCE,
            result=VerificationResult.PASSED if passed else VerificationResult.FAILED,
            confidence=1.0 if passed else 0.0,
            details={"has_source": has_source, "has_hash": has_hash, "has_registry": has_registry},
        )


class EvidenceVerifier:
    """Verifies evidence completeness."""

    def verify(self, knowledge_uuid: str, evidence_items: list[dict]) -> VerificationRecord:
        count = len(evidence_items)
        has_external = any(e.get("source") not in ("original_pdf", "ocr_output") for e in evidence_items)
        confidence = min(1.0, count * 0.2) if count > 0 else 0.0
        result = VerificationResult.PASSED if count >= 1 else VerificationResult.INCONCLUSIVE
        return VerificationRecord(
            knowledge_uuid=knowledge_uuid,
            stage=VerificationStage.EVIDENCE,
            result=result,
            confidence=confidence,
            details={"evidence_count": count, "has_external_evidence": has_external},
        )


class CrossEditionVerifier:
    """Verifies consistency across editions."""

    def verify(self, knowledge_uuid: str, editions: list[dict]) -> VerificationRecord:
        if len(editions) <= 1:
            return VerificationRecord(
                knowledge_uuid=knowledge_uuid,
                stage=VerificationStage.CROSS_EDITION,
                result=VerificationResult.INCONCLUSIVE,
                confidence=0.5,
                details={"edition_count": len(editions)},
            )
        agreements = 0
        for i in range(len(editions)):
            for j in range(i + 1, len(editions)):
                if editions[i].get("content_hash") == editions[j].get("content_hash"):
                    agreements += 1
        total_pairs = len(editions) * (len(editions) - 1) // 2
        confidence = agreements / total_pairs if total_pairs > 0 else 0.0
        return VerificationRecord(
            knowledge_uuid=knowledge_uuid,
            stage=VerificationStage.CROSS_EDITION,
            result=VerificationResult.PASSED if confidence > 0.5 else VerificationResult.FAILED,
            confidence=confidence,
            details={"edition_count": len(editions), "agreement_ratio": confidence},
        )


class StructureVerifier:
    """Verifies document structure preservation."""

    def verify(self, knowledge_uuid: str, structure_data: dict) -> VerificationRecord:
        checks = {
            "has_title": bool(structure_data.get("title")),
            "has_headings": len(structure_data.get("headings", [])) > 0,
            "has_paragraphs": len(structure_data.get("paragraphs", [])) > 0,
            "valid_hierarchy": structure_data.get("hierarchy_depth", 0) > 0,
        }
        passed = sum(checks.values()) >= 2
        confidence = sum(checks.values()) / len(checks) if checks else 0.0
        return VerificationRecord(
            knowledge_uuid=knowledge_uuid,
            stage=VerificationStage.STRUCTURE,
            result=VerificationResult.PASSED if passed else VerificationResult.FAILED,
            confidence=confidence,
            details=checks,
        )


class MetadataVerifier:
    """Verifies metadata completeness and consistency."""

    REQUIRED_FIELDS = ["title", "language", "source"]

    def verify(self, knowledge_uuid: str, metadata: dict) -> VerificationRecord:
        present = [f for f in self.REQUIRED_FIELDS if metadata.get(f)]
        missing = [f for f in self.REQUIRED_FIELDS if not metadata.get(f)]
        confidence = len(present) / len(self.REQUIRED_FIELDS) if self.REQUIRED_FIELDS else 1.0
        return VerificationRecord(
            knowledge_uuid=knowledge_uuid,
            stage=VerificationStage.METADATA,
            result=VerificationResult.PASSED if not missing else VerificationResult.FAILED,
            confidence=confidence,
            details={"present": present, "missing": missing},
        )


class CitationVerifier:
    """Verifies citation completeness."""

    def verify(self, knowledge_uuid: str, citations: list[dict]) -> VerificationRecord:
        count = len(citations)
        valid = sum(1 for c in citations if c.get("source") and c.get("page"))
        confidence = valid / count if count > 0 else 0.0
        result = VerificationResult.PASSED if count > 0 else VerificationResult.INCONCLUSIVE
        return VerificationRecord(
            knowledge_uuid=knowledge_uuid,
            stage=VerificationStage.CITATION,
            result=result,
            confidence=confidence,
            details={"citation_count": count, "valid_citations": valid},
        )


class ConfidenceVerifier:
    """Verifies overall confidence threshold."""

    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold

    def verify(self, knowledge_uuid: str, confidence_score: float) -> VerificationRecord:
        return VerificationRecord(
            knowledge_uuid=knowledge_uuid,
            stage=VerificationStage.CONFIDENCE,
            result=VerificationResult.PASSED if confidence_score >= self.threshold else VerificationResult.FAILED,
            confidence=confidence_score,
            details={"threshold": self.threshold, "actual": confidence_score},
        )


class HumanApprovalVerifier:
    """Tracks human review and approval status."""

    def __init__(self):
        self._approvals: dict[str, ApprovalStatus] = {}

    def submit_for_review(self, knowledge_uuid: str) -> str:
        self._approvals[knowledge_uuid] = ApprovalStatus.PENDING
        return knowledge_uuid

    def approve(self, knowledge_uuid: str, reviewer: str = "human") -> VerificationRecord:
        self._approvals[knowledge_uuid] = ApprovalStatus.APPROVED
        return VerificationRecord(
            knowledge_uuid=knowledge_uuid,
            stage=VerificationStage.HUMAN_APPROVAL,
            result=VerificationResult.PASSED,
            confidence=1.0,
            verifier=reviewer,
            details={"status": "approved"},
        )

    def reject(self, knowledge_uuid: str, reviewer: str = "human", reason: str = "") -> VerificationRecord:
        self._approvals[knowledge_uuid] = ApprovalStatus.REJECTED
        return VerificationRecord(
            knowledge_uuid=knowledge_uuid,
            stage=VerificationStage.HUMAN_APPROVAL,
            result=VerificationResult.FAILED,
            confidence=0.0,
            verifier=reviewer,
            details={"status": "rejected", "reason": reason},
        )

    def get_status(self, knowledge_uuid: str) -> ApprovalStatus:
        return self._approvals.get(knowledge_uuid, ApprovalStatus.UNREVIEWED)


class VerificationEngine:
    """
    Multi-stage verification engine.

    Orchestrates all verification stages for a knowledge item.
    Supports both automated and human verification.
    """

    def __init__(self):
        self.source_verifier = SourceVerifier()
        self.evidence_verifier = EvidenceVerifier()
        self.cross_edition_verifier = CrossEditionVerifier()
        self.structure_verifier = StructureVerifier()
        self.metadata_verifier = MetadataVerifier()
        self.citation_verifier = CitationVerifier()
        self.confidence_verifier = ConfidenceVerifier()
        self.human_verifier = HumanApprovalVerifier()
        self._records: dict[str, list[VerificationRecord]] = {}

    def verify_all(self, knowledge_uuid: str, data: dict[str, Any]) -> dict[str, VerificationRecord]:
        """Run all applicable verification stages. Returns stage->record mapping."""
        results: dict[str, VerificationRecord] = {}

        if "source" in data:
            r = self.source_verifier.verify(knowledge_uuid, data["source"])
            results["source"] = r

        if "evidence" in data:
            r = self.evidence_verifier.verify(knowledge_uuid, data["evidence"])
            results["evidence"] = r

        if "editions" in data:
            r = self.cross_edition_verifier.verify(knowledge_uuid, data["editions"])
            results["cross_edition"] = r

        if "structure" in data:
            r = self.structure_verifier.verify(knowledge_uuid, data["structure"])
            results["structure"] = r

        if "metadata" in data:
            r = self.metadata_verifier.verify(knowledge_uuid, data["metadata"])
            results["metadata"] = r

        if "citations" in data:
            r = self.citation_verifier.verify(knowledge_uuid, data["citations"])
            results["citation"] = r

        if "confidence" in data:
            r = self.confidence_verifier.verify(knowledge_uuid, data["confidence"])
            results["confidence"] = r

        # Store records
        if knowledge_uuid not in self._records:
            self._records[knowledge_uuid] = []
        self._records[knowledge_uuid].extend(results.values())

        return results

    def overall_result(self, records: dict[str, VerificationRecord]) -> VerificationResult:
        """Determine overall verification result from individual stage results."""
        if not records:
            return VerificationResult.INCONCLUSIVE
        results = [r.result for r in records.values()]
        if all(r == VerificationResult.PASSED for r in results):
            return VerificationResult.PASSED
        if any(r == VerificationResult.FAILED for r in results):
            return VerificationResult.FAILED
        if any(r == VerificationResult.CONFLICTED for r in results):
            return VerificationResult.CONFLICTED
        return VerificationResult.INCONCLUSIVE

    def get_history(self, knowledge_uuid: str) -> list[VerificationRecord]:
        return self._records.get(knowledge_uuid, [])

    def summary(self) -> dict:
        total_records = sum(len(r) for r in self._records.values())
        stage_counts: dict[str, int] = {}
        for records in self._records.values():
            for r in records:
                stage_counts[r.stage.value] = stage_counts.get(r.stage.value, 0) + 1
        return {
            "total_items_verified": len(self._records),
            "total_records": total_records,
            "by_stage": stage_counts,
        }
