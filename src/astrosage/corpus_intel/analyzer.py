"""
Corpus Intelligence Engine.

Profiles the entire knowledge library:
  - Document counts, sizes, types
  - Language/script distribution
  - Metadata completeness
  - Quality indicators
  - Subject classification
  - Publisher/author distribution
  - Duplicate analysis
  - OCR readiness
  - Media analysis
"""
from __future__ import annotations

import csv
import hashlib
import json
import logging
import os
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class CorpusProfile:
    """Complete profile of the knowledge corpus."""
    # Counts
    total_files: int = 0
    total_size_bytes: int = 0
    
    # By type
    by_extension: dict = field(default_factory=dict)
    by_mime_type: dict = field(default_factory=dict)
    
    # PDF analysis
    pdf_count: int = 0
    native_pdf_count: int = 0
    scanned_pdf_count: int = 0
    mixed_pdf_count: int = 0
    unknown_pdf_count: int = 0
    
    # Language
    by_language: dict = field(default_factory=dict)
    by_script: dict = field(default_factory=dict)
    multilingual_count: int = 0
    
    # Subjects (from folder paths)
    by_subject: dict = field(default_factory=dict)
    
    # Media
    audio_count: int = 0
    audio_duration_seconds: float = 0.0
    video_count: int = 0
    video_duration_seconds: float = 0.0
    image_count: int = 0
    
    # Books
    largest_books: list = field(default_factory=list)
    smallest_books: list = field(default_factory=list)
    median_size: float = 0.0
    
    # Duplicates
    duplicate_groups: int = 0
    duplicate_files: int = 0
    unique_content_items: int = 0
    
    # Metadata
    metadata_completeness: dict = field(default_factory=dict)
    missing_metadata: list = field(default_factory=list)
    authors: dict = field(default_factory=dict)
    publishers: dict = field(default_factory=dict)
    titles_extracted: int = 0
    
    # Pages
    total_pages: int = 0
    pages_with_text: int = 0
    pages_needing_ocr: int = 0
    
    # Quality
    corruption_risk: list = field(default_factory=list)
    empty_files: int = 0
    
    # Timestamps
    generated_at: str = ""
    generation_time_seconds: float = 0.0


