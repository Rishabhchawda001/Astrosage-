"""Phase 11 — Corpus Gap Analysis & Evidence Discovery Tests."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestGapEngine:
    def test_imports(self):
        from core.corpus.gaps import CorpusGapEngine, GapType, GapSeverity
        assert CorpusGapEngine is not None

    def test_detect_gap(self):
        from core.corpus.gaps import CorpusGapEngine, GapType, GapSeverity
        engine = CorpusGapEngine()
        gap = engine.detect_gap(gap_type=GapType.MISSING_VERSE, severity=GapSeverity.HIGH, book_uuid="BK-1")
        assert gap.gap_id.startswith("GA-")
        assert engine.count() == 1

    def test_scan_empty(self):
        from core.corpus.gaps import CorpusGapEngine
        engine = CorpusGapEngine()
        gaps = engine.scan_empty_content("", book_uuid="BK-1")
        assert len(gaps) == 1

    def test_scan_encoding(self):
        from core.corpus.gaps import CorpusGapEngine
        engine = CorpusGapEngine()
        gaps = engine.scan_encoding("Hello \ufffd world")
        assert len(gaps) == 1

    def test_scan_low_confidence(self):
        from core.corpus.gaps import CorpusGapEngine
        engine = CorpusGapEngine()
        gaps = engine.scan_low_confidence("text", 0.3)
        assert len(gaps) == 1

    def test_scan_document(self):
        from core.corpus.gaps import CorpusGapEngine
        engine = CorpusGapEngine()
        gaps = engine.scan_document("", book_uuid="BK-1", ocr_confidence=0.2)
        assert len(gaps) >= 2

    def test_by_severity(self):
        from core.corpus.gaps import CorpusGapEngine, GapType, GapSeverity
        engine = CorpusGapEngine()
        engine.detect_gap(gap_type=GapType.MISSING_VERSE, severity=GapSeverity.CRITICAL)
        engine.detect_gap(gap_type=GapType.BROKEN_OCR, severity=GapSeverity.LOW)
        assert len(engine.get_gaps_by_severity(GapSeverity.CRITICAL)) == 1

    def test_summary(self):
        from core.corpus.gaps import CorpusGapEngine, GapType, GapSeverity
        engine = CorpusGapEngine()
        engine.detect_gap(gap_type=GapType.MISSING_PAGE, severity=GapSeverity.HIGH, book_uuid="BK-1")
        s = engine.summary()
        assert s["total_gaps"] == 1
        assert s["books_affected"] == 1


class TestRecoveryQueue:
    def test_imports(self):
        from core.corpus.recovery_queue import RecoveryQueue, RecoveryJob, RecoveryPriority
        assert RecoveryQueue is not None

    def test_enqueue_from_gap(self):
        from core.corpus.recovery_queue import RecoveryQueue
        from core.corpus.gaps import Gap, GapType, GapSeverity
        queue = RecoveryQueue()
        gap = Gap(gap_type=GapType.MISSING_VERSE, severity=GapSeverity.HIGH, book_uuid="BK-1")
        job = queue.enqueue_from_gap(gap, source_count=3)
        assert job.priority.value == "high"
        assert queue.size() == 1

    def test_dequeue_order(self):
        from core.corpus.recovery_queue import RecoveryQueue
        from core.corpus.gaps import Gap, GapType, GapSeverity
        queue = RecoveryQueue()
        queue.enqueue_from_gap(Gap(gap_type=GapType.MISSING_PAGE, severity=GapSeverity.LOW))
        queue.enqueue_from_gap(Gap(gap_type=GapType.MISSING_VERSE, severity=GapSeverity.CRITICAL))
        job = queue.dequeue()
        assert job.priority.value == "critical"

    def test_retry(self):
        from core.corpus.recovery_queue import RecoveryQueue, RecoveryJob
        queue = RecoveryQueue()
        job = RecoveryJob(job_id="RJ-1")
        queue.enqueue(job)
        queue.dequeue()
        queue.complete("RJ-1", success=False)
        assert queue.retry("RJ-1")

    def test_summary(self):
        from core.corpus.recovery_queue import RecoveryQueue
        queue = RecoveryQueue()
        assert queue.summary()["total_jobs"] == 0


class TestSourceRegistry:
    def test_imports(self):
        from core.corpus.sources import SourceRegistry, SourceRecord, SourceCategory
        assert SourceRegistry is not None

    def test_register(self):
        from core.corpus.sources import SourceRegistry, SourceRecord, SourceCategory
        reg = SourceRegistry()
        reg.register_source(SourceRecord(name="Archive", category=SourceCategory.DIGITAL_LIBRARY))
        assert reg.count() == 1

    def test_by_category(self):
        from core.corpus.sources import SourceRegistry, SourceRecord, SourceCategory
        reg = SourceRegistry()
        reg.register_source(SourceRecord(name="A", category=SourceCategory.DIGITAL_LIBRARY))
        reg.register_source(SourceRecord(name="B", category=SourceCategory.ACADEMIC))
        assert len(reg.get_by_category(SourceCategory.DIGITAL_LIBRARY)) == 1


class TestTrustEngine:
    def test_imports(self):
        from core.corpus.trust import CorpusSourceTrustEngine
        assert CorpusSourceTrustEngine is not None

    def test_evaluate(self):
        from core.corpus.trust import CorpusSourceTrustEngine
        engine = CorpusSourceTrustEngine()
        record = engine.evaluate("SRC-1", authority=0.9, authenticity=0.8)
        assert record.trust_score > 0.0

    def test_summary(self):
        from core.corpus.trust import CorpusSourceTrustEngine
        engine = CorpusSourceTrustEngine()
        engine.evaluate("SRC-1", authority=0.5)
        assert engine.summary()["total"] == 1


class TestComparisonEngine:
    def test_imports(self):
        from core.corpus.comparison import CorpusComparisonEngine
        assert CorpusComparisonEngine is not None

    def test_compare_identical(self):
        from core.corpus.comparison import CorpusComparisonEngine
        engine = CorpusComparisonEngine()
        r = engine.compare_texts("Hello world", "Hello world")
        assert r.similarity == 1.0

    def test_compare_different(self):
        from core.corpus.comparison import CorpusComparisonEngine
        engine = CorpusComparisonEngine()
        r = engine.compare_texts("completely different text", "nothing alike at all")
        assert r.similarity < 1.0


class TestAlignmentEngine:
    def test_imports(self):
        from core.corpus.alignment import CorpusAlignmentEngine
        assert CorpusAlignmentEngine is not None

    def test_propose(self):
        from core.corpus.alignment import CorpusAlignmentEngine
        engine = CorpusAlignmentEngine()
        a = engine.propose(["ED-1", "ED-2"])
        assert a.alignment_id.startswith("EA-")

    def test_add_segment(self):
        from core.corpus.alignment import CorpusAlignmentEngine, CorpusAlignmentSegment
        engine = CorpusAlignmentEngine()
        a = engine.propose(["ED-1", "ED-2"])
        engine.add_segment(a.alignment_id, CorpusAlignmentSegment(text_a="Hindi", text_b="English"))
        assert a.segment_count == 1


class TestVerificationEngine:
    def test_imports(self):
        from core.corpus.verification import CorpusTruthVerificationEngine
        assert CorpusTruthVerificationEngine is not None

    def test_verify(self):
        from core.corpus.verification import CorpusTruthVerificationEngine, CorpusVerificationStage
        engine = CorpusTruthVerificationEngine()
        r = engine.verify("KU-1", CorpusVerificationStage.EVIDENCE, passed=True)
        assert r.status.value == "passed"

    def test_is_verified(self):
        from core.corpus.verification import CorpusTruthVerificationEngine, CorpusVerificationStage
        engine = CorpusTruthVerificationEngine()
        engine.verify("KU-1", CorpusVerificationStage.EVIDENCE, passed=True)
        engine.verify("KU-1", CorpusVerificationStage.CHECKSUM, passed=True)
        assert engine.is_verified("KU-1")


class TestReconstructionEngine:
    def test_imports(self):
        from core.corpus.reconstruction import ReconstructionEngine
        assert ReconstructionEngine is not None

    def test_create_candidate(self):
        from core.corpus.reconstruction import ReconstructionEngine
        engine = ReconstructionEngine()
        c = engine.create_candidate(gap_id="GA-1", original_text="", recovered_text="recovered", confidence=0.7)
        assert c.requires_human_review is True

    def test_approve_reject(self):
        from core.corpus.reconstruction import ReconstructionEngine
        engine = ReconstructionEngine()
        c = engine.create_candidate(gap_id="GA-1", original_text="", recovered_text="text")
        engine.approve(c.candidate_id)
        assert c.status.value == "approved"
        engine.reject(c.candidate_id, reason="wrong")
        assert c.status.value == "rejected"


class TestProvenance:
    def test_imports(self):
        from core.corpus.provenance import CorpusProvenanceLedger
        assert CorpusProvenanceLedger is not None

    def test_record(self):
        from core.corpus.provenance import CorpusProvenanceLedger
        ledger = CorpusProvenanceLedger()
        ledger.record("KU-1", "gap_detect")
        assert ledger.count() == 1

    def test_lineage(self):
        from core.corpus.provenance import CorpusProvenanceLedger
        ledger = CorpusProvenanceLedger()
        ledger.record("KU-1", "gap_detect")
        ledger.record("KU-1", "evidence_collect")
        ledger.record("KU-1", "verify")
        assert len(ledger.get_lineage("KU-1")) == 3
        assert ledger.verify_integrity("KU-1")


class TestConflictEngine:
    def test_imports(self):
        from core.corpus.conflicts import ConflictEngine, ConflictType
        assert ConflictEngine is not None

    def test_detect(self):
        from core.corpus.conflicts import ConflictEngine, ConflictType
        engine = ConflictEngine()
        c = engine.detect(ConflictType.WORDING, "A", "B")
        assert c.conflict_id.startswith("CF-")

    def test_unresolved(self):
        from core.corpus.conflicts import ConflictEngine, ConflictType
        engine = ConflictEngine()
        engine.detect(ConflictType.WORDING, "A", "B")
        assert len(engine.get_unresolved()) == 1


class TestEvidenceEngine:
    def test_imports(self):
        from core.corpus.evidence import CorpusEvidenceEngine
        assert CorpusEvidenceEngine is not None

    def test_submit(self):
        from core.corpus.evidence import CorpusEvidenceEngine, CorpusEvidenceItem
        engine = CorpusEvidenceEngine()
        engine.submit(CorpusEvidenceItem(content="test"))
        assert engine.count() == 1

    def test_dedup(self):
        from core.corpus.evidence import CorpusEvidenceEngine, CorpusEvidenceItem
        engine = CorpusEvidenceEngine()
        engine.submit(CorpusEvidenceItem(content="same"))
        engine.submit(CorpusEvidenceItem(content="same"))
        engine.submit(CorpusEvidenceItem(content="different"))
        removed = engine.deduplicate()
        assert removed == 1


class TestDiscoveryEngine:
    def test_imports(self):
        from core.corpus.discovery import DiscoveryEngine
        assert DiscoveryEngine is not None

    def test_create_request(self):
        from core.corpus.discovery import DiscoveryEngine
        engine = DiscoveryEngine()
        req = engine.create_request(query="Bhagavad Gita")
        assert req.request_id.startswith("DR-")


class TestPhase11Integration:
    def test_full_pipeline(self):
        from core.corpus.gaps import CorpusGapEngine, GapType, GapSeverity
        from core.corpus.recovery_queue import RecoveryQueue
        from core.corpus.sources import SourceRegistry, SourceRecord, SourceCategory
        from core.corpus.trust import CorpusSourceTrustEngine
        from core.corpus.comparison import CorpusComparisonEngine
        from core.corpus.alignment import CorpusAlignmentEngine
        from core.corpus.verification import CorpusTruthVerificationEngine, CorpusVerificationStage
        from core.corpus.reconstruction import ReconstructionEngine
        from core.corpus.provenance import CorpusProvenanceLedger
        from core.corpus.conflicts import ConflictEngine, ConflictType
        from core.corpus.evidence import CorpusEvidenceEngine, CorpusEvidenceItem
        from core.corpus.discovery import DiscoveryEngine

        gaps = CorpusGapEngine()
        gap = gaps.detect_gap(gap_type=GapType.MISSING_VERSE, severity=GapSeverity.HIGH, book_uuid="BK-1")
        gaps.scan_empty_content("", book_uuid="BK-1")
        assert gaps.count() == 2

        queue = RecoveryQueue()
        queue.enqueue_from_gap(gap, source_count=2)
        assert queue.size() == 1

        src_reg = SourceRegistry()
        src_reg.register_source(SourceRecord(name="Archive", category=SourceCategory.DIGITAL_LIBRARY))
        assert src_reg.count() == 1

        trust = CorpusSourceTrustEngine()
        trust.evaluate("SRC-1", authority=0.9)

        comp = CorpusComparisonEngine()
        comp.compare_texts("verse A", "verse B")
        assert comp.count() == 1

        align = CorpusAlignmentEngine()
        align.propose(["ED-1", "ED-2"])

        verify = CorpusTruthVerificationEngine()
        verify.verify("KU-1", CorpusVerificationStage.EVIDENCE, passed=True)
        assert verify.is_verified("KU-1")

        recon = ReconstructionEngine()
        c = recon.create_candidate(gap_id=gap.gap_id, original_text="", recovered_text="recovered", confidence=0.7)
        assert c.requires_human_review

        ledger = CorpusProvenanceLedger()
        ledger.record("KU-1", "gap_detect")
        ledger.record("KU-1", "verify")
        assert ledger.verify_integrity("KU-1")

        conflicts = ConflictEngine()
        conflicts.detect(ConflictType.WORDING, "A", "B", knowledge_uuid="KU-1")
        assert len(conflicts.get_unresolved()) == 1

        evidence = CorpusEvidenceEngine()
        evidence.submit(CorpusEvidenceItem(content="support"))
        assert evidence.count() == 1

        discovery = DiscoveryEngine(src_reg)
        discovery.create_request(query="test")
        assert discovery.count_requests() == 1
