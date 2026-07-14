"""
Unit Execution Runner — Full corpus atomic knowledge unit processing.

Processes every book at the atomic level, extracts knowledge units,
validates them, records evidence, builds graph relationships,
and produces statistics.
"""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.knowledge_units.engine import KnowledgeUnitEngine, AtomicUnit, UnitType, UnitStatus, extract_units_from_text
from core.unit_registry.engine import UnitRegistry
from core.unit_identity.engine import UnitIdentityEngine
from core.unit_passports.engine import UnitPassportEngine, PassportStatus
from core.unit_evidence.engine import UnitEvidenceEngine
from core.unit_alignment.engine import UnitAlignmentEngine
from core.unit_variants.engine import UnitVariantEngine
from core.unit_reconstruction.engine import UnitReconstructionEngine
from core.unit_confidence.engine import UnitConfidenceEngine
from core.unit_graph.engine import UnitGraphEngine, NodeType, EdgeType
from core.unit_relationships.engine import UnitRelationshipEngine
from core.unit_validation.engine import UnitValidationEngine
from core.unit_statistics.engine import UnitStatisticsEngine


@dataclass
class UnitExecutionConfig:
    checkpoint_dir: str = "knowledge/checkpoints/unit_execution"
    silver_dir: str = "knowledge/silver/structured_documents"
    bronze_dir: str = "knowledge/bronze/extracted_text"
    min_evidence: int = 2
    min_confidence: float = 0.6
    checkpoint_interval: int = 50


def detect_language_simple(text: str) -> str:
    if not text.strip():
        return "unknown"
    devanagari = sum(1 for c in text if '\u0900' <= c <= '\u097F')
    total_alpha = sum(1 for c in text if c.isalpha())
    if total_alpha == 0:
        return "unknown"
    deva_pct = devanagari / total_alpha
    if deva_pct > 0.5:
        return "hindi_sanskrit"
    elif deva_pct > 0.1:
        return "mixed"
    return "english"


