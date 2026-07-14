"""Phase APEE v2 — Adaptive Parallel Execution Engine Tests."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


# ── Event Bus Tests ───────────────────────────────────────────────────

class TestEventBus:
    def test_imports(self):
        from core.events import EventBus, Event, EventType
        assert EventBus is not None

    def test_publish_and_subscribe(self):
        from core.events.bus import EventBus, EventType
        bus = EventBus()
        received = []
        bus.subscribe(EventType.TASK_CREATED, lambda e: received.append(e))
        bus.emit(EventType.TASK_CREATED, source="test")
        assert len(received) == 1
        assert received[0].source == "test"

    def test_wildcard_subscribe(self):
        from core.events.bus import EventBus, EventType
        bus = EventBus()
        received = []
        bus.subscribe_all(lambda e: received.append(e))
        bus.emit(EventType.TASK_CREATED)
        bus.emit(EventType.TASK_COMPLETED)
        assert len(received) == 2

    def test_unsubscribe(self):
        from core.events.bus import EventBus, EventType
        bus = EventBus()
        handler = lambda e: None
        bus.subscribe(EventType.TASK_CREATED, handler)
        assert bus.unsubscribe(EventType.TASK_CREATED, handler)

    def test_history(self):
        from core.events.bus import EventBus, EventType
        bus = EventBus()
        bus.emit(EventType.TASK_CREATED)
        bus.emit(EventType.TASK_COMPLETED)
        history = bus.get_history()
        assert len(history) == 2

    def test_summary(self):
        from core.events.bus import EventBus, EventType
        bus = EventBus()
        bus.emit(EventType.TASK_CREATED)
        s = bus.summary()
        assert s["total_events"] == 1


# ── Task Graph Tests ──────────────────────────────────────────────────

class TestTaskGraph:
    def test_imports(self):
        from core.taskgraph import TaskGraph, Task, TaskStatus, TaskPriority, WorkerType
        assert TaskGraph is not None

    def test_add_tasks(self):
        from core.taskgraph.graph import TaskGraph, Task
        g = TaskGraph()
        t1 = Task(name="T1", task_id="T1")
        t2 = Task(name="T2", task_id="T2")
        g.add_task(t1)
        g.add_task(t2)
        assert g.count() == 2

    def test_dependency(self):
        from core.taskgraph.graph import TaskGraph, Task
        g = TaskGraph()
        g.add_task(Task(name="A", task_id="A"))
        g.add_task(Task(name="B", task_id="B", dependencies=["A"]))
        assert not g.has_cycle()
        order = g.topological_sort()
        assert order.index("A") < order.index("B")

    def test_cycle_detection(self):
        from core.taskgraph.graph import TaskGraph, Task
        g = TaskGraph()
        g.add_task(Task(name="A", task_id="A", dependencies=["C"]))
        g.add_task(Task(name="B", task_id="B", dependencies=["A"]))
        g.add_task(Task(name="C", task_id="C", dependencies=["B"]))
        assert g.has_cycle()

    def test_ready_tasks(self):
        from core.taskgraph.graph import TaskGraph, Task, TaskStatus
        g = TaskGraph()
        g.add_task(Task(name="A", task_id="A"))
        g.add_task(Task(name="B", task_id="B", dependencies=["A"]))
        ready = g.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].task_id == "A"
        # Complete A
        g.mark_completed("A")
        ready2 = g.get_ready_tasks()
        assert len(ready2) == 1

    def test_critical_path(self):
        from core.taskgraph.graph import TaskGraph, Task
        g = TaskGraph()
        g.add_task(Task(name="A", task_id="A", estimated_time=5))
        g.add_task(Task(name="B", task_id="B", estimated_time=3, dependencies=["A"]))
        g.add_task(Task(name="C", task_id="C", estimated_time=10))
        path = g.get_critical_path()
        assert len(path) >= 1

    def test_independent_sets(self):
        from core.taskgraph.graph import TaskGraph, Task
        g = TaskGraph()
        g.add_task(Task(name="A", task_id="A"))
        g.add_task(Task(name="B", task_id="B"))
        g.add_task(Task(name="C", task_id="C", dependencies=["A"]))
        levels = g.get_independent_sets()
        assert len(levels) >= 2
        assert "A" in levels[0]
        assert "B" in levels[0]

    def test_summary(self):
        from core.taskgraph.graph import TaskGraph, Task
        g = TaskGraph()
        g.add_task(Task(name="T1", task_id="T1"))
        s = g.summary()
        assert s["total_tasks"] == 1


# ── Worker Manager Tests ──────────────────────────────────────────────

class TestWorkerManager:
    def test_imports(self):
        from core.workers import WorkerManager, Worker, WorkerStatus
        assert WorkerManager is not None

    def test_register_worker(self):
        from core.workers.manager import WorkerManager, Worker
        mgr = WorkerManager()
        w = mgr.register()
        assert mgr.count() == 1
        assert w.worker_id.startswith("WR-")

    def test_find_worker(self):
        from core.workers.manager import WorkerManager, Worker, WorkerCapabilities, WorkerType
        from core.taskgraph.graph import Task, WorkerType as WT
        mgr = WorkerManager()
        mgr.register(Worker(capabilities=WorkerCapabilities(supported_types=[WT.CORE_ENGINE])))
        task = Task(name="T1", worker_type=WT.CORE_ENGINE)
        found = mgr.find_worker(task)
        assert found is not None

    def test_assign_and_complete(self):
        from core.workers.manager import WorkerManager
        from core.taskgraph.graph import Task
        mgr = WorkerManager()
        mgr.register()
        task = Task(name="T1", task_id="T1")
        worker = mgr.assign_task(task)
        assert worker is not None
        assert worker.status.value == "busy"
        mgr.complete_task("T1", success=True)
        assert worker.status.value == "idle"
        assert worker.metrics.tasks_completed == 1

    def test_worker_match(self):
        from core.workers.manager import Worker, WorkerCapabilities
        from core.taskgraph.graph import Task, WorkerType
        w = Worker(capabilities=WorkerCapabilities(supported_types=[WorkerType.CORE_ENGINE]))
        task = Task(name="T1", worker_type=WorkerType.CORE_ENGINE)
        assert w.matches_task(task)
        task2 = Task(name="T2", worker_type=WorkerType.PLUGIN)
        assert not w.matches_task(task2)

    def test_summary(self):
        from core.workers.manager import WorkerManager
        mgr = WorkerManager()
        mgr.register()
        s = mgr.summary()
        assert s["total_workers"] == 1


# ── Validator Registry Tests ──────────────────────────────────────────

class TestValidatorRegistry:
    def test_imports(self):
        from core.validators import ValidatorRegistry, Validator, ValidationCategory, ValidationResult
        assert ValidatorRegistry is not None

    def test_register_validator(self):
        from core.validators.registry import ValidatorRegistry, Validator, ValidationCategory
        reg = ValidatorRegistry()
        v = Validator(name="test", category=ValidationCategory.TESTING)
        reg.register(v)
        assert reg.count() == 1

    def test_run_validator(self):
        from core.validators.registry import ValidatorRegistry, Validator, ValidationCategory, ValidationResult
        reg = ValidatorRegistry()
        v = Validator(name="pass_test", category=ValidationCategory.TESTING, validate_fn=lambda ctx: True)
        reg.register(v)
        report = reg.run_validator(v.validator_id)
        assert report.result == ValidationResult.PASSED

    def test_run_all(self):
        from core.validators.registry import ValidatorRegistry, Validator, ValidationCategory
        reg = ValidatorRegistry()
        reg.register(Validator(name="v1", category=ValidationCategory.ARCHITECTURE))
        reg.register(Validator(name="v2", category=ValidationCategory.TESTING))
        results = reg.run_all()
        assert len(results) == 2

    def test_all_passed(self):
        from core.validators.registry import ValidatorRegistry, Validator, ValidationCategory, ValidationReport, ValidationResult
        reg = ValidatorRegistry()
        vid = reg.register(Validator(name="v1", category=ValidationCategory.CODE_QUALITY))
        report = ValidationReport(result=ValidationResult.PASSED)
        assert reg.all_passed({vid: report})

    def test_summary(self):
        from core.validators.registry import ValidatorRegistry, Validator, ValidationCategory
        reg = ValidatorRegistry()
        reg.register(Validator(name="v1", category=ValidationCategory.SECURITY))
        s = reg.summary()
        assert s["total_validators"] == 1


# ── Scheduler Tests ───────────────────────────────────────────────────

class TestScheduler:
    def test_imports(self):
        from core.scheduler import SmartScheduler, SchedulerMode
        assert SmartScheduler is not None

    def test_schedule_tasks(self):
        from core.scheduler.engine import SmartScheduler
        from core.taskgraph.graph import TaskGraph, Task
        sched = SmartScheduler()
        g = TaskGraph()
        g.add_task(Task(name="A", task_id="A", priority="high"))
        g.add_task(Task(name="B", task_id="B"))
        scheduled = sched.schedule(g)
        assert len(scheduled) == 2

    def test_dependency_order(self):
        from core.scheduler.engine import SmartScheduler
        from core.taskgraph.graph import TaskGraph, Task
        sched = SmartScheduler()
        g = TaskGraph()
        g.add_task(Task(name="A", task_id="A"))
        g.add_task(Task(name="B", task_id="B", dependencies=["A"]))
        sched.schedule(g)
        # Get next — should be A
        next_id = sched.get_next_task()
        assert next_id == "A"

    def test_retry(self):
        from core.scheduler.engine import SmartScheduler
        from core.taskgraph.graph import TaskGraph, Task, TaskStatus
        sched = SmartScheduler()
        g = TaskGraph()
        g.add_task(Task(name="A", task_id="A"))
        sched.schedule(g)
        sched.get_next_task()
        result = sched.on_task_failed(g, "A", "error")
        assert result == "A"  # Retried

    def test_empty_queue(self):
        from core.scheduler.engine import SmartScheduler
        sched = SmartScheduler()
        assert sched.get_next_task() is None
        assert sched.is_empty()

    def test_summary(self):
        from core.scheduler.engine import SmartScheduler
        sched = SmartScheduler()
        s = sched.summary()
        assert s["queue_size"] == 0


# ── Planner Tests ─────────────────────────────────────────────────────

class TestPlanner:
    def test_imports(self):
        from core.planner import PlannerEngine, WorkPackage
        assert PlannerEngine is not None

    def test_plan_phase(self):
        from core.planner.engine import PlannerEngine, WorkPackage
        from core.taskgraph.graph import WorkerType
        planner = PlannerEngine()
        pkgs = [
            WorkPackage(name="P1", worker_type=WorkerType.ARCHITECTURE),
            WorkPackage(name="P2", worker_type=WorkerType.CORE_ENGINE, dependencies=[""]),
        ]
        graph = planner.plan_phase("TestPhase", pkgs)
        assert graph.count() == 2

    def test_analyze(self):
        from core.planner.engine import PlannerEngine, WorkPackage
        planner = PlannerEngine()
        pkgs = [WorkPackage(name="P1"), WorkPackage(name="P2")]
        graph = planner.plan_phase("Phase", pkgs)
        analysis = planner.analyze_dependencies(graph)
        assert analysis["total_tasks"] == 2
        assert not analysis["has_cycle"]

    def test_estimate_time(self):
        from core.planner.engine import PlannerEngine, WorkPackage
        planner = PlannerEngine()
        pkgs = [WorkPackage(name="P1", estimated_time=5), WorkPackage(name="P2", estimated_time=3)]
        graph = planner.plan_phase("Phase", pkgs)
        total = planner.estimate_total_time(graph)
        assert total >= 5


# ── Executor Tests ────────────────────────────────────────────────────

class TestExecutor:
    def test_imports(self):
        from core.executor import ExecutorEngine, ExecutionMode, ExecutionResult
        assert ExecutorEngine is not None

    def test_execute_task(self):
        from core.executor.engine import ExecutorEngine
        from core.workers.manager import WorkerManager
        from core.taskgraph.graph import Task
        mgr = WorkerManager()
        mgr.register()
        executor = ExecutorEngine(mgr)
        executor.register_default_handler(lambda t, w: "output")
        task = Task(name="T1", task_id="T1")
        result = executor.execute_task(task)
        assert result.success
        assert result.output == "output"

    def test_execute_no_worker(self):
        from core.executor.engine import ExecutorEngine
        from core.workers.manager import WorkerManager
        from core.taskgraph.graph import Task
        mgr = WorkerManager()
        executor = ExecutorEngine(mgr)
        task = Task(name="T1", task_id="T1")
        result = executor.execute_task(task)
        assert not result.success
        assert "No available worker" in result.error

    def test_summary(self):
        from core.executor.engine import ExecutorEngine
        from core.workers.manager import WorkerManager
        mgr = WorkerManager()
        executor = ExecutorEngine(mgr)
        s = executor.summary()
        assert s["total_executions"] == 0


# ── Checkpoint Tests ──────────────────────────────────────────────────

class TestCheckpoint:
    def test_imports(self):
        from core.checkpoints import CheckpointEngine, Checkpoint
        assert CheckpointEngine is not None

    def test_create_checkpoint(self):
        from core.checkpoints.engine import CheckpointEngine, Checkpoint
        cp = Checkpoint(phase="test", completed_tasks=["T1", "T2"])
        assert cp.checkpoint_id.startswith("CP-")
        assert len(cp.completed_tasks) == 2

    def test_save_and_load(self):
        from core.checkpoints.engine import CheckpointEngine, Checkpoint
        engine = CheckpointEngine()
        cp = Checkpoint(phase="test")
        engine.save(cp)
        loaded = engine.load(cp.checkpoint_id)
        assert loaded is not None

    def test_create_from_graph(self):
        from core.checkpoints.engine import CheckpointEngine
        from core.taskgraph.graph import TaskGraph, Task, TaskStatus
        g = TaskGraph()
        g.add_task(Task(name="T1", task_id="T1"))
        g.mark_completed("T1")
        engine = CheckpointEngine()
        cp = engine.create_from_graph("test", g.tasks(), [])
        assert len(cp.completed_tasks) == 1

    def test_summary(self):
        from core.checkpoints.engine import CheckpointEngine
        engine = CheckpointEngine()
        s = engine.summary()
        assert s["total_checkpoints"] == 0


# ── Progress Tracker Tests ────────────────────────────────────────────

class TestProgressTracker:
    def test_imports(self):
        from core.progress import ProgressTracker, ProgressSnapshot
        assert ProgressTracker is not None

    def test_snapshot(self):
        from core.progress.tracker import ProgressTracker
        pt = ProgressTracker()
        pt.start()
        snap = pt.snapshot(10, 5, 1, 2, 2, 4, 1)
        assert snap.completion_pct == 50.0
        assert snap.utilization == 0.75

    def test_retry_tracking(self):
        from core.progress.tracker import ProgressTracker
        pt = ProgressTracker()
        pt.record_retry()
        pt.record_retry()
        assert pt.summary()["retry_count"] == 2

    def test_summary(self):
        from core.progress.tracker import ProgressTracker
        pt = ProgressTracker()
        pt.start()
        s = pt.summary()
        assert s["snapshots"] == 0


# ── Resource Manager Tests ────────────────────────────────────────────

class TestResourceManager:
    def test_imports(self):
        from core.resources import ResourceManager, ResourceSnapshot, ResourceLimits
        assert ResourceManager is not None

    def test_snapshot(self):
        from core.resources.manager import ResourceManager
        rm = ResourceManager()
        snap = rm.snapshot()
        assert snap.timestamp != ""

    def test_allocate_release(self):
        from core.resources.manager import ResourceManager
        rm = ResourceManager()
        assert rm.allocate("task-1", cpu=2.0, ram=100.0)
        rm.release("task-1")

    def test_summary(self):
        from core.resources.manager import ResourceManager
        rm = ResourceManager()
        s = rm.summary()
        assert s["snapshots"] == 0


# ── Queue Manager Tests ───────────────────────────────────────────────

class TestQueueManager:
    def test_imports(self):
        from core.queues import QueueManager, TaskQueue, QueueItem, QueueType
        assert QueueManager is not None

    def test_enqueue_dequeue(self):
        from core.queues.manager import QueueManager, QueueItem
        qm = QueueManager()
        qm.enqueue("default", QueueItem(task_id="T1", priority=1))
        qm.enqueue("default", QueueItem(task_id="T2", priority=0))
        item = qm.dequeue("default")
        assert item.task_id == "T2"  # Higher priority first

    def test_create_queue(self):
        from core.queues.manager import QueueManager, QueueType
        qm = QueueManager()
        qm.create_queue("priority", QueueType.PRIORITY)
        assert "priority" in qm.queue_names()

    def test_steal(self):
        from core.queues.manager import QueueManager, QueueItem
        qm = QueueManager()
        qm.enqueue("worker-1", QueueItem(task_id="T1", priority=1))
        qm.enqueue("worker-1", QueueItem(task_id="T2", priority=0))
        stolen = qm.steal("worker-1")
        assert stolen.task_id == "T1"  # Lowest priority stolen

    def test_summary(self):
        from core.queues.manager import QueueManager
        qm = QueueManager()
        s = qm.summary()
        assert s["total_queues"] == 1


# ── Orchestrator Tests ────────────────────────────────────────────────

class TestOrchestrator:
    def test_imports(self):
        from core.orchestrator import OrchestratorEngine, OrchestratorStatus, PhaseExecution
        assert OrchestratorEngine is not None

    def test_plan_phase(self):
        from core.orchestrator.engine import OrchestratorEngine
        from core.planner.engine import WorkPackage
        orch = OrchestratorEngine()
        pkgs = [WorkPackage(name="P1"), WorkPackage(name="P2")]
        graph = orch.plan_phase("TestPhase", pkgs)
        assert graph.count() == 2

    def test_execute_phase(self):
        from core.orchestrator.engine import OrchestratorEngine
        from core.workers.manager import Worker
        from core.planner.engine import WorkPackage
        orch = OrchestratorEngine()
        orch.worker_manager.register()
        orch.executor.register_default_handler(lambda t, w: "done")
        pkgs = [WorkPackage(name="P1")]
        graph = orch.plan_phase("TestPhase", pkgs)
        execution = orch.execute_phase("TestPhase", graph)
        assert execution.completed == 1

    def test_register_validator(self):
        from core.orchestrator.engine import OrchestratorEngine
        from core.validators.registry import ValidationCategory
        orch = OrchestratorEngine()
        vid = orch.register_validator(ValidationCategory.TESTING, "test_val")
        assert vid is not None

    def test_summary(self):
        from core.orchestrator.engine import OrchestratorEngine
        orch = OrchestratorEngine()
        s = orch.summary()
        assert "workers" in s
        assert "validators" in s


# ── Integration Tests ─────────────────────────────────────────────────

class TestAPEEv2Integration:
    def test_full_orchestration(self):
        """Test complete APEE v2 pipeline: plan → schedule → execute → validate → checkpoint."""
        from core.orchestrator.engine import OrchestratorEngine
        from core.workers.manager import Worker, WorkerCapabilities
        from core.validators.registry import Validator, ValidationCategory
        from core.planner.engine import WorkPackage

        orch = OrchestratorEngine()

        # Register workers
        for i in range(3):
            orch.worker_manager.register(Worker(
                capabilities=WorkerCapabilities(supported_types=["any"]),
            ))

        # Register validators
        for cat in ValidationCategory:
            orch.register_validator(cat, cat.value)

        # Register handler
        orch.executor.register_default_handler(lambda t, w: f"completed:{t.name}")

        # Plan phase
        pkgs = [
            WorkPackage(name="Architecture", estimated_time=2),
            WorkPackage(name="Core Engine", estimated_time=5),
            WorkPackage(name="Testing", estimated_time=3),
        ]
        graph = orch.plan_phase("TestPhase", pkgs)

        # Execute
        execution = orch.execute_phase("TestPhase", graph)
        assert execution.completed >= 1

        # Checkpoint
        cp_id = orch.save_checkpoint()

        # Validate
        results = orch.run_validators()

        # Event history
        events = orch.event_bus.get_history()
        assert len(events) >= 1

        # Progress
        progress = orch.progress.summary()

        # Summary
        summary = orch.summary()
        assert summary["executions"] >= 1
