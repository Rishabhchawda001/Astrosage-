"""Phase 12 — Global Evidence Discovery Tests."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSourceDiscovery:
    def test_imports(self):
        from core.source_discovery import GlobalSourceDiscovery, ConnectorType
        assert GlobalSourceDiscovery is not None

    def test_search(self):
        from core.source_discovery.engine import GlobalSourceDiscovery, SourceConnector, ConnectorType, DiscoveryHit
        class MockConnector(SourceConnector):
            def name(self): return "mock"
            def connector_type(self): return ConnectorType.CUSTOM
            def search(self, q, max_results=10):
                return [DiscoveryHit(title=f"Result for {q}", language="english")]
            def health(self): return {"status": "ok"}
        eng = GlobalSourceDiscovery()
        eng.register_connector(MockConnector())
        hits = eng.search("Bhagavad Gita")
        assert len(hits) == 1
        assert eng.count() == 1


class TestSourceRegistry:
    def test_register(self):
        from core.source_registry import SourceRegistry, SourceEntry, SourceType
        reg = SourceRegistry()
        reg.register(SourceEntry(name="Archive.org", source_type=SourceType.DIGITAL_LIBRARY))
        assert reg.count() == 1

    def test_by_type(self):
        from core.source_registry import SourceRegistry, SourceEntry, SourceType
        reg = SourceRegistry()
        reg.register(SourceEntry(name="A", source_type=SourceType.ACADEMIC))
        assert len(reg.get_by_type(SourceType.ACADEMIC)) == 1


class TestSourceScoring:
    def test_score(self):
        from core.source_scoring import SourceScoringEngine
        eng = SourceScoringEngine()
        s = eng.score("SRC-1", publisher_reputation=0.9, academic_authority=0.8)
        assert s.trust_score > 0.0

    def test_get(self):
        from core.source_scoring import SourceScoringEngine
        eng = SourceScoringEngine()
        eng.score("SRC-1", publisher_reputation=0.5)
        assert eng.get_score("SRC-1") is not None


class TestEditionRegistry:
    def test_register(self):
        from core.edition_registry import EditionRegistry, EditionEntry
        reg = EditionRegistry()
        reg.register(EditionEntry(book_title="Bhagavad Gita", language="sanskrit", author="Vyasa"))
        assert reg.count() == 1

    def test_find(self):
        from core.edition_registry import EditionRegistry, EditionEntry
        reg = EditionRegistry()
        reg.register(EditionEntry(book_title="Bhagavad Gita", language="sanskrit"))
        reg.register(EditionEntry(book_title="Bhagavad Gita", language="hindi"))
        assert len(reg.find_by_title("Bhagavad Gita")) == 2
        assert len(reg.find_by_language("sanskrit")) == 1


class TestBookMatching:
    def test_match(self):
        from core.book_matching import BookMatchingEngine
        eng = BookMatchingEngine()
        m = eng.match("ED-1", "ED-2", title_a="Bhagavad Gita", title_b="Bhagavad Gita", author_a="Vyasa", author_b="Vyasa")
        assert m.overall_confidence > 0.0

    def test_confident(self):
        from core.book_matching import BookMatchingEngine
        eng = BookMatchingEngine(confidence_threshold=0.5)
        eng.match("ED-1", "ED-2", title_a="Same Book", title_b="Same Book", author_a="Author", author_b="Author")
        assert len(eng.get_confident_matches()) >= 1


class TestEditionMatching:
    def test_match(self):
        from core.edition_matching import EditionMatchingEngine
        eng = EditionMatchingEngine()
        m = eng.match("ED-1", "ED-2", signals={"title": 0.9, "isbn": 1.0})
        assert m.confidence > 0.0


class TestTranslationAlignment:
    def test_align(self):
        from core.translation_alignment import TranslationAlignmentEngine
        eng = TranslationAlignmentEngine()
        p = eng.align("ED-1", "ED-2", source_lang="sanskrit", target_lang="hindi", segments_aligned=100, segments_total=120)
        assert p.alignment_ratio > 0.8


class TestCommentaryAlignment:
    def test_link(self):
        from core.commentary_alignment import CommentaryAlignmentEngine
        eng = CommentaryAlignmentEngine()
        l = eng.link("BG-ED-1", "BG-COMMENTARY-1", commentator="Adi Shankara", coverage=0.9)
        assert l.confidence == 0.9


class TestReferenceAlignment:
    def test_link(self):
        from core.reference_alignment import ReferenceAlignmentEngine
        eng = ReferenceAlignmentEngine()
        l = eng.link("BG", "UPANISHADS", reference_type="vedanta", description="Cross-reference")
        assert eng.count() == 1


class TestEvidenceMerging:
    def test_merge(self):
        from core.evidence_merging import EvidenceMergingEngine
        eng = EvidenceMergingEngine()
        m = eng.merge("KU-1", primary_evidence=["EV-1"], supporting_editions=["ED-1"])
        assert m.total_evidence_count == 2

    def test_incremental_merge(self):
        from core.evidence_merging import EvidenceMergingEngine
        eng = EvidenceMergingEngine()
        eng.merge("KU-1", primary_evidence=["EV-1"])
        eng.merge("KU-1", secondary_evidence=["EV-2"])
        m = eng.get("KU-1")
        assert m.total_evidence_count == 2


class TestEvidenceRanking:
    def test_rank(self):
        from core.evidence_ranking import EvidenceRankingEngine
        eng = EvidenceRankingEngine()
        ranked = eng.rank("KU-1", [
            {"evidence_id": "EV-1", "source_trust": 0.9},
            {"evidence_id": "EV-2", "source_trust": 0.3},
        ])
        assert ranked[0].score > ranked[1].score
        assert ranked[0].rank == 1


class TestSourceCache:
    def test_put_get(self):
        from core.source_cache import SourceCache
        cache = SourceCache()
        cache.put("Bhagavad Gita", "archive", [{"title": "BG"}])
        entry = cache.get("Bhagavad Gita", "archive")
        assert entry is not None
        assert entry.hit_count == 1

    def test_invalidate(self):
        from core.source_cache import SourceCache
        cache = SourceCache()
        cache.put("test", "mock", [])
        assert cache.invalidate("test", "mock")
        assert cache.get("test", "mock") is None


class TestChangeDetection:
    def test_detect(self):
        from core.change_detection import ChangeDetectionEngine, ChangeType
        eng = ChangeDetectionEngine()
        r = eng.detect(ChangeType.NEW_EDITION, source_id="SRC-1", description="New scan found")
        assert r.change_id.startswith("CD-")

    def test_pending(self):
        from core.change_detection import ChangeDetectionEngine, ChangeType
        eng = ChangeDetectionEngine()
        eng.detect(ChangeType.NEW_EDITION)
        eng.detect(ChangeType.BETTER_OCR)
        assert len(eng.get_pending()) == 2


class TestLicense:
    def test_register(self):
        from core.license import LicenseEngine, LicenseRecord, LicenseType
        eng = LicenseEngine()
        r = LicenseRecord(source_id="SRC-1", license_type=LicenseType.PUBLIC_DOMAIN, allows_distribution=True)
        eng.register(r)
        assert eng.is_distributable("SRC-1")

    def test_violations(self):
        from core.license import LicenseEngine, LicenseRecord, LicenseStatus
        eng = LicenseEngine()
        r = LicenseRecord(source_id="SRC-1", status=LicenseStatus.VIOLATION)
        eng.register(r)
        assert len(eng.get_violations()) == 1


class TestPhase12Integration:
    def test_full_pipeline(self):
        from core.source_discovery import GlobalSourceDiscovery, SourceConnector, ConnectorType, DiscoveryHit
        from core.source_registry import SourceRegistry, SourceEntry, SourceType
        from core.source_scoring import SourceScoringEngine
        from core.edition_registry import EditionRegistry, EditionEntry
        from core.book_matching import BookMatchingEngine
        from core.translation_alignment import TranslationAlignmentEngine
        from core.commentary_alignment import CommentaryAlignmentEngine
        from core.reference_alignment import ReferenceAlignmentEngine
        from core.evidence_merging import EvidenceMergingEngine
        from core.evidence_ranking import EvidenceRankingEngine
        from core.change_detection import ChangeDetectionEngine, ChangeType
        from core.license import LicenseEngine, LicenseRecord, LicenseType

        class MockConn(SourceConnector):
            def name(self): return "mock"
            def connector_type(self): return ConnectorType.CUSTOM
            def search(self, q, max_results=10):
                return [DiscoveryHit(title="Bhagavad Gita", author="Vyasa", language="sanskrit")]
            def health(self): return {"status": "ok"}

        # Discovery
        disc = GlobalSourceDiscovery()
        disc.register_connector(MockConn())
        hits = disc.search("Bhagavad Gita")
        assert len(hits) == 1

        # Source registry
        src_reg = SourceRegistry()
        src_reg.register(SourceEntry(name="Archive.org", source_type=SourceType.DIGITAL_LIBRARY))

        # Source scoring
        scoring = SourceScoringEngine()
        scoring.score("SRC-1", publisher_reputation=0.9, academic_authority=0.8)

        # Edition registry
        ed_reg = EditionRegistry()
        ed1 = ed_reg.register(EditionEntry(book_title="Bhagavad Gita", language="sanskrit", author="Vyasa"))
        ed2 = ed_reg.register(EditionEntry(book_title="Bhagavad Gita", language="hindi", author="Vyasa", translator="Rampal"))

        # Book matching
        bm = BookMatchingEngine()
        bm.match(ed1, ed2, title_a="Bhagavad Gita", title_b="Bhagavad Gita", author_a="Vyasa", author_b="Vyasa")

        # Translation alignment
        ta = TranslationAlignmentEngine()
        ta.align(ed1, ed2, source_lang="sanskrit", target_lang="hindi", segments_aligned=500, segments_total=600)

        # Commentary alignment
        ca = CommentaryAlignmentEngine()
        ca.link(ed1, "COMMENTARY-1", commentator="Adi Shankara", coverage=0.85)

        # Reference alignment
        ra = ReferenceAlignmentEngine()
        ra.link("BG", "UPANISHADS", reference_type="vedanta")

        # Evidence merging
        em = EvidenceMergingEngine()
        em.merge("KU-1", primary_evidence=["EV-1"], supporting_editions=[ed1, ed2])

        # Evidence ranking
        er = EvidenceRankingEngine()
        er.rank("KU-1", [{"evidence_id": "EV-1", "source_trust": 0.9}, {"evidence_id": "EV-2", "source_trust": 0.4}])

        # Change detection
        cd = ChangeDetectionEngine()
        cd.detect(ChangeType.NEW_EDITION, source_id="SRC-1")

        # License
        le = LicenseEngine()
        le.register(LicenseRecord(source_id="SRC-1", license_type=LicenseType.PUBLIC_DOMAIN, allows_distribution=True))
        assert le.is_distributable("SRC-1")

        # Verify all counts
        assert disc.count() == 1
        assert src_reg.count() == 1
        assert scoring.count() == 1
        assert ed_reg.count() == 2
        assert bm.count() == 1
        assert ta.count() == 1
        assert ca.count() == 1
        assert ra.count() == 1
        assert em.count() == 1
        assert er.count() == 2
        assert cd.count() == 1
        assert le.count() == 1
