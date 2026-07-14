
"""Safe filesystem operations."""
from __future__ import annotations
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))
from astrosage.research.plugin_arch import Plugin, PluginManifest

class FilesystemPlugin(Plugin):
    def __init__(self):
        super().__init__(PluginManifest(name="filesystem", version="1.0.0", category="mcp",
            description="File read/write/search", dependencies=[]))
    def initialize(self, config=None) -> bool: return True
    def execute(self, op: str, **kw) -> dict:
        if op == "read": p=Path(kw.get("path","")); return {"content": p.read_text("utf-8","replace")[:10000], "size":p.stat().st_size}
        if op == "write": p=Path(kw.get("path","")); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(kw.get("content","")); return {"written": True, "path": str(p)}
        return {"error": f"Unknown: {op}"}
    def health_check(self) -> dict: return {"status": "ok", "tool": "filesystem"}
