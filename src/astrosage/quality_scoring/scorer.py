"""
Document Quality Scoring Engine.

Assigns every document a multi-dimensional quality score.
Dimensions:
  - metadata_completeness (0-100)
  - ocr_readiness (0-100)
  - native_text_quality (0-100)
  - structural_quality (0-100)
  - parsing_complexity (0-100, lower = easier)
  - language_confidence (0-100)
  - duplicate_confidence (0-100, lower = more likely duplicate)
  - corruption_risk (0-100, lower = less risk)
  - processing_readiness (0-100)

Overall score = weighted average.
"""
from __future__ import annotations

import csv
import json
import logging
import re
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class QualityScore:
    """Quality scores for a single document."""
    filename: str
    filepath: str
    sha256: str = ""
    
    # Individual dimensions (0-100)
    metadata_completeness: float = 0.0
    ocr_readiness: float = 0.0
    native_text_quality: float = 0.0
    structural_quality: float = 0.0
    parsing_complexity: float = 0.0  # Lower = easier to parse
    language_confidence: float = 0.0
    duplicate_confidence: float = 0.0  # Lower = more likely duplicate
    corruption_risk: float = 0.0  # Lower = less risk
    
    # Overall
    overall_score: float = 0.0
    
    # Explanations
    score_explanations: dict = field(default_factory=dict)
    
    # Flags
    needs_ocr: bool = False
    is_duplicate: bool = False
    is_corrupted: bool = False
    is_empty: bool = False
    
    def compute_overall(self):
        """Compute weighted overall score."""
        weights = {
            "metadata_completeness": 0.15,
            "ocr_readiness": 0.10,
            "native_text_quality": 0.20,
            "structural_quality": 0.15,
            "language_confidence": 0.15,
            "duplicate_confidence": 0.10,
            "corruption_risk": 0.15,
        }
        
        total = 0.0
        weight_sum = 0.0
        for dim, w in weights.items():
            val = getattr(self, dim, 0)
            total += val * w
            weight_sum += w
        
        self.overall_score = round(total / max(weight_sum, 0.01), 1)
        return self.overall_score


