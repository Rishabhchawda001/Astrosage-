"""
Duplicate Detection Engine — Three independent methods.

1. SHA256 (exact byte-level duplicate)
2. SimHash (near-duplicate detection)
3. Semantic similarity (conceptual duplicates)

Reports duplicates but never removes them automatically.
"""
from __future__ import annotations

import hashlib
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class DuplicateGroup:
    """A group of files that are duplicates by some method."""
    method: str  # "sha256", "simhash", "semantic"
    similarity: float  # 1.0 for exact, <1.0 for near-duplicates
    files: list[dict] = field(default_factory=list)  # [{path, sha256, size}]


@dataclass
class DuplicateReport:
    """Complete duplicate detection report."""
    total_files: int = 0
    unique_sha256: int = 0
    sha256_groups: list[DuplicateGroup] = field(default_factory=list)
    simhash_groups: list[DuplicateGroup] = field(default_factory=list)
    
    @property
    def sha256_duplicate_count(self) -> int:
        return sum(len(g.files) - 1 for g in self.sha256_groups)
    
    @property
    def total_duplicate_files(self) -> int:
        return self.sha256_duplicate_count + sum(len(g.files) - 1 for g in self.simhash_groups)


# ── SHA256 Detection ──

def compute_file_sha256(filepath: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()


def detect_sha256_duplicates(filepaths: list[Path]) -> list[DuplicateGroup]:
    """Find exact duplicates by SHA256 hash."""
    hash_to_files: dict[str, list[dict]] = defaultdict(list)
    
    for fp in filepaths:
        try:
            sha = compute_file_sha256(fp)
            hash_to_files[sha].append({
                "path": str(fp),
                "filename": fp.name,
                "size": fp.stat().st_size,
                "sha256": sha,
            })
        except Exception as e:
            logger.warning(f"SHA256 failed for {fp}: {e}")
    
    groups = []
    for sha, files in hash_to_files.items():
        if len(files) > 1:
            groups.append(DuplicateGroup(
                method="sha256",
                similarity=1.0,
                files=files,
            ))
    
    return groups


# ── SimHash (Near-Duplicate Detection) ──

def _simhash(text: str, hashbits: int = 64) -> int:
    """Compute SimHash fingerprint for near-duplicate detection."""
    import re
    
    # Tokenize
    tokens = re.findall(r"\w+", text.lower())
    if not tokens:
        return 0
    
    # Compute hash vector
    v = [0] * hashbits
    for token in tokens:
        h = int(hashlib.md5(token.encode()).hexdigest(), 16)
        for i in range(hashbits):
            if h & (1 << i):
                v[i] += 1
            else:
                v[i] -= 1
    
    # Convert to fingerprint
    fingerprint = 0
    for i in range(hashbits):
        if v[i] > 0:
            fingerprint |= (1 << i)
    
    return fingerprint


def _hamming_distance(hash1: int, hash2: int) -> int:
    """Compute Hamming distance between two SimHash fingerprints."""
    x = hash1 ^ hash2
    distance = 0
    while x:
        distance += 1
        x &= x - 1
    return distance


def _text_sample(filepath: Path, max_bytes: int = 100000) -> str:
    """Extract a text sample from a file for SimHash."""
    ext = filepath.suffix.lower()
    
    if ext == ".pdf":
        try:
            import pymupdf
            doc = pymupdf.open(str(filepath))
            text = ""
            for i in range(min(5, len(doc))):
                text += doc[i].get_text()
            doc.close()
            return text[:max_bytes]
        except Exception:
            return ""
    
    elif ext in (".txt", ".md", ".html"):
        try:
            return filepath.read_text(encoding="utf-8", errors="replace")[:max_bytes]
        except Exception:
            return ""
    
    elif ext == ".docx":
        try:
            from docx import Document as DocxDocument
            doc = DocxDocument(str(filepath))
            return "\n".join(p.text for p in doc.paragraphs[:50])[:max_bytes]
        except Exception:
            return ""
    
    return ""


def detect_simhash_duplicates(
    filepaths: list[Path],
    threshold: int = 10,
) -> list[DuplicateGroup]:
    """
    Find near-duplicates using SimHash.
    
    threshold: maximum Hamming distance to consider two files as duplicates.
    Lower threshold = stricter matching.
    """
    # Compute SimHash for each file
    file_hashes: list[tuple[Path, int, str]] = []  # (path, simhash, text_sample)
    
    for fp in filepaths:
        try:
            text = _text_sample(fp)
            if text and len(text) > 100:
                sh = _simhash(text)
                file_hashes.append((fp, sh, text[:200]))
        except Exception as e:
            logger.warning(f"SimHash failed for {fp}: {e}")
    
    # Compare all pairs (O(n²) — acceptable for ~1000 files)
    groups: list[DuplicateGroup] = []
    assigned: set[int] = set()
    
    for i, (fp_i, sh_i, _) in enumerate(file_hashes):
        if i in assigned:
            continue
        
        group_files = [{
            "path": str(fp_i),
            "filename": fp_i.name,
            "size": fp_i.stat().st_size,
            "simhash_distance": 0,
        }]
        
        for j, (fp_j, sh_j, _) in enumerate(file_hashes):
            if j <= i or j in assigned:
                continue
            
            dist = _hamming_distance(sh_i, sh_j)
            if dist <= threshold:
                group_files.append({
                    "path": str(fp_j),
                    "filename": fp_j.name,
                    "size": fp_j.stat().st_size,
                    "simhash_distance": dist,
                })
                assigned.add(j)
        
        if len(group_files) > 1:
            avg_dist = sum(g["simhash_distance"] for g in group_files[1:]) / max(1, len(group_files) - 1)
            groups.append(DuplicateGroup(
                method="simhash",
                similarity=1.0 - (avg_dist / 64),
                files=group_files,
            ))
            assigned.add(i)
    
    return groups


# ── Full Report ──

def detect_all_duplicates(
    filepaths: list[Path],
    include_simhash: bool = True,
) -> DuplicateReport:
    """Run all duplicate detection methods and produce a report."""
    report = DuplicateReport(total_files=len(filepaths))
    
    # SHA256
    logger.info("Running SHA256 duplicate detection...")
    report.sha256_groups = detect_sha256_duplicates(filepaths)
    report.unique_sha256 = len(filepaths) - report.sha256_duplicate_count
    
    # SimHash
    if include_simhash:
        logger.info("Running SimHash near-duplicate detection...")
        report.simhash_groups = detect_simhash_duplicates(filepaths)
    
    logger.info(
        f"Duplicate detection complete: {report.sha256_duplicate_count} exact duplicates, "
        f"{len(report.simhash_groups)} near-duplicate groups"
    )
    
    return report
