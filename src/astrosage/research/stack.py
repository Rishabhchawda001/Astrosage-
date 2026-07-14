
"""AstroSage Research Stack."""
from __future__ import annotations
from pathlib import Path
from .scoring import TechnologyCatalog
from .plugin_arch import PluginRegistry
from .benchmark import BenchmarkHarness

class ResearchStack:
    def __init__(self, base_dir: str = "."):
        self.base = Path(base_dir)
        self.catalog = TechnologyCatalog(self.base / "research/catalog/technology_catalog.json")
        self.registry = PluginRegistry()
        self.benchmarks = BenchmarkHarness(self.base / "research/benchmarks")

    def initialize(self) -> dict:
        self.catalog = TechnologyCatalog.load(self.base / "research/catalog/technology_catalog.json")
        return {"catalog_loaded": len(self.catalog.technologies), "plugins": len(self.registry._plugins),
                "categories": self.catalog.get_categories()}

    def status(self) -> dict:
        return {"catalog": self.catalog.summary(), "plugins": self.registry.list_plugins()}
