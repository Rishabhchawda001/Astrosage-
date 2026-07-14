"""Phase 10 — Semantic Chunking Engine Tests."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


# ── Chunk Model Tests ─────────────────────────────────────────────────

class TestChunkModel:
    def test_imports(self):
        from core.chunking import Chunk, ChunkType, ChunkBoundaryStrategy, ChunkingConfig, ChunkingEngine
        assert Chunk is not None

    def test_chunk_creation(self):
        from core.chunking.engine import Chunk, ChunkType
        c = Chunk(text="Hello world", chunk_type=ChunkType.PARAGRAPH, language="english")
        assert c.chunk_id.startswith("CH-")
        assert c.word_count == 2
        assert c.char_count == 11

    def test_chunk_types(self):
        from core.chunking.engine import ChunkType
        assert ChunkType.VERSE.value == "verse"
        assert ChunkType.COMMENTARY.value == "commentary"
        assert ChunkType.KNOWLEDGE_UNIT.value == "knowledge_unit"
        assert len(ChunkType) == 18

    def test_chunk_hierarchy(self):
        from core.chunking.engine import Chunk
        parent = Chunk(text="Chapter 1", chunk_type="chapter")
        child = Chunk(text="Verse 1", chunk_type="verse", parent_id=parent.chunk_id)
        parent.add_child(child.chunk_id)
        assert parent.child_ids == [child.chunk_id]
        assert not parent.is_leaf
        assert child.is_leaf

    def test_chunk_to_dict(self):
        from core.chunking.engine import Chunk
        c = Chunk(text="Test", language="hindi")
        d = c.to_dict()
        assert "chunk_id" in d
        assert d["language"] == "hindi"

    def test_chunk_depth(self):
        from core.chunking.engine import Chunk
        c = Chunk(text="Deep", ancestor_ids=["a1", "a2", "a3"])
        assert c.depth == 3


# ── Chunking Engine Tests ─────────────────────────────────────────────

class TestChunkingEngine:
    def test_create_chunk(self):
        from core.chunking.engine import ChunkingEngine, ChunkType
        engine = ChunkingEngine()
        c = engine.create_chunk(text="Test", chunk_type=ChunkType.PARAGRAPH)
        assert engine.count() == 1
        assert engine.get_chunk(c.chunk_id) is not None

    def test_hierarchical_chunking(self):
        from core.chunking.engine import ChunkingEngine, ChunkType
        engine = ChunkingEngine()
        book = engine.create_hierarchical_chunk(text="Book", chunk_type=ChunkType.BOOK)
        chapter = engine.create_hierarchical_chunk(
            text="Chapter 1", chunk_type=ChunkType.CHAPTER,
            parent_id=book.chunk_id
        )
        verse = engine.create_hierarchical_chunk(
            text="Verse 1", chunk_type=ChunkType.VERSE,
            parent_id=chapter.chunk_id
        )
        assert verse.parent_id == chapter.chunk_id
        assert chapter.chunk_id in book.child_ids
        assert len(verse.ancestor_ids) == 2
        assert verse.hierarchy_path.endswith("chapter/verse")

    def test_split_by_hierarchy(self):
        from core.chunking.engine import ChunkingEngine
        engine = ChunkingEngine()
        docs = [
            {"text": "Chapter 1", "type": "chapter"},
            {"text": "Verse 1 text", "type": "verse"},
            {"text": "Verse 2 text", "type": "verse"},
        ]
        chunks = engine.split_by_hierarchy(docs)
        assert len(chunks) == 3
        assert engine.count() == 3

    def test_split_by_verses(self):
        from core.chunking.engine import ChunkingEngine
        engine = ChunkingEngine()
        text = "Verse one। Verse two। Verse three।"
        chunks = engine.split_by_verses(text, language="hindi")
        assert len(chunks) >= 2

    def test_get_by_type(self):
        from core.chunking.engine import ChunkingEngine, ChunkType
        engine = ChunkingEngine()
        engine.create_chunk(text="v1", chunk_type=ChunkType.VERSE)
        engine.create_chunk(text="v2", chunk_type=ChunkType.VERSE)
        engine.create_chunk(text="p1", chunk_type=ChunkType.PARAGRAPH)
        verses = engine.get_by_type(ChunkType.VERSE)
        assert len(verses) == 2

    def test_get_by_language(self):
        from core.chunking.engine import ChunkingEngine
        engine = ChunkingEngine()
        engine.create_chunk(text="Hindi text", language="hindi")
        engine.create_chunk(text="English text", language="english")
        assert len(engine.get_by_language("hindi")) == 1

    def test_get_by_book(self):
        from core.chunking.engine import ChunkingEngine
        engine = ChunkingEngine()
        engine.create_chunk(text="A", book_id="BK-1")
        engine.create_chunk(text="B", book_id="BK-1")
        engine.create_chunk(text="C", book_id="BK-2")
        assert len(engine.get_by_book("BK-1")) == 2

    def test_get_children_and_ancestors(self):
        from core.chunking.engine import ChunkingEngine, ChunkType
        engine = ChunkingEngine()
        root = engine.create_hierarchical_chunk(text="Root", chunk_type=ChunkType.BOOK)
        child = engine.create_hierarchical_chunk(text="Child", chunk_type=ChunkType.CHAPTER, parent_id=root.chunk_id)
        grandchild = engine.create_hierarchical_chunk(text="Grandchild", chunk_type=ChunkType.VERSE, parent_id=child.chunk_id)
        assert len(engine.get_children(root.chunk_id)) == 1
        assert len(engine.get_ancestors(grandchild.chunk_id)) == 2
        assert len(engine.get_descendants(root.chunk_id)) == 2

    def test_summary(self):
        from core.chunking.engine import ChunkingEngine, ChunkType
        engine = ChunkingEngine()
        engine.create_chunk(text="A", chunk_type=ChunkType.VERSE, language="hindi")
        engine.create_chunk(text="B", chunk_type=ChunkType.PARAGRAPH, language="english")
        s = engine.summary()
        assert s["total_chunks"] == 2


# ── Chunk Models Tests ────────────────────────────────────────────────

class TestChunkModels:
    def test_chunk_metadata(self):
        from core.chunks.models import ChunkMetadata
        m = ChunkMetadata(chunk_id="CH-1", source_file="test.pdf", ocr_confidence=0.9)
        assert m.chunk_id == "CH-1"
        assert m.ocr_confidence == 0.9

    def test_embedding_interface(self):
        from core.chunks.models import ChunkEmbeddingInterface
        e = ChunkEmbeddingInterface(chunk_id="CH-1", text="test", language="hindi")
        d = e.to_embedding_input()
        assert d["id"] == "CH-1"
        assert d["language"] == "hindi"

    def test_search_interface(self):
        from core.chunks.models import ChunkSearchInterface
        s = ChunkSearchInterface(chunk_id="CH-1", text="test", confidence=0.8)
        d = s.to_search_index()
        assert d["chunk_id"] == "CH-1"
        assert d["confidence"] == 0.8


# ── Hierarchy Engine Tests ────────────────────────────────────────────

class TestHierarchyEngine:
    def test_register_and_get(self):
        from core.hierarchy.engine import HierarchyEngine
        from core.chunking.engine import Chunk
        engine = HierarchyEngine()
        c = Chunk(text="Root", chunk_type="book")
        node_id = engine.register_chunk(c)
        assert engine.get_node(node_id) is not None
        assert engine.get_node_for_chunk(c.chunk_id) is not None

    def test_children(self):
        from core.hierarchy.engine import HierarchyEngine
        from core.chunking.engine import Chunk
        engine = HierarchyEngine()
        parent = Chunk(text="Parent", chunk_type="book", ancestor_ids=[])
        parent_id = engine.register_chunk(parent)
        child = Chunk(text="Child", chunk_type="chapter", parent_id=parent.chunk_id, ancestor_ids=[parent.chunk_id])
        child_id = engine.register_chunk(child)
        children = engine.get_children(parent_id)
        assert len(children) == 1

    def test_ancestors(self):
        from core.hierarchy.engine import HierarchyEngine
        from core.chunking.engine import Chunk
        engine = HierarchyEngine()
        root = Chunk(text="R", chunk_type="book")
        rid = engine.register_chunk(root)
        mid = engine.register_chunk(Chunk(text="M", chunk_type="chapter", parent_id=root.chunk_id, ancestor_ids=[root.chunk_id]))
        engine.register_chunk(Chunk(text="L", chunk_type="verse", parent_id=mid, ancestor_ids=[root.chunk_id, mid]))
        # Get descendants of root
        desc = engine.get_descendants(rid)
        assert len(desc) >= 1

    def test_depth(self):
        from core.hierarchy.engine import HierarchyEngine
        from core.chunking.engine import Chunk
        engine = HierarchyEngine()
        nid = engine.register_chunk(Chunk(text="Deep", chunk_type="verse", ancestor_ids=["a", "b", "c"]))
        assert engine.get_depth(nid) == 3

    def test_roots(self):
        from core.hierarchy.engine import HierarchyEngine
        from core.chunking.engine import Chunk
        engine = HierarchyEngine()
        engine.register_chunk(Chunk(text="Root1", chunk_type="book"))
        engine.register_chunk(Chunk(text="Root2", chunk_type="book"))
        assert len(engine.get_roots()) == 2

    def test_max_depth(self):
        from core.hierarchy.engine import HierarchyEngine
        from core.chunking.engine import Chunk
        engine = HierarchyEngine()
        engine.register_chunk(Chunk(text="A", chunk_type="book", ancestor_ids=[]))
        engine.register_chunk(Chunk(text="B", chunk_type="verse", ancestor_ids=["a", "b", "c"]))
        assert engine.get_max_depth() >= 3

    def test_subtree(self):
        from core.hierarchy.engine import HierarchyEngine
        from core.chunking.engine import Chunk
        engine = HierarchyEngine()
        rid = engine.register_chunk(Chunk(text="Root", chunk_type="book"))
        tree = engine.get_subtree(rid)
        assert "children" in tree

    def test_summary(self):
        from core.hierarchy.engine import HierarchyEngine
        from core.chunking.engine import Chunk
        engine = HierarchyEngine()
        engine.register_chunk(Chunk(text="X", chunk_type="book"))
        s = engine.summary()
        assert s["total_nodes"] == 1


# ── Semantic Engine Tests ─────────────────────────────────────────────

class TestSemanticEngine:
    def test_boundary_detection(self):
        from core.semantic.engine import SemanticEngine
        engine = SemanticEngine()
        boundaries = engine.detect_boundaries("Line one। Line two। Line three।")
        assert len(boundaries) >= 1

    def test_text_segmentation(self):
        from core.semantic.engine import SemanticEngine
        engine = SemanticEngine()
        segments = engine.segment_text("Para one.\n\nPara two.\n\nPara three.")
        assert len(segments) >= 1

    def test_add_pattern(self):
        from core.semantic.engine import SemanticEngine
        engine = SemanticEngine()
        engine.add_pattern("custom", r"---")
        boundaries = engine.detect_boundaries("A---B---C")
        assert len(boundaries) >= 2

    def test_language_boundary(self):
        from core.semantic.engine import SemanticEngine
        from core.chunking.engine import Chunk
        engine = SemanticEngine()
        chunks = [
            Chunk(text="English", language="english"),
            Chunk(text="Hindi", language="hindi"),
            Chunk(text="Hindi2", language="hindi"),
        ]
        changes = engine.detect_language_boundary(chunks)
        assert changes == [1]

    def test_summary(self):
        from core.semantic.engine import SemanticEngine
        engine = SemanticEngine()
        s = engine.summary()
        assert s["pattern_count"] > 0


# ── Deduplication Engine Tests ────────────────────────────────────────

class TestDeduplicationEngine:
    def test_exact_duplicates(self):
        from core.deduplication.engine import DeduplicationEngine
        from core.chunking.engine import Chunk
        engine = DeduplicationEngine()
        c1 = Chunk(text="Identical text here")
        c2 = Chunk(text="Identical text here")
        groups = engine.detect_exact_duplicates([c1, c2])
        assert len(groups) == 1
        assert groups[0].similarity_score == 1.0

    def test_near_duplicates(self):
        from core.deduplication.engine import DeduplicationEngine
        from core.chunking.engine import Chunk
        engine = DeduplicationEngine(similarity_threshold=0.3)
        c1 = Chunk(text="The quick brown fox jumps over the lazy dog")
        c2 = Chunk(text="The quick brown fox jumps over a lazy dog")
        groups = engine.detect_near_duplicates([c1, c2])
        assert len(groups) >= 1

    def test_parallel_translations(self):
        from core.deduplication.engine import DeduplicationEngine
        from core.chunking.engine import Chunk
        engine = DeduplicationEngine()
        en = [Chunk(text="Hello world", language="english")]
        hi = [Chunk(text="Namaste duniya", language="hindi")]
        groups = engine.detect_parallel_translations(en, hi)
        # These may not be parallel since they are different texts
        assert isinstance(groups, list)

    def test_link_chunks(self):
        from core.deduplication.engine import DeduplicationEngine, DuplicateType
        engine = DeduplicationEngine()
        group = engine.link_chunks("CH-1", "CH-2", DuplicateType.EQUIVALENT)
        assert group.primary_chunk_id == "CH-1"
        assert "CH-2" in group.duplicate_chunk_ids
        assert engine.get_all_duplicates("CH-1") == ["CH-2"]

    def test_get_group(self):
        from core.deduplication.engine import DeduplicationEngine
        from core.chunking.engine import Chunk
        engine = DeduplicationEngine()
        c1 = Chunk(text="Same text")
        c2 = Chunk(text="Same text")
        groups = engine.detect_exact_duplicates([c1, c2])
        g = engine.get_group(groups[0].group_id)
        assert g is not None

    def test_summary(self):
        from core.deduplication.engine import DeduplicationEngine
        from core.chunking.engine import Chunk
        engine = DeduplicationEngine()
        c1 = Chunk(text="Text A")
        c2 = Chunk(text="Text A")
        engine.detect_exact_duplicates([c1, c2])
        s = engine.summary()
        assert s["total_groups"] == 1


# ── Chunk Registry Tests ──────────────────────────────────────────────

class TestChunkRegistry:
    def test_register_and_get(self):
        from core.chunk_registry.registry import ChunkRegistry, ChunkRecord, ChunkStatus
        reg = ChunkRegistry()
        r = ChunkRecord(chunk_id="CH-1", version=1, status=ChunkStatus.CREATED)
        reg.register(r)
        assert reg.get("CH-1") is not None

    def test_update_status(self):
        from core.chunk_registry.registry import ChunkRegistry, ChunkRecord, ChunkStatus
        reg = ChunkRegistry()
        reg.register(ChunkRecord(chunk_id="CH-1"))
        assert reg.update_status("CH-1", ChunkStatus.VALIDATED)
        assert reg.get("CH-1").status == ChunkStatus.VALIDATED

    def test_version_increment(self):
        from core.chunk_registry.registry import ChunkRegistry, ChunkRecord
        reg = ChunkRegistry()
        reg.register(ChunkRecord(chunk_id="CH-1", version=1))
        v = reg.increment_version("CH-1")
        assert v == 2
        assert reg.get_versions("CH-1") == [1, 2]

    def test_list_by_status(self):
        from core.chunk_registry.registry import ChunkRegistry, ChunkRecord, ChunkStatus
        reg = ChunkRegistry()
        reg.register(ChunkRecord(chunk_id="CH-1", status=ChunkStatus.CREATED))
        reg.register(ChunkRecord(chunk_id="CH-2", status=ChunkStatus.VALIDATED))
        assert len(reg.list_by_status(ChunkStatus.CREATED)) == 1

    def test_summary(self):
        from core.chunk_registry.registry import ChunkRegistry, ChunkRecord
        reg = ChunkRegistry()
        reg.register(ChunkRecord(chunk_id="CH-1"))
        s = reg.summary()
        assert s["total_records"] == 1


# ── Chunk Validation Tests ────────────────────────────────────────────

class TestChunkValidation:
    def test_valid_chunk(self):
        from core.chunk_validation.validator import ChunkValidator
        from core.chunking.engine import Chunk
        v = ChunkValidator()
        c = Chunk(text="Good text content", language="english", book_id="BK-1")
        result = v.validate(c)
        assert result.is_valid

    def test_empty_chunk(self):
        from core.chunk_validation.validator import ChunkValidator
        from core.chunking.engine import Chunk
        v = ChunkValidator()
        c = Chunk(text="")
        result = v.validate(c)
        assert not result.is_valid
        assert result.errors > 0

    def test_missing_passport_warning(self):
        from core.chunk_validation.validator import ChunkValidator
        from core.chunking.engine import Chunk
        v = ChunkValidator()
        c = Chunk(text="Content", passport_id="")
        result = v.validate(c)
        assert any(i.issue_type == "missing_passport" for i in result.issues)

    def test_batch_validation(self):
        from core.chunk_validation.validator import ChunkValidator
        from core.chunking.engine import Chunk
        v = ChunkValidator()
        chunks = [Chunk(text=f"Chunk {i}", language="english") for i in range(5)]
        results = v.validate_batch(chunks)
        assert len(results) == 5
        assert all(r.is_valid for r in results.values())

    def test_get_invalid_chunks(self):
        from core.chunk_validation.validator import ChunkValidator
        from core.chunking.engine import Chunk
        v = ChunkValidator()
        v.validate(Chunk(text="Valid"))
        v.validate(Chunk(text=""))
        invalid = v.get_invalid_chunks()
        assert len(invalid) == 1

    def test_summary(self):
        from core.chunk_validation.validator import ChunkValidator
        from core.chunking.engine import Chunk
        v = ChunkValidator()
        v.validate(Chunk(text="A"))
        v.validate(Chunk(text="B"))
        s = v.summary()
        assert s["total_validated"] == 2


# ── Chunk Quality Tests ───────────────────────────────────────────────

class TestChunkQuality:
    def test_score_chunk(self):
        from core.chunk_quality.quality import ChunkQualityEngine
        from core.chunking.engine import Chunk
        q = ChunkQualityEngine()
        c = Chunk(
            text="Comprehensive text content for quality testing",
            language="hindi",
            book_id="BK-1",
            edition_id="ED-1",
            passport_id="PP-1",
            confidence=0.9,
            evidence_refs=["EV-1"],
            citation_refs=["CR-1"],
            graph_refs=["GR-1"],
        )
        result = q.score(c)
        assert result.overall_score > 0.0
        assert result.grade in ("A", "B", "C", "D", "F")

    def test_high_quality_chunk(self):
        from core.chunk_quality.quality import ChunkQualityEngine
        from core.chunking.engine import Chunk
        q = ChunkQualityEngine()
        c = Chunk(
            text=" ".join(["word"] * 100),
            language="english",
            book_id="BK-1",
            edition_id="ED-1",
            passport_id="PP-1",
            confidence=1.0,
            evidence_refs=["EV-1", "EV-2", "EV-3", "EV-4"],
            citation_refs=["CR-1", "CR-2"],
            graph_refs=["GR-1", "GR-2", "GR-3"],
            hierarchy_path="book/chapter/verse",
        )
        result = q.score(c)
        assert result.overall_score >= 0.6

    def test_low_quality_chunk(self):
        from core.chunk_quality.quality import ChunkQualityEngine
        from core.chunking.engine import Chunk
        q = ChunkQualityEngine()
        c = Chunk(text="")
        result = q.score(c)
        assert result.grade == "F"

    def test_batch_scoring(self):
        from core.chunk_quality.quality import ChunkQualityEngine
        from core.chunking.engine import Chunk
        q = ChunkQualityEngine()
        chunks = [Chunk(text=f"Content {i}", language="english") for i in range(3)]
        results = q.score_batch(chunks)
        assert len(results) == 3

    def test_average_score(self):
        from core.chunk_quality.quality import ChunkQualityEngine
        from core.chunking.engine import Chunk
        q = ChunkQualityEngine()
        q.score(Chunk(text="A", language="english"))
        q.score(Chunk(text="B", language="hindi"))
        avg = q.get_average_score()
        assert 0.0 <= avg <= 1.0

    def test_grade_distribution(self):
        from core.chunk_quality.quality import ChunkQualityEngine
        from core.chunking.engine import Chunk
        q = ChunkQualityEngine()
        q.score(Chunk(text="Good content here", language="english"))
        dist = q.get_grade_distribution()
        assert len(dist) >= 1

    def test_summary(self):
        from core.chunk_quality.quality import ChunkQualityEngine
        from core.chunking.engine import Chunk
        q = ChunkQualityEngine()
        q.score(Chunk(text="Test", language="en"))
        s = q.summary()
        assert s["total_scored"] == 1


# ── Integration Tests ─────────────────────────────────────────────────

class TestPhase10Integration:
    def test_full_pipeline(self):
        """Test complete chunking → hierarchy → quality → validation → registry pipeline."""
        from core.chunking.engine import ChunkingEngine, ChunkType
        from core.hierarchy.engine import HierarchyEngine
        from core.semantic.engine import SemanticEngine
        from core.deduplication.engine import DeduplicationEngine
        from core.chunk_registry.registry import ChunkRegistry, ChunkRecord
        from core.chunk_validation.validator import ChunkValidator
        from core.chunk_quality.quality import ChunkQualityEngine

        # Chunking
        chunker = ChunkingEngine()
        book = chunker.create_hierarchical_chunk(
            text="Bhagavad Gita", chunk_type=ChunkType.BOOK,
            language="sanskrit", book_id="BK-1", edition_id="ED-1", passport_id="PP-1",
        )
        ch1 = chunker.create_hierarchical_chunk(
            text="Chapter 1: Arjuna Vishada Yoga",
            chunk_type=ChunkType.CHAPTER,
            parent_id=book.chunk_id, language="sanskrit",
            book_id="BK-1", edition_id="ED-1", passport_id="PP-1",
        )
        v1 = chunker.create_hierarchical_chunk(
            text="Dhritarashtra uvaca — What happened on the field of Dharma?",
            chunk_type=ChunkType.VERSE,
            parent_id=ch1.chunk_id, language="sanskrit",
            book_id="BK-1", edition_id="ED-1", passport_id="PP-1",
        )
        assert chunker.count() == 3

        # Hierarchy
        hierarchy = HierarchyEngine()
        hierarchy.register_chunk(book)
        hierarchy.register_chunk(ch1)
        hierarchy.register_chunk(v1)
        assert hierarchy.count() == 3
        assert hierarchy.get_max_depth() >= 1

        # Semantic
        semantic = SemanticEngine()
        boundaries = semantic.detect_boundaries(v1.text)
        assert isinstance(boundaries, list)

        # Deduplication
        dedup = DeduplicationEngine()
        exact = dedup.detect_exact_duplicates([book, ch1, v1])
        assert isinstance(exact, list)

        # Registry
        registry = ChunkRegistry()
        for c in [book, ch1, v1]:
            registry.register(ChunkRecord(chunk_id=c.chunk_id))
        assert registry.count() == 3

        # Validation
        validator = ChunkValidator()
        results = validator.validate_batch([book, ch1, v1])
        assert len(results) == 3

        # Quality
        quality = ChunkQualityEngine()
        qr = quality.score(v1)
        assert qr.overall_score > 0.0

    def test_multilingual_chunking(self):
        from core.chunking.engine import ChunkingEngine, ChunkType
        engine = ChunkingEngine()
        engine.create_hierarchical_chunk(text="English text", chunk_type=ChunkType.PARAGRAPH, language="english", book_id="BK-1")
        engine.create_hierarchical_chunk(text="हिंदी पाठ", chunk_type=ChunkType.PARAGRAPH, language="hindi", book_id="BK-1")
        engine.create_hierarchical_chunk(text="संस्कृत श्लोक", chunk_type=ChunkType.VERSE, language="sanskrit", book_id="BK-1")
        assert len(engine.get_by_language("hindi")) == 1
        assert len(engine.get_by_language("sanskrit")) == 1
        assert len(engine.get_by_language("english")) == 1
