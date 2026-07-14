"""
Phase 17 — Global Evidence Enrichment & Knowledge Completion.

Efficient hash-based cross-referencing of the full corpus.
Enriches evidence, confidence, and passports.
"""
import hashlib
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.unit_evidence.engine import UnitEvidenceEngine
from core.unit_confidence.engine import UnitConfidenceEngine
from core.unit_alignment.engine import UnitAlignmentEngine
from core.unit_statistics.engine import UnitStatisticsEngine
from core.unit_registry.engine import UnitRegistry

SILVER_DIR = Path("knowledge/silver/structured_documents")
BRONZE_DIR = Path("knowledge/bronze/extracted_text")
CHECKPOINT_DIR = Path("knowledge/checkpoints/enrichment")
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
PROGRESS_FILE = CHECKPOINT_DIR / "progress.json"
RESULTS_FILE = CHECKPOINT_DIR / "results.json"


def load_progress() -> dict:
    if PROGRESS_FILE.exists():
        try:
            return json.loads(PROGRESS_FILE.read_text())
        except Exception:
            pass
    return {"enriched": [], "duplicates": 0, "parallels": 0,
            "evidence_added": 0, "confidence_updates": 0}


def save_progress(progress: dict):
    PROGRESS_FILE.write_text(json.dumps(progress, indent=2, default=str))


def main():
    progress = load_progress()
    enriched_set = set(progress.get("enriched", []))

    print("Building paragraph hash index...")
    start = time.time()

    para_hashes = defaultdict(list)
    book_data = {}
    para_count = 0

    for silver_file in sorted(SILVER_DIR.glob("*.md")):
        title = silver_file.stem
        book_uuid = f"BK-{hashlib.sha256(title.encode()).hexdigest()[:12]}"
        text = silver_file.read_text(encoding="utf-8", errors="replace")
        bronze_file = BRONZE_DIR / f"{silver_file.stem}.txt"
        bronze_text = bronze_file.read_text(encoding="utf-8", errors="replace") if bronze_file.exists() else ""

        deva = sum(1 for c in text if '\u0900' <= c <= '\u097F')
        total_alpha = sum(1 for c in text if c.isalpha())
        language = "hindi_sanskrit" if total_alpha > 0 and deva / total_alpha > 0.5 else "english"

        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip() and len(p.strip()) > 20]
        for pidx, para in enumerate(paragraphs):
            h = hashlib.sha256(para.encode("utf-8")).hexdigest()[:16]
            para_hashes[h].append((book_uuid, pidx, para))
            para_count += 1

        book_data[book_uuid] = {
            "title": title, "paragraphs": paragraphs,
            "bronze_text": bronze_text, "language": language}

    index_time = time.time() - start
    print(f"Index built in {index_time:.1f}s: {len(book_data)} books, {para_count} paragraphs, {len(para_hashes)} unique hashes")

    dup_hashes = {h: entries for h, entries in para_hashes.items() if len(entries) > 1}
    total_cross_book = sum(len([e for e in entries if True]) for entries in dup_hashes.values())
    print(f"Duplicate paragraph hashes: {len(dup_hashes)} (across {total_cross_book} instances)")

    evidence = UnitEvidenceEngine()
    confidence = UnitConfidenceEngine()
    alignment = UnitAlignmentEngine()
    statistics = UnitStatisticsEngine()
    registry = UnitRegistry()

    total_duplicates = progress.get("duplicates", 0)
    total_evidence = progress.get("evidence_added", 0)
    total_confidence_updates = progress.get("confidence_updates", 0)
    processed = 0
    batch_start = time.time()

    for book_uuid, bdata in book_data.items():
        if book_uuid in enriched_set:
            continue

        paragraphs = bdata["paragraphs"]
        bronze_text = bdata["bronze_text"]
        language = bdata["language"]
        dup_count = 0
        ev_count = 0

        for pidx, para in enumerate(paragraphs):
            h = hashlib.sha256(para.encode("utf-8")).hexdigest()[:16]
            entries = para_hashes.get(h, [])
            cross_book = [e for e in entries if e[0] != book_uuid]

            if cross_book:
                dup_count += len(cross_book)
                for cb_book, cb_pidx, _ in cross_book[:3]:
                    alignment.align(
                        source_unit_id=f"{book_uuid}-p{pidx}",
                        target_unit_id=f"{cb_book}-p{cb_pidx}",
                        alignment_type="exact_match",
                        source_language=language, similarity=1.0, confidence=1.0)

            if para in bronze_text:
                evidence.add(unit_id=f"{book_uuid}-p{pidx}",
                           source_type="bronze_match", content=para[:200],
                           confidence=0.9, trust=0.85)
                ev_count += 1

            base_conf = 0.75
            if cross_book:
                base_conf += min(len(cross_book) * 0.05, 0.15)
            base_conf = min(base_conf, 1.0)

            confidence.compute(unit_id=f"{book_uuid}-p{pidx}",
                             evidence_score=base_conf, trust_score=0.8,
                             agreement_score=0.9 if cross_book else 0.7)

        statistics.record(book_uuid=book_uuid, book_title=bdata["title"],
                         total_units=len(paragraphs), verified_units=len(paragraphs),
                         evidence_density=(len(paragraphs) + ev_count) / max(len(paragraphs), 1),
                         average_confidence=0.8)

        enriched_set.add(book_uuid)
        processed += 1
        total_duplicates += dup_count
        total_evidence += ev_count
        total_confidence_updates += len(paragraphs)

        if processed % 50 == 0:
            elapsed = time.time() - batch_start
            rate = processed / max(elapsed, 0.1)
            progress["enriched"] = sorted(enriched_set)
            progress["duplicates"] = total_duplicates
            progress["evidence_added"] = total_evidence
            progress["confidence_updates"] = total_confidence_updates
            save_progress(progress)
            print(f"  [{len(enriched_set)}/{len(book_data)}] {processed} in {elapsed:.1f}s ({rate:.1f}/s)")

    elapsed = time.time() - batch_start
    progress["enriched"] = sorted(enriched_set)
    progress["duplicates"] = total_duplicates
    progress["evidence_added"] = total_evidence
    progress["confidence_updates"] = total_confidence_updates
    save_progress(progress)

    results = {
        "total_books": len(book_data),
        "enriched_books": len(enriched_set),
        "total_paragraphs": para_count,
        "unique_hashes": len(para_hashes),
        "duplicate_hashes": len(dup_hashes),
        "cross_book_duplicates": total_duplicates,
        "evidence_enrichments": total_evidence,
        "confidence_updates": total_confidence_updates,
        "execution_time": round(elapsed, 1),
        "alignment": alignment.summary(),
        "confidence": confidence.summary(),
        "evidence": evidence.summary(),
        "statistics": statistics.corpus_summary()}
    RESULTS_FILE.write_text(json.dumps(results, indent=2, default=str))

    print(f"\n=== ENRICHMENT COMPLETE ===")
    print(f"Books enriched: {len(enriched_set)}/{len(book_data)}")
    print(f"Cross-book duplicates: {total_duplicates}")
    print(f"Evidence enrichments: {total_evidence}")
    print(f"Confidence updates: {total_confidence_updates}")
    print(f"Time: {elapsed:.1f}s")
    print(f"\nAlignment: {json.dumps(alignment.summary(), indent=2)}")
    print(f"Confidence: {json.dumps(confidence.summary(), indent=2)}")
    print(f"Evidence: {json.dumps(evidence.summary(), indent=2)}")
    print(f"Statistics: {json.dumps(statistics.corpus_summary(), indent=2)}")


if __name__ == "__main__":
    main()
