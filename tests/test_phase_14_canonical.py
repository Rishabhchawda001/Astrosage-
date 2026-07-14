"""Phase 14 — Canonical Layer Tests."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import tempfile


class TestCanonical:
    def test_imports(self):
        from core.canonical.engine import CanonicalEngine, CanonicalParagraph
        assert CanonicalEngine is not None

    def test_add_paragraph(self):
        from core.canonical.engine import CanonicalEngine
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = CanonicalEngine(canonical_dir=tmpdir)
            p = engine.add_paragraph(
                knowledge_uuid="KU-001", book_uuid="BK-001",
                chapter="Chapter 1", page=1, paragraph_index=0,
                text="Test text", language="english", confidence=0.9)
            assert p.paragraph_id is not None
            assert p.knowledge_uuid == "KU-001"
            assert p.text_hash is not None

    def test_get_paragraph(self):
        from core.canonical.engine import CanonicalEngine
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = CanonicalEngine(canonical_dir=tmpdir)
            p = engine.add_paragraph(knowledge_uuid="KU-001", text="test")
            retrieved = engine.get_paragraph(p.paragraph_id)
            assert retrieved is not None
            assert retrieved.paragraph_id == p.paragraph_id

    def test_get_by_book(self):
        from core.canonical.engine import CanonicalEngine
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = CanonicalEngine(canonical_dir=tmpdir)
            engine.add_paragraph(knowledge_uuid="KU-001", book_uuid="BK-001", text="p1")
            engine.add_paragraph(knowledge_uuid="KU-002", book_uuid="BK-001", text="p2")
            engine.add_paragraph(knowledge_uuid="KU-003", book_uuid="BK-002", text="p3")
            book_paragraphs = engine.get_by_book("BK-001")
            assert len(book_paragraphs) == 2

    def test_get_by_knowledge(self):
        from core.canonical.engine import CanonicalEngine
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = CanonicalEngine(canonical_dir=tmpdir)
            engine.add_paragraph(knowledge_uuid="KU-010", text="test")
            knowledge = engine.get_by_knowledge("KU-010")
            assert len(knowledge) == 1

    def test_count(self):
        from core.canonical.engine import CanonicalEngine
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = CanonicalEngine(canonical_dir=tmpdir)
            assert engine.count() == 0
            engine.add_paragraph(knowledge_uuid="KU-001", text="test")
            assert engine.count() == 1

    def test_summary(self):
        from core.canonical.engine import CanonicalEngine
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = CanonicalEngine(canonical_dir=tmpdir)
            engine.add_paragraph(knowledge_uuid="KU-001", text="test", truth_status="accepted")
            engine.add_paragraph(knowledge_uuid="KU-002", text="test2", truth_status="pending")
            s = engine.summary()
            assert s["total_paragraphs"] == 2
            assert s["by_truth_status"]["accepted"] == 1
            assert s["by_truth_status"]["pending"] == 1

    def test_text_hash_generated(self):
        from core.canonical.engine import CanonicalParagraph
        p = CanonicalParagraph(text="Hello World")
        assert len(p.text_hash) == 16
        p2 = CanonicalParagraph(text="Hello World")
        assert p.text_hash == p2.text_hash

    def test_different_text_different_hash(self):
        from core.canonical.engine import CanonicalParagraph
        p1 = CanonicalParagraph(text="Hello World")
        p2 = CanonicalParagraph(text="Different Text")
        assert p1.text_hash != p2.text_hash

    def test_truth_status_tracking(self):
        from core.canonical.engine import CanonicalEngine
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = CanonicalEngine(canonical_dir=tmpdir)
            engine.add_paragraph(knowledge_uuid="KU-001", text="a", truth_status="accepted")
            engine.add_paragraph(knowledge_uuid="KU-002", text="b", truth_status="rejected")
            engine.add_paragraph(knowledge_uuid="KU-003", text="c", truth_status="needs_review")
            s = engine.summary()
            assert s["by_truth_status"]["accepted"] == 1
            assert s["by_truth_status"]["rejected"] == 1
            assert s["by_truth_status"]["needs_review"] == 1
