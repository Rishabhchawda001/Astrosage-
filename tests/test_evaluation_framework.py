"""Tests for the v1.1 Evaluation Framework."""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestGoldenDatasetLoader:
    def test_loads_dataset(self):
        from evaluation.golden_loader import GoldenDatasetLoader
        loader = GoldenDatasetLoader()
        loader.load()
        assert loader.total > 0

    def test_has_all_categories(self):
        from evaluation.golden_loader import GoldenDatasetLoader
        loader = GoldenDatasetLoader()
        loader.load()
        cats = loader.categories
        assert "entity_factual" in cats
        assert "relationship" in cats
        assert "conceptual" in cats
        assert "cross_scripture" in cats
        assert "reasoning" in cats
        assert "adversarial" in cats

    def test_by_category(self):
        from evaluation.golden_loader import GoldenDatasetLoader
        loader = GoldenDatasetLoader()
        loader.load()
        adversarial = loader.by_category("adversarial")
        assert len(adversarial) >= 5
        for q in adversarial:
            assert q.difficulty == "adversarial"

    def test_by_difficulty(self):
        from evaluation.golden_loader import GoldenDatasetLoader
        loader = GoldenDatasetLoader()
        loader.load()
        easy = loader.by_difficulty("easy")
        assert len(easy) > 0

    def test_validate(self):
        from evaluation.golden_loader import GoldenDatasetLoader
        loader = GoldenDatasetLoader()
        loader.load()
        result = loader.validate()
        assert result["valid"]
        assert result["total_questions"] > 0

    def test_unique_ids(self):
        from evaluation.golden_loader import GoldenDatasetLoader
        loader = GoldenDatasetLoader()
        loader.load()
        ids = [q.id for q in loader.questions]
        assert len(ids) == len(set(ids))


class TestRetrievalEvaluator:
    def test_evaluate_relevant_result(self):
        from evaluation.retrieval_eval import RetrievalEvaluator
        from evaluation.golden_loader import EvalQuestion
        evaluator = RetrievalEvaluator()
        q = EvalQuestion(
            id="test", category="test", question="Who is Vishnu?",
            expected_entities=["Vishnu"], expected_scriptures=["BG"],
        )
        chunks = [
            {"entity_links": [{"name": "Vishnu"}], "scripture_id": "BG"},
            {"entity_links": [{"name": "Shiva"}], "scripture_id": "SHIV"},
        ]
        result = evaluator.evaluate_question(q, chunks, 10.0)
        assert result.expected_entities_found == 1
        assert result.expected_scriptures_found == 1
        assert result.passed

    def test_evaluate_irrelevant_result(self):
        from evaluation.retrieval_eval import RetrievalEvaluator
        from evaluation.golden_loader import EvalQuestion
        evaluator = RetrievalEvaluator()
        q = EvalQuestion(
            id="test", category="test", question="Who is Vishnu?",
            expected_entities=["Vishnu"], expected_scriptures=["BG"],
        )
        chunks = [
            {"entity_links": [{"name": "Shiva"}], "scripture_id": "SHIV"},
        ]
        result = evaluator.evaluate_question(q, chunks, 10.0)
        assert result.expected_entities_found == 0
        assert not result.passed

    def test_empty_results(self):
        from evaluation.retrieval_eval import RetrievalEvaluator
        from evaluation.golden_loader import EvalQuestion
        evaluator = RetrievalEvaluator()
        q = EvalQuestion(
            id="test", category="test", question="Who is Vishnu?",
            expected_entities=["Vishnu"], expected_scriptures=["BG"],
        )
        result = evaluator.evaluate_question(q, [], 10.0)
        assert not result.passed

    def test_aggregate(self):
        from evaluation.retrieval_eval import RetrievalEvaluator, RetrievalResult
        evaluator = RetrievalEvaluator()
        results = [
            RetrievalResult(
                question_id="q1", query="test", latency_ms=10.0,
                expected_entities_found=1, expected_entities_total=1,
                expected_scriptures_found=1, expected_scriptures_total=1,
                precision_at_k=0.5, recall_at_k=0.5, ndcg=0.8, passed=True,
            ),
            RetrievalResult(
                question_id="q2", query="test", latency_ms=20.0,
                expected_entities_found=0, expected_entities_total=1,
                expected_scriptures_found=0, expected_scriptures_total=1,
                precision_at_k=0.0, recall_at_k=0.0, ndcg=0.0, passed=False,
            ),
        ]
        bench = evaluator.aggregate(results)
        assert bench.total_queries == 2
        assert bench.passed_queries == 1
        assert bench.avg_latency_ms == 15.0

    def test_latency_threshold(self):
        from evaluation.retrieval_eval import RetrievalEvaluator
        from evaluation.golden_loader import EvalQuestion
        evaluator = RetrievalEvaluator(latency_threshold_ms=5.0)
        q = EvalQuestion(
            id="test", category="test", question="test",
            expected_entities=["Vishnu"], expected_scriptures=["BG"],
        )
        chunks = [{"entity_links": [{"name": "Vishnu"}], "scripture_id": "BG"}]
        result = evaluator.evaluate_question(q, chunks, 10.0)  # Above threshold
        assert not result.passed  # Latency too high

    def test_to_dict(self):
        from evaluation.retrieval_eval import RetrievalEvaluator, RetrievalBenchmark
        evaluator = RetrievalEvaluator()
        bench = RetrievalBenchmark(avg_latency_ms=10.0, total_queries=1, passed_queries=1)
        d = evaluator.to_dict(bench)
        assert "avg_latency_ms" in d
        assert "pass_rate" in d


