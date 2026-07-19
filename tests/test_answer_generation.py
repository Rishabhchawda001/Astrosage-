"""Tests for the Natural Language Answer Generator."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestAnswerGenerator:
    def test_imports(self):
        from core.answer_generation.generator import AnswerGenerator
        assert AnswerGenerator is not None

    def test_init(self):
        from core.answer_generation.generator import AnswerGenerator
        gen = AnswerGenerator()
        assert gen is not None

    def test_classify_question_who(self):
        from core.answer_generation.generator import AnswerGenerator
        gen = AnswerGenerator()
        assert gen._classify_question("Who is Vishnu?") == "who"

    def test_classify_question_what(self):
        from core.answer_generation.generator import AnswerGenerator
        gen = AnswerGenerator()
        assert gen._classify_question("What is dharma?") == "what"

    def test_classify_question_where(self):
        from core.answer_generation.generator import AnswerGenerator
        gen = AnswerGenerator()
        assert gen._classify_question("Where is Kurukshetra?") == "where"

    def test_classify_question_default(self):
        from core.answer_generation.generator import AnswerGenerator
        gen = AnswerGenerator()
        assert gen._classify_question("Tell me about yoga") == "default"

    def test_generate_basic(self):
        from core.answer_generation.generator import AnswerGenerator
        gen = AnswerGenerator()
        evidence = [
            {"scripture": "BG", "text": "Krishna speaks to Arjuna"},
            {"scripture": "MBH", "text": "Mahabharata contains the Gita"},
        ]
        entities = [
            {"name": "Krishna", "type": "Deity"},
            {"name": "Arjuna", "type": "Person"},
        ]
        answer = gen.generate("Who is Krishna?", evidence, entities)
        assert answer.question == "Who is Krishna?"
        assert len(answer.answer_text) > 0
        assert answer.confidence > 0
        assert answer.evidence_count == 2

    def test_generate_with_citations(self):
        from core.answer_generation.generator import AnswerGenerator
        gen = AnswerGenerator()
        evidence = [
            {"scripture": "BG", "chapter": "2", "verse": "47", "text": "You have the right to work only"},
        ]
        entities = [{"name": "Krishna", "type": "Deity"}]
        answer = gen.generate("What does Krishna teach?", evidence, entities)
        assert len(answer.citations) > 0
        assert answer.citations[0].scripture == "BG"

    def test_generate_empty_evidence(self):
        from core.answer_generation.generator import AnswerGenerator
        gen = AnswerGenerator()
        answer = gen.generate("Who is X?", [], [])
        assert answer.confidence == 0.0
        assert answer.evidence_count == 0

    def test_generate_multiple_entities(self):
        from core.answer_generation.generator import AnswerGenerator
        gen = AnswerGenerator()
        evidence = [{"scripture": "BG", "text": "test"}]
        entities = [
            {"name": "Krishna", "type": "Deity"},
            {"name": "Arjuna", "type": "Person"},
            {"name": "Dharma", "type": "Concept"},
        ]
        answer = gen.generate("Tell me about these entities", evidence, entities)
        assert len(answer.entities_mentioned) == 3

    def test_confidence_range(self):
        from core.answer_generation.generator import AnswerGenerator
        gen = AnswerGenerator()
        evidence = [{"scripture": "BG", "text": "test"}]
        entities = [{"name": "Krishna", "type": "Deity"}]
        answer = gen.generate("Who is Krishna?", evidence, entities)
        assert 0.0 <= answer.confidence <= 1.0

    def test_citation_structure(self):
        from core.answer_generation.generator import AnswerGenerator
        gen = AnswerGenerator()
        evidence = [
            {"scripture": "BG", "chapter": "2", "verse": "47", "text": "test snippet"},
        ]
        entities = [{"name": "Krishna", "type": "Deity"}]
        answer = gen.generate("What does Krishna say?", evidence, entities)
        assert answer.citations[0].scripture == "BG"
        assert answer.citations[0].chapter == "2"
        assert answer.citations[0].verse == "47"

    def test_provenance_tracking(self):
        from core.answer_generation.generator import AnswerGenerator
        gen = AnswerGenerator()
        evidence = [{"scripture": "BG", "text": "test"}]
        entities = [{"name": "Krishna", "type": "Deity"}]
        answer = gen.generate("Who is Krishna?", evidence, entities)
        assert "generator" in answer.provenance
        assert "question_type" in answer.provenance
        assert "scriptures_cited" in answer.provenance

    def test_extract_scriptures(self):
        from core.answer_generation.generator import AnswerGenerator
        gen = AnswerGenerator()
        evidence = [
            {"scripture": "BG"},
            {"source": "MBH"},
            {"scripture": "BG"},  # duplicate
        ]
        scriptures = gen._extract_scriptures(evidence)
        assert "BG" in scriptures
        assert "MBH" in scriptures
        assert len(scriptures) == 2
