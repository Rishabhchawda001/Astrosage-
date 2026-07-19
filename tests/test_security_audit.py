"""Tests for the Security Audit Module."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSecurityAuditor:
    def test_imports(self):
        from core.security.audit import SecurityAuditor
        assert SecurityAuditor is not None

    def test_init(self):
        from core.security.audit import SecurityAuditor
        auditor = SecurityAuditor()
        assert auditor is not None

    def test_load_graph(self):
        from core.security.audit import SecurityAuditor
        auditor = SecurityAuditor()
        auditor.load_graph()
        assert auditor._graph is not None

    def test_audit(self):
        from core.security.audit import SecurityAuditor
        auditor = SecurityAuditor()
        auditor.load_graph()
        report = auditor.audit()
        assert report.total_checks > 0
        assert report.passed_checks > 0

    def test_graph_integrity_check(self):
        from core.security.audit import SecurityAuditor
        auditor = SecurityAuditor()
        auditor.load_graph()
        check = auditor._check_graph_integrity()
        assert check.passed
        assert check.severity == "critical"

    def test_orphan_nodes_check(self):
        from core.security.audit import SecurityAuditor
        auditor = SecurityAuditor()
        auditor.load_graph()
        check = auditor._check_orphan_nodes()
        assert check.check_name == "orphan_nodes"

    def test_duplicate_guids_check(self):
        from core.security.audit import SecurityAuditor
        auditor = SecurityAuditor()
        auditor.load_graph()
        check = auditor._check_duplicate_guids()
        assert check.passed

    def test_broken_references_check(self):
        from core.security.audit import SecurityAuditor
        auditor = SecurityAuditor()
        auditor.load_graph()
        check = auditor._check_broken_references()
        assert check.check_name == "broken_references"

    def test_schema_compliance_check(self):
        from core.security.audit import SecurityAuditor
        auditor = SecurityAuditor()
        auditor.load_graph()
        check = auditor._check_schema_compliance()
        assert check.check_name == "schema_compliance"

    def test_provenance_check(self):
        from core.security.audit import SecurityAuditor
        auditor = SecurityAuditor()
        auditor.load_graph()
        check = auditor._check_provenance()
        assert check.check_name == "provenance"

    def test_data_validation_check(self):
        from core.security.audit import SecurityAuditor
        auditor = SecurityAuditor()
        auditor.load_graph()
        check = auditor._check_data_validation()
        assert check.check_name == "data_validation"

    def test_input_validation_check(self):
        from core.security.audit import SecurityAuditor
        auditor = SecurityAuditor()
        check = auditor._check_input_validation()
        assert check.passed

    def test_overall_passed(self):
        from core.security.audit import SecurityAuditor
        auditor = SecurityAuditor()
        auditor.load_graph()
        report = auditor.audit()
        assert isinstance(report.overall_passed, bool)

    def test_to_dict(self):
        from core.security.audit import SecurityAuditor
        auditor = SecurityAuditor()
        auditor.load_graph()
        report = auditor.audit()
        d = auditor.to_dict(report)
        assert "total_checks" in d
        assert "checks" in d
        assert len(d["checks"]) > 0
