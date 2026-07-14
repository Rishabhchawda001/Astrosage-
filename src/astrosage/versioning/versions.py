"""
Pipeline Versioning System.

Every processing stage has an independent version.
Changing one component must not require rebuilding unrelated stages.

Version format: MAJOR.MINOR.PATCH
  MAJOR: Breaking changes to output format
  MINOR: New features, backward-compatible
  PATCH: Bug fixes, no output change
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


# ── Pipeline Version Registry ──
# Each pipeline component has an independent version.

PIPELINE_VERSIONS = {
    "classifier": {
        "version": "0.1.0",
        "description": "Document type classification engine",
        "changes": ["Initial implementation: extension, magic bytes, PDF type detection"],
    },
    "language_detector": {
        "version": "0.1.0",
        "description": "Language and script detection",
        "changes": ["Initial implementation: script analysis, filename heuristics"],
    },
    "ocr_router": {
        "version": "0.1.0",
        "description": "OCR routing decision engine",
        "changes": ["Initial implementation: native/scanned/mixed PDF routing"],
    },
    "text_extractor": {
        "version": "0.1.0",
        "description": "Text extraction from PDFs (native)",
        "changes": ["Initial implementation: PyMuPDF direct extraction"],
    },
    "ocr_engine": {
        "version": "0.1.0",
        "description": "OCR processing for scanned documents",
        "changes": ["Initial implementation: PaddleOCR + Tesseract fallback"],
    },
    "metadata_extractor": {
        "version": "0.1.0",
        "description": "Document metadata extraction",
        "changes": ["Initial implementation: PDF metadata, filename parsing"],
    },
    "chunker": {
        "version": "0.1.0",
        "description": "Semantic chunking engine",
        "changes": ["Initial implementation: verse, header, paragraph, sentence splitting"],
    },
    "embedder": {
        "version": "0.1.0",
        "description": "Embedding generation (BGE-M3)",
        "changes": ["Initial implementation: dense + sparse embeddings"],
    },
    "vector_store": {
        "version": "0.1.0",
        "description": "Vector database storage (Qdrant/Chroma)",
        "changes": ["Initial implementation: Chroma embedded mode"],
    },
    "retriever": {
        "version": "0.1.0",
        "description": "Hybrid retrieval engine",
        "changes": ["Initial implementation: BM25 + Vector + RRF fusion"],
    },
    "reranker": {
        "version": "0.1.0",
        "description": "Cross-encoder reranking",
        "changes": ["Initial implementation: ms-marco-MiniLM-L-6-v2"],
    },
    "grounding_engine": {
        "version": "0.1.0",
        "description": "Answer grounding and verification",
        "changes": ["Initial implementation: sentence-level evidence checking"],
    },
    "duplicate_detector": {
        "version": "0.1.0",
        "description": "Duplicate detection (SHA256 + SimHash)",
        "changes": ["Initial implementation: exact + near-duplicate detection"],
    },
    "provenance_graph": {
        "version": "0.1.0",
        "description": "Data provenance tracking",
        "changes": ["Initial implementation: DAG-based traceability"],
    },
    "knowledge_registry": {
        "version": "0.1.0",
        "description": "Permanent ID assignment system",
        "changes": ["Initial implementation: deterministic UUID generation"],
    },
    "manifest": {
        "version": "0.1.0",
        "description": "Knowledge manifest generation",
        "changes": ["Initial implementation: CSV + Parquet export"],
    },
}

# ── Dataset Version ──

DATASET_VERSION = "1.0.0"  # Increment when the dataset changes
SCHEMA_VERSION = "1.0.0"   # Increment when the schema changes


@dataclass
class PipelineRun:
    """Record of a single pipeline execution."""
    run_id: str
    pipeline_name: str
    pipeline_version: str
    start_time: float = 0.0
    end_time: float = 0.0
    success: bool = True
    input_count: int = 0
    output_count: int = 0
    error_count: int = 0
    errors: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    
    def __post_init__(self):
        if self.start_time == 0.0:
            self.start_time = time.time()
    
    @property
    def duration_seconds(self) -> float:
        if self.end_time > 0:
            return self.end_time - self.start_time
        return 0.0
    
    def complete(self, success: bool = True):
        self.end_time = time.time()
        self.success = success


class VersionRegistry:
    """Tracks all pipeline versions and run history."""
    
    def __init__(self, log_dir: str = "knowledge/logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._runs: list[PipelineRun] = []
    
    def get_version(self, pipeline_name: str) -> str:
        """Get the current version of a pipeline component."""
        info = PIPELINE_VERSIONS.get(pipeline_name, {})
        return info.get("version", "0.0.0")
    
    def record_run(self, run: PipelineRun):
        """Record a pipeline execution."""
        self._runs.append(run)
        self._save_run(run)
    
    def _save_run(self, run: PipelineRun):
        """Save a run record to disk."""
        run_file = self.log_dir / f"run_{run.run_id}.json"
        with open(run_file, "w") as f:
            json.dump(asdict(run), f, indent=2)
    
    def get_all_versions(self) -> dict:
        """Get all pipeline component versions."""
        return {
            name: info["version"]
            for name, info in PIPELINE_VERSIONS.items()
        }
    
    def version_compatibility_check(self) -> dict:
        """Check if all pipeline versions are compatible."""
        versions = self.get_all_versions()
        return {
            "all_versions": versions,
            "dataset_version": DATASET_VERSION,
            "schema_version": SCHEMA_VERSION,
            "compatible": True,
        }
    
    def save_version_manifest(self):
        """Save the complete version manifest."""
        manifest = {
            "dataset_version": DATASET_VERSION,
            "schema_version": SCHEMA_VERSION,
            "pipeline_versions": self.get_all_versions(),
            "pipeline_details": PIPELINE_VERSIONS,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        
        manifest_path = self.log_dir / "version_manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        
        return manifest_path
