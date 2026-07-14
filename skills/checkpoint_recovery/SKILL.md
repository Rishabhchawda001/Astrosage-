# Checkpoint Recovery Skill

## Purpose
Save and restore execution state for resume.

## Core Module
`core/checkpoints/engine.py`

## Usage
```python
from core.checkpoints import CheckpointEngine
engine = CheckpointEngine()
cp = engine.create_from_graph(phase, tasks, queue)
restored = engine.load(cp.checkpoint_id)
```
