
"""GitHub search plugin."""
from __future__ import annotations
import json
import subprocess
from typing import Any
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))
from astrosage.research.plugin_arch import Plugin, PluginManifest

class GitHubPlugin(Plugin):
    def __init__(self):
        super().__init__(PluginManifest(name="github_search", version="1.0.0", category="mcp",
            description="GitHub repository and code search", dependencies=["curl"]))

    def initialize(self, config=None) -> bool:
        return True

    def execute(self, operation: str, **kwargs) -> Any:
        if operation == "search_repos":
            return self._search_repos(kwargs.get("query", ""))
        return {"error": f"Unknown operation: {operation}"}

    def _search_repos(self, query: str) -> dict:
        try:
            result = subprocess.run(
                ["curl", "-s", f"https://api.github.com/search/repositories?q={query}&sort=stars&per_page=5"],
                capture_output=True, text=True, timeout=10)
            data = json.loads(result.stdout)
            repos = []
            for item in data.get("items", [])[:5]:
                repos.append({"name": item["full_name"], "stars": item["stargazers_count"],
                    "license": item.get("license", {}).get("spdx_id", "Unknown"),
                    "description": item.get("description", "")[:100], "url": item["html_url"]})
            return {"repos": repos, "total": data.get("total_count", 0)}
        except Exception as e:
            return {"error": str(e)}

    def health_check(self) -> dict:
        return {"status": "ok", "tool": "github_search"}