class TestHallucinationEvaluator:
    def test_low_confidence_passes(self):
        from evaluation.hallucination_eval import HallucinationEvaluator
        from evaluation.golden_loader import EvalQuestion
        evaluator = HallucinationEvaluator()
        q = EvalQuestion(
            id="AV-001", category="adversarial", question="test",
            difficulty="adversarial", min_confidence="low",
        )
        result = evaluator.evaluate_question(q, {
            "confidence": "low",
            "evidence": {"sources": []},
            "entities": [],
        })
        assert result.correctly_low_confidence
        assert result.passed

    def test_high_confidence_fails(self):
        from evaluation.hallucination_eval import HallucinationEvaluator
        from evaluation.golden_loader import EvalQuestion
        evaluator = HallucinationEvaluator()
        q = EvalQuestion(
            id="AV-001", category="adversarial", question="test",
            difficulty="adversarial", min_confidence="low",
        )
        result = evaluator.evaluate_question(q, {
            "confidence": "high",
            "evidence": {"sources": [{"x": 1}] * 10},
            "entities": [],
        })
        assert not result.correctly_low_confidence
        assert not result.passed

    def test_aggregate(self):
        from evaluation.hallucination_eval import HallucinationEvaluator, HallucinationResult
        evaluator = HallucinationEvaluator()
        results = [
            HallucinationResult(question_id="q1", query="t", confidence_score=0.25, correctly_low_confidence=True, passed=True),
            HallucinationResult(question_id="q2", query="t", confidence_score=0.25, correctly_low_confidence=True, passed=True),
        ]
        bench = evaluator.aggregate(results)
        assert bench.total_adversarial == 2
        assert bench.correctly_rejected == 2
        assert bench.passed

    def test_to_dict(self):
        from evaluation.hallucination_eval import HallucinationEvaluator, HallucinationBenchmark
        evaluator = HallucinationEvaluator()
        bench = HallucinationBenchmark(total_adversarial=10, correctly_rejected=9, passed=False)
        d = evaluator.to_dict(bench)
        assert "rejection_rate" in d
        assert d["rejection_rate"] == 0.9


class TestRegressionEvaluator:
    def test_no_baseline(self):
        from evaluation.regression_eval import RegressionEvaluator
        evaluator = RegressionEvaluator(baseline_path="/tmp/test_nonexist.json")
        report = evaluator.evaluate({"metric1": 1.0})
        assert report.passed  # No baseline = pass

    def test_with_baseline(self):
        from evaluation.regression_eval import RegressionEvaluator
        evaluator = RegressionEvaluator(
            baseline_path="/tmp/test_regression_baseline.json",
            tolerance=0.1,
        )
        evaluator.save_baseline({"metric1": 1.0, "metric2": 2.0}, commit="test")
        report = evaluator.evaluate({"metric1": 1.05, "metric2": 1.8})
        assert report.passed  # Within 10% tolerance

    def test_regression_detected(self):
        from evaluation.regression_eval import RegressionEvaluator
        evaluator = RegressionEvaluator(
            baseline_path="/tmp/test_regression_detect.json",
            tolerance=0.05,
        )
        evaluator.save_baseline({"metric1": 1.0}, commit="test")
        report = evaluator.evaluate({"metric1": 0.8})  # 20% drop
        assert not report.passed
        assert report.degraded_metrics == 1

    def test_improvement_detected(self):
        from evaluation.regression_eval import RegressionEvaluator
        evaluator = RegressionEvaluator(
            baseline_path="/tmp/test_regression_improve.json",
            tolerance=0.05,
        )
        evaluator.save_baseline({"metric1": 1.0}, commit="test")
        report = evaluator.evaluate({"metric1": 1.2})  # 20% improvement
        assert report.passed
        assert report.improved_metrics == 1

    def test_to_dict(self):
        from evaluation.regression_eval import RegressionEvaluator, RegressionReport
        evaluator = RegressionEvaluator()
        report = RegressionReport(total_metrics=5, passed_metrics=5, passed=True)
        d = evaluator.to_dict(report)
        assert "regression_rate" in d
        assert d["regression_rate"] == 0.0


