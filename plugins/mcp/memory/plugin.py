
"""Persistent memory for technology evaluations."""
from __future__ import annotations
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))
from astrosage.research.plugin_arch import Plugin, PluginManifest

class MemoryPlugin(Plugin):
    def __init__(self, memory_dir: str = "research/memory"):
        super().__init__(PluginManifest(name="memory", version="1.0.0", category="mcp",
            description="Persistent memory", dependencies=[]))
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)

    def initialize(self, config=None) -> bool: return True
    def execute(self, op: str, **kw) -> dict:
        if op == "store": return self._store(kw.get("key",""), kw.get("value",{}))
        if op == "retrieve": return self._retrieve(kw.get("key",""))
        if op == "list": return {"keys": [f.stem for f in self.memory_dir.glob("*.json")]}
        return {"error": f"Unknown: {op}"}
    def _store(self, k, v) -> dict: (self.memory_dir / f"{k}.json").write_text(json.dumps(v, indent=2)); return {"stored": True, "key": k}
    def _retrieve(self, k) -> dict: p = self.memory_dir / f"{k}.json"; return json.loads(p.read_text()) if p.exists() else {"error": f"Not found: {k}"}
    def health_check(self) -> dict: return {"status": "ok", "tool": "memory"}
