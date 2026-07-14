"""Phase 14 — Citation Management Engine Tests."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestCitation:
    def test_imports(self):
        from core.citation.engine import CitationEngine, Citation, CitationType
        assert CitationEngine is not None

    def test_add_citation(self):
        from core.citation.engine import CitationEngine, CitationType
        engine = CitationEngine()
        c = engine.add("KU-001", CitationType.PRIMARY,
                       source_title="Bhagavad Gita", source_author="Vyasa",
                       source_publisher="Gita Press", source_year="1965",
                       book_uuid="BK-001", page_reference="p.42")
        assert c.citation_id is not None
        assert c.source_title == "Bhagavad Gita"

    def test_verify_citation(self):
        from core.citation.engine import CitationEngine, CitationType, CitationStatus
        engine = CitationEngine()
        c = engine.add("KU-002", CitationType.ACADEMIC, source_title="Research Paper")
        engine.verify(c.citation_id, verified=True)
        assert engine._citations[c.citation_id].status == CitationStatus.VALID

    def test_get_by_knowledge(self):
        from core.citation.engine import CitationEngine, CitationType
        engine = CitationEngine()
        engine.add("KU-010", CitationType.PRIMARY, source_title="Book A")
        engine.add("KU-010", CitationType.CROSS_REFERENCE, source_title="Book B")
        engine.add("KU-011", CitationType.PRIMARY, source_title="Book C")
        cites = engine.get_by_knowledge("KU-010")
        assert len(cites) == 2

    def test_get_by_book(self):
        from core.citation.engine import CitationEngine, CitationType
        engine = CitationEngine()
        engine.add("KU-001", CitationType.PRIMARY, book_uuid="BK-001", source_title="A")
        engine.add("KU-002", CitationType.PRIMARY, book_uuid="BK-001", source_title="B")
        engine.add("KU-003", CitationType.PRIMARY, book_uuid="BK-002", source_title="C")
        cites = engine.get_by_book("BK-001")
        assert len(cites) == 2

    def test_get_broken(self):
        from core.citation.engine import CitationEngine, CitationType
        engine = CitationEngine()
        c1 = engine.add("KU-020", CitationType.EXTERNAL, source_title="External")
        c2 = engine.add("KU-021", CitationType.PRIMARY, source_title="Primary")
        engine.verify(c1.citation_id, verified=False)
        broken = engine.get_broken()
        assert len(broken) == 1

    def test_citation_integrity(self):
        from core.citation.engine import CitationEngine, CitationType
        engine = CitationEngine()
        c1 = engine.add("KU-030", CitationType.PRIMARY, book_uuid="BK-010")
        c2 = engine.add("KU-031", CitationType.PRIMARY, book_uuid="BK-010")
        engine.verify(c1.citation_id, verified=True)
        integrity = engine.citation_integrity("BK-010")
        assert integrity["total"] == 2
        assert integrity["verified"] == 1
        assert integrity["integrity"] == 50.0

    def test_empty_book_integrity(self):
        from core.citation.engine import CitationEngine
        engine = CitationEngine()
        integrity = engine.citation_integrity("BK-999")
        assert integrity["total"] == 0
        assert integrity["integrity"] == 0.0

    def test_summary(self):
        from core.citation.engine import CitationEngine, CitationType
        engine = CitationEngine()
        engine.add("KU-040", CitationType.PRIMARY)
        engine.add("KU-041", CitationType.ACADEMIC)
        s = engine.summary()
        assert s["total"] == 2
        assert "by_type" in s
        assert "by_status" in s

    def test_count(self):
        from core.citation.engine import CitationEngine, CitationType
        engine = CitationEngine()
        assert engine.count() == 0
        engine.add("KU-050", CitationType.COMMENTARY)
        assert engine.count() == 1

    def test_all_citation_types(self):
        from core.citation.engine import CitationEngine, CitationType
        engine = CitationEngine()
        for ct in CitationType:
            engine.add("KU-060", ct)
        assert engine.count() == len(CitationType)
