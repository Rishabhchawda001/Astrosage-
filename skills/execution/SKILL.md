# Execution Skill

## Purpose
Execute tasks using the orchestrator engine.

## Core Module
`core/orchestrator/engine.py`

## Usage
```python
from core.orchestrator import OrchestratorEngine
from core.planner import WorkPackage
orch = OrchestratorEngine()
graph = orch.plan_phase("Phase", packages)
execution = orch.execute_phase("Phase", graph)
```