def analyze_corpus(
    source_dir: Path,
    manifest_path: Optional[Path] = None,
) -> CorpusProfile:
    """
    Analyze the entire corpus and produce a comprehensive profile.
    """
    start = time.time()
    profile = CorpusProfile()
    profile.generated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Discover all files
    all_files = sorted([f for f in source_dir.rglob("*") if f.is_file()])
    profile.total_files = len(all_files)
    profile.total_size_bytes = sum(f.stat().st_size for f in all_files)
    
    logger.info(f"Analyzing {len(all_files)} files ({profile.total_size_bytes / 1048576 / 1024:.1f} GB)")
    
    # ── Extension distribution ──
    ext_counts = defaultdict(int)
    ext_sizes = defaultdict(int)
    for f in all_files:
        ext = f.suffix.lower()
        ext_counts[ext] += 1
        ext_sizes[ext] += f.stat().st_size
    profile.by_extension = {
        ext: {"count": count, "size_mb": round(ext_sizes[ext] / 1048576, 1)}
        for ext, count in sorted(ext_counts.items(), key=lambda x: -x[1])
    }
    
    # ── PDF analysis ──
    pdf_files = [f for f in all_files if f.suffix.lower() == ".pdf"]
    profile.pdf_count = len(pdf_files)
    
    for fp in pdf_files:
        try:
            import pymupdf
            doc = pymupdf.open(str(fp))
            page_count = len(doc)
            profile.total_pages += page_count
            
            # Sample text extraction quality
            text_chars = 0
            sample_pages = min(5, page_count)
            for i in range(sample_pages):
                text_chars += len(doc[i].get_text().strip())
            
            doc.close()
            
            avg_chars = text_chars / max(1, sample_pages)
            if avg_chars > 200:
                profile.native_pdf_count += 1
                profile.pages_with_text += page_count
            elif avg_chars < 10:
                profile.scanned_pdf_count += 1
                profile.pages_needing_ocr += page_count
            else:
                profile.mixed_pdf_count += 1
                profile.pages_needing_ocr += page_count // 2
        except Exception:
            profile.unknown_pdf_count += 1
    
    # ── Audio/Video ──
    audio_exts = {".mp3", ".wav", ".flac", ".ogg"}
    video_exts = {".mp4", ".avi", ".mkv", ".webm"}
    image_exts = {".jpg", ".jpeg", ".png", ".gif", ".tiff", ".bmp"}
    
    for f in all_files:
        ext = f.suffix.lower()
        if ext in audio_exts:
            profile.audio_count += 1
        elif ext in video_exts:
            profile.video_count += 1
        elif ext in image_exts:
            profile.image_count += 1
    
    # ── Subject classification ──
    subject_counts = defaultdict(int)
    for f in all_files:
        parts = f.relative_to(source_dir).parts
        if len(parts) > 1:
            subject = parts[0]
            subject_counts[subject] += 1
    profile.by_subject = dict(sorted(subject_counts.items(), key=lambda x: -x[1]))
    
    # ── Load manifest for metadata analysis ──
    if manifest_path and manifest_path.exists():
        _analyze_manifest(profile, manifest_path)
    
    # ── Duplicate detection ──
    _analyze_duplicates(profile, all_files)
    
    # ── Size statistics ──
    sizes = sorted([f.stat().st_size for f in all_files])
    if sizes:
        profile.median_size = sizes[len(sizes) // 2]
        
        # Top 10 largest
        large = sorted(all_files, key=lambda f: f.stat().st_size, reverse=True)[:10]
        profile.largest_books = [
            {"name": f.name, "size_mb": round(f.stat().st_size / 1048576, 1), "path": str(f.relative_to(source_dir))}
            for f in large
        ]
        
        # Top 10 smallest (excluding empty)
        small = sorted([f for f in all_files if f.stat().st_size > 0], key=lambda f: f.stat().st_size)[:10]
        profile.smallest_books = [
            {"name": f.name, "size_kb": round(f.stat().st_size / 1024, 1), "path": str(f.relative_to(source_dir))}
            for f in small
        ]
    
    # ── Empty files ──
    profile.empty_files = sum(1 for f in all_files if f.stat().st_size == 0)
    
    # ── Corruption risk ──
    for f in all_files:
        if f.suffix.lower() == ".pdf":
            try:
                with open(f, "rb") as fh:
                    header = fh.read(4)
                if not header.startswith(b"%PDF"):
                    profile.corruption_risk.append({
                        "file": f.name,
                        "reason": "Missing PDF header",
                        "path": str(f.relative_to(source_dir)),
                    })
            except Exception:
                pass
    
    profile.generation_time_seconds = round(time.time() - start, 1)
    logger.info(f"Corpus analysis complete in {profile.generation_time_seconds}s")
    
    return profile


def _analyze_manifest(profile: CorpusProfile, manifest_path: Path):
    """Analyze metadata from the manifest CSV."""
    try:
        with open(manifest_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except Exception as e:
        logger.warning(f"Could not read manifest: {e}")
        return
    
    # Language distribution
    lang_counts = defaultdict(int)
    script_counts = defaultdict(int)
    author_counts = defaultdict(int)
    publisher_counts = defaultdict(int)
    missing = defaultdict(int)
    has_title = 0
    has_author = 0
    has_publisher = 0
    has_language = 0
    has_page_count = 0
    
    for row in rows:
        lang = row.get("language", "unknown")
        lang_counts[lang] += 1
        
        script = row.get("script", "unknown")
        script_counts[script] += 1
        
        author = row.get("author", "").strip()
        if author:
            author_counts[author] += 1
            has_author += 1
        else:
            missing["author"] += 1
        
        publisher = row.get("publisher", "").strip()
        if publisher:
            publisher_counts[publisher] += 1
            has_publisher += 1
        else:
            missing["publisher"] += 1
        
        title = row.get("title", "").strip()
        if title and title != row.get("original_filename", ""):
            has_title += 1
        else:
            missing["title"] += 1
        
        if lang and lang != "unknown":
            has_language += 1
        else:
            missing["language"] += 1
        
        pages = row.get("page_count", "0")
        try:
            if int(pages) > 0:
                has_page_count += 1
            else:
                missing["page_count"] += 1
        except:
            missing["page_count"] += 1
    
    profile.by_language = dict(lang_counts)
    profile.by_script = dict(script_counts)
    profile.authors = dict(sorted(author_counts.items(), key=lambda x: -x[1])[:50])
    profile.publishers = dict(sorted(publisher_counts.items(), key=lambda x: -x[1])[:30])
    profile.titles_extracted = has_title
    profile.missing_metadata = dict(missing)
    
    total = len(rows)
    profile.metadata_completeness = {
        "title": round(has_title / max(1, total) * 100, 1),
        "author": round(has_author / max(1, total) * 100, 1),
        "publisher": round(has_publisher / max(1, total) * 100, 1),
        "language": round(has_language / max(1, total) * 100, 1),
        "page_count": round(has_page_count / max(1, total) * 100, 1),
    }


def _analyze_duplicates(profile: CorpusProfile, files: list[Path]):
    """Fast duplicate analysis using SHA256."""
    hash_map = defaultdict(list)
    for f in files:
        try:
            sha = hashlib.sha256()
            with open(f, "rb") as fh:
                for chunk in iter(lambda: fh.read(65536), b""):
                    sha.update(chunk)
            hash_map[sha.hexdigest()].append(str(f))
        except Exception:
            pass
    
    profile.unique_content_items = len(hash_map)
    dup_groups = {h: paths for h, paths in hash_map.items() if len(paths) > 1}
    profile.duplicate_groups = len(dup_groups)
    profile.duplicate_files = sum(len(paths) - 1 for paths in dup_groups.values())


def save_corpus_profile(profile: CorpusProfile, output_dir: Path):
    """Save the corpus profile as JSON and Markdown."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # JSON
    with open(output_dir / "corpus_intelligence.json", "w", encoding="utf-8") as f:
        json.dump(asdict(profile), f, indent=2, ensure_ascii=False)
    
    # Markdown report
    md = _generate_intelligence_markdown(profile)
    with open(output_dir / "CORPUS_INTELLIGENCE.md", "w", encoding="utf-8") as f:
        f.write(md)
    
    logger.info(f"Corpus intelligence saved to {output_dir}")


def _generate_intelligence_markdown(profile: CorpusProfile) -> str:
    """Generate a human-readable markdown report."""
    total_gb = profile.total_size_bytes / 1048576 / 1024
    
    lines = [
        "# Corpus Intelligence Report",
        f"\n*Generated: {profile.generated_at}*",
        f"*Analysis time: {profile.generation_time_seconds}s*\n",
        "## Overview",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total files | {profile.total_files} |",
        f"| Total size | {total_gb:.1f} GB |",
        f"| Total pages (PDFs) | {profile.total_pages:,} |",
        f"| Unique content items | {profile.unique_content_items} |",
        f"| Duplicate groups | {profile.duplicate_groups} |",
        f"| Duplicate files | {profile.duplicate_files} |",
        "",
        "## File Types",
        "| Type | Count | Size |",
        "|------|-------|------|",
    ]
    for ext, info in profile.by_extension.items():
        lines.append(f"| {ext} | {info['count']} | {info['size_mb']:.1f} MB |")
    
    lines.extend([
        "",
        "## PDF Analysis",
        f"| Category | Count |",
        f"|----------|-------|",
        f"| Total PDFs | {profile.pdf_count} |",
        f"| Native (text extractable) | {profile.native_pdf_count} |",
        f"| Scanned (needs OCR) | {profile.scanned_pdf_count} |",
        f"| Mixed | {profile.mixed_pdf_count} |",
        f"| Unknown | {profile.unknown_pdf_count} |",
        f"| Pages with text | {profile.pages_with_text:,} |",
        f"| Pages needing OCR | {profile.pages_needing_ocr:,} |",
        "",
        "## Languages",
        "| Language | Count |",
        "|----------|-------|",
    ])
    for lang, count in sorted(profile.by_language.items(), key=lambda x: -x[1]):
        lines.append(f"| {lang} | {count} |")
    
    lines.extend([
        "",
        "## Scripts",
        "| Script | Count |",
        "|--------|-------|",
    ])
    for script, count in sorted(profile.by_script.items(), key=lambda x: -x[1]):
        lines.append(f"| {script} | {count} |")
    
    lines.extend([
        "",
        "## Metadata Completeness",
        "| Field | Completeness |",
        "|-------|-------------|",
    ])
    for field_name, pct in profile.metadata_completeness.items():
        lines.append(f"| {field_name} | {pct:.1f}% |")
    
    lines.extend([
        "",
        "## Subject Distribution (Top 20)",
        "| Subject | Files |",
        "|---------|-------|",
    ])
    for subject, count in list(profile.by_subject.items())[:20]:
        lines.append(f"| {subject} | {count} |")
    
    lines.extend([
        "",
        "## Largest Books",
        "| File | Size |",
        "|------|------|",
    ])
    for book in profile.largest_books[:10]:
        lines.append(f"| {book['name'][:60]} | {book['size_mb']:.1f} MB |")
    
    if profile.corruption_risk:
        lines.extend([
            "",
            "## Corruption Risk",
            "| File | Reason |",
            "|------|--------|",
        ])
        for item in profile.corruption_risk[:20]:
            lines.append(f"| {item['file'][:50]} | {item['reason']} |")
    
    if profile.empty_files > 0:
        lines.append(f"\n**Empty files:** {profile.empty_files}")
    
    return "\n".join(lines)