class TestExplainability:
    def test_build_trace(self):
        from evaluation.explainability import ExplainabilityEngine
        engine = ExplainabilityEngine()
        answer = {
            "confidence": "high",
            "entities": [{"name": "Vishnu", "type": "Deity"}],
            "evidence": {
                "sources": [
                    {"source_entity": "Vishnu", "target_entity": "Krishna",
                     "relationship": "INCARNATION_OF", "confidence": "high",
                     "scripture": "BHAG"},
                ],
                "provenance_traced": True,
            },
        }
        trace = engine.build_trace("Who is Vishnu?", answer)
        assert "Vishnu" in trace.entities_identified
        assert len(trace.evidence_chains) == 1
        assert trace.confidence == "high"

    def test_narrative(self):
        from evaluation.explainability import ExplainabilityEngine
        engine = ExplainabilityEngine()
        answer = {
            "confidence": "medium",
            "entities": [{"name": "Krishna"}],
            "evidence": {"sources": [
                {"source_entity": "Krishna", "target_entity": "Arjuna",
                 "relationship": "TEACHER_OF", "confidence": "medium",
                 "scripture": "BG"},
            ], "provenance_traced": True},
        }
        trace = engine.build_trace("Who is Krishna?", answer)
        narrative = trace.to_narrative()
        assert "Krishna" in narrative
        assert "high" in narrative or "medium" in narrative

    def test_to_dict(self):
        from evaluation.explainability import ExplainabilityEngine
        engine = ExplainabilityEngine()
        answer = {"confidence": "low", "entities": [], "evidence": {"sources": []}}
        trace = engine.build_trace("test", answer)
        d = trace.to_dict()
        assert "question" in d
        assert "reasoning_steps" in d


class TestQualityGates:
    def test_all_pass(self):
        from evaluation.quality_gates import QualityGates
        gates = QualityGates()
        metrics = {
            "retrieval_latency_p95_ms": 50.0,
            "retrieval_entity_recall": 0.8,
            "retrieval_ndcg_at_5": 0.7,
            "hallucination_rejection_rate": 1.0,
            "hallucination_max_confidence": 0.3,
            "regression_rate": 0.0,
            "graph_integrity": 1.0,
            "test_pass_rate": 1.0,
        }
        report = gates.evaluate(metrics)
        assert report.verdict == "PASS"

    def test_one_fails(self):
        from evaluation.quality_gates import QualityGates
        gates = QualityGates()
        metrics = {
            "retrieval_latency_p95_ms": 200.0,  # Over threshold
            "retrieval_entity_recall": 0.8,
            "retrieval_ndcg_at_5": 0.7,
            "hallucination_rejection_rate": 1.0,
            "hallucination_max_confidence": 0.3,
            "regression_rate": 0.0,
            "graph_integrity": 1.0,
            "test_pass_rate": 1.0,
        }
        report = gates.evaluate(metrics)
        assert report.verdict == "FAIL"
        assert report.failed_gates == 1

    def test_to_dict(self):
        from evaluation.quality_gates import QualityGates
        gates = QualityGates()
        report = gates.evaluate({}, version="1.0")
        d = gates.to_dict(report)
        assert "verdict" in d
        assert "gates" in d


class TestEvaluationRunner:
    def test_runner_init(self):
        from evaluation.runner import EvaluationRunner
        runner = EvaluationRunner()
        assert runner.dataset.total > 0

    def test_full_evaluation(self):
        from evaluation.runner import EvaluationRunner
        runner = EvaluationRunner()
        report = runner.run_full_evaluation(commit="test")
        assert "retrieval" in report
        assert "hallucination" in report
        assert "quality_gates" in report
        assert "regression" in report
        assert "sample_explainability" in report

    def test_runner_mock_search(self):
        from evaluation.runner import EvaluationRunner
        runner = EvaluationRunner()
        chunks = runner._mock_search(runner.dataset.questions[0])
        assert isinstance(chunks, list)

    def test_runner_mock_answer(self):
        from evaluation.runner import EvaluationRunner
        runner = EvaluationRunner()
        answer = runner._mock_answer(runner.dataset.questions[0])
        assert "confidence" in answer
        assert "entities" in answer
        assert "evidence" in answer
