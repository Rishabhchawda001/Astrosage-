"""
Corpus Execution Runner — Phase 13 production pipeline.

Processes every bronze document through gap detection, evidence collection,
candidate recovery, and provenance recording. Checkpoints continuously.
"""
from __future__ import annotations

import json
import hashlib
import os
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from core.corpus.gaps import CorpusGapEngine, GapType, GapSeverity, Gap
from core.corpus.recovery_queue import RecoveryQueue, RecoveryJob
from core.corpus.evidence import CorpusEvidenceEngine, CorpusEvidenceItem, CorpusEvidenceType
from core.corpus.comparison import CorpusComparisonEngine
from core.corpus.verification import CorpusTruthVerificationEngine, CorpusVerificationStage
from core.corpus.provenance import CorpusProvenanceLedger
from core.corpus.conflicts import ConflictEngine, ConflictType
from core.corpus.reconstruction import ReconstructionEngine


# ── Language Detection ────────────────────────────────────────────────

DEVANAGARI_RANGE = (0x0900, 0x097F)
TELUGU_RANGE = (0x0C00, 0x0C7F)
TAMIL_RANGE = (0x0B80, 0x0BFF)
KANNADA_RANGE = (0x0C80, 0x0CFF)
MALAYALAM_RANGE = (0x0D00, 0x0D7F)
BENGALI_RANGE = (0x0980, 0x09FF)
GUJARATI_RANGE = (0x0A80, 0x0AFF)
GURMUKHI_RANGE = (0x0A00, 0x0A7F)


def detect_language(text: str) -> str:
    if not text:
        return "unknown"
    sample = text[:5000]
    counts: dict[str, int] = {}
    for ch in sample:
        cp = ord(ch)
        if DEVANAGARI_RANGE[0] <= cp <= DEVANAGARI_RANGE[1]:
            counts["devanagari"] = counts.get("devanagari", 0) + 1
        elif TELUGU_RANGE[0] <= cp <= TELUGU_RANGE[1]:
            counts["telugu"] = counts.get("telugu", 0) + 1
        elif TAMIL_RANGE[0] <= cp <= TAMIL_RANGE[1]:
            counts["tamil"] = counts.get("tamil", 0) + 1
        elif KANNADA_RANGE[0] <= cp <= KANNADA_RANGE[1]:
            counts["kannada"] = counts.get("kannada", 0) + 1
        elif MALAYALAM_RANGE[0] <= cp <= MALAYALAM_RANGE[1]:
            counts["malayalam"] = counts.get("malayalam", 0) + 1
        elif BENGALI_RANGE[0] <= cp <= BENGALI_RANGE[1]:
            counts["bengali"] = counts.get("bengali", 0) + 1
        elif GUJARATI_RANGE[0] <= cp <= GUJARATI_RANGE[1]:
            counts["gujarati"] = counts.get("gujarati", 0) + 1
        elif GURMUKHI_RANGE[0] <= cp <= GURMUKHI_RANGE[1]:
            counts["gurmukhi"] = counts.get("gurmukhi", 0) + 1
        elif ch.isascii() and ch.isalpha():
            counts["latin"] = counts.get("latin", 0) + 1

    if not counts:
        return "unknown"

    primary = max(counts, key=counts.get)
    total = sum(counts.values())

    lang_map = {
        "devanagari": "hindi_sanskrit",
        "telugu": "telugu",
        "tamil": "tamil",
        "kannada": "kannada",
        "malayalam": "malayalam",
        "bengali": "bengali",
        "gujarati": "gujarati",
        "gurmukhi": "punjabi",
        "latin": "english",
    }
    lang = lang_map.get(primary, "unknown")

    if counts.get("devanagari", 0) > 0 and counts.get("latin", 0) > 0:
        ratio = counts["devanagari"] / max(counts["latin"], 1)
        if ratio > 0.3:
            lang = "mixed_hindi_english"

    return lang


def detect_script(text: str) -> str:
    if not text:
        return "unknown"
    sample = text[:3000]
    for ch in sample:
        cp = ord(ch)
        if DEVANAGARI_RANGE[0] <= cp <= DEVANAGARI_RANGE[1]:
            return "devanagari"
        elif TELUGU_RANGE[0] <= cp <= TELUGU_RANGE[1]:
            return "telugu"
        elif ch.isascii() and ch.isalpha():
            return "latin"
    return "unknown"


# ── Document Classifier ──────────────────────────────────────────────

class DocumentTier(str):
    TIER1 = "tier1_english_hindi_sanskrit"
    TIER2 = "tier2_other_languages"
    TIER3 = "tier3_media"


