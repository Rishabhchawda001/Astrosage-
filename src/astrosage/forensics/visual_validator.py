"""
Visual Validation — Renders sample pages for manual inspection.

For each classification category, renders:
  - The page as an image
  - The extracted text
  - The classification evidence
  - The forensic evidence

Produces human-readable reports that can be manually inspected.
"""
from __future__ import annotations

import json
import logging
import os
import random
import tempfile
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def generate_visual_samples(
    pdf_path: Path,
    page_signals: list,
    page_forensics: list,
    output_dir: Path,
    max_samples_per_class: int = 3,
) -> list[dict]:
    """
    Generate visual validation samples for a single PDF.
    Renders page images and text previews for manual inspection.
    """
    import pymupdf
    
    output_dir.mkdir(parents=True, exist_ok=True)
    samples = []
    
    # Group pages by classification
    class_pages = {}
    for sig in page_signals:
        cls = sig.page_class if hasattr(sig, 'page_class') else sig.get("page_class", "unknown")
        if cls not in class_pages:
            class_pages[cls] = []
        class_pages[cls].append(sig)
    
    try:
        doc = pymupdf.open(str(pdf_path))
        
        for cls, pages in class_pages.items():
            # Sample pages from each class
            sampled = random.sample(pages, min(max_samples_per_class, len(pages)))
            
            for page_data in sampled:
                page_num = page_data.page_number if hasattr(page_data, 'page_number') else page_data.get("page_number", 1)
                
                if page_num < 1 or page_num > len(doc):
                    continue
                
                page = doc[page_num - 1]
                
                # Render page image
                pix = page.get_pixmap(dpi=150)
                img_path = output_dir / f"page_{page_num:03d}_{cls}.png"
                pix.save(str(img_path))
                
                # Extract text
                text = page.get_text("text")
                text_preview = text[:1000] if text else "(no text)"
                
                # Get evidence
                evidence = page_data.classification_evidence if hasattr(page_data, 'classification_evidence') else page_data.get("classification_evidence", [])
                confidence = page_data.confidence if hasattr(page_data, 'confidence') else page_data.get("confidence", 0)
                
                sample = {
                    "page_number": page_num,
                    "classification": cls,
                    "confidence": confidence,
                    "evidence": evidence,
                    "text_preview": text_preview,
                    "image_path": str(img_path),
                    "text_length": len(text.strip()),
                    "image_count": page_data.image_count if hasattr(page_data, 'image_count') else page_data.get("image_count", 0),
                }
                samples.append(sample)
        
        doc.close()
    except Exception as e:
        logger.error(f"Visual validation failed for {pdf_path.name}: {e}")
    
    return samples


def generate_validation_report(
    all_samples: list[dict],
    output_dir: Path,
):
    """Generate a human-readable visual validation report."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Group by classification
    by_class = {}
    for s in all_samples:
        cls = s["classification"]
        if cls not in by_class:
            by_class[cls] = []
        by_class[cls].append(s)
    
    # Save JSON
    with open(output_dir / "visual_validation.json", "w", encoding="utf-8") as f:
        json.dump(all_samples, f, indent=2, ensure_ascii=False)
    
    # Generate markdown report
    lines = ["# Visual Validation Report\n"]
    lines.append(f"Total samples: {len(all_samples)}\n")
    lines.append("Each sample shows: rendered page image, extracted text, classification, and evidence.\n")
    
    for cls, samples in sorted(by_class.items()):
        lines.append(f"\n## {cls.upper()} ({len(samples)} samples)\n")
        for s in samples:
            lines.append(f"### Page {s['page_number']} — Confidence: {s['confidence']}\n")
            lines.append(f"- **Text length:** {s['text_length']} chars")
            lines.append(f"- **Images:** {s['image_count']}")
            lines.append(f"- **Image:** `{s['image_path']}`")
            lines.append(f"- **Evidence:** {'; '.join(s['evidence'][:3])}")
            lines.append(f"- **Text preview:** `{s['text_preview'][:200]}...`")
            lines.append("")
    
    with open(output_dir / "VISUAL_VALIDATION.md", "w") as f:
        f.write("\n".join(lines))
    
    logger.info(f"Visual validation: {len(all_samples)} samples across {len(by_class)} classes")
