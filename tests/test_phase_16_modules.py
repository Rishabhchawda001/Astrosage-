"""Phase 16 — Unit Registry, Identity, Passports, Evidence Tests."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestUnitRegistry:
    def test_register(self):
        from core.unit_registry.engine import UnitRegistry
        reg = UnitRegistry()
        e = reg.register("KU-001", book_uuid="BK-001", unit_type="word")
        assert e.entry_id is not None

    def test_get_by_unit(self):
        from core.unit_registry.engine import UnitRegistry
        reg = UnitRegistry()
        reg.register("KU-002", book_uuid="BK-001")
        e = reg.get_by_unit("KU-002")
        assert e is not None

    def test_count(self):
        from core.unit_registry.engine import UnitRegistry
        reg = UnitRegistry()
        reg.register("KU-003")
        assert reg.count() == 1

    def test_summary(self):
        from core.unit_registry.engine import UnitRegistry
        reg = UnitRegistry()
        reg.register("KU-004", unit_type="word")
        reg.register("KU-005", unit_type="verse")
        s = reg.summary()
        assert s["total"] == 2


class TestUnitIdentity:
    def test_create(self):
        from core.unit_identity.engine import UnitIdentityEngine
        engine = UnitIdentityEngine()
        ident = engine.create("KU-001", book_uuid="BK-001", language="english")
        assert ident.identity_id is not None

    def test_get_by_unit(self):
        from core.unit_identity.engine import UnitIdentityEngine
        engine = UnitIdentityEngine()
        engine.create("KU-002", book_uuid="BK-001")
        ident = engine.get_by_unit("KU-002")
        assert ident is not None

    def test_count(self):
        from core.unit_identity.engine import UnitIdentityEngine
        engine = UnitIdentityEngine()
        engine.create("KU-003")
        assert engine.count() == 1


class TestUnitPassports:
    def test_create(self):
        from core.unit_passports.engine import UnitPassportEngine
        engine = UnitPassportEngine()
        p = engine.create("KU-001", book_uuid="BK-001")
        assert p.passport_id is not None

    def test_update_evidence(self):
        from core.unit_passports.engine import UnitPassportEngine
        engine = UnitPassportEngine()
        engine.create("KU-002")
        engine.update_evidence("KU-002", "EV-001")
        p = engine.get_by_unit("KU-002")
        assert "EV-001" in p.evidence

    def test_verify(self):
        from core.unit_passports.engine import UnitPassportEngine, PassportStatus
        engine = UnitPassportEngine()
        engine.create("KU-003")
        engine.verify("KU-003", PassportStatus.VERIFIED, confidence=0.9)
        p = engine.get_by_unit("KU-003")
        assert p.verification_status == PassportStatus.VERIFIED

    def test_count(self):
        from core.unit_passports.engine import UnitPassportEngine
        engine = UnitPassportEngine()
        engine.create("KU-004")
        assert engine.count() == 1

    def test_summary(self):
        from core.unit_passports.engine import UnitPassportEngine, PassportStatus
        engine = UnitPassportEngine()
        engine.create("KU-005")
        engine.verify("KU-005", PassportStatus.VERIFIED)
        s = engine.summary()
        assert s["total"] == 1


class TestUnitEvidence:
    def test_add(self):
        from core.unit_evidence.engine import UnitEvidenceEngine
        engine = UnitEvidenceEngine()
        rec = engine.add("KU-001", source_type="silver", content="test text")
        assert rec.record_id is not None

    def test_get_by_unit(self):
        from core.unit_evidence.engine import UnitEvidenceEngine
        engine = UnitEvidenceEngine()
        engine.add("KU-002", source_type="silver", content="A")
        engine.add("KU-002", source_type="bronze", content="B")
        recs = engine.get_by_unit("KU-002")
        assert len(recs) == 2

    def test_evidence_count(self):
        from core.unit_evidence.engine import UnitEvidenceEngine
        engine = UnitEvidenceEngine()
        engine.add("KU-003", content="A")
        engine.add("KU-003", content="B")
        assert engine.evidence_count("KU-003") == 2

    def test_deduplicate(self):
        from core.unit_evidence.engine import UnitEvidenceEngine
        engine = UnitEvidenceEngine()
        engine.add("KU-004", content="same text")
        engine.add("KU-004", content="same text")
        removed = engine.deduplicate()
        assert removed == 1

    def test_summary(self):
        from core.unit_evidence.engine import UnitEvidenceEngine
        engine = UnitEvidenceEngine()
        engine.add("KU-005", source_type="silver", content="A")
        engine.add("KU-006", source_type="bronze", content="B")
        s = engine.summary()
        assert s["total"] == 2
        assert s["unique_units"] == 2
