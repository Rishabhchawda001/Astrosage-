"""Tests for the Query Expansion Engine."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestQueryExpansion:
    def test_imports(self):
        from core.query_expansion.engine import QueryExpansionEngine
        assert QueryExpansionEngine is not None

    def test_init_without_graph(self):
        from core.query_expansion.engine import QueryExpansionEngine
        engine = QueryExpansionEngine()
        assert engine is not None
        assert engine.sanskrit_english is not None

    def test_load_graph(self):
        from core.query_expansion.engine import QueryExpansionEngine
        engine = QueryExpansionEngine()
        engine.load()
        assert engine._loaded

    def test_sanskrit_expansion(self):
        from core.query_expansion.engine import QueryExpansionEngine
        engine = QueryExpansionEngine()
        engine.load()
        result = engine.expand("dharma")
        assert "dharma" in result.expanded_terms
        assert any("righteousness" in t for t in result.expanded_terms)
        assert result.expansion_confidence >= 0.3

    def test_hindi_expansion(self):
        from core.query_expansion.engine import QueryExpansionEngine
        engine = QueryExpansionEngine()
        engine.load()
        result = engine.expand("bhagwan")
        assert "bhagwan" in result.expanded_terms
        assert any("god" in t for t in result.expanded_terms)

    def test_multi_word_expansion(self):
        from core.query_expansion.engine import QueryExpansionEngine
        engine = QueryExpansionEngine()
        engine.load()
        result = engine.expand("bhakti yoga moksha")
        assert result.expansion_confidence > 0.5

    def test_expand_for_search(self):
        from core.query_expansion.engine import QueryExpansionEngine
        engine = QueryExpansionEngine()
        engine.load()
        expanded = engine.expand_for_search("What is dharma")
        assert "dharma" in expanded
        assert len(expanded.split()) > 2

    def test_expand_entity_query(self):
        from core.query_expansion.engine import QueryExpansionEngine
        engine = QueryExpansionEngine()
        engine.load()
        result = engine.expand("Vishnu")
        assert result.original_query == "Vishnu"

    def test_synonyms_structure(self):
        from core.query_expansion.engine import QueryExpansionEngine
        engine = QueryExpansionEngine()
        engine.load()
        result = engine.expand("karma")
        assert "karma" in result.synonyms
        assert len(result.synonyms["karma"]) > 0

    def test_semantic_variants(self):
        from core.query_expansion.engine import QueryExpansionEngine
        engine = QueryExpansionEngine()
        engine.load()
        result = engine.expand("What is Brahman")
        assert len(result.semantic_variants) > 0

    def test_no_unknown_word(self):
        from core.query_expansion.engine import QueryExpansionEngine
        engine = QueryExpansionEngine()
        engine.load()
        result = engine.expand("zxyzabc")
        assert len(result.expanded_terms) == 1
