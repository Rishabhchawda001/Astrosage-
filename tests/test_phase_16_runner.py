"""Phase 16 — Unit Execution Runner Tests."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import tempfile


class TestUnitExecutionRunner:
    def test_imports(self):
        from core.unit_execution.runner import UnitExecutionRunner, UnitExecutionConfig
        assert UnitExecutionRunner is not None

    def test_initialization(self):
        from core.unit_execution.runner import UnitExecutionRunner, UnitExecutionConfig
        with tempfile.TemporaryDirectory() as tmpdir:
            config = UnitExecutionConfig(
                checkpoint_dir=f"{tmpdir}/checkpoints",
                silver_dir=f"{tmpdir}/silver",
                bronze_dir=f"{tmpdir}/bronze")
            runner = UnitExecutionRunner(config)
            assert runner.units is not None

    def test_process_book(self):
        from core.unit_execution.runner import UnitExecutionRunner, UnitExecutionConfig
        with tempfile.TemporaryDirectory() as tmpdir:
            config = UnitExecutionConfig(
                checkpoint_dir=f"{tmpdir}/checkpoints",
                silver_dir=f"{tmpdir}/silver",
                bronze_dir=f"{tmpdir}/bronze")
            runner = UnitExecutionRunner(config)
            text = "# Chapter 1\n\nThis is the first paragraph with multiple sentences. Another sentence here.\n\nSecond paragraph here."
            result = runner.process_book("BK-001", "Test Book", text, language="english")
            assert result["units"] > 0
            assert result["book_uuid"] == "BK-001"

    def test_run_corpus(self):
        from core.unit_execution.runner import UnitExecutionRunner, UnitExecutionConfig
        with tempfile.TemporaryDirectory() as tmpdir:
            silver_dir = Path(tmpdir) / "silver"
            silver_dir.mkdir()
            bronze_dir = Path(tmpdir) / "bronze"
            bronze_dir.mkdir()
            (silver_dir / "book1.md").write_text("# Book 1\n\nContent here.\n\nMore content.")
            (silver_dir / "book2.md").write_text("# Book 2\n\nDifferent content.")
            config = UnitExecutionConfig(
                checkpoint_dir=f"{tmpdir}/checkpoints",
                silver_dir=str(silver_dir),
                bronze_dir=str(bronze_dir))
            runner = UnitExecutionRunner(config)
            results = runner.run_corpus()
            assert results["books_processed"] == 2
            assert results["units_extracted"] > 0

    def test_checkpoint_saved(self):
        from core.unit_execution.runner import UnitExecutionRunner, UnitExecutionConfig
        with tempfile.TemporaryDirectory() as tmpdir:
            silver_dir = Path(tmpdir) / "silver"
            silver_dir.mkdir()
            bronze_dir = Path(tmpdir) / "bronze"
            bronze_dir.mkdir()
            (silver_dir / "book1.md").write_text("# Book 1\nContent.")
            config = UnitExecutionConfig(
                checkpoint_dir=f"{tmpdir}/checkpoints",
                silver_dir=str(silver_dir),
                bronze_dir=str(bronze_dir))
            runner = UnitExecutionRunner(config)
            runner.run_corpus()
            checkpoints = list(Path(tmpdir, "checkpoints").glob("UE-*.json"))
            assert len(checkpoints) >= 1

    def test_detect_language(self):
        from core.unit_execution.runner import detect_language_simple
        assert detect_language_simple("This is English") == "english"
        assert detect_language_simple("") == "unknown"
        assert detect_language_simple("नमस्ते यह हिंदी पाठ है भगवद् गीता") == "hindi_sanskrit"

    def test_empty_corpus(self):
        from core.unit_execution.runner import UnitExecutionRunner, UnitExecutionConfig
        with tempfile.TemporaryDirectory() as tmpdir:
            silver_dir = Path(tmpdir) / "silver"
            silver_dir.mkdir()
            bronze_dir = Path(tmpdir) / "bronze"
            bronze_dir.mkdir()
            config = UnitExecutionConfig(
                checkpoint_dir=f"{tmpdir}/checkpoints",
                silver_dir=str(silver_dir),
                bronze_dir=str(bronze_dir))
            runner = UnitExecutionRunner(config)
            results = runner.run_corpus()
            assert results["books_processed"] == 0
