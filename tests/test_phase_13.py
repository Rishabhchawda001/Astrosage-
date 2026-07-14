"""Phase 13 — Corpus Execution Runner Tests."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestLanguageDetection:
    def test_english(self):
        from core.corpus_execution.runner import detect_language
        assert detect_language("This is English text with words.") == "english"

    def test_devanagari(self):
        from core.corpus_execution.runner import detect_language
        assert detect_language("यह हिंदी पाठ है। भगवद् गीता।") == "hindi_sanskrit"

    def test_empty(self):
        from core.corpus_execution.runner import detect_language
        assert detect_language("") == "unknown"

    def test_script(self):
        from core.corpus_execution.runner import detect_script
        assert detect_script("Hello world") == "latin"
        assert detect_script("नमस्ते दुनिया") == "devanagari"

    def test_tier(self):
        from core.corpus_execution.runner import classify_tier
        assert classify_tier("english") == "tier1_english_hindi_sanskrit"
        assert classify_tier("hindi_sanskrit") == "tier1_english_hindi_sanskrit"
        assert classify_tier("telugu") == "tier2_other_languages"


class TestExecutionEngine:
    def test_scan_corpus(self):
        from core.corpus_execution.runner import CorpusExecutionEngine
        engine = CorpusExecutionEngine()
        docs = engine.scan_corpus()
        assert len(docs) > 0
        assert all("name" in d for d in docs)

    def test_process_single(self):
        from core.corpus_execution.runner import CorpusExecutionEngine
        engine = CorpusExecutionEngine()
        docs = engine.scan_corpus()
        if docs:
            result = engine.process_document(docs[0])
            assert "gaps" in result
            assert "evidence_items" in result

    def test_execute_sample(self):
        from core.corpus_execution.runner import CorpusExecutionEngine
        engine = CorpusExecutionEngine()
        result = engine.execute(max_documents=10)
        assert result["processed"] >= 0
        assert result["total_gaps"] >= 0

    def test_full_execution(self):
        from core.corpus_execution.runner import CorpusExecutionEngine
        engine = CorpusExecutionEngine()
        result = engine.execute()
        assert result["total_documents"] > 500
        assert result["processed"] + result["skipped"] > 0
