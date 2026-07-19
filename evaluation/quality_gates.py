"""Release quality gates — defines pass/fail criteria for releases."""
import json
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GateResult:
    gate_name: str
    metric: str
    threshold: float
    actual: float
    passed: bool
    message: str = ""


@dataclass
class QualityGateReport:
    timestamp: str = ""
    version: str = ""
    gates: list[GateResult] = field(default_factory=list)
    total_gates: int = 0
    passed_gates: int = 0
    failed_gates: int = 0
    verdict: str = "PENDING"

    @property
    def passed(self) -> bool:
        return self.verdict == "PASS"


# Default quality gate thresholds
DEFAULT_GATES = {
    "retrieval_latency_p95_ms": {
        "threshold": 100.0,
        "direction": "lower_is_better",
        "description": "P95 retrieval latency must be under 100ms",
    },
    "retrieval_entity_recall": {
        "threshold": 0.3,
        "direction": "higher_is_better",
        "description": "Entity recall must be at least 30%",
    },
    "retrieval_ndcg_at_5": {
        "threshold": 0.3,
        "direction": "higher_is_better",
        "description": "NDCG@5 must be at least 0.3",
    },
    "hallucination_rejection_rate": {
        "threshold": 0.8,
        "direction": "higher_is_better",
        "description": "Must reject at least 80% of adversarial queries",
    },
    "hallucination_max_confidence": {
        "threshold": 0.6,
        "direction": "lower_is_better",
        "description": "Max confidence on adversarial queries must be under 0.6",
    },
    "regression_rate": {
        "threshold": 0.1,
        "direction": "lower_is_better",
        "description": "No more than 10% of metrics should regress",
    },
    "graph_integrity": {
        "threshold": 1.0,
        "direction": "higher_is_better",
        "description": "Graph integrity score must be 100%",
    },
    "test_pass_rate": {
        "threshold": 0.95,
        "direction": "higher_is_better",
        "description": "At least 95% of tests must pass",
    },
}


class QualityGates:
    """Evaluates whether a version meets release quality criteria."""

    def __init__(self, gates: Optional[dict] = None):
        self.gates_config = gates or DEFAULT_GATES

    def evaluate(self, metrics: dict, version: str = "1.1.0") -> QualityGateReport:
        results = []
        for gate_name, config in self.gates_config.items():
            actual = metrics.get(gate_name)
            if actual is None:
                results.append(
                    GateResult(
                        gate_name=gate_name,
                        metric=gate_name,
                        threshold=config["threshold"],
                        actual=0.0,
                        passed=False,
                        message="Metric not reported",
                    )
                )
                continue

            threshold = config["threshold"]
            direction = config["direction"]

            if direction == "higher_is_better":
                passed = actual >= threshold
            else:
                passed = actual <= threshold

            results.append(
                GateResult(
                    gate_name=gate_name,
                    metric=gate_name,
                    threshold=threshold,
                    actual=actual,
                    passed=passed,
                    message=f"{config['description']}: {actual} vs {threshold}",
                )
            )

        passed_count = sum(1 for r in results if r.passed)
        failed_count = len(results) - passed_count

        report = QualityGateReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            version=version,
            gates=results,
            total_gates=len(results),
            passed_gates=passed_count,
            failed_gates=failed_count,
            verdict="PASS" if failed_count == 0 else "FAIL",
        )
        return report

    def to_dict(self, report: QualityGateReport) -> dict:
        return {
            "timestamp": report.timestamp,
            "version": report.version,
            "verdict": report.verdict,
            "total_gates": report.total_gates,
            "passed_gates": report.passed_gates,
            "failed_gates": report.failed_gates,
            "pass_rate": round(
                report.passed_gates / max(report.total_gates, 1), 4
            ),
            "gates": [
                {
                    "name": g.gate_name,
                    "threshold": g.threshold,
                    "actual": g.actual,
                    "passed": g.passed,
                    "message": g.message,
                }
                for g in report.gates
            ],
        }
