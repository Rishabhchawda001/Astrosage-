"""Benchmark tests for Query Expansion Engine — coverage of edge cases."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestQueryExpansionEdgeCases:
    def test_empty_query(self):
        from core.query_expansion.engine import QueryExpansionEngine
        engine = QueryExpansionEngine()
        engine.load()
        result = engine.expand("")
        assert result.original_query == ""
        assert isinstance(result.expanded_terms, list)

    def test_single_char_query(self):
        from core.query_expansion.engine import QueryExpansionEngine
        engine = QueryExpansionEngine()
        engine.load()
        result = engine.expand("a")
        assert result.original_query == "a"

    def test_all_stop_words(self):
        from core.query_expansion.engine import QueryExpansionEngine
        engine = QueryExpansionEngine()
        engine.load()
        result = engine.expand("what is the")
        assert result.original_query == "what is the"

    def test_entity_in_graph(self):
        from core.query_expansion.engine import QueryExpansionEngine
        engine = QueryExpansionEngine()
        engine.load()
        result = engine.expand("Vishnu Krishna Rama")
        assert len(result.expanded_terms) >= 3

    def test_expand_for_search_short(self):
        from core.query_expansion.engine import QueryExpansionEngine
        engine = QueryExpansionEngine()
        engine.load()
        expanded = engine.expand_for_search("yoga", max_terms=5)
        assert len(expanded.split()) <= 5

    def test_expand_for_search_long(self):
        from core.query_expansion.engine import QueryExpansionEngine
        engine = QueryExpansionEngine()
        engine.load()
        expanded = engine.expand_for_search("dharma karma moksha bhakti jnana")
        assert len(expanded.split()) > 5

    def test_transliteration_mapping(self):
        from core.query_expansion.engine import QueryExpansionEngine
        engine = QueryExpansionEngine()
        engine.load()
        result = engine.expand("yoga")
        assert "yoga" in result.expanded_terms

    def test_scripture_alias(self):
        from core.query_expansion.engine import QueryExpansionEngine
        engine = QueryExpansionEngine()
        engine.load()
        result = engine.expand("bhagavad gita")
        assert len(result.expanded_terms) > 0

    def test_multiple_synonym_sources(self):
        from core.query_expansion.engine import QueryExpansionEngine
        engine = QueryExpansionEngine()
        engine.load()
        result = engine.expand("dharma karma")
        total_expanded = len(result.expanded_terms)
        assert total_expanded > 2

    def test_expansion_confidence_range(self):
        from core.query_expansion.engine import QueryExpansionEngine
        engine = QueryExpansionEngine()
        engine.load()
        result = engine.expand("agni")
        assert 0.0 <= result.expansion_confidence <= 1.0

    def test_synonyms_are_lists(self):
        from core.query_expansion.engine import QueryExpansionEngine
        engine = QueryExpansionEngine()
        engine.load()
        result = engine.expand("moksha")
        for key, val in result.synonyms.items():
            assert isinstance(val, list)
            assert len(val) > 0

    def test_unicode_query(self):
        from core.query_expansion.engine import QueryExpansionEngine
        engine = QueryExpansionEngine()
        engine.load()
        result = engine.expand("ॐ नमः शिवाय")
        assert result.original_query == "ॐ नमः शिवाय"

    def test_punctuation_query(self):
        from core.query_expansion.engine import QueryExpansionEngine
        engine = QueryExpansionEngine()
        engine.load()
        result = engine.expand("What is dharma?")
        assert len(result.expanded_terms) > 0

    def test_mixed_case_query(self):
        from core.query_expansion.engine import QueryExpansionEngine
        engine = QueryExpansionEngine()
        engine.load()
        result = engine.expand("DHARMA")
        assert len(result.expanded_terms) > 0

    def test_expand_for_search_dedup(self):
        from core.query_expansion.engine import QueryExpansionEngine
        engine = QueryExpansionEngine()
        engine.load()
        expanded = engine.expand_for_search("dharma")
        terms = expanded.split()
        assert len(terms) == len(set(terms))
