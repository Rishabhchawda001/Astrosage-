"""Phase R1 — Research Stack & MCP Ecosystem Tests."""
import json
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE / "src"))


class TestTechnologyScoring:
    def test_scoring_imports(self):
        from astrosage.research.scoring import TechScore, TechnologyCatalog
        assert TechScore is not None
        assert TechnologyCatalog is not None

    def test_tech_score_computation(self):
        from astrosage.research.scoring import TechScore
        t = TechScore(name="test", category="test", engineering_quality=8, performance=7,
                      documentation=6, testing=5, security=5, community=5,
                      offline_capability=8, maintainability=7, integration_effort=6, future_outlook=5)
        score = t.compute_overall()
        assert 0.0 <= score <= 10.0
        assert t.recommendation in ("integrate", "evaluate", "catalog", "reject")

    def test_catalog_load(self):
        from astrosage.research.scoring import TechnologyCatalog
        cat = TechnologyCatalog.load(BASE / "research/catalog/technology_catalog.json")
        assert len(cat.technologies) > 20

    def test_catalog_has_all_categories(self):
        from astrosage.research.scoring import TechnologyCatalog
        cat = TechnologyCatalog.load(BASE / "research/catalog/technology_catalog.json")
        categories = cat.get_categories()
        assert "ocr" in categories
        assert "mcp" in categories
        assert "vector_db" in categories
        assert "evaluation" in categories

    def test_catalog_has_recommendations(self):
        from astrosage.research.scoring import TechnologyCatalog
        cat = TechnologyCatalog.load(BASE / "research/catalog/technology_catalog.json")
        integrated = cat.get_integrated()
        assert len(integrated) > 0

    def test_catalog_summary(self):
        from astrosage.research.scoring import TechnologyCatalog
        cat = TechnologyCatalog.load(BASE / "research/catalog/technology_catalog.json")
        s = cat.summary()
        assert s["total_technologies"] > 20
        assert "categories" in s

    def test_catalog_save_load_roundtrip(self):
        from astrosage.research.scoring import TechnologyCatalog, TechScore
        cat = TechnologyCatalog()
        cat.add(TechScore(name="roundtrip", category="test", engineering_quality=8, performance=8,
                          documentation=7, testing=7, security=7, community=7,
                          offline_capability=8, maintainability=7, integration_effort=7, future_outlook=7))
        cat.save(BASE / "research/catalog/roundtrip_test.json")
        loaded = TechnologyCatalog.load(BASE / "research/catalog/roundtrip_test.json")
        assert "roundtrip" in loaded.technologies
        (BASE / "research/catalog/roundtrip_test.json").unlink()


class TestPluginArchitecture:
    def test_plugin_imports(self):
        from astrosage.research.plugin_arch import Plugin, PluginManifest, PluginRegistry
        assert Plugin is not None
        assert PluginRegistry is not None

    def test_plugin_registry(self):
        from astrosage.research.plugin_arch import PluginRegistry
        reg = PluginRegistry()
        assert len(reg.list_plugins()) == 0

    def test_plugin_manifest(self):
        from astrosage.research.plugin_arch import PluginManifest
        m = PluginManifest(name="test", version="1.0.0", category="test")
        assert m.name == "test"
        assert m.enabled is True


class TestBenchmarkFramework:
    def test_benchmark_imports(self):
        from astrosage.research.benchmark import BenchmarkHarness, BenchmarkResult
        assert BenchmarkHarness is not None

    def test_benchmark_run(self):
        from astrosage.research.benchmark import BenchmarkHarness
        harness = BenchmarkHarness(BASE / "research/benchmarks")
        result = harness.run_benchmark("test_bench", "test_tool", "1.0",
                                       lambda: {"score": 42})
        assert result.passed is True
        assert result.metrics["score"] == 42

    def test_benchmark_failure(self):
        from astrosage.research.benchmark import BenchmarkHarness
        harness = BenchmarkHarness(BASE / "research/benchmarks")
        result = harness.run_benchmark("fail_bench", "tool", "1.0",
                                       lambda: (_ for _ in ()).throw(ValueError("test")))
        assert result.passed is False


class TestMCPServer:
    def test_mcp_server_imports(self):
        from astrosage.mcp.server import AstroSageMCPServer
        assert AstroSageMCPServer is not None

    def test_mcp_server_tools(self):
        from astrosage.mcp.server import AstroSageMCPServer
        server = AstroSageMCPServer(str(BASE))
        tools = server.get_tools()
        assert len(tools) >= 5
        tool_names = [t["name"] for t in tools]
        assert "search_books" in tool_names
        assert "list_books" in tool_names
        assert "pipeline_status" in tool_names

    def test_mcp_list_books(self):
        from astrosage.mcp.server import AstroSageMCPServer
        server = AstroSageMCPServer(str(BASE))
        result = server.call_tool("list_books")
        assert "result" in result
        assert result["result"]["total"] > 0

    def test_mcp_pipeline_status(self):
        from astrosage.mcp.server import AstroSageMCPServer
        server = AstroSageMCPServer(str(BASE))
        result = server.call_tool("pipeline_status")
        assert result["result"]["status"] == "operational"

    def test_mcp_index_statistics(self):
        from astrosage.mcp.server import AstroSageMCPServer
        server = AstroSageMCPServer(str(BASE))
        result = server.call_tool("index_statistics")
        assert result["result"]["total_documents"] > 0


class TestPluginFiles:
    def test_github_plugin_exists(self):
        assert (BASE / "plugins/mcp/github/plugin.py").exists()

    def test_filesystem_plugin_exists(self):
        assert (BASE / "plugins/mcp/filesystem/plugin.py").exists()

    def test_browser_plugin_exists(self):
        assert (BASE / "plugins/mcp/browser/plugin.py").exists()

    def test_memory_plugin_exists(self):
        assert (BASE / "plugins/mcp/memory/plugin.py").exists()


class TestResearchReports:
    def test_technology_catalog_report(self):
        assert (BASE / "research/catalog/TECHNOLOGY_CATALOG.md").exists()

    def test_github_discovery_report(self):
        assert (BASE / "research/reports/GITHUB_ECOSYSTEM_DISCOVERY.md").exists()

    def test_adr_009(self):
        assert (BASE / "adrs/ADR-009-research-stack.md").exists()

    def test_catalog_json(self):
        assert (BASE / "research/catalog/technology_catalog.json").exists()
        data = json.loads((BASE / "research/catalog/technology_catalog.json").read_text())
        assert data["summary"]["total_technologies"] > 20
