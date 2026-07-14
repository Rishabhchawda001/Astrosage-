"""Phase 13 — Agent Infrastructure Expansion Tests."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestOmniRouter:
    def test_imports(self):
        from core.providers import OmniRouter, ProviderConfig, ModelCapabilities
        assert OmniRouter is not None

    def test_disabled_passthrough(self):
        from core.providers.router import OmniRouter
        router = OmniRouter(enabled=False)
        result = router.route("gpt-4")
        assert result["routed"] is False

    def test_register_and_route(self):
        from core.providers.router import OmniRouter, ProviderConfig, ModelCapabilities
        router = OmniRouter(enabled=True)
        router.register_provider(ProviderConfig(
            provider_id="openai", name="OpenAI",
            models=[ModelCapabilities(model_id="gpt-4", provider="openai")]))
        result = router.route("gpt-4")
        assert result["routed"] is True
        assert result["provider"] == "openai"

    def test_fallback_chain(self):
        from core.providers.router import OmniRouter, ProviderConfig, ModelCapabilities
        router = OmniRouter(enabled=True)
        router.register_provider(ProviderConfig(provider_id="p1", models=[ModelCapabilities(model_id="m1")], enabled=False))
        router.register_provider(ProviderConfig(provider_id="p2", models=[ModelCapabilities(model_id="m2")]))
        router.set_fallback_chain("m1", ["m2"])
        result = router.route("m1")
        assert result["routed"] is True
        assert result["provider"] == "p2"

    def test_health(self):
        from core.providers.router import OmniRouter, ProviderConfig, ModelCapabilities
        router = OmniRouter(enabled=True)
        router.register_provider(ProviderConfig(provider_id="p1", models=[ModelCapabilities(model_id="m1")]))
        router.record_result("p1", success=True, cost=0.01)
        health = router.get_provider_health()
        assert health["p1"]["success_rate"] == 1.0

    def test_capabilities(self):
        from core.providers.router import OmniRouter, ProviderConfig, ModelCapabilities
        router = OmniRouter(enabled=True)
        router.register_provider(ProviderConfig(provider_id="p1", models=[
            ModelCapabilities(model_id="m1", max_tokens=8192, supports_vision=True)]))
        caps = router.get_capabilities("m1")
        assert len(caps) == 1
        assert caps[0].max_tokens == 8192

    def test_summary(self):
        from core.providers.router import OmniRouter, ProviderConfig, ModelCapabilities
        router = OmniRouter(enabled=True)
        router.register_provider(ProviderConfig(provider_id="p1", models=[ModelCapabilities(model_id="m1")]))
        s = router.summary()
        assert s["providers"] == 1


class TestWorkflowEngine:
    def test_imports(self):
        from core.workflows import WorkflowEngine
        assert WorkflowEngine is not None

    def test_disabled(self):
        from core.workflows.engine import WorkflowEngine
        engine = WorkflowEngine(enabled=False)
        wf = engine.create_book_workflow("test")
        assert engine.execute_step(wf.workflow_id) is False

    def test_create_workflow(self):
        from core.workflows.engine import WorkflowEngine
        engine = WorkflowEngine(enabled=True)
        wf = engine.create_book_workflow("Bhagavad Gita", "/path/to/bg.pdf")
        assert len(wf.steps) == 10
        assert wf.name == "book:Bhagavad Gita"

    def test_execute_step(self):
        from core.workflows.engine import WorkflowEngine
        engine = WorkflowEngine(enabled=True)
        engine.register_step_handler("ocr", lambda inputs, ctx: {"text": "ocr output"})
        wf = engine.create_book_workflow("test")
        result = engine.execute_step(wf.workflow_id)
        assert result is True
        assert wf.current_step == 1
        assert wf.steps[0].outputs == {"text": "ocr output"}

    def test_execute_all_steps(self):
        from core.workflows.engine import WorkflowEngine, WorkflowStatus
        engine = WorkflowEngine(enabled=True)
        for name in ["ocr", "language_detection", "metadata_extraction", "evidence_search",
                      "cross_source_verification", "translation_alignment", "truth_reconstruction",
                      "quality_validation", "knowledge_graph_update", "checkpoint"]:
            engine.register_step_handler(name, lambda inputs, ctx: {"ok": True})
        wf = engine.create_book_workflow("test")
        for _ in range(10):
            engine.execute_step(wf.workflow_id)
        assert wf.status == WorkflowStatus.COMPLETED

    def test_resume(self):
        from core.workflows.engine import WorkflowEngine, WorkflowStatus
        engine = WorkflowEngine(enabled=True)
        wf = engine.create_book_workflow("test")
        wf.status = WorkflowStatus.FAILED
        assert engine.resume(wf.workflow_id)
        assert wf.status == WorkflowStatus.PENDING


class TestOrcaAdapter:
    def test_imports(self):
        from core.orchestration import OrcaAdapter
        assert OrcaAdapter is not None

    def test_create_worker(self):
        from core.orchestration.adapter import OrcaAdapter, OrcaWorkerType
        adapter = OrcaAdapter(enabled=True)
        w = adapter.create_worker(OrcaWorkerType.RESEARCH, ["search", "analyze"])
        assert adapter.count() == 1
        assert w.worker_type == OrcaWorkerType.RESEARCH

    def test_shutdown(self):
        from core.orchestration.adapter import OrcaAdapter, OrcaWorkerType
        adapter = OrcaAdapter(enabled=True)
        w = adapter.create_worker(OrcaWorkerType.OCR)
        assert adapter.shutdown_worker(w.worker_id)
        assert adapter.count() == 1

    def test_summary(self):
        from core.orchestration.adapter import OrcaAdapter, OrcaWorkerType
        adapter = OrcaAdapter(enabled=True)
        adapter.create_worker(OrcaWorkerType.RESEARCH)
        adapter.create_worker(OrcaWorkerType.VERIFICATION)
        s = adapter.summary()
        assert s["workers"] == 2


class TestMemoryEngine:
    def test_imports(self):
        from core.memory import MemoryEngine, MemoryScope
        assert MemoryEngine is not None

    def test_store_retrieve(self):
        from core.memory.engine import MemoryEngine, MemoryScope
        mem = MemoryEngine()
        mem.store(MemoryScope.PROJECT, "arch_version", "1.0")
        results = mem.retrieve(MemoryScope.PROJECT, "arch_version")
        assert len(results) == 1
        assert results[0].value == "1.0"

    def test_search(self):
        from core.memory.engine import MemoryEngine, MemoryScope
        mem = MemoryEngine()
        mem.store(MemoryScope.RESEARCH, "ocr_tesseract", "works well")
        mem.store(MemoryScope.RESEARCH, "ocr_paddle", "better for hindi")
        results = mem.search("ocr")
        assert len(results) == 2

    def test_scoped_search(self):
        from core.memory.engine import MemoryEngine, MemoryScope
        mem = MemoryEngine()
        mem.store(MemoryScope.PROJECT, "key1", "val1")
        mem.store(MemoryScope.RESEARCH, "key1", "val2")
        results = mem.search("key1", scope=MemoryScope.PROJECT)
        assert len(results) == 1

    def test_summary(self):
        from core.memory.engine import MemoryEngine, MemoryScope
        mem = MemoryEngine()
        mem.store(MemoryScope.PROJECT, "a", 1)
        mem.store(MemoryScope.RESEARCH, "b", 2)
        s = mem.summary()
        assert s["total"] == 2


class TestAgencyRegistry:
    def test_imports(self):
        from core.automation.agents import AgencyRegistry, AgentType, AgentConfig
        assert AgencyRegistry is not None

    def test_register(self):
        from core.automation.agents import AgencyRegistry, AgentType, AgentConfig
        reg = AgencyRegistry()
        reg.register(AgentConfig(name="Research Agent", agent_type=AgentType.RESEARCH))
        assert reg.count() == 1

    def test_by_type(self):
        from core.automation.agents import AgencyRegistry, AgentType, AgentConfig
        reg = AgencyRegistry()
        reg.register(AgentConfig(name="R1", agent_type=AgentType.RESEARCH))
        reg.register(AgentConfig(name="V1", agent_type=AgentType.VERIFICATION))
        assert len(reg.get_by_type(AgentType.RESEARCH)) == 1


class TestObservability:
    def test_imports(self):
        from core.integrations import ObservabilityEngine
        assert ObservabilityEngine is not None

    def test_record(self):
        from core.integrations.observability import ObservabilityEngine
        eng = ObservabilityEngine()
        eng.record(running_workers=5, parallel_tasks=10, queue_size=3)
        snap = eng.get_latest()
        assert snap.running_workers == 5

    def test_history(self):
        from core.integrations.observability import ObservabilityEngine
        eng = ObservabilityEngine()
        for i in range(5):
            eng.record(running_workers=i)
        history = eng.get_history(3)
        assert len(history) == 3


class TestCodebaseMemory:
    def test_imports(self):
        from core.integrations import CodebaseMemory
        assert CodebaseMemory is not None

    def test_index_file(self):
        from core.integrations.codebase_memory import CodebaseMemory
        cbm = CodebaseMemory()
        idx = cbm.index_file("core/providers/router.py")
        assert idx.line_count > 0
        assert len(idx.functions) > 0

    def test_index_directory(self):
        from core.integrations.codebase_memory import CodebaseMemory
        cbm = CodebaseMemory()
        count = cbm.index_directory("core", extensions=[".py"])
        assert count > 0

    def test_symbol_search(self):
        from core.integrations.codebase_memory import CodebaseMemory
        cbm = CodebaseMemory()
        cbm.index_file("core/providers/router.py")
        results = cbm.search_symbol("OmniRouter")
        assert len(results) >= 1

    def test_summary(self):
        from core.integrations.codebase_memory import CodebaseMemory
        cbm = CodebaseMemory()
        cbm.index_file("core/providers/router.py")
        s = cbm.summary()
        assert s["total_files"] == 1


class TestPhase13InfraIntegration:
    def test_full_stack(self):
        from core.providers.router import OmniRouter, ProviderConfig, ModelCapabilities
        from core.workflows.engine import WorkflowEngine
        from core.orchestration.adapter import OrcaAdapter, OrcaWorkerType
        from core.memory.engine import MemoryEngine, MemoryScope
        from core.automation.agents import AgencyRegistry, AgentType, AgentConfig
        from core.integrations.observability import ObservabilityEngine
        from core.integrations.codebase_memory import CodebaseMemory

        # OmniRoute
        router = OmniRouter(enabled=True)
        router.register_provider(ProviderConfig(provider_id="openai", models=[ModelCapabilities(model_id="gpt-4")]))
        assert router.route("gpt-4")["routed"]

        # Workflows
        wf_eng = WorkflowEngine(enabled=True)
        wf_eng.register_step_handler("ocr", lambda i, c: {"ok": True})
        wf = wf_eng.create_book_workflow("BG")
        wf_eng.execute_step(wf.workflow_id)
        assert wf.current_step == 1

        # Orca
        orca = OrcaAdapter(enabled=True)
        orca.create_worker(OrcaWorkerType.RESEARCH)
        assert orca.count() == 1

        # Memory
        mem = MemoryEngine()
        mem.store(MemoryScope.EXECUTION, "last_run", "2026-07-13")
        assert len(mem.retrieve(MemoryScope.EXECUTION, "last_run")) == 1

        # Agency
        agency = AgencyRegistry()
        agency.register(AgentConfig(name="Evidence Agent", agent_type=AgentType.EVIDENCE))
        assert agency.count() == 1

        # Observability
        obs = ObservabilityEngine()
        obs.record(running_workers=3, parallel_tasks=8, evidence_confidence_avg=0.85)
        assert obs.get_latest().evidence_confidence_avg == 0.85

        # Codebase Memory
        cbm = CodebaseMemory()
        count = cbm.index_directory("core", extensions=[".py"])
        assert count > 10
