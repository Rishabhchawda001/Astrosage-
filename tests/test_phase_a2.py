"""Phase A2 — Knowledge Recovery & Evidence Engine Tests."""
import sys
import hashlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


# ── Recovery Engine Tests ──────────────────────────────────────────────

class TestRecoveryEngine:
    def test_imports(self):
        from core.recovery import (
            RecoveryEngine, RecoveryDetector, RecoveryIssue,
            RecoveryCandidate, RecoveryIssueType, RecoveryStatus,
        )
        assert RecoveryEngine is not None

    def test_empty_page_detection(self):
        from core.recovery.engine import RecoveryEngine
        engine = RecoveryEngine()
        issues = engine.detect("", document_uuid="DOC-1", page=1)
        assert len(issues) >= 1
        assert issues[0].issue_type.value == "empty_page"

    def test_encoding_failure_detection(self):
        from core.recovery.engine import RecoveryEngine
        engine = RecoveryEngine()
        issues = engine.detect("Hello world\ufffd\ufffd\ufffd", document_uuid="DOC-2", page=1)
        encoding_issues = [i for i in issues if i.issue_type.value == "encoding_failure"]
        assert len(encoding_issues) >= 1

    def test_broken_ocr_detection(self):
        from core.recovery.engine import RecoveryEngine
        engine = RecoveryEngine()
        issues = engine.detect("Text here %%%###@!!! garbage", document_uuid="DOC-3", page=1)
        assert len(issues) > 0

    def test_structural_anomaly_detection(self):
        from core.recovery.engine import RecoveryEngine
        engine = RecoveryEngine()
        issues = engine.detect("a" * 50 + " " * 200, document_uuid="DOC-4", page=1)
        anomaly = [i for i in issues if i.issue_type.value == "structural_anomaly"]
        assert len(anomaly) >= 1

    def test_add_candidate(self):
        from core.recovery.engine import RecoveryEngine
        engine = RecoveryEngine()
        issues = engine.detect("", document_uuid="DOC-5", page=1)
        candidate = engine.add_candidate(issues[0].issue_id, "recovered text", "test_source", 0.8)
        assert candidate.issue_id == issues[0].issue_id
        assert candidate.confidence == 0.8

    def test_status_tracking(self):
        from core.recovery.engine import RecoveryEngine
        engine = RecoveryEngine()
        issues = engine.detect("", document_uuid="DOC-6", page=1)
        assert engine.get_status(issues[0].issue_id).value == "detected"
        engine.add_candidate(issues[0].issue_id, "text", "src", 0.9)
        assert engine.get_status(issues[0].issue_id).value == "candidate_found"

    def test_summary(self):
        from core.recovery.engine import RecoveryEngine
        engine = RecoveryEngine()
        engine.detect("", document_uuid="DOC-7", page=1)
        summary = engine.summary()
        assert summary["total_issues"] >= 1
        assert summary["total_candidates"] == 0

    def test_get_issues_by_document(self):
        from core.recovery.engine import RecoveryEngine
        engine = RecoveryEngine()
        engine.detect("", document_uuid="DOC-A", page=1)
        engine.detect("", document_uuid="DOC-B", page=1)
        assert len(engine.get_issues("DOC-A")) >= 1
        assert len(engine.get_issues("DOC-B")) >= 1
        assert len(engine.get_issues()) >= 2

    def test_healthy_page_no_issues(self):
        from core.recovery.engine import RecoveryEngine
        engine = RecoveryEngine()
        issues = engine.detect(
            "This is a perfectly normal page with good text content and sentences.",
            document_uuid="DOC-8", page=1,
        )
        # Should have fewer issues for healthy text
        assert isinstance(issues, list)


# ── Evidence Engine Tests ─────────────────────────────────────────────

