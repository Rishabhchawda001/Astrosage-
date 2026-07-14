# Hierarchy Builder Skill

## Purpose
Build parent-child graphs for document structure.

## Core Module
`core/hierarchy/engine.py`

## Usage
```python
from core.hierarchy import HierarchyEngine
engine = HierarchyEngine()
engine.register_chunk(chunk)
children = engine.get_children(node_id)
ancestors = engine.get_ancestors(node_id)
```