def score_document(
    filepath: Path,
    manifest_row: Optional[dict] = None,
    language_result=None,
    classification_result=None,
    is_duplicate: bool = False,
    sha256: str = "",
) -> QualityScore:
    """Score a single document across all quality dimensions."""
    filepath = Path(filepath)
    ext = filepath.suffix.lower()
    file_size = filepath.stat().st_size if filepath.exists() else 0
    
    score = QualityScore(
        filename=filepath.name,
        filepath=str(filepath),
        sha256=sha256,
    )
    
    # ── Empty file check ──
    if file_size == 0:
        score.is_empty = True
        score.overall_score = 0.0
        score.score_explanations = {"error": "Empty file"}
        return score
    
    # ── Metadata completeness (from manifest) ──
    if manifest_row:
        fields = ["title", "author", "publisher", "edition", "language", "subject"]
        present = sum(1 for f in fields if manifest_row.get(f, "").strip())
        score.metadata_completeness = round(present / len(fields) * 100, 1)
        score.score_explanations["metadata"] = f"{present}/{len(fields)} fields present"
    else:
        score.metadata_completeness = 20.0  # Minimal score for filename only
        score.score_explanations["metadata"] = "No manifest data"
    
    # ── OCR readiness ──
    if ext == ".pdf":
        if classification_result:
            if classification_result.is_native_pdf:
                score.ocr_readiness = 100.0
                score.score_explanations["ocr"] = "Native PDF — no OCR needed"
            elif classification_result.is_scanned_pdf:
                score.ocr_readiness = 80.0
                score.needs_ocr = True
                score.score_explanations["ocr"] = "Scanned PDF — OCR required"
            elif classification_result.is_mixed_pdf:
                score.ocr_readiness = 60.0
                score.needs_ocr = True
                score.score_explanations["ocr"] = "Mixed PDF — partial OCR needed"
            else:
                score.ocr_readiness = 50.0
                score.score_explanations["ocr"] = "PDF type unknown"
        else:
            score.ocr_readiness = 50.0
            score.score_explanations["ocr"] = "No classification data"
    elif ext in (".txt", ".md", ".docx"):
        score.ocr_readiness = 100.0
        score.score_explanations["ocr"] = "Text format — no OCR needed"
    elif ext in (".jpg", ".jpeg", ".png"):
        score.ocr_readiness = 30.0
        score.needs_ocr = True
        score.score_explanations["ocr"] = "Image — OCR required"
    elif ext in (".mp3", ".mp4"):
        score.ocr_readiness = 0.0
        score.score_explanations["ocr"] = "Media file — no text extraction"
    else:
        score.ocr_readiness = 40.0
        score.score_explanations["ocr"] = f"Unknown format ({ext})"
    
    # ── Native text quality ──
    if ext == ".pdf" and file_size > 0:
        try:
            import pymupdf
            doc = pymupdf.open(str(filepath))
            total_chars = 0
            sample = min(10, len(doc))
            for i in range(sample):
                total_chars += len(doc[i].get_text().strip())
            doc.close()
            
            avg_chars = total_chars / max(1, sample)
            if avg_chars > 500:
                score.native_text_quality = 95.0
                score.score_explanations["text_quality"] = f"Dense text ({avg_chars:.0f} chars/page avg)"
            elif avg_chars > 100:
                score.native_text_quality = 70.0
                score.score_explanations["text_quality"] = f"Moderate text ({avg_chars:.0f} chars/page avg)"
            elif avg_chars > 10:
                score.native_text_quality = 30.0
                score.score_explanations["text_quality"] = f"Sparse text ({avg_chars:.0f} chars/page avg)"
            else:
                score.native_text_quality = 5.0
                score.score_explanations["text_quality"] = "Near-zero text (scanned?)"
        except Exception as e:
            score.native_text_quality = 40.0
            score.score_explanations["text_quality"] = f"Analysis failed: {e}"
    elif ext in (".txt", ".md"):
        score.native_text_quality = 90.0
        score.score_explanations["text_quality"] = "Plain text — full quality"
    elif ext == ".docx":
        score.native_text_quality = 85.0
        score.score_explanations["text_quality"] = "DOCX — good text quality"
    else:
        score.native_text_quality = 0.0
        score.score_explanations["text_quality"] = "Non-text format"
    
    # ── Structural quality ──
    if ext == ".pdf":
        # Heuristic: well-structured PDFs have consistent page sizes
        score.structural_quality = 70.0  # Default for PDFs
        if file_size > 10 * 1024 * 1024:  # Large PDFs often well-structured
            score.structural_quality = 80.0
        elif file_size < 100 * 1024:  # Very small PDFs may be simple
            score.structural_quality = 60.0
    elif ext == ".docx":
        score.structural_quality = 75.0
    elif ext in (".txt", ".md"):
        score.structural_quality = 50.0  # Flat structure
    else:
        score.structural_quality = 30.0
    
    # ── Parsing complexity ──
    if ext in (".txt", ".md"):
        score.parsing_complexity = 10.0  # Very easy
    elif ext == ".docx":
        score.parsing_complexity = 25.0
    elif ext == ".pdf":
        score.parsing_complexity = 60.0  # Moderate
        if file_size > 50 * 1024 * 1024:
            score.parsing_complexity = 75.0  # Large PDFs are complex
    else:
        score.parsing_complexity = 80.0
    
    # ── Language confidence ──
    if language_result:
        score.language_confidence = round(language_result.confidence * 100, 1)
        score.score_explanations["language"] = f"{language_result.primary_language} ({language_result.source})"
    else:
        score.language_confidence = 30.0
        score.score_explanations["language"] = "No language detection"
    
    # ── Duplicate confidence ──
    if is_duplicate:
        score.duplicate_confidence = 20.0
        score.is_duplicate = True
        score.score_explanations["duplicate"] = "Known duplicate"
    else:
        score.duplicate_confidence = 95.0
        score.score_explanations["duplicate"] = "Unique content"
    
    # ── Corruption risk ──
    if ext == ".pdf" and file_size > 0:
        try:
            with open(filepath, "rb") as f:
                header = f.read(4)
            if header.startswith(b"%PDF"):
                score.corruption_risk = 95.0  # Low risk
            else:
                score.corruption_risk = 10.0  # High risk — not a real PDF
                score.is_corrupted = True
                score.score_explanations["corruption"] = "Missing PDF header"
        except:
            score.corruption_risk = 50.0
    else:
        score.corruption_risk = 90.0  # Low risk for non-PDF
    
    # ── Compute overall ──
    score.compute_overall()
    
    return score