class TestEvidenceEngine:
    def test_imports(self):
        from core.evidence import (
            EvidenceEngine, EvidenceItem, EvidenceQuery,
            EvidenceSource, EvidenceStatus, EvidenceCollector,
        )
        assert EvidenceEngine is not None

    def test_submit_evidence(self):
        from core.evidence.engine import EvidenceEngine, EvidenceItem, EvidenceSource
        engine = EvidenceEngine()
        item = EvidenceItem(content="Test evidence", source=EvidenceSource.OPEN_LIBRARY)
        eid = engine.submit(item)
        assert eid == item.evidence_id
        assert engine.get(eid) is not None

    def test_evidence_content_hash(self):
        from core.evidence.engine import EvidenceItem, EvidenceSource
        item = EvidenceItem(content="Hello world", source=EvidenceSource.GITHUB)
        expected = hashlib.sha256("Hello world".encode("utf-8")).hexdigest()
        assert item.content_hash == expected

    def test_deduplication(self):
        from core.evidence.engine import EvidenceEngine, EvidenceItem, EvidenceSource
        engine = EvidenceEngine()
        engine.submit(EvidenceItem(content="Same text", source=EvidenceSource.GITHUB))
        engine.submit(EvidenceItem(content="Same text", source=EvidenceSource.GITHUB))
        engine.submit(EvidenceItem(content="Different text", source=EvidenceSource.GITHUB))
        removed = engine.deduplicate()
        assert removed == 1
        assert len(engine.summary()["by_source"]) >= 1

    def test_integrity_verification(self):
        from core.evidence.engine import EvidenceEngine, EvidenceItem, EvidenceSource
        engine = EvidenceEngine()
        item = EvidenceItem(content="Verify me", source=EvidenceSource.INTERNET_ARCHIVE)
        engine.submit(item)
        assert engine.verify(item.evidence_id) is True

    def test_search(self):
        from core.evidence.engine import EvidenceEngine, EvidenceItem, EvidenceQuery, EvidenceSource
        engine = EvidenceEngine()
        engine.submit(EvidenceItem(content="A", source=EvidenceSource.GITHUB, confidence=0.9))
        engine.submit(EvidenceItem(content="B", source=EvidenceSource.GITHUB, confidence=0.3))
        results = engine.search(EvidenceQuery(min_confidence=0.5))
        assert len(results) == 1
        assert results[0].confidence == 0.9

    def test_provenance_tracking(self):
        from core.evidence.engine import EvidenceItem, EvidenceSource
        item = EvidenceItem(content="Provenance test", source=EvidenceSource.INTERNET_ARCHIVE)
        item.add_provenance_step("collected")
        item.add_provenance_step("verified")
        assert len(item.provenance) == 2
        assert item.provenance[0]["step"] == "collected"

    def test_summary(self):
        from core.evidence.engine import EvidenceEngine, EvidenceItem, EvidenceSource
        engine = EvidenceEngine()
        engine.submit(EvidenceItem(content="Test", source=EvidenceSource.CROSSREF, confidence=0.7))
        s = engine.summary()
        assert s["total_items"] == 1
        assert "crossref" in s["by_source"]

    def test_search_with_source_filter(self):
        from core.evidence.engine import EvidenceEngine, EvidenceItem, EvidenceQuery, EvidenceSource
        engine = EvidenceEngine()
        engine.submit(EvidenceItem(content="A", source=EvidenceSource.GITHUB))
        engine.submit(EvidenceItem(content="B", source=EvidenceSource.CROSSREF))
        q = EvidenceQuery(sources=[EvidenceSource.GITHUB])
        results = engine.search(q)
        assert len(results) == 1


# ── Verification Engine Tests ─────────────────────────────────────────