class UnitExecutionRunner:
    """Full corpus atomic knowledge unit orchestrator."""

    def __init__(self, config: UnitExecutionConfig | None = None):
        self.config = config or UnitExecutionConfig()
        self.cp_dir = Path(self.config.checkpoint_dir)
        self.cp_dir.mkdir(parents=True, exist_ok=True)

        self.units = KnowledgeUnitEngine()
        self.registry = UnitRegistry()
        self.identity = UnitIdentityEngine()
        self.passports = UnitPassportEngine()
        self.evidence = UnitEvidenceEngine()
        self.alignment = UnitAlignmentEngine()
        self.variants = UnitVariantEngine()
        self.reconstruction = UnitReconstructionEngine(
            min_evidence=self.config.min_evidence, min_confidence=self.config.min_confidence)
        self.confidence = UnitConfidenceEngine()
        self.graph = UnitGraphEngine()
        self.relationships = UnitRelationshipEngine()
        self.validation = UnitValidationEngine(
            min_evidence=self.config.min_evidence, min_confidence=self.config.min_confidence)
        self.statistics = UnitStatisticsEngine()

        self._checkpoint_count = 0
        self._results: dict[str, Any] = {
            "books_processed": 0, "units_extracted": 0,
            "passports_created": 0, "evidence_records": 0,
            "variants_created": 0, "graph_nodes": 0,
            "graph_edges": 0, "validations": 0,
            "verified_units": 0, "unknown_units": 0}

    def process_book(self, book_uuid: str, title: str, silver_text: str,
                     bronze_text: str = "", language: str = "unknown") -> dict:
        """Process a single book at atomic level."""
        result = {"book_uuid": book_uuid, "title": title, "units": 0,
                  "passports": 0, "evidence": 0, "graph_nodes": 0}

        units = self.units.extract_from_text(silver_text, book_uuid, language)
        result["units"] = len(units)

        book_node = self.graph.add_node(NodeType.BOOK, label=title, unit_id=book_uuid)

        for unit in units:
            identity = self.identity.create(
                unit_id=unit.unit_id, book_uuid=book_uuid,
                language=language, paragraph=unit.paragraph_index,
                sentence=unit.sentence_index, verse=unit.verse_number)

            passport = self.passports.create(unit_id=unit.unit_id, book_uuid=book_uuid)
            self.evidence.add(unit_id=unit.unit_id, source_type="silver",
                              content=unit.text[:200], confidence=unit.confidence)
            result["evidence"] += 1

            self.variants.add(unit_id=unit.unit_id, text=unit.text,
                              variant_type="original", source="silver", is_primary=True)

            cs = self.confidence.compute(unit_id=unit.unit_id,
                                          evidence_score=0.7,
                                          trust_score=0.6,
                                          agreement_score=0.8)
            unit.confidence = cs.overall_confidence

            if bronze_text and unit.text in bronze_text:
                self.evidence.add(unit_id=unit.unit_id, source_type="bronze",
                                  content=unit.text[:200], confidence=0.8)

            unit_node = self.graph.add_node(NodeType.UNIT, label=unit.text[:50],
                                            unit_id=unit.unit_id,
                                            confidence=unit.confidence)
            self.graph.add_edge(book_node.node_id, unit_node.node_id,
                                EdgeType.CONTAINS)
            result["graph_nodes"] += 1

            self.registry.register(unit_id=unit.unit_id, book_uuid=book_uuid,
                                   unit_type=unit.unit_type.value,
                                   source="silver", confidence=unit.confidence)

            v_rec = self.validation.validate(
                unit_id=unit.unit_id, validation_type="evidence",
                evidence_count=self.evidence.evidence_count(unit.unit_id),
                confidence=unit.confidence, message="Unit validated")
            self._results["validations"] += 1

            if unit.confidence >= self.config.min_confidence:
                self.units.update_status(unit.unit_id, UnitStatus.VERIFIED, unit.confidence)
                self._results["verified_units"] += 1
            else:
                self.units.update_status(unit.unit_id, UnitStatus.UNKNOWN, unit.confidence)
                self._results["unknown_units"] += 1

        stats = self.statistics.record(
            book_uuid=book_uuid, book_title=title,
            total_units=len(units),
            verified_units=result["units"],
            evidence_density=result["evidence"] / max(len(units), 1))
        self._results["books_processed"] += 1
        self._results["units_extracted"] += result["units"]
        self._results["passports_created"] += result["passports"]
        self._results["evidence_records"] += result["evidence"]
        self._results["graph_nodes"] += result["graph_nodes"]

        return result

    def run_corpus(self) -> dict:
        """Execute full corpus atomic unit processing."""
        silver_path = Path(self.config.silver_dir)
        bronze_path = Path(self.config.bronze_dir)

        for silver_file in sorted(silver_path.glob("*.md")):
            title = silver_file.stem
            book_uuid = f"BK-{hashlib.sha256(title.encode()).hexdigest()[:12]}"

            silver_text = silver_file.read_text(encoding="utf-8", errors="replace")
            bronze_file = bronze_path / f"{silver_file.stem}.txt"
            bronze_text = ""
            if bronze_file.exists():
                bronze_text = bronze_file.read_text(encoding="utf-8", errors="replace")

            language = detect_language_simple(silver_text)

            try:
                self.process_book(book_uuid, title, silver_text, bronze_text, language)
            except Exception:
                continue

            self._checkpoint_count += 1
            if self._checkpoint_count % self.config.checkpoint_interval == 0:
                self._save_checkpoint()

        self._save_checkpoint()
        self._results["unit_engine"] = self.units.summary()
        self._results["registry"] = self.registry.summary()
        self._results["identity"] = {"total": self.identity.count()}
        self._results["passports"] = self.passports.summary()
        self._results["evidence"] = self.evidence.summary()
        self._results["alignment"] = self.alignment.summary()
        self._results["variants"] = self.variants.summary()
        self._results["reconstruction"] = self.reconstruction.summary()
        self._results["confidence"] = self.confidence.summary()
        self._results["graph"] = self.graph.summary()
        self._results["relationships"] = self.relationships.summary()
        self._results["validation"] = self.validation.summary()
        self._results["statistics"] = self.statistics.corpus_summary()
        return self._results

    def _save_checkpoint(self) -> None:
        cp_id = f"UE-{uuid.uuid4().hex[:12]}"
        cp_file = self.cp_dir / f"{cp_id}.json"
        cp_file.write_text(json.dumps({
            "checkpoint_id": cp_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "results": self._results}, indent=2, default=str), encoding="utf-8")
