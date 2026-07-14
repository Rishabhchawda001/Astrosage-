"""Phase 14.5 — Recovery Validation Engine Tests."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestRecoveryValidation:
    def test_imports(self):
        from core.recovery_validation.engine import RecoveryValidationEngine, ValidationResult
        assert RecoveryValidationEngine is not None

    def test_validate_evidence_pass(self):
        from core.recovery_validation.engine import RecoveryValidationEngine, ValidationType, ValidationStatus
        engine = RecoveryValidationEngine(min_evidence=2)
        result = engine.validate("KU-001", ValidationType.EVIDENCE_CHECK, evidence_count=5)
        assert result.status == ValidationStatus.PASSED

    def test_validate_evidence_fail(self):
        from core.recovery_validation.engine import RecoveryValidationEngine, ValidationType, ValidationStatus
        engine = RecoveryValidationEngine(min_evidence=3)
        result = engine.validate("KU-002", ValidationType.EVIDENCE_CHECK, evidence_count=1)
        assert result.status == ValidationStatus.FAILED

    def test_validate_confidence_pass(self):
        from core.recovery_validation.engine import RecoveryValidationEngine, ValidationType, ValidationStatus
        engine = RecoveryValidationEngine(min_confidence=0.6)
        result = engine.validate("KU-003", ValidationType.CONFIDENCE_CHECK, confidence=0.8)
        assert result.status == ValidationStatus.PASSED

    def test_validate_confidence_fail(self):
        from core.recovery_validation.engine import RecoveryValidationEngine, ValidationType, ValidationStatus
        engine = RecoveryValidationEngine(min_confidence=0.7)
        result = engine.validate("KU-004", ValidationType.CONFIDENCE_CHECK, confidence=0.4)
        assert result.status == ValidationStatus.FAILED

    def test_validate_all(self):
        from core.recovery_validation.engine import RecoveryValidationEngine, ValidationStatus
        engine = RecoveryValidationEngine(min_evidence=2, min_confidence=0.6)
        results = engine.validate_all("KU-005", evidence_count=3, confidence=0.8)
        assert len(results) >= 2
        all_passed = all(r.status == ValidationStatus.PASSED for r in results)
        assert all_passed

    def test_get_failed(self):
        from core.recovery_validation.engine import RecoveryValidationEngine, ValidationType
        engine = RecoveryValidationEngine(min_evidence=5)
        engine.validate("KU-010", ValidationType.EVIDENCE_CHECK, evidence_count=1)
        engine.validate("KU-011", ValidationType.EVIDENCE_CHECK, evidence_count=10)
        failed = engine.get_failed()
        assert len(failed) == 1

    def test_summary(self):
        from core.recovery_validation.engine import RecoveryValidationEngine, ValidationType
        engine = RecoveryValidationEngine(min_evidence=1)
        engine.validate("KU-020", ValidationType.PROVENANCE_CHECK, message="OK")
        s = engine.summary()
        assert s["total"] == 1
        assert s["failed"] == 0

    def test_count(self):
        from core.recovery_validation.engine import RecoveryValidationEngine, ValidationType
        engine = RecoveryValidationEngine()
        assert engine.count() == 0
        engine.validate("KU-030", ValidationType.STRUCTURE_CHECK, message="ok")
        assert engine.count() == 1