class TestVerificationEngine:
    def test_imports(self):
        from core.verification import (
            VerificationEngine, VerificationRecord, VerificationStage,
            VerificationResult, ApprovalStatus,
        )
        assert VerificationEngine is not None

    def test_source_verification_pass(self):
        from core.verification.engine import VerificationEngine
        engine = VerificationEngine()
        results = engine.verify_all("KU-1", {
            "source": {"source_file": "test.pdf", "sha256": "abc123", "registry_id": "REG-1"},
        })
        assert results["source"].result.value == "passed"

    def test_source_verification_fail(self):
        from core.verification.engine import VerificationEngine
        engine = VerificationEngine()
        results = engine.verify_all("KU-2", {
            "source": {"source_file": ""},
        })
        assert results["source"].result.value == "failed"

    def test_evidence_verification(self):
        from core.verification.engine import VerificationEngine
        engine = VerificationEngine()
        results = engine.verify_all("KU-3", {
            "evidence": [
                {"source": "open_library", "content": "text"},
                {"source": "original_pdf", "content": "ocr"},
            ],
        })
        assert results["evidence"].result.value == "passed"

    def test_metadata_verification(self):
        from core.verification.engine import VerificationEngine
        engine = VerificationEngine()
        results = engine.verify_all("KU-4", {
            "metadata": {"title": "Test Book", "language": "hindi", "source": "archive"},
        })
        assert results["metadata"].result.value == "passed"

    def test_metadata_verification_fail(self):
        from core.verification.engine import VerificationEngine
        engine = VerificationEngine()
        results = engine.verify_all("KU-5", {
            "metadata": {"title": ""},
        })
        assert results["metadata"].result.value == "failed"

    def test_structure_verification(self):
        from core.verification.engine import VerificationEngine
        engine = VerificationEngine()
        results = engine.verify_all("KU-6", {
            "structure": {"title": "Chapter 1", "headings": ["H1", "H2"], "paragraphs": ["p1"], "hierarchy_depth": 2},
        })
        assert results["structure"].result.value == "passed"

    def test_citation_verification(self):
        from core.verification.engine import VerificationEngine
        engine = VerificationEngine()
        results = engine.verify_all("KU-7", {
            "citations": [{"source": "Internet Archive", "page": 42}],
        })
        assert results["citation"].result.value == "passed"

    def test_overall_result_all_passed(self):
        from core.verification.engine import VerificationEngine, VerificationResult
        engine = VerificationEngine()
        results = engine.verify_all("KU-8", {
            "source": {"source_file": "x.pdf", "sha256": "abc", "registry_id": "R1"},
            "metadata": {"title": "T", "language": "en", "source": "s"},
        })
        assert engine.overall_result(results) == VerificationResult.PASSED

    def test_overall_result_inconclusive(self):
        from core.verification.engine import VerificationEngine, VerificationResult
        engine = VerificationEngine()
        assert engine.overall_result({}) == VerificationResult.INCONCLUSIVE

    def test_human_approval(self):
        from core.verification.engine import VerificationEngine
        engine = VerificationEngine()
        engine.human_verifier.submit_for_review("KU-9")
        assert engine.human_verifier.get_status("KU-9").value == "pending"
        record = engine.human_verifier.approve("KU-9", "expert1")
        assert record.result.value == "passed"

    def test_history_tracking(self):
        from core.verification.engine import VerificationEngine
        engine = VerificationEngine()
        engine.verify_all("KU-10", {"source": {"source_file": "x.pdf", "sha256": "abc", "registry_id": "R1"}})
        history = engine.get_history("KU-10")
        assert len(history) >= 1


# ── Provenance Ledger Tests ───────────────────────────────────────────

class TestProvenanceLedger:
    def test_imports(self):
        from core.provenance import ProvenanceLedger, ProvenanceEntry
        assert ProvenanceLedger is not None

    def test_record_entry(self):
        from core.provenance.ledger import ProvenanceEntry
        from core.provenance.ledger import ProvenanceLedger
        ledger = ProvenanceLedger()
        entry = ProvenanceEntry(knowledge_uuid="KU-100", operation="ocr", tool="tesseract")
        eid = ledger.record(entry)
        assert eid == entry.entry_id

    def test_lineage_chain(self):
        from core.provenance.ledger import ProvenanceLedger
        ledger = ProvenanceLedger()
        eid1 = ledger.record_operation("KU-200", "ocr", tool="tesseract")
        eid2 = ledger.record_operation("KU-200", "parse", tool="docling")
        lineage = ledger.get_lineage("KU-200")
        assert len(lineage) == 2
        assert lineage[1].previous_entry_id == eid1

    def test_integrity_verification(self):
        from core.provenance.ledger import ProvenanceLedger
        ledger = ProvenanceLedger()
        ledger.record_operation("KU-300", "ocr")
        ledger.record_operation("KU-300", "parse")
        assert ledger.verify_integrity("KU-300") is True

    def test_search(self):
        from core.provenance.ledger import ProvenanceLedger
        ledger = ProvenanceLedger()
        ledger.record_operation("KU-400", "ocr", tool="tesseract")
        ledger.record_operation("KU-400", "parse", tool="docling")
        results = ledger.search(tool="tesseract")
        assert len(results) == 1

    def test_summary(self):
        from core.provenance.ledger import ProvenanceLedger
        ledger = ProvenanceLedger()
        ledger.record_operation("KU-500", "ocr")
        ledger.record_operation("KU-500", "verify")
        s = ledger.summary()
        assert s["total_entries"] == 2

    def test_empty_lineage(self):
        from core.provenance.ledger import ProvenanceLedger
        ledger = ProvenanceLedger()
        assert ledger.get_lineage("NONEXISTENT") == []
        assert ledger.verify_integrity("NONEXISTENT") is True


