"""Phase 14 — Truth Execution Runner Tests."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import tempfile


class TestTruthRunner:
    def test_imports(self):
        from core.truth_execution.runner import TruthRunner, CorpusDocument
        assert TruthRunner is not None

    def test_initialization(self):
        from core.truth_execution.runner import TruthRunner
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TruthRunner(checkpoint_dir=f"{tmpdir}/checkpoints",
                                 canonical_dir=f"{tmpdir}/canonical")
            assert runner.truth_engine is not None
            assert runner.reconstruction_engine is not None
            assert runner.canonical_engine is not None

    def test_load_documents_empty(self):
        from core.truth_execution.runner import TruthRunner
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TruthRunner(checkpoint_dir=f"{tmpdir}/checkpoints",
                                 canonical_dir=f"{tmpdir}/canonical")
            count = runner.load_documents(corpus_dir=f"{tmpdir}/empty")
            assert count == 0

    def test_load_documents(self):
        from core.truth_execution.runner import TruthRunner
        with tempfile.TemporaryDirectory() as tmpdir:
            corpus_dir = Path(tmpdir) / "corpus"
            corpus_dir.mkdir()
            (corpus_dir / "book1.md").write_text("# Book 1\nContent")
            (corpus_dir / "book2.md").write_text("# Book 2\nContent")
            runner = TruthRunner(checkpoint_dir=f"{tmpdir}/checkpoints",
                                 canonical_dir=f"{tmpdir}/canonical")
            count = runner.load_documents(corpus_dir=str(corpus_dir))
            assert count == 2

    def test_load_gaps_empty(self):
        from core.truth_execution.runner import TruthRunner
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TruthRunner(checkpoint_dir=f"{tmpdir}/checkpoints",
                                 canonical_dir=f"{tmpdir}/canonical")
            count = runner.load_gaps(gap_file=f"{tmpdir}/nonexistent.json")
            assert count == 0

    def test_load_gaps(self):
        from core.truth_execution.runner import TruthRunner
        import json
        with tempfile.TemporaryDirectory() as tmpdir:
            gap_file = Path(tmpdir) / "gaps.json"
            gap_file.write_text(json.dumps({"gaps": [{"type": "missing_page"}, {"type": "broken_ocr"}]}))
            runner = TruthRunner(checkpoint_dir=f"{tmpdir}/checkpoints",
                                 canonical_dir=f"{tmpdir}/canonical")
            count = runner.load_gaps(gap_file=str(gap_file))
            assert count == 2

    def test_process_document(self):
        from core.truth_execution.runner import TruthRunner, CorpusDocument
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TruthRunner(checkpoint_dir=f"{tmpdir}/checkpoints",
                                 canonical_dir=f"{tmpdir}/canonical")
            doc = CorpusDocument(doc_id="DOC-001", book_uuid="BK-001",
                                 title="Test Book", paragraph_count=5, gap_count=2,
                                 confidence_sum=4.0)
            result = runner.process_document(doc)
            assert result["doc_id"] == "DOC-001"
            assert result["verdicts"] >= 1

    def test_run_corpus(self):
        from core.truth_execution.runner import TruthRunner
        with tempfile.TemporaryDirectory() as tmpdir:
            corpus_dir = Path(tmpdir) / "corpus"
            corpus_dir.mkdir()
            (corpus_dir / "book1.md").write_text("# Book 1\nContent")
            (corpus_dir / "book2.md").write_text("# Book 2\nMore content")
            runner = TruthRunner(checkpoint_dir=f"{tmpdir}/checkpoints",
                                 canonical_dir=f"{tmpdir}/canonical")
            results = runner.run_corpus(corpus_dir=str(corpus_dir),
                                        gap_file=f"{tmpdir}/nonexistent.json")
            assert results["processed"] == 2
            assert results["documents"] == 2

    def test_summary(self):
        from core.truth_execution.runner import TruthRunner
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TruthRunner(checkpoint_dir=f"{tmpdir}/checkpoints",
                                 canonical_dir=f"{tmpdir}/canonical")
            s = runner.summary()
            assert "documents" in s
            assert "truth_engine" in s
            assert "reconstruction" in s
            assert "canonical" in s
            assert "review" in s
            assert "quality" in s
            assert "conflicts" in s
            assert "citations" in s
            assert "checkpoints" in s

    def test_checkpoint_saved(self):
        from core.truth_execution.runner import TruthRunner
        with tempfile.TemporaryDirectory() as tmpdir:
            corpus_dir = Path(tmpdir) / "corpus"
            corpus_dir.mkdir()
            (corpus_dir / "book1.md").write_text("# Book 1\nContent")
            runner = TruthRunner(checkpoint_dir=f"{tmpdir}/checkpoints",
                                 canonical_dir=f"{tmpdir}/canonical")
            runner.run_corpus(corpus_dir=str(corpus_dir),
                              gap_file=f"{tmpdir}/nonexistent.json")
            cp_dir = Path(tmpdir) / "checkpoints"
            checkpoints = list(cp_dir.glob("TC-*.json"))
            assert len(checkpoints) == 1

    def test_corpus_document_fields(self):
        from core.truth_execution.runner import CorpusDocument
        doc = CorpusDocument(doc_id="DOC-100", book_uuid="BK-100",
                             title="Test", language="hindi", page_count=50,
                             paragraph_count=200, gap_count=10)
        assert doc.language == "hindi"
        assert doc.page_count == 50
