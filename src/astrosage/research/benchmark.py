
"""Reusable Benchmark Framework."""
from __future__ import annotations
import json, time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

@dataclass
class BenchmarkResult:
    benchmark_name: str
    tool_name: str
    version: str
    timestamp: str = ""
    duration_sec: float = 0.0
    metrics: dict = field(default_factory=dict)
    passed: bool = True
    notes: str = ""
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

class BenchmarkHarness:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: list[BenchmarkResult] = []

    def run_benchmark(self, name: str, tool: str, version: str, func, **kwargs) -> BenchmarkResult:
        start = time.time()
        metrics, passed, notes = {}, True, ""
        try:
            metrics = func(**kwargs)
        except Exception as e:
            passed, notes = False, str(e)
            metrics = {"error": str(e)}
        result = BenchmarkResult(benchmark_name=name, tool_name=tool, version=version,
            duration_sec=round(time.time() - start, 3), metrics=metrics, passed=passed, notes=notes)
        self.results.append(result)
        return result

    def save_results(self, name: str) -> str:
        path = self.output_dir / f"{name}_benchmark.json"
        path.write_text(json.dumps([asdict(r) for r in self.results], indent=2, default=str))
        return str(path)

    def get_summary(self) -> dict:
        return {"total": len(self.results), "passed": sum(1 for r in self.results if r.passed),
                "failed": sum(1 for r in self.results if not r.passed)}