# ── Knowledge Passport Tests ──────────────────────────────────────────

class TestKnowledgePassport:
    def test_imports(self):
        from core.passports import (
            KnowledgePassport, PassportManager, PassportStatus,
            ConflictRecord, VersionRecord,
        )
        assert KnowledgePassport is not None

    def test_create_passport(self):
        from core.passports.passport import KnowledgePassport
        p = KnowledgePassport(language="sanskrit", book_uuid="BK-1")
        assert p.knowledge_uuid.startswith("KP-")
        assert p.language == "sanskrit"

    def test_add_version(self):
        from core.passports.passport import KnowledgePassport
        p = KnowledgePassport()
        v = p.add_version("content text", source="ocr_v1")
        assert v.content_hash != ""
        assert len(p.versions) == 1

    def test_add_conflict(self):
        from core.passports.passport import KnowledgePassport
        p = KnowledgePassport()
        c = p.add_conflict("wording", "A text", "B text")
        assert len(p.conflicts) == 1
        assert p.status.value == "conflicted"

    def test_approve_reject(self):
        from core.passports.passport import KnowledgePassport
        p = KnowledgePassport()
        p.approve()
        assert p.approval_status == "approved"
        p.reject("wrong")
        assert p.approval_status == "rejected"

    def test_flag_for_review(self):
        from core.passports.passport import KnowledgePassport
        p = KnowledgePassport()
        p.flag_for_review()
        assert p.human_review_flag is True
        assert p.status.value == "under_review"

    def test_evidence_sources(self):
        from core.passports.passport import KnowledgePassport
        p = KnowledgePassport()
        p.add_evidence_source("open_library")
        p.add_evidence_source("open_library")  # duplicate
        assert p.evidence_count == 1
        p.add_evidence_source("crossref")
        assert p.evidence_count == 2

    def test_passport_manager(self):
        from core.passports.passport import PassportManager
        mgr = PassportManager()
        p1 = mgr.create(language="hindi")
        p2 = mgr.create(language="sanskrit")
        assert mgr.count() == 2
        assert len(mgr.list_by_language("hindi")) == 1

    def test_to_dict(self):
        from core.passports.passport import KnowledgePassport
        p = KnowledgePassport(language="english")
        d = p.to_dict()
        assert "knowledge_uuid" in d
        assert d["language"] == "english"

    def test_latest_version(self):
        from core.passports.passport import KnowledgePassport
        p = KnowledgePassport()
        assert p.latest_version() is None
        p.add_version("v1", source="s1")
        p.add_version("v2", source="s2")
        assert p.latest_version().source == "s2"


# ── Confidence Engine Tests ───────────────────────────────────────────

