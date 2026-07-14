"""Phase 14.5 — Variant Management Engine Tests."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestVariantManagement:
    def test_imports(self):
        from core.variant_management.engine import VariantManager, KnowledgeVariant
        assert VariantManager is not None

    def test_add_variant(self):
        from core.variant_management.engine import VariantManager, VariantType
        engine = VariantManager()
        v = engine.add_variant("KU-001", "Original text", VariantType.ORIGINAL,
                               source="edition_a", is_primary=True)
        assert v.variant_id is not None
        assert v.is_primary is True

    def test_get_primary(self):
        from core.variant_management.engine import VariantManager, VariantType
        engine = VariantManager()
        engine.add_variant("KU-002", "Primary", is_primary=True)
        engine.add_variant("KU-002", "Secondary", VariantType.EDITION_VARIANT)
        primary = engine.get_primary("KU-002")
        assert primary.text == "Primary"

    def test_get_variants(self):
        from core.variant_management.engine import VariantManager, VariantType
        engine = VariantManager()
        engine.add_variant("KU-003", "V1", VariantType.ORIGINAL)
        engine.add_variant("KU-003", "V2", VariantType.TRANSLATION)
        variants = engine.get_variants("KU-003")
        assert len(variants) == 2

    def test_find_similar(self):
        from core.variant_management.engine import VariantManager
        engine = VariantManager()
        engine.add_variant("KU-004", "The quick brown fox jumps over the lazy dog")
        similar = engine.find_similar("The quick brown fox jumps over the lazy dog")
        assert len(similar) == 1

    def test_text_hash(self):
        from core.variant_management.engine import KnowledgeVariant, VariantType
        v = KnowledgeVariant(text="Hello World", variant_type=VariantType.ORIGINAL)
        assert len(v.text_hash) == 16

    def test_summary(self):
        from core.variant_management.engine import VariantManager, VariantType
        engine = VariantManager()
        engine.add_variant("KU-006", "V1", VariantType.ORIGINAL)
        engine.add_variant("KU-007", "V2", VariantType.TRANSLATION)
        s = engine.summary()
        assert s["total_variants"] == 2
        assert s["knowledge_units"] == 2

    def test_count(self):
        from core.variant_management.engine import VariantManager
        engine = VariantManager()
        assert engine.count() == 0
        engine.add_variant("KU-008", "text")
        assert engine.count() == 1
