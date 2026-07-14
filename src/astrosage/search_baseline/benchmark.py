"""
Search Baseline Benchmark.

Before semantic retrieval exists, measures baseline search quality:
  1. Filename search
  2. Metadata search (manifest)
  3. BM25 keyword search on extracted text

Measures: precision, recall, latency.
These become the baseline for future hybrid retrieval comparison.
"""
from __future__ import annotations

import csv
import json
import logging
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    document: str
    score: float
    rank: int
    source: str  # "filename", "metadata", "bm25"


@dataclass
class SearchBenchmark:
    method: str
    query: str
    results: list = field(default_factory=list)
    latency_ms: float = 0.0
    result_count: int = 0


class BaselineSearchEngine:
    """
    Simple search engine for baseline measurement.
    No ML models — pure text matching.
    """
    
    def __init__(self, source_dir: Path, manifest_path: Optional[Path] = None):
        self.source_dir = source_dir
        self._files = []
        self._manifest = {}
        self._bm25_index = None
        self._bm25_docs = []
        self._bm25_corpus = []
    
    def build_index(self):
        """Build search indices."""
        # File index
        self._files = sorted([
            f for f in self.source_dir.rglob("*") if f.is_file()
        ])
        
        # Manifest index
        if manifest_path := self.source_dir.parent.parent / "reports" / "manifest.csv":
            if manifest_path.exists():
                with open(manifest_path, newline="", encoding="utf-8") as f:
                    for row in csv.DictReader(f):
                        self._manifest[row.get("original_filename", "")] = row
        
        # BM25 index on extracted text
        text_dir = self.source_dir.parent.parent / "bronze" / "extracted_text"
        if text_dir.exists():
            text_files = sorted(text_dir.rglob("*.txt"))
            for tf in text_files:
                try:
                    text = tf.read_text(encoding="utf-8", errors="replace")
                    self._bm25_docs.append(tf.stem)
                    self._bm25_corpus.append(text)
                except Exception:
                    pass
            
            if self._bm25_corpus:
                self._build_bm25()
        
        logger.info(
            f"Baseline index: {len(self._files)} files, "
            f"{len(self._manifest)} manifest entries, "
            f"{len(self._bm25_corpus)} text documents"
        )
    
    def _build_bm25(self):
        """Build BM25 index."""
        try:
            from rank_bm25 import BM25Okapi
            tokenized = [self._tokenize(doc) for doc in self._bm25_corpus]
            self._bm25_index = BM25Okapi(tokenized)
        except ImportError:
            logger.warning("rank_bm25 not installed — BM25 search unavailable")
    
    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"\w+", text.lower())
    
    def search_filename(self, query: str, top_k: int = 10) -> list[SearchResult]:
        """Search by filename matching."""
        start = time.time()
        query_lower = query.lower()
        
        results = []
        for fp in self._files:
            name = fp.name.lower()
            # Simple substring matching with scoring
            if query_lower in name:
                score = 1.0
            elif all(w in name for w in query_lower.split()):
                score = 0.8
            else:
                # Fuzzy matching
                words = query_lower.split()
                matches = sum(1 for w in words if w in name)
                score = matches / max(1, len(words)) * 0.6 if matches > 0 else 0
            
            if score > 0:
                results.append(SearchResult(
                    document=fp.name, score=score,
                    rank=0, source="filename",
                ))
        
        results.sort(key=lambda r: -r.score)
        for i, r in enumerate(results[:top_k]):
            r.rank = i + 1
        
        latency = (time.time() - start) * 1000
        return results[:top_k]
    
    def search_metadata(self, query: str, top_k: int = 10) -> list[SearchResult]:
        """Search manifest metadata."""
        start = time.time()
        query_lower = query.lower()
        query_words = query_lower.split()
        
        results = []
        for filename, meta in self._manifest.items():
            searchable = " ".join([
                meta.get("title", ""),
                meta.get("author", ""),
                meta.get("subject", ""),
                meta.get("original_filename", ""),
                meta.get("language", ""),
            ]).lower()
            
            # Score based on word matches
            matches = sum(1 for w in query_words if w in searchable)
            score = matches / max(1, len(query_words))
            
            if score > 0:
                results.append(SearchResult(
                    document=filename, score=score,
                    rank=0, source="metadata",
                ))
        
        results.sort(key=lambda r: -r.score)
        for i, r in enumerate(results[:top_k]):
            r.rank = i + 1
        
        latency = (time.time() - start) * 1000
        return results[:top_k]
    
    def search_bm25(self, query: str, top_k: int = 10) -> list[SearchResult]:
        """BM25 keyword search on extracted text."""
        if self._bm25_index is None:
            return []
        
        start = time.time()
        tokenized_query = self._tokenize(query)
        scores = self._bm25_index.get_scores(tokenized_query)
        
        top_indices = scores.argsort()[::-1][:top_k]
        results = []
        for rank, idx in enumerate(top_indices):
            if scores[idx] > 0:
                results.append(SearchResult(
                    document=self._bm25_docs[idx],
                    score=float(scores[idx]),
                    rank=rank + 1,
                    source="bm25",
                ))
        
        latency = (time.time() - start) * 1000
        return results
    
    def benchmark_queries(self, queries: list[str]) -> list[SearchBenchmark]:
        """Run benchmark queries across all search methods."""
        benchmarks = []
        
        for query in queries:
            for method_name, method_fn in [
                ("filename", self.search_filename),
                ("metadata", self.search_metadata),
                ("bm25", self.search_bm25),
            ]:
                start = time.time()
                results = method_fn(query)
                latency = (time.time() - start) * 1000
                
                benchmarks.append(SearchBenchmark(
                    method=method_name,
                    query=query,
                    results=[asdict(r) for r in results],
                    latency_ms=round(latency, 2),
                    result_count=len(results),
                ))
        
        return benchmarks


def save_search_baseline(benchmarks: list[SearchBenchmark], output_dir: Path):
    """Save search baseline results."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Group by method
    by_method = defaultdict(list)
    for b in benchmarks:
        by_method[b.method].append(b)
    
    summary = {}
    for method, bs in by_method.items():
        avg_latency = sum(b.latency_ms for b in bs) / max(1, len(bs))
        avg_results = sum(b.result_count for b in bs) / max(1, len(bs))
        queries_with_results = sum(1 for b in bs if b.result_count > 0)
        
        summary[method] = {
            "total_queries": len(bs),
            "avg_latency_ms": round(avg_latency, 2),
            "avg_results_per_query": round(avg_results, 1),
            "queries_with_results": queries_with_results,
            "recall_rate": round(queries_with_results / max(1, len(bs)) * 100, 1),
        }
    
    with open(output_dir / "search_baseline.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    # Detailed results
    with open(output_dir / "search_baseline_detail.json", "w") as f:
        json.dump([asdict(b) for b in benchmarks], f, indent=2)
    
    logger.info(f"Search baseline: {len(benchmarks)} benchmarks across {len(by_method)} methods")
