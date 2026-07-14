"""Phase 14.5 — Knowledge Versions Engine Tests."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestKnowledgeVersions:
    def test_imports(self):
        from core.knowledge_versions.engine import KnowledgeVersionEngine, KnowledgeVersion
        assert KnowledgeVersionEngine is not None

    def test_create_version(self):
        from core.knowledge_versions.engine import KnowledgeVersionEngine, VersionType
        engine = KnowledgeVersionEngine()
        v = engine.create_version("KU-001", "Original text", VersionType.ORIGINAL)
        assert v.version_number == 1
        assert v.is_current is True

    def test_create_multiple_versions(self):
        from core.knowledge_versions.engine import KnowledgeVersionEngine, VersionType
        engine = KnowledgeVersionEngine()
        engine.create_version("KU-002", "V1 text", VersionType.ORIGINAL)
        engine.create_version("KU-002", "V2 recovered text", VersionType.RECOVERED)
        v3 = engine.create_version("KU-002", "V3 verified text", VersionType.VERIFIED)
        assert v3.version_number == 3
        assert v3.is_current is True

    def test_old_version_not_current(self):
        from core.knowledge_versions.engine import KnowledgeVersionEngine, VersionType
        engine = KnowledgeVersionEngine()
        v1 = engine.create_version("KU-003", "V1", VersionType.ORIGINAL)
        engine.create_version("KU-003", "V2", VersionType.RECOVERED)
        assert v1.is_current is False

    def test_get_current(self):
        from core.knowledge_versions.engine import KnowledgeVersionEngine, VersionType
        engine = KnowledgeVersionEngine()
        engine.create_version("KU-004", "V1", VersionType.ORIGINAL)
        v2 = engine.create_version("KU-004", "V2", VersionType.RECOVERED)
        current = engine.get_current("KU-004")
        assert current.version_id == v2.version_id

    def test_get_all_versions(self):
        from core.knowledge_versions.engine import KnowledgeVersionEngine, VersionType
        engine = KnowledgeVersionEngine()
        engine.create_version("KU-005", "V1", VersionType.ORIGINAL)
        engine.create_version("KU-005", "V2", VersionType.RECOVERED)
        versions = engine.get_all_versions("KU-005")
        assert len(versions) == 2
        assert versions[0].version_number == 1

    def test_text_hash(self):
        from core.knowledge_versions.engine import KnowledgeVersion, VersionType
        v = KnowledgeVersion(text="Hello World", version_type=VersionType.ORIGINAL)
        assert len(v.text_hash) == 16

    def test_summary(self):
        from core.knowledge_versions.engine import KnowledgeVersionEngine, VersionType
        engine = KnowledgeVersionEngine()
        engine.create_version("KU-006", "V1", VersionType.ORIGINAL)
        engine.create_version("KU-007", "V2", VersionType.RECOVERED)
        s = engine.summary()
        assert s["total_versions"] == 2
        assert s["knowledge_units"] == 2

    def test_count(self):
        from core.knowledge_versions.engine import KnowledgeVersionEngine, VersionType
        engine = KnowledgeVersionEngine()
        assert engine.count() == 0
        engine.create_version("KU-008", "text", VersionType.ORIGINAL)
        assert engine.count() == 1
