"""Phase A1 — Foundation Installation & Configuration Tests."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


# ── Plugin System Tests ──────────────────────────────────────────────────

class TestPluginSystem:
    def test_plugin_base_import(self):
        from core.plugin import Plugin, PluginMetadata, PluginState
        assert Plugin is not None
        assert PluginMetadata is not None
        assert PluginState is not None

    def test_plugin_metadata(self):
        from core.plugin.base import PluginMetadata
        meta = PluginMetadata(name="test", version="1.0.0", description="Test plugin")
        assert meta.name == "test"
        assert meta.version == "1.0.0"

    def test_plugin_state(self):
        from core.plugin.base import PluginState
        assert PluginState.DISCOVERED.value == "discovered"
        assert PluginState.READY.value == "ready"

    def test_plugin_loader(self):
        from core.plugin.loader import PluginLoader
        loader = PluginLoader()
        discovered = loader.discover()
        assert isinstance(discovered, dict)

    def test_plugin_registry(self):
        from core.plugin.registry import PluginRegistry
        reg = PluginRegistry()
        assert reg.count == 0
        assert reg.summary()["total"] == 0


# ── Service Registry Tests ───────────────────────────────────────────────

class TestServiceRegistry:
    def test_import(self):
        from core.service import ServiceRegistry, Service
        assert ServiceRegistry is not None

    def test_register_and_resolve(self):
        from core.service.registry import ServiceRegistry
        reg = ServiceRegistry()
        reg.register("test_service", str, implementation="hello")
        result = reg.resolve("test_service")
        assert result == "hello"

    def test_has_service(self):
        from core.service.registry import ServiceRegistry
        reg = ServiceRegistry()
        reg.register("svc", str, implementation="x")
        assert reg.has("svc")
        assert not reg.has("nope")

    def test_list_services(self):
        from core.service.registry import ServiceRegistry
        reg = ServiceRegistry()
        reg.register("a", str, implementation="1")
        reg.register("b", int, implementation=2)
        assert len(reg.list_services()) == 2

    def test_summary(self):
        from core.service.registry import ServiceRegistry
        reg = ServiceRegistry()
        reg.register("s1", str, implementation="v1")
        s = reg.summary()
        assert s["total"] == 1


# ── Config System Tests ─────────────────────────────────────────────────

class TestConfigSystem:
    def test_import(self):
        from core.config import ConfigLoader, Config
        assert ConfigLoader is not None

    def test_config_get_set(self):
        from core.config.loader import Config
        c = Config({"a": {"b": 42}})
        assert c.get("a.b") == 42
        assert c.get("a.c", "default") == "default"
        c.set("x.y", "hello")
        assert c.get("x.y") == "hello"

    def test_config_load_json(self):
        from core.config.loader import ConfigLoader, Config
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            import json
            json.dump({"key": "value", "nested": {"a": 1}}, f)
            f.flush()
            loader = ConfigLoader()
            config = loader.load_file(f.name)
            assert config.get("key") == "value"
            assert config.get("nested.a") == 1

    def test_config_env_override(self):
        import os
        from core.config.loader import ConfigLoader
        os.environ["ASTROSAGE_TEST_KEY"] = "env_value"
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                import json
                json.dump({"test_key": "file_value"}, f)
                f.flush()
                loader = ConfigLoader()
                config = loader.load_file(f.name)
                assert config.get("test_key") == "env_value"
        finally:
            del os.environ["ASTROSAGE_TEST_KEY"]


# ── Versioning Tests ────────────────────────────────────────────────────

class TestVersioning:
    def test_import(self):
        from core.versioning import ComponentVersionRegistry, ComponentVersion
        assert ComponentVersionRegistry is not None

    def test_register_and_get(self):
        from core.versioning.registry import ComponentVersionRegistry
        reg = ComponentVersionRegistry()
        reg.register("plugin_ocr", "1.0.0", component_type="plugin", description="OCR plugin")
        v = reg.get_current("plugin_ocr")
        assert v is not None
        assert v.version == "1.0.0"

    def test_multiple_versions(self):
        from core.versioning.registry import ComponentVersionRegistry
        reg = ComponentVersionRegistry()
        reg.register("x", "1.0.0")
        reg.register("x", "2.0.0")
        v = reg.get_current("x")
        assert v.version == "2.0.0"
        assert len(reg.get_all_versions("x")) == 2

    def test_summary(self):
        from core.versioning.registry import ComponentVersionRegistry
        reg = ComponentVersionRegistry()
        reg.register("a", "1.0.0")
        reg.register("b", "2.0.0")
        s = reg.summary()
        assert s["a"] == "1.0.0"


# ── Logging Tests ───────────────────────────────────────────────────────

class TestLogging:
    def test_import(self):
        from core.logging import StructuredLogger, LogLevel
        assert StructuredLogger is not None

    def test_logger_creation(self):
        from core.logging.structured import StructuredLogger
        logger = StructuredLogger("test")
        assert logger.name == "test"

    def test_log_entry(self):
        from core.logging.structured import LogEntry
        entry = LogEntry(message="test", level="info")
        assert entry.message == "test"


# ── DI Container Tests ──────────────────────────────────────────────────

class TestDIContainer:
    def test_import(self):
        from core.di import Container
        assert Container is not None

    def test_register_and_resolve(self):
        from core.di.container import Container
        c = Container()
        c.register_singleton("test", "hello")
        assert c.resolve("test") == "hello"

    def test_register_factory(self):
        from core.di.container import Container
        c = Container()
        c.register_factory("counter", lambda: {"count": 0})
        r1 = c.resolve("counter")
        r2 = c.resolve("counter")
        assert r1 is r2  # singleton after first resolve

    def test_has(self):
        from core.di.container import Container
        c = Container()
        c.register_singleton("x", 42)
        assert c.has("x")
        assert not c.has("y")


# ── Technology Registry Tests ───────────────────────────────────────────

class TestTechnologyRegistry:
    def test_import(self):
        from registries.technology_registry import TechnologyRegistry
        assert TechnologyRegistry is not None

    def test_register_and_get(self):
        from registries.technology_registry import TechnologyRegistry, TechnologyEntry
        with tempfile.TemporaryDirectory() as tmp:
            reg = TechnologyRegistry(registry_dir=tmp)
            entry = TechnologyEntry(name="PyMuPDF", purpose="PDF extraction", subsystem="document")
            tid = reg.register(entry)
            assert tid.startswith("TECH-")
            assert reg.get(tid) is not None

    def test_find_by_status(self):
        from registries.technology_registry import TechnologyRegistry, TechnologyEntry
        with tempfile.TemporaryDirectory() as tmp:
            reg = TechnologyRegistry(registry_dir=tmp)
            reg.register(TechnologyEntry(name="A", status="approved"))
            reg.register(TechnologyEntry(name="B", status="candidate"))
            approved = reg.find_by_status("approved")
            assert len(approved) == 1

    def test_summary(self):
        from registries.technology_registry import TechnologyRegistry, TechnologyEntry
        with tempfile.TemporaryDirectory() as tmp:
            reg = TechnologyRegistry(registry_dir=tmp)
            reg.register(TechnologyEntry(name="X"))
            s = reg.summary()
            assert s["total"] == 1


# ── Skill Registry Tests ────────────────────────────────────────────────

class TestSkillRegistry:
    def test_import(self):
        from registries.skill_registry import SkillRegistry
        assert SkillRegistry is not None

    def test_register(self):
        from registries.skill_registry import SkillRegistry, SkillEntry
        with tempfile.TemporaryDirectory() as tmp:
            reg = SkillRegistry(registry_dir=tmp)
            entry = SkillEntry(name="ocr_skill", category="core")
            sid = reg.register(entry)
            assert sid.startswith("SKILL-")

    def test_find_by_category(self):
        from registries.skill_registry import SkillRegistry, SkillEntry
        with tempfile.TemporaryDirectory() as tmp:
            reg = SkillRegistry(registry_dir=tmp)
            reg.register(SkillEntry(name="a", category="core"))
            reg.register(SkillEntry(name="b", category="research"))
            core = reg.find_by_category("core")
            assert len(core) == 1


# ── Benchmark Registry Tests ────────────────────────────────────────────

class TestBenchmarkRegistry:
    def test_import(self):
        from registries.benchmark_registry import BenchmarkRegistry
        assert BenchmarkRegistry is not None

    def test_register(self):
        from registries.benchmark_registry import BenchmarkRegistry, BenchmarkEntry
        with tempfile.TemporaryDirectory() as tmp:
            reg = BenchmarkRegistry(registry_dir=tmp)
            entry = BenchmarkEntry(name="ocr_bench", category="ocr", results={"accuracy": 0.95})
            bid = reg.register(entry)
            assert bid.startswith("BENCH-")

    def test_get_latest(self):
        from registries.benchmark_registry import BenchmarkRegistry, BenchmarkEntry
        with tempfile.TemporaryDirectory() as tmp:
            reg = BenchmarkRegistry(registry_dir=tmp)
            reg.register(BenchmarkEntry(name="b1", category="ocr", created_at="2026-01-01"))
            reg.register(BenchmarkEntry(name="b2", category="ocr", created_at="2026-07-01"))
            latest = reg.get_latest("ocr")
            assert latest.name == "b2"


# ── Research Registry Tests ─────────────────────────────────────────────

class TestResearchRegistry:
    def test_import(self):
        from registries.research_registry import ResearchRegistry
        assert ResearchRegistry is not None

    def test_register(self):
        from registries.research_registry import ResearchRegistry, ResearchEntry
        with tempfile.TemporaryDirectory() as tmp:
            reg = ResearchRegistry(registry_dir=tmp)
            entry = ResearchEntry(title="New OCR paper", category="arxiv", tags=["ocr", "hindi"])
            rid = reg.register(entry)
            assert rid.startswith("RES-")


# ── Adapter Interface Tests ─────────────────────────────────────────────

class TestAdapters:
    def test_document_adapters(self):
        from adapters.document.base import (
            PyMuPDFAdapter, TesseractAdapter, PaddleOCRAdapter, OCRmyPDFAdapter, UnstructuredAdapter
        )
        for Adapter in [PyMuPDFAdapter, TesseractAdapter, PaddleOCRAdapter, OCRmyPDFAdapter, UnstructuredAdapter]:
            a = Adapter()
            assert a.name()
            assert a.health()["status"] == "scaffold"

    def test_search_adapters(self):
        from adapters.search.base import (
            BM25Adapter, HybridSearchAdapter, MetadataSearchAdapter, VectorSearchAdapter
        )
        for Adapter in [BM25Adapter, HybridSearchAdapter, MetadataSearchAdapter, VectorSearchAdapter]:
            a = Adapter()
            assert a.name()

    def test_vector_adapters(self):
        from adapters.vector.base import QdrantAdapter, ChromaAdapter, PgvectorAdapter
        for Adapter in [QdrantAdapter, ChromaAdapter, PgvectorAdapter]:
            a = Adapter()
            assert a.name()

    def test_memory_adapters(self):
        from adapters.memory.base import (
            KnowledgeMemoryAdapter, AgentMemoryAdapter, SessionMemoryAdapter,
            ProjectMemoryAdapter, BenchmarkMemoryAdapter, RecoveryMemoryAdapter
        )
        for Adapter in [KnowledgeMemoryAdapter, AgentMemoryAdapter, SessionMemoryAdapter,
                        ProjectMemoryAdapter, BenchmarkMemoryAdapter, RecoveryMemoryAdapter]:
            a = Adapter()
            assert a.name()

    def test_guardrail_adapters(self):
        from adapters.guardrails.base import RAGASAdapter, DeepEvalAdapter, LangfuseAdapter
        for Adapter in [RAGASAdapter, DeepEvalAdapter, LangfuseAdapter]:
            a = Adapter()
            assert a.name()

    def test_browser_adapters(self):
        from adapters.browser.base import (
            PlaywrightAdapter, GitHubAdapter, BraveAdapter, ExaAdapter, ArxivAdapter,
            GoogleDriveAdapter, InternetArchiveAdapter, OpenLibraryAdapter,
            CrossrefAdapter, OpenAlexAdapter
        )
        for Adapter in [PlaywrightAdapter, GitHubAdapter, BraveAdapter, ExaAdapter, ArxivAdapter,
                        GoogleDriveAdapter, InternetArchiveAdapter, OpenLibraryAdapter,
                        CrossrefAdapter, OpenAlexAdapter]:
            a = Adapter()
            assert a.name()


# ── Schema Tests ────────────────────────────────────────────────────────

class TestSchemas:
    def test_mcp_schemas(self):
        from schemas.mcp import MCPTool, MCPToolCall, MCPToolResult, ASTROSAGE_MCP_TOOLS
        assert len(ASTROSAGE_MCP_TOOLS) == 12
        assert ASTROSAGE_MCP_TOOLS[0].name == "search_books"

    def test_a2a_schemas(self):
        from schemas.a2a import AgentIdentity, TaskRequest, TaskResponse, Heartbeat, AgentStatus, TaskStatus
        agent = AgentIdentity(agent_id="a1", name="Test Agent")
        assert agent.status == AgentStatus.IDLE
        task = TaskRequest(task_id="t1", from_agent="a1", to_agent="a2")
        assert task.priority == 5

    def test_prompt_schemas(self):
        from schemas.prompts import PromptTemplate, DEFAULT_PROMPTS
        assert len(DEFAULT_PROMPTS) == 3
        assert DEFAULT_PROMPTS[0].framework == "Constitutional"

    def test_openapi_schemas(self):
        from schemas.openapi import OpenAPIService, ASTROSAGE_SERVICES
        assert len(ASTROSAGE_SERVICES) == 10
        assert ASTROSAGE_SERVICES[0].name == "knowledge_service"


# ── Contract Tests ──────────────────────────────────────────────────────

class TestContracts:
    def test_interfaces_exist(self):
        from contracts.interfaces import (
            KnowledgeService, RecoveryService, VerificationService,
            CorpusService, OCRService, CitationService,
            KnowledgeGraphService, ResearchService, GitHubService, BrowserService
        )
        assert all([KnowledgeService, RecoveryService, VerificationService,
                    CorpusService, OCRService, CitationService,
                    KnowledgeGraphService, ResearchService, GitHubService, BrowserService])


# ── Command System Tests ────────────────────────────────────────────────

class TestCommandSystem:
    def test_import(self):
        from commands import CommandRegistry, Command
        assert CommandRegistry is not None

    def test_known_commands(self):
        from commands.known_commands import KNOWN_COMMANDS
        assert len(KNOWN_COMMANDS) == 14
        names = [c["name"] for c in KNOWN_COMMANDS]
        assert "verify" in names
        assert "recover" in names
        assert "research" in names

    def test_registry(self):
        from commands.registry import CommandRegistry
        reg = CommandRegistry()
        assert reg.count == 0


# ── MCP Server Tests ────────────────────────────────────────────────────

class TestMCPServer:
    def test_import(self):
        from services.mcp_server import MCPServer, MCPServerConfig
        assert MCPServer is not None

    def test_server_creation(self):
        from services.mcp_server import MCPServer, MCPServerConfig
        server = MCPServer(MCPServerConfig(name="test"))
        assert server.health()["status"] == "scaffold"
        assert len(server.list_tools()) == 0

    def test_register_tool(self):
        from services.mcp_server import MCPServer
        server = MCPServer()
        server.register_tool("test_tool", lambda x: x, description="Test")
        assert len(server.list_tools()) == 1


# ── A2A Server Tests ────────────────────────────────────────────────────

class TestA2AServer:
    def test_import(self):
        from services.a2a_server import A2AServer, A2AConfig
        assert A2AServer is not None

    def test_server_creation(self):
        from services.a2a_server import A2AServer, A2AConfig
        server = A2AServer(A2AConfig(agent_id="agent-1", agent_name="Test"))
        assert server.health()["status"] == "scaffold"

    def test_register_and_heartbeat(self):
        from services.a2a_server import A2AServer
        server = A2AServer()
        server.register_agent("a1", capabilities=["search", "verify"])
        hb = server.heartbeat()
        assert hb["registered_agents"] == 1


# ── Skill Loader Tests ──────────────────────────────────────────────────

class TestSkillLoader:
    def test_import(self):
        from skills import SkillLoader, Skill
        assert SkillLoader is not None

    def test_discover_empty(self):
        from skills.loader import SkillLoader
        loader = SkillLoader()
        skills = loader.discover()
        assert len(skills) == 0

    def test_discover_with_skills(self):
        from skills.loader import SkillLoader
        with tempfile.TemporaryDirectory() as tmp:
            # Create a skill
            skill_dir = Path(tmp) / "my_skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("# My Skill\n\nDescription: Test skill\nVersion: 1.0.0\n")
            loader = SkillLoader(skill_dirs=[tmp])
            skills = loader.discover()
            assert "My Skill" in skills

    def test_summary(self):
        from skills.loader import SkillLoader
        loader = SkillLoader()
        s = loader.summary()
        assert "total" in s


# ── Integration Tests ───────────────────────────────────────────────────

class TestIntegration:
    def test_full_infrastructure(self):
        """Test that all infrastructure components work together."""
        from core.plugin import PluginRegistry
        from core.service import ServiceRegistry
        from core.config import ConfigLoader
        from core.versioning import ComponentVersionRegistry
        from core.di import Container
        from core.logging import StructuredLogger
        from registries.technology_registry import TechnologyRegistry
        from registries.skill_registry import SkillRegistry
        from registries.benchmark_registry import BenchmarkRegistry
        from registries.research_registry import ResearchRegistry
        from commands import CommandRegistry
        from services.mcp_server import MCPServer
        from services.a2a_server import A2AServer
        from skills import SkillLoader

        with tempfile.TemporaryDirectory() as tmp:
            # All registries
            tech_reg = TechnologyRegistry(registry_dir=tmp)
            skill_reg = SkillRegistry(registry_dir=tmp)
            bench_reg = BenchmarkRegistry(registry_dir=tmp)
            research_reg = ResearchRegistry(registry_dir=tmp)

            # Plugin system
            plugin_reg = PluginRegistry()

            # Service registry
            svc_reg = ServiceRegistry()
            svc_reg.register("tech_registry", TechnologyRegistry, implementation=tech_reg)

            # Config
            config_loader = ConfigLoader()
            config = config_loader.load_file("/nonexistent")  # returns defaults

            # Versioning
            ver_reg = ComponentVersionRegistry()
            ver_reg.register("plugin_ocr", "1.0.0", "plugin")

            # DI container
            container = Container()
            container.register_singleton("tech_registry", tech_reg)
            container.register_singleton("skill_registry", skill_reg)

            # Commands
            cmd_reg = CommandRegistry()

            # MCP
            mcp = MCPServer()

            # A2A
            a2a = A2AServer()

            # Skills
            skill_loader = SkillLoader()

            # Verify all work
            assert tech_reg.summary()["total"] == 0
            assert skill_reg.summary()["total"] == 0
            assert bench_reg.summary()["total"] == 0
            assert research_reg.summary()["total"] == 0
            assert plugin_reg.count == 0
            assert svc_reg.has("tech_registry")
            assert ver_reg.summary()["plugin_ocr"] == "1.0.0"
            assert container.has("tech_registry")
            assert cmd_reg.count == 0
            assert mcp.health()["status"] == "scaffold"
            assert a2a.health()["status"] == "scaffold"
            assert skill_loader.count == 0

            # Register a technology
            from registries.technology_registry import TechnologyEntry
            tech_reg.register(TechnologyEntry(name="PyMuPDF", purpose="PDF extraction", status="approved"))
            assert tech_reg.summary()["total"] == 1

            # Verify DI resolution resolves correctly
            resolved = container.resolve("tech_registry")
            assert resolved is tech_reg
