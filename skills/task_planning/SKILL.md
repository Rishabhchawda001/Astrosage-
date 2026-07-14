# Task Planning Skill

## Purpose
Automatic task decomposition and execution graph generation.

## Core Module
`core/planner/engine.py`

## Usage
```python
from core.planner import PlannerEngine, WorkPackage
planner = PlannerEngine()
graph = planner.plan_phase("PhaseName", packages)
analysis = planner.analyze_dependencies(graph)
```