def classify_tier(language: str) -> str:
    if language in ("english", "hindi_sanskrit", "mixed_hindi_english", "hindi", "sanskrit"):
        return DocumentTier.TIER1
    elif language in ("telugu", "tamil", "kannada", "malayalam", "bengali", "gujarati", "punjabi", "odia"):
        return DocumentTier.TIER2
    else:
        return DocumentTier.TIER3


# ── Checkpoint Manager ───────────────────────────────────────────────

@dataclass
class ExecutionCheckpoint:
    phase: str = ""
    processed_books: list[str] = field(default_factory=list)
    failed_books: list[str] = field(default_factory=list)
    gap_count: int = 0
    evidence_count: int = 0
    candidate_count: int = 0
    conflict_count: int = 0
    started_at: str = ""
    last_updated: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class CheckpointManager:
    def __init__(self, checkpoint_path: str = "knowledge/checkpoints/phase13.json"):
        self.path = Path(checkpoint_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._checkpoint = ExecutionCheckpoint(started_at=datetime.now(timezone.utc).isoformat())
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text())
                self._checkpoint = ExecutionCheckpoint(**{k: v for k, v in data.items() if hasattr(self._checkpoint, k)})
            except Exception:
                pass

    def save(self):
        self._checkpoint.last_updated = datetime.now(timezone.utc).isoformat()
        self.path.write_text(json.dumps(self._checkpoint.__dict__, indent=2, ensure_ascii=False))

    @property
    def checkpoint(self) -> ExecutionCheckpoint:
        return self._checkpoint

    def is_processed(self, book_name: str) -> bool:
        return book_name in self._checkpoint.processed_books

    def mark_processed(self, book_name: str):
        if book_name not in self._checkpoint.processed_books:
            self._checkpoint.processed_books.append(book_name)

    def mark_failed(self, book_name: str):
        if book_name not in self._checkpoint.failed_books:
            self._checkpoint.failed_books.append(book_name)


# ── Corpus Execution Engine ──────────────────────────────────────────

