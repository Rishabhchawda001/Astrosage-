"""Regression evaluator — detects quality degradation across runs."""
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RegressionBaseline:
    timestamp: str = ""
    commit: str = ""
    metrics: dict = field(default_factory=dict)
    fingerprint: str = ""


@dataclass
class RegressionResult:
    metric_name: str
    baseline_value: float
    current_value: float
    delta: float
    delta_pct: float
    direction: str  # "higher_is_better" or "lower_is_better"
    degraded: bool = False
    within_tolerance: bool = True


@dataclass
class RegressionReport:
    timestamp: str = ""
    commit: str = ""
    baseline_timestamp: str = ""
    total_metrics: int = 0
    passed_metrics: int = 0
    degraded_metrics: int = 0
    improved_metrics: int = 0
    results: list[RegressionResult] = field(default_factory=list)
    passed: bool = False


DEFAULT_TOLERANCE = 0.05  # 5% degradation allowed


class RegressionEvaluator:
    """Detects quality regression by comparing against a baseline."""

    def __init__(
        self,
        baseline_path: str = "evaluation/regression_baseline.json",
        tolerance: float = DEFAULT_TOLERANCE,
    ):
        self.baseline_path = Path(baseline_path)
        self.tolerance = tolerance
        self._baseline: Optional[RegressionBaseline] = None

    def load_baseline(self) -> Optional[RegressionBaseline]:
        if not self.baseline_path.exists():
            return None
        with open(self.baseline_path) as f:
            data = json.load(f)
        self._baseline = RegressionBaseline(**data)
        return self._baseline

    def save_baseline(self, metrics: dict, commit: str = ""):
        baseline = RegressionBaseline(
            timestamp=datetime.now(timezone.utc).isoformat(),
            commit=commit,
            metrics=metrics,
            fingerprint=hashlib.sha256(
                json.dumps(metrics, sort_keys=True).encode()
            ).hexdigest(),
        )
        self.baseline_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.baseline_path, "w") as f:
            json.dump(
                {
                    "timestamp": baseline.timestamp,
                    "commit": baseline.commit,
                    "metrics": baseline.metrics,
                    "fingerprint": baseline.fingerprint,
                },
                f,
                indent=2,
            )
        self._baseline = baseline
        return baseline

    def evaluate(
        self,
        current_metrics: dict,
        directions: Optional[dict[str, str]] = None,
    ) -> RegressionReport:
        """Compare current metrics against baseline."""
        if self._baseline is None:
            self.load_baseline()
        if self._baseline is None:
            return RegressionReport(
                timestamp=datetime.now(timezone.utc).isoformat(),
                total_metrics=len(current_metrics),
                passed=True,
                results=[],
            )

        directions = directions or {}
        results = []
        for metric_name, current_val in current_metrics.items():
            baseline_val = self._baseline.metrics.get(metric_name)
            if baseline_val is None:
                continue
            if not isinstance(current_val, (int, float)) or not isinstance(
                baseline_val, (int, float)
            ):
                continue

            direction = directions.get(metric_name, "higher_is_better")
            delta = current_val - baseline_val
            delta_pct = abs(delta) / max(abs(baseline_val), 0.0001)

            if direction == "higher_is_better":
                degraded = delta < 0 and delta_pct > self.tolerance
                improved = delta > 0 and delta_pct > self.tolerance
            else:
                degraded = delta > 0 and delta_pct > self.tolerance
                improved = delta < 0 and delta_pct > self.tolerance

            results.append(
                RegressionResult(
                    metric_name=metric_name,
                    baseline_value=baseline_val,
                    current_value=current_val,
                    delta=delta,
                    delta_pct=delta_pct,
                    direction=direction,
                    degraded=degraded,
                    within_tolerance=not degraded,
                )
            )

        degraded_count = sum(1 for r in results if r.degraded)
        improved_count = sum(
            1
            for r in results
            if (r.direction == "higher_is_better" and r.delta > 0)
            or (r.direction == "lower_is_better" and r.delta < 0)
        )

        return RegressionReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            commit=self._baseline.commit,
            baseline_timestamp=self._baseline.timestamp,
            total_metrics=len(results),
            passed_metrics=len(results) - degraded_count,
            degraded_metrics=degraded_count,
            improved_metrics=improved_count,
            results=results,
            passed=degraded_count == 0,
        )

    def to_dict(self, report: RegressionReport) -> dict:
        return {
            "timestamp": report.timestamp,
            "baseline_timestamp": report.baseline_timestamp,
            "total_metrics": report.total_metrics,
            "passed_metrics": report.passed_metrics,
            "degraded_metrics": report.degraded_metrics,
            "improved_metrics": report.improved_metrics,
            "regression_rate": round(
                report.degraded_metrics / max(report.total_metrics, 1), 4
            ),
            "details": [
                {
                    "metric": r.metric_name,
                    "baseline": r.baseline_value,
                    "current": r.current_value,
                    "delta_pct": round(r.delta_pct, 4),
                    "degraded": r.degraded,
                }
                for r in report.results
            ],
            "passed": report.passed,
        }
