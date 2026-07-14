"""Phase 14.5 — Recovery Execution Runner Tests."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import tempfile


class TestRecoveryRunner:
    def test_imports(self):
        from core.recovery_execution.runner import RecoveryRunner, RecoveryConfig
        assert RecoveryRunner is not None

    def test_initialization(self):
        from core.recovery_execution.runner import RecoveryRunner, RecoveryConfig
        with tempfile.TemporaryDirectory() as tmpdir:
            config = RecoveryConfig(
                checkpoint_dir=f"{tmpdir}/checkpoints",
                silver_dir=f"{tmpdir}/silver",
                bronze_dir=f"{tmpdir}/bronze")
            runner = RecoveryRunner(config)
            assert runner.recovery is not None
            assert runner.passports is not None

    def test_scan_empty_corpus(self):
        from core.recovery_execution.runner import RecoveryRunner, RecoveryConfig
        with tempfile.TemporaryDirectory() as tmpdir:
            silver_dir = Path(tmpdir) / "silver"
            silver_dir.mkdir()
            bronze_dir = Path(tmpdir) / "bronze"
            bronze_dir.mkdir()
            config = RecoveryConfig(
                checkpoint_dir=f"{tmpdir}/checkpoints",
                silver_dir=str(silver_dir),
                bronze_dir=str(bronze_dir))
            runner = RecoveryRunner(config)
            analyses = runner.scan_corpus()
            assert len(analyses) == 0

    def test_scan_corpus(self):
        from core.recovery_execution.runner import RecoveryRunner, RecoveryConfig
        with tempfile.TemporaryDirectory() as tmpdir:
            silver_dir = Path(tmpdir) / "silver"
            silver_dir.mkdir()
            bronze_dir = Path(tmpdir) / "bronze"
            bronze_dir.mkdir()
            (silver_dir / "book1.md").write_text("# Book 1\n\nContent here.\n\nMore content.")
            (silver_dir / "book2.md").write_text("# Book 2\n\nDifferent content.")
            config = RecoveryConfig(
                checkpoint_dir=f"{tmpdir}/checkpoints",
                silver_dir=str(silver_dir),
                bronze_dir=str(bronze_dir))
            runner = RecoveryRunner(config)
            analyses = runner.scan_corpus()
            assert len(analyses) == 2

    def test_process_book(self):
        from core.recovery_execution.runner import RecoveryRunner, RecoveryConfig, BookAnalysis
        with tempfile.TemporaryDirectory() as tmpdir:
            config = RecoveryConfig(
                checkpoint_dir=f"{tmpdir}/checkpoints",
                silver_dir=f"{tmpdir}/silver",
                bronze_dir=f"{tmpdir}/bronze")
            runner = RecoveryRunner(config)
            analysis = BookAnalysis(
                book_uuid="BK-001", title="Test Book",
                paragraph_count=10, confidence_estimate=0.85,
                language="english")
            result = runner.process_book(analysis)
            assert result["status"] == "processed"
            assert result["passports"] == 1
            assert result["versions"] == 1

    def test_run_corpus(self):
        from core.recovery_execution.runner import RecoveryRunner, RecoveryConfig
        with tempfile.TemporaryDirectory() as tmpdir:
            silver_dir = Path(tmpdir) / "silver"
            silver_dir.mkdir()
            bronze_dir = Path(tmpdir) / "bronze"
            bronze_dir.mkdir()
            (silver_dir / "book1.md").write_text("# Book 1\n\nContent.")
            (silver_dir / "book2.md").write_text("# Book 2\n\nMore content.")
            config = RecoveryConfig(
                checkpoint_dir=f"{tmpdir}/checkpoints",
                silver_dir=str(silver_dir),
                bronze_dir=str(bronze_dir))
            runner = RecoveryRunner(config)
            results = runner.run_corpus()
            assert results["processed"] == 2
            assert results["scanned"] == 2

    def test_checkpoint_saved(self):
        from core.recovery_execution.runner import RecoveryRunner, RecoveryConfig
        with tempfile.TemporaryDirectory() as tmpdir:
            silver_dir = Path(tmpdir) / "silver"
            silver_dir.mkdir()
            bronze_dir = Path(tmpdir) / "bronze"
            bronze_dir.mkdir()
            (silver_dir / "book1.md").write_text("# Book 1\nContent.")
            config = RecoveryConfig(
                checkpoint_dir=f"{tmpdir}/checkpoints",
                silver_dir=str(silver_dir),
                bronze_dir=str(bronze_dir))
            runner = RecoveryRunner(config)
            runner.run_corpus()
            cp_dir = Path(tmpdir) / "checkpoints"
            checkpoints = list(cp_dir.glob("RC-*.json"))
            assert len(checkpoints) >= 1

    def test_detect_language(self):
        from core.recovery_execution.runner import detect_language_simple
        assert detect_language_simple("This is English text") == "english"
        assert detect_language_simple("") == "unknown"
        assert detect_language_simple("नमस्ते दुनिया यह हिंदी पाठ है") == "hindi_sanskrit"

    def test_estimate_paragraphs(self):
        from core.recovery_execution.runner import estimate_paragraph_count
        assert estimate_paragraph_count("") == 0
        assert estimate_paragraph_count("single paragraph") == 1
        assert estimate_paragraph_count("para1\n\npara2\n\npara3") == 3
