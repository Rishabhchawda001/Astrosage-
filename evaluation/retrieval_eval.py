"""Retrieval quality evaluator — measures precision, recall, and relevance."""
import json
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from evaluation.golden_loader import EvalQuestion


@dataclass
class RetrievalResult:
    question_id: str
    query: str
    top_results: list[dict] = field(default_factory=list)
    latency_ms: float = 0.0
    expected_entities_found: int = 0
    expected_entities_total: int = 0
    expected_scriptures_found: int = 0
    expected_scriptures_total: int = 0
    precision_at_k: float = 0.0
    recall_at_k: float = 0.0
    ndcg: float = 0.0
    passed: bool = False


@dataclass
class RetrievalBenchmark:
    avg_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    avg_precision_at_5: float = 0.0
    avg_recall_at_5: float = 0.0
    avg_ndcg_at_5: float = 0.0
    entity_recall: float = 0.0
    scripture_recall: float = 0.0
    total_queries: int = 0
    passed_queries: int = 0
    results: list[RetrievalResult] = field(default_factory=list)
    passed: bool = False


class RetrievalEvaluator:
    """Evaluates retrieval quality against the golden dataset."""

    def __init__(self, k: int = 5, latency_threshold_ms: float = 100.0):
        self.k = k
        self.latency_threshold_ms = latency_threshold_ms

    def evaluate_question(
        self,
        question: EvalQuestion,
        retrieved_chunks: list[dict],
        latency_ms: float,
    ) -> RetrievalResult:
        """Score a single retrieval result against expected evidence."""
        # Extract entities from retrieved chunks
        retrieved_entities = set()
        retrieved_scriptures = set()
        for chunk in retrieved_chunks:
            for link in chunk.get("entity_links", []):
                name = link.get("name", "") if isinstance(link, dict) else str(link)
                if name:
                    retrieved_entities.add(name.lower())
            # Check explicit scripture_id
            sid = chunk.get("scripture_id", "")
            if sid:
                retrieved_scriptures.add(sid)
            # Check _scriptures from mock search
            for s in chunk.get("_scriptures", []):
                if s:
                    retrieved_scriptures.add(s)

        # Calculate entity recall
        expected_ent = [e.lower() for e in question.expected_entities]
        found_ent = [e for e in expected_ent if e in retrieved_entities]
        entity_recall = len(found_ent) / max(len(expected_ent), 1)

        # Calculate scripture recall
        expected_scr = [s for s in question.expected_scriptures]
        found_scr = [s for s in expected_scr if s in retrieved_scriptures]
        scripture_recall = len(found_scr) / max(len(expected_scr), 1)

        # Precision@k
        relevant_count = len(found_ent) + len(found_scr)
        precision_at_k = min(relevant_count / max(self.k, 1), 1.0)

        # Recall@k
        total_expected = len(expected_ent) + len(expected_scr)
        recall_at_k = min(relevant_count / max(total_expected, 1), 1.0)

        # NDCG@k
        dcg = sum(
            1.0 / (i + 1)
            for i, chunk in enumerate(retrieved_chunks[: self.k])
            if any(
                e.lower() in retrieved_entities
                for e in question.expected_entities
            )
            or any(
                s in retrieved_scriptures
                for s in question.expected_scriptures
            )
        )
        ideal_dcg = sum(1.0 / (i + 1) for i in range(min(self.k, total_expected)))
        ndcg = dcg / max(ideal_dcg, 0.001)

        # Pass criteria
        passed = (
            entity_recall >= 0.3
            and latency_ms < self.latency_threshold_ms
            and len(retrieved_chunks) > 0
        )

        return RetrievalResult(
            question_id=question.id,
            query=question.question,
            top_results=retrieved_chunks[: self.k],
            latency_ms=latency_ms,
            expected_entities_found=len(found_ent),
            expected_entities_total=len(expected_ent),
            expected_scriptures_found=len(found_scr),
            expected_scriptures_total=len(expected_scr),
            precision_at_k=precision_at_k,
            recall_at_k=recall_at_k,
            ndcg=ndcg,
            passed=passed,
        )

    def aggregate(self, results: list[RetrievalResult]) -> RetrievalBenchmark:
        if not results:
            return RetrievalBenchmark()

        latencies = sorted([r.latency_ms for r in results])
        n = len(latencies)
        benchmark = RetrievalBenchmark(
            avg_latency_ms=sum(latencies) / n,
            p50_latency_ms=latencies[n // 2],
            p95_latency_ms=latencies[int(n * 0.95)] if n >= 20 else latencies[-1],
            p99_latency_ms=latencies[int(n * 0.99)] if n >= 100 else latencies[-1],
            avg_precision_at_5=sum(r.precision_at_k for r in results) / n,
            avg_recall_at_5=sum(r.recall_at_k for r in results) / n,
            avg_ndcg_at_5=sum(r.ndcg for r in results) / n,
            entity_recall=sum(
                r.expected_entities_found / max(r.expected_entities_total, 1)
                for r in results
            )
            / n,
            scripture_recall=sum(
                r.expected_scriptures_found / max(r.expected_scriptures_total, 1)
                for r in results
            )
            / n,
            total_queries=n,
            passed_queries=sum(1 for r in results if r.passed),
            results=results,
            passed=all(r.passed for r in results),
        )
        return benchmark

    def to_dict(self, benchmark: RetrievalBenchmark) -> dict:
        return {
            "avg_latency_ms": round(benchmark.avg_latency_ms, 2),
            "p50_latency_ms": round(benchmark.p50_latency_ms, 2),
            "p95_latency_ms": round(benchmark.p95_latency_ms, 2),
            "p99_latency_ms": round(benchmark.p99_latency_ms, 2),
            "avg_precision_at_5": round(benchmark.avg_precision_at_5, 4),
            "avg_recall_at_5": round(benchmark.avg_recall_at_5, 4),
            "avg_ndcg_at_5": round(benchmark.avg_ndcg_at_5, 4),
            "entity_recall": round(benchmark.entity_recall, 4),
            "scripture_recall": round(benchmark.scripture_recall, 4),
            "total_queries": benchmark.total_queries,
            "passed_queries": benchmark.passed_queries,
            "pass_rate": round(
                benchmark.passed_queries / max(benchmark.total_queries, 1), 4
            ),
            "passed": benchmark.passed,
        }
