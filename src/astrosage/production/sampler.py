"""
Representative Validation Corpus Sampler.

Automatically constructs a validation corpus covering every document type,
language, and layout discovered during Phase 3.1 forensics.
"""
from __future__ import annotations

import json
import random
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional


def build_validation_corpus(
    forensics_results_path: Path,
    raw_dir: Path,
    manifest_path: Optional[Path] = None,
    max_samples: int = 60,
    seed: int = 42,
) -> tuple[list[dict], dict]:
    """
    Construct a representative validation corpus.

    Strategy:
      - Stratified sampling across document_class x language
      - Guarantees at least 1 sample per class
      - Remaining slots filled proportionally
    """
    rng = random.Random(seed)

    data = json.loads(forensics_results_path.read_text())
    manifest = {}
    if manifest_path and manifest_path.exists():
        with open(manifest_path) as f:
            for row in csv.DictReader(f):
                manifest[row["original_filename"]] = row

    enriched = []
    for r in data:
        fp = raw_dir / r.get("relative_path", "")
        if not fp.exists():
            continue
        m = manifest.get(r["filename"], {})
        enriched.append({
            "filename": r["filename"],
            "relative_path": r.get("relative_path", ""),
            "filepath": str(fp),
            "document_class": r.get("document_class", "unknown"),
            "page_count": r.get("total_pages", 0),
            "page_class_counts": r.get("page_class_counts", {}),
            "language": m.get("language", "unknown"),
            "extension": ".pdf",
            "file_size": fp.stat().st_size,
        })

    for e in enriched:
        sz = e["file_size"]
        if sz < 500_000:
            e["size_bucket"] = "small"
        elif sz < 5_000_000:
            e["size_bucket"] = "medium"
        elif sz < 50_000_000:
            e["size_bucket"] = "large"
        else:
            e["size_bucket"] = "very_large"

    skip_classes = {"timeout", "error"}
    max_pages = 300  # Validation speed limit
    valid = [e for e in enriched if e["document_class"] not in skip_classes and e["page_count"] <= max_pages]

    selected = []
    selected_files = set()

    by_class = defaultdict(list)
    for e in valid:
        by_class[e["document_class"]].append(e)

    # Phase 1: At least 1 per document_class
    for cls, docs in by_class.items():
        if len(selected) >= max_samples:
            break
        best = max(docs, key=lambda d: d["page_count"])
        if best["filename"] not in selected_files:
            selected.append(best)
            selected_files.add(best["filename"])

    # Phase 2: At least 1 per language per class
    for cls in by_class:
        langs = defaultdict(list)
        for e in by_class[cls]:
            langs[e["language"]].append(e)
        for lang, docs in langs.items():
            if len(selected) >= max_samples:
                break
            for d in sorted(docs, key=lambda x: -x["page_count"]):
                if d["filename"] not in selected_files:
                    selected.append(d)
                    selected_files.add(d["filename"])
                    break

    # Phase 3: Fill remaining slots proportionally
    remaining = max_samples - len(selected)
    candidates = [e for e in valid if e["filename"] not in selected_files]
    if candidates and remaining > 0:
        extra = rng.sample(candidates, min(remaining, len(candidates)))
        for e in extra:
            if e["filename"] not in selected_files:
                selected.append(e)
                selected_files.add(e["filename"])

    selected.sort(key=lambda e: (e["document_class"], e["filename"]))

    summary = {
        "total_selected": len(selected),
        "by_class": dict(Counter(e["document_class"] for e in selected)),
        "by_language": dict(Counter(e["language"] for e in selected)),
        "by_size": dict(Counter(e["size_bucket"] for e in selected)),
        "total_pages": sum(e["page_count"] for e in selected),
        "total_bytes": sum(e["file_size"] for e in selected),
    }

    return selected, summary