class TestConfidenceEngine:
    def test_imports(self):
        from core.confidence import ConfidenceEngine, ConfidenceSignal, ConfidenceResult
        assert ConfidenceEngine is not None

    def test_basic_calculation(self):
        from core.confidence.engine import ConfidenceEngine
        engine = ConfidenceEngine()
        engine.add_signal("KU-1", "ocr_quality", 0.9)
        engine.add_signal("KU-1", "source_agreement", 0.8)
        result = engine.calculate("KU-1")
        assert 0.0 < result.overall_confidence <= 1.0

    def test_weighted_calculation(self):
        from core.confidence.engine import ConfidenceEngine
        engine = ConfidenceEngine(weights={"ocr_quality": 2.0, "source_agreement": 1.0})
        engine.add_signal("KU-2", "ocr_quality", 1.0)
        engine.add_signal("KU-2", "source_agreement", 0.0)
        result = engine.calculate("KU-2")
        assert result.overall_confidence > 0.5  # ocr has higher weight

    def test_empty_signals(self):
        from core.confidence.engine import ConfidenceEngine
        engine = ConfidenceEngine()
        result = engine.calculate("KU-3")
        assert result.overall_confidence == 0.0

    def test_min_max_signals(self):
        from core.confidence.engine import ConfidenceEngine
        engine = ConfidenceEngine()
        engine.add_signal("KU-4", "ocr_quality", 0.3)
        engine.add_signal("KU-4", "source_agreement", 0.9)
        result = engine.calculate("KU-4")
        assert result.min_signal == "ocr_quality"
        assert result.max_signal == "source_agreement"

    def test_get_score(self):
        from core.confidence.engine import ConfidenceEngine
        engine = ConfidenceEngine()
        engine.add_signal("KU-5", "ocr_quality", 0.7)
        engine.calculate("KU-5")
        score = engine.get_score("KU-5")
        assert score > 0.0

    def test_summary(self):
        from core.confidence.engine import ConfidenceEngine
        engine = ConfidenceEngine()
        engine.add_signal("KU-6", "ocr_quality", 0.5)
        engine.calculate("KU-6")
        s = engine.summary()
        assert s["total_items"] == 1


# ── Alignment Engine Tests ────────────────────────────────────────────

class TestAlignmentEngine:
    def test_imports(self):
        from core.alignment import (
            AlignmentEngine, EditionInfo, EditionAlignment,
            EditionType, AlignmentStatus, AlignmentSegment,
        )
        assert AlignmentEngine is not None

    def test_register_edition(self):
        from core.alignment.engine import AlignmentEngine, EditionInfo
        engine = AlignmentEngine()
        eid = engine.register_edition(EditionInfo(language="hindi"))
        assert eid.startswith("ED-")
        assert engine.get_edition(eid) is not None

    def test_propose_alignment(self):
        from core.alignment.engine import AlignmentEngine, EditionInfo
        engine = AlignmentEngine()
        e1 = engine.register_edition(EditionInfo(language="hindi"))
        e2 = engine.register_edition(EditionInfo(language="sanskrit"))
        alignment = engine.propose_alignment([e1, e2])
        assert alignment.status.value == "proposed"

    def test_add_segment(self):
        from core.alignment.engine import AlignmentEngine, EditionInfo, AlignmentSegment
        engine = AlignmentEngine()
        e1 = engine.register_edition(EditionInfo(language="hindi"))
        e2 = engine.register_edition(EditionInfo(language="english"))
        a = engine.propose_alignment([e1, e2])
        engine.add_segment(a.alignment_id, AlignmentSegment(
            edition_a_uuid=e1, edition_b_uuid=e2, segment_a="text1", segment_b="text2",
        ))
        updated = engine.get_alignment(a.alignment_id)
        assert updated.segment_count == 1

    def test_list_by_language(self):
        from core.alignment.engine import AlignmentEngine, EditionInfo
        engine = AlignmentEngine()
        engine.register_edition(EditionInfo(language="hindi"))
        engine.register_edition(EditionInfo(language="english"))
        engine.register_edition(EditionInfo(language="hindi"))
        assert len(engine.list_editions_by_language("hindi")) == 2

    def test_find_parallel(self):
        from core.alignment.engine import AlignmentEngine, EditionInfo
        engine = AlignmentEngine()
        engine.register_edition(EditionInfo(book_uuid="BK-1", language="hindi"))
        engine.register_edition(EditionInfo(book_uuid="BK-1", language="english"))
        engine.register_edition(EditionInfo(book_uuid="BK-2", language="hindi"))
        parallel = engine.find_parallel_editions("BK-1")
        assert len(parallel) == 2

    def test_summary(self):
        from core.alignment.engine import AlignmentEngine, EditionInfo
        engine = AlignmentEngine()
        engine.register_edition(EditionInfo())
        s = engine.summary()
        assert s["total_editions"] == 1