class CorpusExecutionEngine:
    """
    Production engine that processes the entire corpus.

    For every bronze document:
    1. Read and classify
    2. Detect language
    3. Run gap detection
    4. Compare with silver (if exists)
    5. Collect evidence
    6. Generate recovery candidates for gaps
    7. Record provenance
    8. Checkpoint
    """

    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.bronze_dir = self.base_dir / "knowledge/bronze/extracted_text"
        self.silver_dir = self.base_dir / "knowledge/silver/structured_documents"
        self.output_dir = self.base_dir / "knowledge/corpus_analysis"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.checkpoint_mgr = CheckpointManager(str(self.base_dir / "knowledge/checkpoints/phase13.json"))
        self.gap_engine = CorpusGapEngine()
        self.evidence_engine = CorpusEvidenceEngine()
        self.comparison_engine = CorpusComparisonEngine()
        self.verification_engine = CorpusTruthVerificationEngine()
        self.provenance = CorpusProvenanceLedger()
        self.conflict_engine = ConflictEngine()
        self.reconstruction_engine = ReconstructionEngine()
        self.recovery_queue = RecoveryQueue()

        self._book_results: dict[str, dict[str, Any]] = {}

    def scan_corpus(self) -> list[dict[str, Any]]:
        """Scan all bronze documents and build execution plan."""
        documents = []
        if not self.bronze_dir.exists():
            return documents

        for f in sorted(self.bronze_dir.iterdir()):
            if not f.suffix == ".txt":
                continue

            text = f.read_text(errors="replace")
            language = detect_language(text)
            tier = classify_tier(language)
            book_name = f.stem

            # Check silver
            silver_path = self.silver_dir / f"{book_name}.md"
            has_silver = silver_path.exists()

            documents.append({
                "name": book_name,
                "bronze_path": str(f),
                "silver_path": str(silver_path) if has_silver else "",
                "has_silver": has_silver,
                "language": language,
                "tier": tier,
                "size_bytes": f.stat().st_size,
                "char_count": len(text),
                "word_count": len(text.split()),
                "text": text,
            })

        return documents

    def process_document(self, doc: dict[str, Any]) -> dict[str, Any]:
        """Process a single document through the full pipeline."""
        name = doc["name"]
        text = doc["text"]
        language = doc["language"]

        result = {
            "name": name,
            "language": language,
            "tier": doc["tier"],
            "size_bytes": doc["size_bytes"],
            "char_count": doc["char_count"],
            "word_count": doc["word_count"],
            "has_silver": doc["has_silver"],
            "gaps": [],
            "evidence_items": 0,
            "comparisons": 0,
            "candidates": 0,
            "conflicts": 0,
            "verified": False,
            "provenance_entries": 0,
        }

        # Step 1: Gap detection
        gaps = self.gap_engine.scan_document(text, book_uuid=name, document_uuid=name)
        # Additional structural analysis
        if doc["has_silver"]:
            silver_text = Path(doc["silver_path"]).read_text(errors="replace")
            if len(silver_text) > 0 and len(text) > 0:
                # Compare bronze vs silver
                ratio = len(silver_text) / max(len(text), 1)
                if ratio > 1.5:
                    gaps.append(self.gap_engine.detect_gap(
                        gap_type=GapType.MISSING_CONTENT,
                        severity=GapSeverity.MEDIUM,
                        book_uuid=name,
                        description=f"Silver has {ratio:.1f}x more content than bronze",
                        confidence=0.7,
                    ))

        # Detect broken structure
        if text:
            lines = text.split("\n")
            blank_lines = sum(1 for l in lines if not l.strip())
            if blank_lines > len(lines) * 0.5:
                gaps.append(self.gap_engine.detect_gap(
                    gap_type=GapType.SUSPICIOUS_WHITEPACE,
                    severity=GapSeverity.LOW,
                    book_uuid=name,
                    description=f"{blank_lines}/{len(lines)} lines are blank",
                    confidence=0.6,
                ))

        # Detect encoding issues
        if "\ufffd" in text:
            count = text.count("\ufffd")
            gaps.append(self.gap_engine.detect_gap(
                gap_type=GapType.UNICODE_CORRUPTION,
                severity=GapSeverity.HIGH,
                book_uuid=name,
                description=f"{count} Unicode replacement characters",
                confidence=0.9,
            ))

        result["gaps"] = [{"type": g.gap_type.value, "severity": g.severity.value, "description": g.description} for g in gaps]

        # Step 2: Evidence collection
        evidence = CorpusEvidenceItem(
            content=text[:1000],
            evidence_type=CorpusEvidenceType.OCR_OUTPUT,
            knowledge_uuid=name,
            language=language,
            confidence=0.8 if doc["has_silver"] else 0.5,
        )
        self.evidence_engine.submit(evidence)
        result["evidence_items"] = 1

        # Step 3: Comparison (bronze vs silver if both exist)
        if doc["has_silver"]:
            silver_text = Path(doc["silver_path"]).read_text(errors="replace")
            comparison = self.comparison_engine.compare_texts(
                text[:2000], silver_text[:2000],
                source_a_id=f"bronze:{name}", source_b_id=f"silver:{name}",
                
            )
            result["comparisons"] = 1
            if comparison.similarity < 0.5:
                self.conflict_engine.detect(
                    ConflictType.WORDING,
                    text[:200], silver_text[:200],
                    source_a="bronze", source_b="silver",
                    knowledge_uuid=name,
                    confidence=1 - comparison.similarity,
                )
                result["conflicts"] = 1

        # Step 4: Recovery candidates for high-severity gaps
        high_gaps = [g for g in gaps if g.severity in (GapSeverity.CRITICAL, GapSeverity.HIGH)]
        for gap in high_gaps:
            candidate = self.reconstruction_engine.create_candidate(
                gap_id=gap.gap_id,
                original_text="",
                recovered_text="",
                knowledge_uuid=name,
                confidence=0.0,
            )
            self.recovery_queue.enqueue_from_gap(gap)
            result["candidates"] += 1

        # Step 5: Verification
        has_content = len(text.strip()) > 100
        has_structure = len(text.split("\n")) > 10
        self.verification_engine.verify(name, CorpusVerificationStage.EVIDENCE, passed=has_content, confidence=0.8)
        self.verification_engine.verify(name, CorpusVerificationStage.METADATA, passed=bool(language and language != "unknown"))
        self.verification_engine.verify(name, CorpusVerificationStage.HIERARCHY, passed=has_structure)
        result["verified"] = self.verification_engine.is_verified(name)

        # Step 6: Provenance
        self.provenance.record(name, "gap_detection", tool="corpus_gap_engine", confidence=0.9)
        self.provenance.record(name, "evidence_collection", tool="evidence_engine")
        result["provenance_entries"] = 2

        return result

    def execute(self, max_documents: int = 0) -> dict[str, Any]:
        """Execute the full pipeline across the corpus."""
        documents = self.scan_corpus()
        if max_documents > 0:
            documents = documents[:max_documents]

        execution_start = datetime.now(timezone.utc).isoformat()
        processed = 0
        failed = 0
        skipped = 0
        total_gaps = 0
        total_evidence = 0
        total_candidates = 0
        total_conflicts = 0

        for i, doc in enumerate(documents):
            name = doc["name"]

            # Checkpoint: skip already processed
            if self.checkpoint_mgr.is_processed(name):
                skipped += 1
                continue

            try:
                result = self.process_document(doc)
                self._book_results[name] = result
                self.checkpoint_mgr.mark_processed(name)

                processed += 1
                total_gaps += len(result["gaps"])
                total_evidence += result["evidence_items"]
                total_candidates += result["candidates"]
                total_conflicts += result["conflicts"]

                # Checkpoint every 50 books
                if processed % 50 == 0:
                    self.checkpoint_mgr.checkpoint.gap_count = total_gaps
                    self.checkpoint_mgr.checkpoint.evidence_count = total_evidence
                    self.checkpoint_mgr.checkpoint.candidate_count = total_candidates
                    self.checkpoint_mgr.checkpoint.conflict_count = total_conflicts
                    self.checkpoint_mgr.save()

            except Exception as e:
                self.checkpoint_mgr.mark_failed(name)
                failed += 1

        # Final checkpoint
        self.checkpoint_mgr.checkpoint.gap_count = total_gaps
        self.checkpoint_mgr.checkpoint.evidence_count = total_evidence
        self.checkpoint_mgr.checkpoint.candidate_count = total_candidates
        self.checkpoint_mgr.checkpoint.conflict_count = total_conflicts
        self.checkpoint_mgr.save()

        # Save analysis results
        self._save_results()

        return {
            "total_documents": len(documents),
            "processed": processed,
            "failed": failed,
            "skipped": skipped,
            "total_gaps": total_gaps,
            "total_evidence": total_evidence,
            "total_candidates": total_candidates,
            "total_conflicts": total_conflicts,
            "execution_start": execution_start,
            "execution_end": datetime.now(timezone.utc).isoformat(),
        }

    def _save_results(self):
        """Save analysis results to corpus_analysis directory."""
        # Gap summary
        gap_summary = self.gap_engine.summary()
        (self.output_dir / "gap_summary.json").write_text(
            json.dumps(gap_summary, indent=2, ensure_ascii=False))

        # Evidence summary
        evidence_summary = self.evidence_engine.summary()
        (self.output_dir / "evidence_summary.json").write_text(
            json.dumps(evidence_summary, indent=2, ensure_ascii=False))

        # Comparison summary
        comparison_summary = self.comparison_engine.summary()
        (self.output_dir / "comparison_summary.json").write_text(
            json.dumps(comparison_summary, indent=2, ensure_ascii=False))

        # Verification summary
        verification_summary = self.verification_engine.summary()
        (self.output_dir / "verification_summary.json").write_text(
            json.dumps(verification_summary, indent=2, ensure_ascii=False))

        # Provenance summary
        provenance_summary = self.provenance.summary()
        (self.output_dir / "provenance_summary.json").write_text(
            json.dumps(provenance_summary, indent=2, ensure_ascii=False))

        # Conflict summary
        conflict_summary = self.conflict_engine.summary()
        (self.output_dir / "conflict_summary.json").write_text(
            json.dumps(conflict_summary, indent=2, ensure_ascii=False))

        # Recovery queue summary
        recovery_summary = self.recovery_queue.summary()
        (self.output_dir / "recovery_summary.json").write_text(
            json.dumps(recovery_summary, indent=2, ensure_ascii=False))

        # Reconstruction summary
        reconstruction_summary = self.reconstruction_engine.summary()
        (self.output_dir / "reconstruction_summary.json").write_text(
            json.dumps(reconstruction_summary, indent=2, ensure_ascii=False))

        # Per-book results
        if self._book_results:
            # Language distribution
            lang_dist: dict[str, int] = {}
            tier_dist: dict[str, int] = {}
            for r in self._book_results.values():
                lang_dist[r["language"]] = lang_dist.get(r["language"], 0) + 1
                tier_dist[r["tier"]] = tier_dist.get(r["tier"], 0) + 1

            corpus_stats = {
                "total_books_analyzed": len(self._book_results),
                "language_distribution": lang_dist,
                "tier_distribution": tier_dist,
                "books_with_gaps": sum(1 for r in self._book_results.values() if r["gaps"]),
                "books_verified": sum(1 for r in self._book_results.values() if r["verified"]),
                "books_with_conflicts": sum(1 for r in self._book_results.values() if r["conflicts"]),
            }
            (self.output_dir / "corpus_stats.json").write_text(
                json.dumps(corpus_stats, indent=2, ensure_ascii=False))
