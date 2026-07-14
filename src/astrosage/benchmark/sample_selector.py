"""
Benchmark Sample Selector.

Creates a representative benchmark corpus from the existing archive.
Every sample is selected for a specific reason.
"""
from __future__ import annotations

import json
import logging
import shutil
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkSample:
    filename: str
    source_path: str
    category: str
    subcategory: str
    language: str
    reason: str
    page_count_estimate: int = 0
    is_scanned: bool = False
    is_native: bool = False
    has_tables: bool = False
    has_verses: bool = False
    has_footnotes: bool = False
    has_figures: bool = False
    difficulty: str = "medium"


def select_benchmark_samples(
    source_dir: Path,
    manifest_path: Optional[Path] = None,
) -> list[BenchmarkSample]:
    """
    Select representative samples from the corpus.
    
    Selection criteria:
    - Cover every major language
    - Cover every PDF type (native, scanned, mixed)
    - Cover every subject category
    - Include edge cases (large, small, complex, simple)
    - Include known duplicates for cross-validation
    """
    samples = []
    
    # Load manifest for metadata
    manifest = {}
    if manifest_path and manifest_path.exists():
        import csv
        with open(manifest_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                manifest[row.get("original_filename", "")] = row
    
    # Discover all PDFs
    pdfs = sorted(source_dir.rglob("*.pdf"))
    
    # ── Category 1: Native English PDFs (5 samples) ──
    english_native = _find_samples(pdfs, manifest, {
        "language": "english",
        "is_native": True,
    }, exclude=scanned_names(pdfs, manifest))
    for fp in english_native[:5]:
        samples.append(BenchmarkSample(
            filename=fp.name, source_path=str(fp),
            category="native_pdf", subcategory="english",
            language="english",
            reason="Native English PDF — baseline for text extraction quality",
            is_native=True,
        ))
    
    # ── Category 2: Native Hindi PDFs (5 samples) ──
    hindi_native = _find_samples(pdfs, manifest, {
        "language": "hindi",
        "is_native": True,
    }, exclude=[s.filename for s in samples])
    for fp in hindi_native[:5]:
        samples.append(BenchmarkSample(
            filename=fp.name, source_path=str(fp),
            category="native_pdf", subcategory="hindi",
            language="hindi",
            reason="Native Hindi PDF — tests Devanagari text extraction",
            is_native=True, has_verses=True,
        ))
    
    # ── Category 3: Native Sanskrit PDFs (3 samples) ──
    sanskrit_native = _find_samples(pdfs, manifest, {
        "language": "sanskrit",
        "is_native": True,
    }, exclude=[s.filename for s in samples])
    for fp in sanskrit_native[:3]:
        samples.append(BenchmarkSample(
            filename=fp.name, source_path=str(fp),
            category="native_pdf", subcategory="sanskrit",
            language="sanskrit",
            reason="Native Sanskrit PDF — tests Vedic text extraction with verse markers",
            is_native=True, has_verses=True,
        ))
    
    # ── Category 4: Scanned PDFs — English (3 samples) ──
    english_scanned = _find_scanned(pdfs, manifest, "english", exclude=[s.filename for s in samples])
    for fp in english_scanned[:3]:
        samples.append(BenchmarkSample(
            filename=fp.name, source_path=str(fp),
            category="scanned_pdf", subcategory="english",
            language="english",
            reason="Scanned English PDF — OCR benchmark baseline",
            is_scanned=True, difficulty="medium",
        ))
    
    # ── Category 5: Scanned PDFs — Hindi (3 samples) ──
    hindi_scanned = _find_scanned(pdfs, manifest, "hindi", exclude=[s.filename for s in samples])
    for fp in hindi_scanned[:3]:
        samples.append(BenchmarkSample(
            filename=fp.name, source_path=str(fp),
            category="scanned_pdf", subcategory="hindi",
            language="hindi",
            reason="Scanned Hindi PDF — OCR benchmark for Devanagari",
            is_scanned=True, difficulty="hard",
        ))
    
    # ── Category 6: Large books (>50MB) (3 samples) ──
    large = sorted(pdfs, key=lambda f: f.stat().st_size, reverse=True)
    large_names = [s.filename for s in samples]
    for fp in large:
        if fp.stat().st_size > 50 * 1024 * 1024 and fp.name not in large_names:
            if len([s for s in samples if s.category == "large_book"]) >= 3:
                break
            samples.append(BenchmarkSample(
                filename=fp.name, source_path=str(fp),
                category="large_book", subcategory="any",
                language="mixed",
                reason=f"Large book ({fp.stat().st_size / 1048576:.0f}MB) — tests memory and processing limits",
                difficulty="hard",
            ))
            large_names.append(fp.name)
    
    # ── Category 7: Small books (<500KB) (3 samples) ──
    small = sorted([f for f in pdfs if f.stat().st_size > 0 and f.stat().st_size < 500 * 1024], key=lambda f: f.stat().st_size)
    small_names = [s.filename for s in samples]
    for fp in small:
        if fp.name not in small_names:
            if len([s for s in samples if s.category == "small_book"]) >= 3:
                break
            samples.append(BenchmarkSample(
                filename=fp.name, source_path=str(fp),
                category="small_book", subcategory="any",
                language="mixed",
                reason=f"Small book ({fp.stat().st_size / 1024:.0f}KB) — tests minimal document handling",
                difficulty="easy",
            ))
            small_names.append(fp.name)
    
    # ── Category 8: Mixed-language (3 samples) ──
    mixed = [f for f in pdfs if f.name not in [s.filename for s in samples]]
    for fp in mixed[:3]:
        name = fp.name.lower()
        if any(kw in name for kw in ["english", "hindi", "sanskrit", "mixed"]):
            samples.append(BenchmarkSample(
                filename=fp.name, source_path=str(fp),
                category="mixed_language", subcategory="any",
                language="mixed",
                reason="Mixed-language document — tests multi-script handling",
                difficulty="hard",
            ))
    
    # ── Category 9: Known good texts (Bhagavad Gita, etc.) (3 samples) ──
    well_known = ["Bhagavad-gita", "Ramayana", "Yoga_Sutras", "artha", "panini"]
    for kw in well_known:
        for fp in pdfs:
            if kw.lower() in fp.name.lower() and fp.name not in [s.filename for s in samples]:
                samples.append(BenchmarkSample(
                    filename=fp.name, source_path=str(fp),
                    category="canonical_text", subcategory=kw,
                    language="sanskrit" if "sanskrit" in fp.name.lower() else "english",
                    reason=f"Canonical text ({kw}) — well-known for validation",
                    has_verses=True,
                ))
                break
    
    logger.info(f"Selected {len(samples)} benchmark samples")
    return samples


def _find_samples(pdfs, manifest, criteria, exclude=None):
    """Find PDFs matching criteria."""
    exclude = set(exclude or [])
    results = []
    for fp in pdfs:
        if fp.name in exclude:
            continue
        meta = manifest.get(fp.name, {})
        
        # Check language
        lang = meta.get("language", "").lower()
        if "language" in criteria and lang != criteria["language"]:
            continue
        
        # Check if native (has extractable text)
        if criteria.get("is_native"):
            try:
                import pymupdf
                doc = pymupdf.open(str(fp))
                text_chars = sum(len(doc[i].get_text().strip()) for i in range(min(5, len(doc))))
                doc.close()
                if text_chars < 100:
                    continue
            except:
                continue
        
        results.append(fp)
    
    return results


def _find_scanned(pdfs, manifest, language, exclude=None):
    """Find scanned PDFs for a language."""
    exclude = set(exclude or [])
    results = []
    for fp in pdfs:
        if fp.name in exclude:
            continue
        meta = manifest.get(fp.name, {})
        lang = meta.get("language", "").lower()
        
        if language and lang != language:
            continue
        
        # Check if scanned (low text content)
        try:
            import pymupdf
            doc = pymupdf.open(str(fp))
            text_chars = sum(len(doc[i].get_text().strip()) for i in range(min(5, len(doc))))
            doc.close()
            if text_chars < 50 and len(doc) > 0:
                results.append(fp)
        except:
            continue
    
    return results


def scanned_names(pdfs, manifest):
    """Get names of scanned PDFs."""
    names = set()
    for fp in pdfs:
        try:
            import pymupdf
            doc = pymupdf.open(str(fp))
            text_chars = sum(len(doc[i].get_text().strip()) for i in range(min(3, len(doc))))
            doc.close()
            if text_chars < 50:
                names.add(fp.name)
        except:
            pass
    return names


def save_sample_dataset(samples: list[BenchmarkSample], output_dir: Path):
    """Save the benchmark sample dataset."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save sample list
    data = [asdict(s) for s in samples]
    with open(output_dir / "benchmark_samples.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Save human-readable catalog
    lines = ["# Benchmark Sample Dataset\n"]
    lines.append(f"Total samples: {len(samples)}\n")
    lines.append("| File | Category | Language | Reason |")
    lines.append("|------|----------|----------|--------|")
    for s in samples:
        lines.append(f"| {s.filename[:50]} | {s.category} | {s.language} | {s.reason[:60]} |")
    
    with open(output_dir / "SAMPLE_CATALOG.md", "w") as f:
        f.write("\n".join(lines))
    
    logger.info(f"Sample dataset saved: {len(samples)} samples")