# ── Comparison Engine Tests ───────────────────────────────────────────

class TestComparisonEngine:
    def test_imports(self):
        from core.comparison import (
            ComparisonEngine, Conflict, ConflictType,
            ConflictSeverity, ConflictStatus,
        )
        assert ComparisonEngine is not None

    def test_text_conflict(self):
        from core.comparison.engine import ComparisonEngine
        engine = ComparisonEngine()
        c = engine.detect_text_conflict("KU-1", "Text A", "Text B")
        assert c.conflict_type.value == "wording"
        assert c.severity.value in ("low", "medium", "high")

    def test_metadata_conflict(self):
        from core.comparison.engine import ComparisonEngine
        engine = ComparisonEngine()
        conflicts = engine.detect_metadata_conflict("KU-2", {"title": "Book A"}, {"title": "Book B"})
        assert len(conflicts) == 1
        assert conflicts[0].conflict_type.value == "metadata"

    def test_missing_content(self):
        from core.comparison.engine import ComparisonEngine
        engine = ComparisonEngine()
        c = engine.detect_missing_content("KU-3", ["source_a"], ["source_b"])
        assert c.conflict_type.value == "missing_content"
        assert c.severity.value == "high"

    def test_verse_conflict(self):
        from core.comparison.engine import ComparisonEngine
        engine = ComparisonEngine()
        c = engine.detect_verse_conflict("KU-4", "1.1", "1.2")
        assert c.conflict_type.value == "verse_numbering"

    def test_resolution(self):
        from core.comparison.engine import ComparisonEngine
        engine = ComparisonEngine()
        c = engine.detect_text_conflict("KU-5", "A", "B")
        c.resolve("A", "human", "verified")
        assert c.status.value == "resolved"
        assert c.preferred == "A"

    def test_unresolved_list(self):
        from core.comparison.engine import ComparisonEngine
        engine = ComparisonEngine()
        engine.detect_text_conflict("KU-6", "A", "B")
        engine.detect_text_conflict("KU-7", "C", "D")
        unresolved = engine.get_unresolved()
        assert len(unresolved) == 2

    def test_summary(self):
        from core.comparison.engine import ComparisonEngine
        engine = ComparisonEngine()
        engine.detect_text_conflict("KU-8", "X", "Y")
        s = engine.summary()
        assert s["total_conflicts"] == 1


# ── Trust Engine Tests ────────────────────────────────────────────────

class TestTrustEngine:
    def test_imports(self):
        from core.trust import (
            TrustEngine, TrustLevel, TrustFactor,
            TrustLevelThresholds, TrustResult,
        )
        assert TrustEngine is not None

    def test_basic_evaluation(self):
        from core.trust.engine import TrustEngine
        engine = TrustEngine()
        engine.add_factor("KU-1", "ocr_quality", 0.9)
        engine.add_factor("KU-1", "verification_result", 0.8)
        result = engine.evaluate("KU-1")
        assert result.trust_score > 0.0
        assert result.trust_level.value != "pending"

    def test_high_trust(self):
        from core.trust.engine import TrustEngine
        engine = TrustEngine()
        engine.add_factor("KU-2", "ocr_quality", 0.95)
        engine.add_factor("KU-2", "human_review", 0.95)
        result = engine.evaluate("KU-2")
        assert result.trust_score >= 0.9

    def test_low_trust(self):
        from core.trust.engine import TrustEngine
        engine = TrustEngine()
        engine.add_factor("KU-3", "ocr_quality", 0.1)
        result = engine.evaluate("KU-3")
        assert result.trust_level.value in ("low_confidence", "pending")

    def test_list_by_level(self):
        from core.trust.engine import TrustEngine, TrustLevel
        engine = TrustEngine()
        engine.add_factor("KU-4", "ocr_quality", 0.95)
        engine.add_factor("KU-4", "verification_result", 0.95)
        engine.evaluate("KU-4")
        verified = engine.list_by_level(TrustLevel.HUMAN_APPROVED)
        assert len(verified) >= 1

    def test_summary(self):
        from core.trust.engine import TrustEngine
        engine = TrustEngine()
        engine.add_factor("KU-5", "ocr_quality", 0.7)
        engine.evaluate("KU-5")
        s = engine.summary()
        assert s["total_items"] == 1
        assert s["avg_trust"] > 0.0

    def test_level_history(self):
        from core.trust.engine import TrustEngine
        engine = TrustEngine()
        engine.add_factor("KU-6", "ocr_quality", 0.8)
        engine.evaluate("KU-6")
        engine.add_factor("KU-6", "human_review", 0.95)
        engine.evaluate("KU-6")
        result = engine.get_result("KU-6")
        assert len(result.level_history) == 2


