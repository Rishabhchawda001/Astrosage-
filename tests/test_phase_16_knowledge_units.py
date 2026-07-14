"""Phase 16 — Knowledge Units Engine Tests."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestKnowledgeUnits:
    def test_imports(self):
        from core.knowledge_units.engine import KnowledgeUnitEngine, AtomicUnit, UnitType
        assert KnowledgeUnitEngine is not None

    def test_extract_units_from_text(self):
        from core.knowledge_units.engine import extract_units_from_text
        text = "This is paragraph one.\n\nThis is paragraph two.\n\nThird paragraph here."
        units = extract_units_from_text(text, book_uuid="BK-001")
        assert len(units) > 0
        assert any(u.unit_type.value == "paragraph" for u in units)

    def test_extract_sentences(self):
        from core.knowledge_units.engine import extract_units_from_text
        text = "This is a very long paragraph that contains many sentences and exceeds two hundred characters in total length. First sentence here. Second sentence here. Third sentence here. Fourth sentence follows. Fifth sentence is next. Sixth sentence concludes. Seventh sentence adds more."
        units = extract_units_from_text(text)
        sentences = [u for u in units if u.unit_type.value == "sentence"]
        assert len(sentences) >= 1

    def test_extract_words(self):
        from core.knowledge_units.engine import extract_units_from_text
        text = "The quick brown fox jumps over the lazy dog"
        units = extract_units_from_text(text)
        words = [u for u in units if u.unit_type.value == "word"]
        assert len(words) > 0

    def test_add_unit(self):
        from core.knowledge_units.engine import KnowledgeUnitEngine, AtomicUnit, UnitType
        engine = KnowledgeUnitEngine()
        unit = AtomicUnit(unit_type=UnitType.VERSE, text="Test verse", book_uuid="BK-001")
        engine.add_unit(unit)
        assert engine.count() == 1

    def test_get_by_book(self):
        from core.knowledge_units.engine import KnowledgeUnitEngine, AtomicUnit, UnitType
        engine = KnowledgeUnitEngine()
        engine.add_unit(AtomicUnit(unit_type=UnitType.WORD, text="A", book_uuid="BK-001"))
        engine.add_unit(AtomicUnit(unit_type=UnitType.WORD, text="B", book_uuid="BK-001"))
        engine.add_unit(AtomicUnit(unit_type=UnitType.WORD, text="C", book_uuid="BK-002"))
        units = engine.get_by_book("BK-001")
        assert len(units) == 2

    def test_get_by_type(self):
        from core.knowledge_units.engine import KnowledgeUnitEngine, AtomicUnit, UnitType
        engine = KnowledgeUnitEngine()
        engine.add_unit(AtomicUnit(unit_type=UnitType.VERSE, text="V1"))
        engine.add_unit(AtomicUnit(unit_type=UnitType.WORD, text="W1"))
        verses = engine.get_by_type(UnitType.VERSE)
        assert len(verses) == 1

    def test_update_status(self):
        from core.knowledge_units.engine import KnowledgeUnitEngine, AtomicUnit, UnitType, UnitStatus
        engine = KnowledgeUnitEngine()
        unit = AtomicUnit(unit_type=UnitType.SENTENCE, text="test")
        engine.add_unit(unit)
        engine.update_status(unit.unit_id, UnitStatus.VERIFIED, confidence=0.9)
        assert unit.status == UnitStatus.VERIFIED

    def test_summary(self):
        from core.knowledge_units.engine import KnowledgeUnitEngine, AtomicUnit, UnitType
        engine = KnowledgeUnitEngine()
        engine.add_unit(AtomicUnit(unit_type=UnitType.VERSE, text="V1"))
        engine.add_unit(AtomicUnit(unit_type=UnitType.WORD, text="W1"))
        s = engine.summary()
        assert s["total"] == 2
        assert "by_type" in s

    def test_children(self):
        from core.knowledge_units.engine import KnowledgeUnitEngine, AtomicUnit, UnitType
        engine = KnowledgeUnitEngine()
        parent = AtomicUnit(unit_type=UnitType.PARAGRAPH, text="parent")
        engine.add_unit(parent)
        engine.add_unit(AtomicUnit(unit_type=UnitType.SENTENCE, text="child1", parent_id=parent.unit_id))
        engine.add_unit(AtomicUnit(unit_type=UnitType.SENTENCE, text="child2", parent_id=parent.unit_id))
        children = engine.get_children(parent.unit_id)
        assert len(children) == 2

    def test_text_hash(self):
        from core.knowledge_units.engine import AtomicUnit, UnitType
        u = AtomicUnit(text="Hello World")
        assert len(u.text_hash) == 16