def score_batch(
    filepaths: list[Path],
    manifest_path: Optional[Path] = None,
    language_results: Optional[dict] = None,
    classification_results: Optional[dict] = None,
    duplicate_set: Optional[set] = None,
) -> list[QualityScore]:
    """Score a batch of documents."""
    # Load manifest if available
    manifest_data = {}
    if manifest_path and manifest_path.exists():
        with open(manifest_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                manifest_data[row.get("original_filename", "")] = row
    
    scores = []
    for fp in filepaths:
        try:
            manifest_row = manifest_data.get(fp.name)
            lang = language_results.get(str(fp)) if language_results else None
            cls = classification_results.get(str(fp)) if classification_results else None
            is_dup = (str(fp) in duplicate_set) if duplicate_set else False
            
            score = score_document(
                fp, manifest_row, lang, cls, is_dup,
            )
            scores.append(score)
        except Exception as e:
            logger.warning(f"Scoring failed for {fp.name}: {e}")
            scores.append(QualityScore(
                filename=fp.name, filepath=str(fp),
                overall_score=0.0,
                score_explanations={"error": str(e)},
            ))
    
    return scores


def save_quality_scores(scores: list[QualityScore], output_dir: Path):
    """Save quality scores as CSV and JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # CSV
    if scores:
        fieldnames = list(asdict(scores[0]).keys())
        with open(output_dir / "quality_scores.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for s in sorted(scores, key=lambda x: -x.overall_score):
                row = asdict(s)
                row["score_explanations"] = json.dumps(row["score_explanations"])
                writer.writerow(row)
    
    # Summary JSON
    summary = {
        "total_documents": len(scores),
        "average_score": round(sum(s.overall_score for s in scores) / max(1, len(scores)), 1),
        "score_distribution": {
            "excellent_90_100": sum(1 for s in scores if s.overall_score >= 90),
            "good_70_89": sum(1 for s in scores if 70 <= s.overall_score < 90),
            "moderate_50_69": sum(1 for s in scores if 50 <= s.overall_score < 70),
            "poor_30_49": sum(1 for s in scores if 30 <= s.overall_score < 50),
            "critical_0_29": sum(1 for s in scores if s.overall_score < 30),
        },
        "needs_ocr": sum(1 for s in scores if s.needs_ocr),
        "is_duplicate": sum(1 for s in scores if s.is_duplicate),
        "is_corrupted": sum(1 for s in scores if s.is_corrupted),
        "is_empty": sum(1 for s in scores if s.is_empty),
        "top_10": [
            {"filename": s.filename, "score": s.overall_score}
            for s in sorted(scores, key=lambda x: -x.overall_score)[:10]
        ],
        "bottom_10": [
            {"filename": s.filename, "score": s.overall_score, "reason": s.score_explanations.get("error", "")}
            for s in sorted(scores, key=lambda x: x.overall_score)[:10]
        ],
    }
    
    with open(output_dir / "quality_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Quality scores saved: {len(scores)} documents")