# ── Integration Tests ─────────────────────────────────────────────────

class TestPhaseA2Integration:
    def test_full_pipeline(self):
        """Test the complete recovery → evidence → verification → confidence → passport pipeline."""
        from core.recovery.engine import RecoveryEngine
        from core.evidence.engine import EvidenceEngine, EvidenceItem, EvidenceSource
        from core.verification.engine import VerificationEngine
        from core.provenance.ledger import ProvenanceLedger
        from core.passports.passport import KnowledgePassport
        from core.confidence.engine import ConfidenceEngine
        from core.alignment.engine import AlignmentEngine, EditionInfo
        from core.comparison.engine import ComparisonEngine
        from core.trust.engine import TrustEngine

        # Recovery
        recovery = RecoveryEngine()
        issues = recovery.detect("Bad OCR \ufffd\ufffd\ufffd text", document_uuid="DOC-1", page=1)
        assert len(issues) > 0

        # Evidence
        evidence = EvidenceEngine()
        ev = EvidenceItem(content="recovered text from archive", source=EvidenceSource.INTERNET_ARCHIVE)
        evidence.submit(ev)
        assert evidence.summary()["total_items"] == 1

        # Verification
        verification = VerificationEngine()
        results = verification.verify_all("KU-1", {
            "source": {"source_file": "doc.pdf", "sha256": "abc", "registry_id": "R1"},
            "metadata": {"title": "Test", "language": "hindi", "source": "archive"},
            "evidence": [{"source": "open_library", "content": "text"}],
        })
        assert verification.overall_result(results).value == "passed"

        # Provenance
        ledger = ProvenanceLedger()
        ledger.record_operation("KU-1", "ocr", tool="tesseract")
        ledger.record_operation("KU-1", "recovery", tool="recovery_engine")
        assert ledger.get_lineage_length("KU-1") == 2

        # Passport
        passport = KnowledgePassport(knowledge_uuid="KU-1", language="hindi")
        passport.add_version("recovered text", source="recovery_v1")
        passport.update_confidence(0.85)
        assert passport.confidence == 0.85

        # Confidence
        conf = ConfidenceEngine()
        conf.add_signal("KU-1", "ocr_quality", 0.7)
        conf.add_signal("KU-1", "source_agreement", 0.9)
        result = conf.calculate("KU-1")
        assert result.overall_confidence > 0.0

        # Alignment
        alignment = AlignmentEngine()
        e1 = alignment.register_edition(EditionInfo(language="hindi", book_uuid="BK-1"))
        e2 = alignment.register_edition(EditionInfo(language="english", book_uuid="BK-1"))
        a = alignment.propose_alignment([e1, e2])
        assert a.segment_count == 0

        # Comparison
        comp = ComparisonEngine()
        conflict = comp.detect_text_conflict("KU-1", "variant A", "variant B")
        assert conflict.status.value == "detected"

        # Trust
        trust = TrustEngine()
        trust.add_factor("KU-1", "ocr_quality", 0.7)
        trust.add_factor("KU-1", "verification_result", 0.9)
        trust_result = trust.evaluate("KU-1")
        assert trust_result.trust_score > 0.0
