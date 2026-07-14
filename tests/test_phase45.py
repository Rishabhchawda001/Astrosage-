"""Phase 4.5 — Knowledge Recovery Infrastructure Tests."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ── Source Registry Tests ────────────────────────────────────────────────

class TestSourceRegistry:
    def test_import(self):
        from astrosage.recovery.source_registry.registry import KnowledgeSourceRegistry
        assert KnowledgeSourceRegistry is not None

    def test_default_sources_loaded(self):
        from astrosage.recovery.source_registry.registry import KnowledgeSourceRegistry
        with tempfile.TemporaryDirectory() as tmp:
            reg = KnowledgeSourceRegistry(registry_dir=tmp)
            sources = reg.list_sources()
            assert len(sources) >= 5  # Internet Archive, Open Library, Crossref, OpenAlex, Wikidata

    def test_register_source(self):
        from astrosage.recovery.source_registry.registry import (
            KnowledgeSourceRegistry, KnowledgeSource, SourceCategory, SourceTrustLevel
        )
        with tempfile.TemporaryDirectory() as tmp:
            reg = KnowledgeSourceRegistry(registry_dir=tmp)
            source = KnowledgeSource(
                source_id="src_test",
                name="Test Source",
                description="A test source",
                category=SourceCategory.CUSTOM,
                trust_level=SourceTrustLevel.MEDIUM,
            )
            sid = reg.register_source(source)
            assert sid == "src_test"
            assert reg.get_source("src_test") is not None

    def test_list_by_category(self):
        from astrosage.recovery.source_registry.registry import (
            KnowledgeSourceRegistry, SourceCategory
        )
        with tempfile.TemporaryDirectory() as tmp:
            reg = KnowledgeSourceRegistry(registry_dir=tmp)
            ia_sources = reg.list_sources(category=SourceCategory.INTERNET_ARCHIVE)
            assert len(ia_sources) >= 1

    def test_get_sources_for_recovery(self):
        from astrosage.recovery.source_registry.registry import (
            KnowledgeSourceRegistry, RecoveryMode
        )
        with tempfile.TemporaryDirectory() as tmp:
            reg = KnowledgeSourceRegistry(registry_dir=tmp)
            sources = reg.get_sources_for_recovery(RecoveryMode.TEXT_RECOVERY)
            assert len(sources) >= 1

    def test_save_and_load(self):
        from astrosage.recovery.source_registry.registry import (
            KnowledgeSourceRegistry, KnowledgeSource, SourceCategory
        )
        with tempfile.TemporaryDirectory() as tmp:
            reg = KnowledgeSourceRegistry(registry_dir=tmp)
            reg.register_source(KnowledgeSource(
                source_id="src_save_test",
                name="Save Test",
                description="Test save/load",
                category=SourceCategory.CUSTOM,
            ))
            reg.save()
            reg2 = KnowledgeSourceRegistry(registry_dir=tmp)
            assert reg2.get_source("src_save_test") is not None

    def test_summary(self):
        from astrosage.recovery.source_registry.registry import KnowledgeSourceRegistry
        with tempfile.TemporaryDirectory() as tmp:
            reg = KnowledgeSourceRegistry(registry_dir=tmp)
            summary = reg.summary()
            assert "total_sources" in summary
            assert summary["total_sources"] >= 5


# ── Trust Engine Tests ──────────────────────────────────────────────────

class TestTrustEngine:
    def test_import(self):
        from astrosage.recovery.trust_engine.engine import TrustEngine
        assert TrustEngine is not None

    def test_score_source(self):
        from astrosage.recovery.trust_engine.engine import TrustEngine
        engine = TrustEngine()
        score = engine.score_source({
            "license_verified": 0.9,
            "api_reliability": 0.8,
            "community_reputation": 0.7,
            "data_freshness": 0.6,
            "metadata_completeness": 0.5,
        })
        assert 0.0 <= score.score <= 1.0
        assert score.category.value == "source"

    def test_score_ocr(self):
        from astrosage.recovery.trust_engine.engine import TrustEngine
        engine = TrustEngine()
        score = engine.score_ocr({
            "character_confidence": 0.9,
            "word_confidence": 0.85,
            "language_model_match": 0.8,
            "layout_preservation": 0.7,
        })
        assert 0.0 <= score.score <= 1.0

    def test_compute_overall(self):
        from astrosage.recovery.trust_engine.engine import TrustEngine, TrustScore, TrustCategory
        engine = TrustEngine()
        scores = [
            TrustScore(category=TrustCategory.SOURCE, score=0.8, confidence=0.9),
            TrustScore(category=TrustCategory.OCR, score=0.7, confidence=0.8),
        ]
        overall = engine.compute_overall(scores)
        assert 0.0 <= overall.score <= 1.0
        assert overall.category.value == "overall"

    def test_recommend_action(self):
        from astrosage.recovery.trust_engine.engine import TrustEngine, TrustScore, TrustCategory
        engine = TrustEngine()
        high = TrustScore(category=TrustCategory.OVERALL, score=0.9, confidence=0.9)
        low = TrustScore(category=TrustCategory.OVERALL, score=0.3, confidence=0.5)
        assert engine.recommend_action(high) == "auto_accept"
        assert engine.recommend_action(low) == "reject"

    def test_configurable_weights(self):
        from astrosage.recovery.trust_engine.engine import TrustEngine
        engine = TrustEngine()
        # Default weights exist
        assert "character_confidence" in engine.config.ocr_weights
        assert "source_agreement" in engine.config.recovery_weights


# ── Knowledge Passport Tests ────────────────────────────────────────────

class TestKnowledgePassport:
    def test_import(self):
        from astrosage.recovery.knowledge_passport.passport import (
            KnowledgePassport, KnowledgePassportRegistry
        )
        assert KnowledgePassport is not None

    def test_create_passport(self):
        from astrosage.recovery.knowledge_passport.passport import (
            KnowledgePassportRegistry, RecoveryStatus
        )
        with tempfile.TemporaryDirectory() as tmp:
            reg = KnowledgePassportRegistry(passports_dir=tmp)
            passport = reg.create_passport("test-knowledge-uuid", "test-book-uuid")
            assert passport.passport_id.startswith("KP-")
            assert passport.recovery_status == RecoveryStatus.NOT_STARTED

    def test_add_evidence(self):
        from astrosage.recovery.knowledge_passport.passport import (
            KnowledgePassport, EvidenceSource
        )
        passport = KnowledgePassport(passport_id="KP-test", knowledge_uuid="test")
        passport.add_evidence(EvidenceSource(
            source_id="src_1",
            source_name="Test Source",
            confidence=0.8,
        ))
        assert passport.agreement_count == 1
        assert passport.total_sources_checked == 1

    def test_add_verification(self):
        from astrosage.recovery.knowledge_passport.passport import (
            KnowledgePassport, VerificationRecord
        )
        passport = KnowledgePassport(passport_id="KP-test", knowledge_uuid="test")
        passport.add_verification(VerificationRecord(
            verifier="system",
            result="verified",
            confidence=0.9,
        ))
        assert len(passport.verification_history) == 1

    def test_compute_confidence(self):
        from astrosage.recovery.knowledge_passport.passport import (
            KnowledgePassport, EvidenceSource
        )
        passport = KnowledgePassport(passport_id="KP-test", knowledge_uuid="test")
        passport.add_evidence(EvidenceSource(source_id="s1", source_name="S1", confidence=0.8))
        passport.add_evidence(EvidenceSource(source_id="s2", source_name="S2", confidence=0.9))
        confidence = passport.compute_overall_confidence()
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.5

    def test_save_and_load(self):
        from astrosage.recovery.knowledge_passport.passport import (
            KnowledgePassportRegistry, KnowledgePassport
        )
        with tempfile.TemporaryDirectory() as tmp:
            reg = KnowledgePassportRegistry(passports_dir=tmp)
            passport = reg.create_passport("test-uuid")
            passport.original_ocr = "Original text"
            passport.recovered_candidate = "Recovered text"
            reg.save_all()
            loaded = KnowledgePassport.load(Path(tmp) / f"{passport.passport_id}.json")
            assert loaded.original_ocr == "Original text"
            assert loaded.recovered_candidate == "Recovered text"


# ── Recovery Queue Tests ────────────────────────────────────────────────

class TestRecoveryQueue:
    def test_import(self):
        from astrosage.recovery.recovery_queue.queue import RecoveryQueue
        assert RecoveryQueue is not None

    def test_enqueue_and_dequeue(self):
        from astrosage.recovery.recovery_queue.queue import RecoveryQueue, Priority
        with tempfile.TemporaryDirectory() as tmp:
            q = RecoveryQueue(queue_dir=tmp)
            jid1 = q.enqueue("doc1", priority=Priority.LOW)
            jid2 = q.enqueue("doc2", priority=Priority.CRITICAL)
            job = q.dequeue()
            assert job is not None
            assert job.document_uuid == "doc2"  # Higher priority first

    def test_complete_job(self):
        from astrosage.recovery.recovery_queue.queue import RecoveryQueue, QueueStatus
        with tempfile.TemporaryDirectory() as tmp:
            q = RecoveryQueue(queue_dir=tmp)
            jid = q.enqueue("doc1")
            q.dequeue()
            q.complete_job(jid)
            job = q.get_job(jid)
            assert job.status == QueueStatus.COMPLETED

    def test_fail_job_retry(self):
        from astrosage.recovery.recovery_queue.queue import (
            RecoveryQueue, QueueStatus, FailureCategory
        )
        with tempfile.TemporaryDirectory() as tmp:
            q = RecoveryQueue(queue_dir=tmp)
            jid = q.enqueue("doc1", max_retries=3)
            q.dequeue()
            q.fail_job(jid, "error", FailureCategory.RETRYABLE)
            job = q.get_job(jid)
            assert job.status == QueueStatus.RETRYING
            assert job.retry_count == 1

    def test_fail_job_fatal(self):
        from astrosage.recovery.recovery_queue.queue import (
            RecoveryQueue, QueueStatus, FailureCategory
        )
        with tempfile.TemporaryDirectory() as tmp:
            q = RecoveryQueue(queue_dir=tmp)
            jid = q.enqueue("doc1")
            q.dequeue()
            q.fail_job(jid, "corrupted", FailureCategory.FATAL)
            job = q.get_job(jid)
            assert job.status == QueueStatus.FAILED

    def test_summary(self):
        from astrosage.recovery.recovery_queue.queue import RecoveryQueue
        with tempfile.TemporaryDirectory() as tmp:
            q = RecoveryQueue(queue_dir=tmp)
            q.enqueue("doc1")
            q.enqueue("doc2")
            summary = q.summary()
            assert summary["total_jobs"] == 2
            assert summary["pending"] == 2


# ── Review Queue Tests ──────────────────────────────────────────────────

class TestReviewQueue:
    def test_import(self):
        from astrosage.recovery.review_queue.queue import ReviewQueue
        assert ReviewQueue is not None

    def test_add_and_approve(self):
        from astrosage.recovery.review_queue.queue import (
            ReviewQueue, ReviewType, ReviewState
        )
        with tempfile.TemporaryDirectory() as tmp:
            q = ReviewQueue(queue_dir=tmp)
            item_id = q.add_item(
                review_type=ReviewType.OCR_CORRECTION,
                document_uuid="doc1",
                original_text="original",
                candidate_text="recovered",
            )
            q.approve(item_id, reviewer="human1", notes="Looks good")
            item = q.get_item(item_id)
            assert item.state == ReviewState.APPROVED
            assert item.reviewer == "human1"

    def test_reject(self):
        from astrosage.recovery.review_queue.queue import (
            ReviewQueue, ReviewType, ReviewState
        )
        with tempfile.TemporaryDirectory() as tmp:
            q = ReviewQueue(queue_dir=tmp)
            item_id = q.add_item(review_type=ReviewType.QUALITY_ISSUE, document_uuid="doc1")
            q.reject(item_id, reviewer="human1", notes="Wrong recovery")
            item = q.get_item(item_id)
            assert item.state == ReviewState.REJECTED

    def test_defer(self):
        from astrosage.recovery.review_queue.queue import (
            ReviewQueue, ReviewType, ReviewState
        )
        with tempfile.TemporaryDirectory() as tmp:
            q = ReviewQueue(queue_dir=tmp)
            item_id = q.add_item(review_type=ReviewType.CONFIDENCE_LOW, document_uuid="doc1")
            q.defer(item_id, reviewer="human1")
            item = q.get_item(item_id)
            assert item.state == ReviewState.DEFERRED

    def test_get_pending(self):
        from astrosage.recovery.review_queue.queue import ReviewQueue, ReviewType
        with tempfile.TemporaryDirectory() as tmp:
            q = ReviewQueue(queue_dir=tmp)
            q.add_item(review_type=ReviewType.OCR_CORRECTION, document_uuid="doc1", priority=5)
            q.add_item(review_type=ReviewType.OCR_CORRECTION, document_uuid="doc2", priority=1)
            pending = q.get_pending()
            assert len(pending) == 2
            assert pending[0].priority == 1  # Higher priority first


# ── Edition Registry Tests ──────────────────────────────────────────────

class TestEditionRegistry:
    def test_import(self):
        from astrosage.recovery.edition_registry.registry import EditionRegistry
        assert EditionRegistry is not None

    def test_register_edition(self):
        from astrosage.recovery.edition_registry.registry import (
            EditionRegistry, Edition, EditionType
        )
        with tempfile.TemporaryDirectory() as tmp:
            reg = EditionRegistry(registry_dir=tmp)
            edition = Edition(
                title="Bhagavad Gita",
                author="Vyasa",
                edition_type=EditionType.ORIGINAL,
                language="Sanskrit",
            )
            eid = reg.register_edition(edition)
            assert eid.startswith("ED-")
            assert reg.get_edition(eid) is not None

    def test_link_editions(self):
        from astrosage.recovery.edition_registry.registry import (
            EditionRegistry, Edition, EditionType, EditionRelationship
        )
        with tempfile.TemporaryDirectory() as tmp:
            reg = EditionRegistry(registry_dir=tmp)
            e1 = Edition(title="Bhagavad Gita", edition_type=EditionType.ORIGINAL, language="Sanskrit")
            e2 = Edition(title="Bhagavad Gita English", edition_type=EditionType.TRANSLATION, language="English")
            eid1 = reg.register_edition(e1)
            eid2 = reg.register_edition(e2)
            reg.link_editions(eid1, eid2, EditionRelationship.TRANSLATION_OF)
            related = reg.get_related_editions(eid1)
            assert len(related) == 1
            assert related[0][1] == EditionRelationship.TRANSLATION_OF

    def test_find_by_title(self):
        from astrosage.recovery.edition_registry.registry import (
            EditionRegistry, Edition, EditionType
        )
        with tempfile.TemporaryDirectory() as tmp:
            reg = EditionRegistry(registry_dir=tmp)
            reg.register_edition(Edition(title="Bhagavad Gita", edition_type=EditionType.ORIGINAL))
            reg.register_edition(Edition(title="Ramayana", edition_type=EditionType.ORIGINAL))
            found = reg.find_editions_by_title("Bhagavad")
            assert len(found) == 1

    def test_summary(self):
        from astrosage.recovery.edition_registry.registry import (
            EditionRegistry, Edition, EditionType
        )
        with tempfile.TemporaryDirectory() as tmp:
            reg = EditionRegistry(registry_dir=tmp)
            reg.register_edition(Edition(title="Book1", edition_type=EditionType.ORIGINAL))
            reg.register_edition(Edition(title="Book2", edition_type=EditionType.TRANSLATION))
            summary = reg.summary()
            assert summary["total_editions"] == 2


# ── Verification Interface Tests ────────────────────────────────────────

class TestVerificationInterface:
    def test_import(self):
        from astrosage.recovery.verification.interface import (
            VerificationInterface, DefaultVerification, VerificationInput
        )
        assert VerificationInterface is not None

    def test_default_verification_verified(self):
        from astrosage.recovery.verification.interface import (
            DefaultVerification, VerificationInput, VerificationResult
        )
        verifier = DefaultVerification()
        result = verifier.verify(VerificationInput(
            original_ocr="Hello world this is a test",
            candidate_text="Hello world this is a test",
            evidence_texts=["Hello world this is a test"],
        ))
        assert result.result == VerificationResult.VERIFIED

    def test_default_verification_no_evidence(self):
        from astrosage.recovery.verification.interface import (
            DefaultVerification, VerificationInput, VerificationResult
        )
        verifier = DefaultVerification()
        result = verifier.verify(VerificationInput(
            original_ocr="Hello",
            candidate_text="Hello",
            evidence_texts=[],
        ))
        assert result.result == VerificationResult.MANUAL_REVIEW

    def test_default_verification_rejected(self):
        from astrosage.recovery.verification.interface import (
            DefaultVerification, VerificationInput, VerificationResult
        )
        verifier = DefaultVerification()
        result = verifier.verify(VerificationInput(
            original_ocr="Completely different text here",
            candidate_text="Something else entirely",
            evidence_texts=["Evidence one", "Evidence two", "Evidence three"],
        ))
        # With very different texts, should be rejected or conflict
        assert result.result in (VerificationResult.REJECTED, VerificationResult.CONFLICT)


# ── Conflict Engine Tests ───────────────────────────────────────────────

class TestConflictEngine:
    def test_import(self):
        from astrosage.recovery.conflict_engine.engine import ConflictEngine
        assert ConflictEngine is not None

    def test_record_and_resolve(self):
        from astrosage.recovery.conflict_engine.engine import (
            ConflictEngine, Variant, ConflictSeverity
        )
        with tempfile.TemporaryDirectory() as tmp:
            engine = ConflictEngine(engine_dir=tmp)
            v1 = Variant(variant_id="v1", text="Text A", source_name="Source 1")
            v2 = Variant(variant_id="v2", text="Text B", source_name="Source 2")
            cid = engine.record_conflict(
                document_uuid="doc1",
                original_ocr="Original",
                variants=[v1, v2],
                severity=ConflictSeverity.MODERATE,
            )
            conflict = engine.get_conflict(cid)
            assert conflict is not None
            assert len(conflict.variants) == 2

            engine.resolve_conflict(cid, preferred_variant_id="v1", notes="Source 1 preferred")
            preferred = engine.get_preferred_text(cid)
            assert preferred == "Text A"

    def test_get_unresolved(self):
        from astrosage.recovery.conflict_engine.engine import (
            ConflictEngine, Variant, ConflictSeverity
        )
        with tempfile.TemporaryDirectory() as tmp:
            engine = ConflictEngine(engine_dir=tmp)
            engine.record_conflict(
                document_uuid="doc1",
                original_ocr="text",
                variants=[Variant(variant_id="v1", text="A")],
            )
            engine.record_conflict(
                document_uuid="doc2",
                original_ocr="text",
                variants=[Variant(variant_id="v2", text="B")],
            )
            engine.resolve_conflict("dummy", "v1")
            unresolved = engine.get_unresolved()
            assert len(unresolved) >= 1


# ── Confidence Engine Tests ─────────────────────────────────────────────

class TestConfidenceEngine:
    def test_import(self):
        from astrosage.recovery.confidence_engine.engine import ConfidenceEngine
        assert ConfidenceEngine is not None

    def test_create_profile_and_compute(self):
        from astrosage.recovery.confidence_engine.engine import ConfidenceEngine
        engine = ConfidenceEngine()
        profile = engine.create_profile("obj-1")
        engine.add_component(profile, "ocr", 0.9)
        engine.add_component(profile, "recovery", 0.8)
        engine.add_component(profile, "verification", 0.85)
        score = engine.compute(profile)
        assert 0.0 <= score <= 1.0
        assert score > 0.5

    def test_confidence_level(self):
        from astrosage.recovery.confidence_engine.engine import ConfidenceEngine
        engine = ConfidenceEngine()
        assert engine.get_confidence_level(0.9) == "high"
        assert engine.get_confidence_level(0.6) == "medium"
        assert engine.get_confidence_level(0.4) == "low"
        assert engine.get_confidence_level(0.1) == "very_low"

    def test_default_weights(self):
        from astrosage.recovery.confidence_engine.engine import ConfidenceEngine
        engine = ConfidenceEngine()
        assert "ocr" in engine.weights
        assert "recovery" in engine.weights
        assert "verification" in engine.weights


# ── Source Connector Tests ──────────────────────────────────────────────

class TestSourceConnectors:
    def test_import_connectors(self):
        from astrosage.recovery.source_registry.connectors import (
            InternetArchiveConnector, OpenLibraryConnector,
            CrossrefConnector, OpenAlexConnector,
        )
        assert InternetArchiveConnector is not None

    def test_connector_registry(self):
        from astrosage.recovery.source_registry.connectors import list_connectors, get_connector
        connectors = list_connectors()
        assert len(connectors) >= 4
        ia = get_connector("internet_archive")
        assert ia is not None
        assert ia.source_id() == "src_internet_archive"

    def test_connector_capabilities(self):
        from astrosage.recovery.source_registry.connectors import get_connector
        ia = get_connector("internet_archive")
        caps = ia.capabilities()
        assert len(caps) >= 2

    def test_plugin_interfaces(self):
        from plugins.recovery import RecoveryPlugin
        from plugins.verification import VerificationPlugin
        from plugins.source_connectors import SourceConnectorPlugin
        assert RecoveryPlugin is not None
        assert VerificationPlugin is not None
        assert SourceConnectorPlugin is not None


# ── Provenance Ledger Tests ─────────────────────────────────────────────

class TestProvenanceLedger:
    def test_import(self):
        from astrosage.recovery.provenance_ledger.ledger import KnowledgeProvenanceLedger
        assert KnowledgeProvenanceLedger is not None

    def test_record_entry(self):
        from astrosage.recovery.provenance_ledger.ledger import (
            KnowledgeProvenanceLedger, LedgerEntryType
        )
        with tempfile.TemporaryDirectory() as tmp:
            ledger = KnowledgeProvenanceLedger(ledger_dir=tmp)
            eid = ledger.record(
                entry_type=LedgerEntryType.OCR,
                object_id="doc-1",
                transformation="OCR extraction",
                pipeline_name="tesseract",
                pipeline_version="5.3.4",
                confidence=0.85,
            )
            assert eid.startswith("PL-")
            entry = ledger.get_entry(eid)
            assert entry is not None
            assert entry.confidence == 0.85

    def test_object_history(self):
        from astrosage.recovery.provenance_ledger.ledger import (
            KnowledgeProvenanceLedger, LedgerEntryType
        )
        with tempfile.TemporaryDirectory() as tmp:
            ledger = KnowledgeProvenanceLedger(ledger_dir=tmp)
            ledger.record(entry_type=LedgerEntryType.OCR, object_id="doc-1", transformation="OCR")
            ledger.record(entry_type=LedgerEntryType.RECOVERY, object_id="doc-1", transformation="Recovery")
            ledger.record(entry_type=LedgerEntryType.VERIFICATION, object_id="doc-1", transformation="Verify")
            history = ledger.get_object_history("doc-1")
            assert len(history) == 3

    def test_chain_trace(self):
        from astrosage.recovery.provenance_ledger.ledger import (
            KnowledgeProvenanceLedger, LedgerEntryType
        )
        with tempfile.TemporaryDirectory() as tmp:
            ledger = KnowledgeProvenanceLedger(ledger_dir=tmp)
            eid1 = ledger.record(entry_type=LedgerEntryType.OCR, object_id="doc-1", transformation="OCR")
            eid2 = ledger.record(entry_type=LedgerEntryType.RECOVERY, object_id="doc-1", transformation="Recovery", parent_entry_id=eid1)
            eid3 = ledger.record(entry_type=LedgerEntryType.VERIFICATION, object_id="doc-1", transformation="Verify", parent_entry_id=eid2)
            chain = ledger.get_chain(eid3)
            assert len(chain) == 3
            assert chain[0].entry_type == LedgerEntryType.OCR

    def test_audit_trail(self):
        from astrosage.recovery.provenance_ledger.ledger import (
            KnowledgeProvenanceLedger, LedgerEntryType
        )
        with tempfile.TemporaryDirectory() as tmp:
            ledger = KnowledgeProvenanceLedger(ledger_dir=tmp)
            ledger.record(entry_type=LedgerEntryType.OCR, object_id="doc-1", transformation="OCR")
            trail = ledger.audit_trail("doc-1")
            assert len(trail) == 1
            assert trail[0]["type"] == "ocr"

    def test_confirm_supersede_revoke(self):
        from astrosage.recovery.provenance_ledger.ledger import (
            KnowledgeProvenanceLedger, LedgerEntryType, LedgerEntryStatus
        )
        with tempfile.TemporaryDirectory() as tmp:
            ledger = KnowledgeProvenanceLedger(ledger_dir=tmp)
            eid = ledger.record(entry_type=LedgerEntryType.RECOVERY, object_id="doc-1")
            ledger.confirm(eid)
            assert ledger.get_entry(eid).status == LedgerEntryStatus.CONFIRMED
            ledger.supersede(eid)
            assert ledger.get_entry(eid).status == LedgerEntryStatus.SUPERSEDED

    def test_summary(self):
        from astrosage.recovery.provenance_ledger.ledger import (
            KnowledgeProvenanceLedger, LedgerEntryType
        )
        with tempfile.TemporaryDirectory() as tmp:
            ledger = KnowledgeProvenanceLedger(ledger_dir=tmp)
            ledger.record(entry_type=LedgerEntryType.OCR, object_id="doc-1")
            ledger.record(entry_type=LedgerEntryType.RECOVERY, object_id="doc-2")
            summary = ledger.summary()
            assert summary["total_entries"] == 2
            assert summary["unique_objects"] == 2

    def test_save_and_load(self):
        from astrosage.recovery.provenance_ledger.ledger import (
            KnowledgeProvenanceLedger, LedgerEntryType
        )
        with tempfile.TemporaryDirectory() as tmp:
            ledger = KnowledgeProvenanceLedger(ledger_dir=tmp)
            ledger.record(entry_type=LedgerEntryType.OCR, object_id="doc-1", confidence=0.9)
            ledger.save()
            ledger2 = KnowledgeProvenanceLedger(ledger_dir=tmp)
            ledger2.load()
            assert ledger2.summary()["total_entries"] == 1


# ── Integration Tests ───────────────────────────────────────────────────

class TestIntegration:
    def test_full_workflow(self):
        """Test a complete recovery workflow using all components."""
        from astrosage.recovery.source_registry.registry import KnowledgeSourceRegistry
        from astrosage.recovery.trust_engine.engine import TrustEngine
        from astrosage.recovery.knowledge_passport.passport import (
            KnowledgePassportRegistry, EvidenceSource
        )
        from astrosage.recovery.recovery_queue.queue import RecoveryQueue, Priority
        from astrosage.recovery.review_queue.queue import ReviewQueue, ReviewType
        from astrosage.recovery.edition_registry.registry import (
            EditionRegistry, Edition, EditionType, EditionRelationship
        )
        from astrosage.recovery.verification.interface import (
            DefaultVerification, VerificationInput, VerificationResult
        )
        from astrosage.recovery.conflict_engine.engine import (
            ConflictEngine, Variant, ConflictSeverity
        )
        from astrosage.recovery.confidence_engine.engine import ConfidenceEngine
        from astrosage.recovery.provenance_ledger.ledger import (
            KnowledgeProvenanceLedger, LedgerEntryType
        )

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)

            # 1. Source Registry
            src_reg = KnowledgeSourceRegistry(registry_dir=str(base / "sources"))
            assert src_reg.summary()["total_sources"] >= 5

            # 2. Trust Engine
            trust = TrustEngine()
            ocr_trust = trust.score_ocr({"character_confidence": 0.85})
            assert ocr_trust.score > 0.5

            # 3. Recovery Queue
            rq = RecoveryQueue(queue_dir=str(base / "rq"))
            jid = rq.enqueue("doc-1", priority=Priority.HIGH, reason="Low OCR confidence")
            assert rq.pending_count == 1

            # 4. Knowledge Passport
            kp_reg = KnowledgePassportRegistry(passports_dir=str(base / "kp"))
            passport = kp_reg.create_passport("doc-1", "book-1")
            passport.add_evidence(EvidenceSource(
                source_id="src_ia", source_name="Internet Archive", confidence=0.9
            ))
            passport.compute_overall_confidence()
            assert passport.confidence_score > 0.5

            # 5. Edition Registry
            ed_reg = EditionRegistry(registry_dir=str(base / "ed"))
            e1 = Edition(title="Gita", edition_type=EditionType.ORIGINAL, language="Sanskrit")
            e2 = Edition(title="Gita English", edition_type=EditionType.TRANSLATION, language="English")
            eid1 = ed_reg.register_edition(e1)
            eid2 = ed_reg.register_edition(e2)
            ed_reg.link_editions(eid1, eid2, EditionRelationship.TRANSLATION_OF)
            related = ed_reg.get_related_editions(eid1)
            assert len(related) == 1

            # 6. Verification
            verifier = DefaultVerification()
            vresult = verifier.verify(VerificationInput(
                original_ocr="Original text",
                candidate_text="Original text",
                evidence_texts=["Original text"],
            ))
            assert vresult.result == VerificationResult.VERIFIED

            # 7. Conflict Engine
            ce = ConflictEngine(engine_dir=str(base / "conflicts"))
            cid = ce.record_conflict(
                document_uuid="doc-1",
                original_ocr="Text A",
                variants=[
                    Variant(variant_id="v1", text="Text A variant 1"),
                    Variant(variant_id="v2", text="Text A variant 2"),
                ],
                severity=ConflictSeverity.MODERATE,
            )
            ce.resolve_conflict(cid, preferred_variant_id="v1")
            assert ce.get_preferred_text(cid) == "Text A variant 1"

            # 8. Confidence Engine
            ceng = ConfidenceEngine()
            profile = ceng.create_profile("doc-1")
            ceng.add_component(profile, "ocr", 0.85)
            ceng.add_component(profile, "recovery", 0.8)
            overall = ceng.compute(profile)
            assert 0.0 <= overall <= 1.0

            # 9. Provenance Ledger
            ledger = KnowledgeProvenanceLedger(ledger_dir=str(base / "ledger"))
            ledger.record(entry_type=LedgerEntryType.OCR, object_id="doc-1", confidence=0.85)
            ledger.record(entry_type=LedgerEntryType.RECOVERY, object_id="doc-1", confidence=0.9)
            assert ledger.summary()["total_entries"] == 2

            # 10. Review Queue
            rvq = ReviewQueue(queue_dir=str(base / "rv"))
            item_id = rvq.add_item(
                review_type=ReviewType.OCR_CORRECTION,
                document_uuid="doc-1",
                original_text="OCR text",
                candidate_text="Recovered text",
            )
            rvq.approve(item_id, reviewer="human1")
            assert rvq.summary()["by_state"]["approved"] == 1
