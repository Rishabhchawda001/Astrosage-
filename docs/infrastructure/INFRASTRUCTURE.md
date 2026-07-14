# AstroSage Infrastructure Layer

## Feature Flags

All integrations are feature-flagged and disabled by default.

| Feature | Flag | Default |
|---------|------|---------|
| OmniRoute | `OMNIROUTE_ENABLED` | `false` |
| N8N Workflows | `N8N_ENABLED` | `false` |
| Orca Adapter | `ORCA_ENABLED` | `false` |
| Codebase Memory | Always available | `true` |
| Agency Agents | Always available | `true` |
| Memory | Always available | `true` |
| Observability | Always available | `true` |

## Modules

- `core/providers/router.py` — OmniRoute model router
- `core/workflows/engine.py` — N8N-style resumable workflows
- `core/orchestration/adapter.py` — Orca compatibility adapter
- `core/memory/engine.py` — Multi-scope memory engine
- `core/automation/agents.py` — Specialist agent registry
- `core/integrations/observability.py` — System monitoring
- `core/integrations/codebase_memory.py` — Repository indexing and search

## Architecture Rules

1. All integrations are optional and feature-flagged
2. Existing pipeline continues working if every integration is disabled
3. No framework lock-in
4. Everything replaceable via plugin architecture
5. APEE remains the primary execution engine
