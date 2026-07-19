#!/usr/bin/env python3
"""
AstroSage Evaluation Runner — CI/CD Integration Script

Usage:
    python3 scripts/run_evaluation.py                    # Run full evaluation
    python3 scripts/run_evaluation.py --retrieval-only   # Run retrieval only
    python3 scripts/run_evaluation.py --hallucination-only  # Run hallucination only
    python3 scripts/run_evaluation.py --validate          # Validate golden dataset
    python3 scripts/run_evaluation.py --report            # Generate report only

Exit codes:
    0 = All quality gates pass
    1 = One or more quality gates fail
    2 = Error during execution
"""
import sys
import json
import argparse
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from evaluation.golden_loader import GoldenDatasetLoader
from evaluation.runner import EvaluationRunner


def main():
    parser = argparse.ArgumentParser(description="AstroSage Evaluation Runner")
    parser.add_argument("--retrieval-only", action="store_true",
                        help="Run retrieval evaluation only")
    parser.add_argument("--hallucination-only", action="store_true",
                        help="Run hallucination evaluation only")
    parser.add_argument("--validate", action="store_true",
                        help="Validate golden dataset only")
    parser.add_argument("--report", action="store_true",
                        help="Print existing report")
    parser.add_argument("--commit", default="",
                        help="Git commit hash for the report")
    args = parser.parse_args()

    if args.report:
        report_path = ROOT / "evaluation" / "evaluation_report.json"
        if not report_path.exists():
            print("No evaluation report found. Run evaluation first.")
            sys.exit(2)
        with open(report_path) as f:
            report = json.load(f)
        print(json.dumps(report["quality_gates"], indent=2))
        sys.exit(0 if report["quality_gates"]["verdict"] == "PASS" else 1)

    if args.validate:
        loader = GoldenDatasetLoader()
        loader.load()
        result = loader.validate()
        print(json.dumps(result, indent=2))
        sys.exit(0 if result["valid"] else 1)

    runner = EvaluationRunner()

    if args.retrieval_only:
        print("Running retrieval evaluation...")
        result = runner.run_retrieval_evaluation()
        print(json.dumps(result, indent=2))
        sys.exit(0)

    if args.hallucination_only:
        print("Running hallucination evaluation...")
        result = runner.run_hallucination_evaluation()
        print(json.dumps(result, indent=2))
        sys.exit(0)

    # Full evaluation
    print("=" * 60)
    print("AstroSage Evaluation Suite v1.1")
    print("=" * 60)
    report = runner.run_full_evaluation(commit=args.commit)

    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)

    r = report["retrieval"]
    print(f"Retrieval:   P95={r['p95_latency_ms']}ms, "
          f"EntityRecall={r['entity_recall']:.1%}, "
          f"NDCG@5={r['avg_ndcg_at_5']:.3f}, "
          f"PassRate={r['pass_rate']:.1%}")

    h = report["hallucination"]
    print(f"Hallucination: RejectRate={h['rejection_rate']:.1%}, "
          f"MaxConf={h['max_confidence_on_adversarial']:.2f}, "
          f"Passed={h['passed']}")

    g = report["quality_gates"]
    print(f"Quality Gates: {g['verdict']} "
          f"({g['passed_gates']}/{g['total_gates']} passed)")

    for gate in g["gates"]:
        status = "✓" if gate["passed"] else "✗"
        print(f"  {status} {gate['name']}: {gate['actual']:.4f} vs {gate['threshold']}")

    print("\n" + "=" * 60)
    print(f"OVERALL VERDICT: {g['verdict']}")
    print("=" * 60)

    sys.exit(0 if g["verdict"] == "PASS" else 1)


if __name__ == "__main__":
    main()
