"""
Multi-Signal Page Classifier.

Classifies every page using MULTIPLE independent signals — not just page.get_text().

Signals measured:
  1. Text layer exists
  2. Text character density
  3. Font count and usage
  4. Image count and coverage
  5. Raster DPI
  6. Vector object count
  7. Text bounding boxes
  8. Image bounding boxes
  9. Text/image overlap (OCR overlay detection)
  10. Whitespace ratio
  11. Rendering complexity

Page classes:
  - native_text: Born-digital text, no images
  - scanned_image: Image-only page (photo/scan), possibly with invisible OCR text
  - ocr_overlay: Image + embedded invisible text layer (OCR'd scan)
  - mixed_content: Both text and significant images
  - vector_drawing: Primarily vector graphics
  - blank: Empty or near-empty page
  - unknown: Cannot determine
"""
from __future__ import annotations

import re
import time
from collections import Counter
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


@dataclass
class PageSignals:
    """All measured signals for a single page."""
    page_number: int = 0
    
    # Text signals
    text_exists: bool = False
    text_length: int = 0
    text_char_density: float = 0.0  # chars per page area
    font_count: int = 0
    font_sizes: list = field(default_factory=list)
    font_names: list = field(default_factory=list)
    text_block_count: int = 0
    text_line_count: int = 0
    
    # Image signals
    image_count: int = 0
    image_coverage_pct: float = 0.0  # % of page covered by images
    raster_dpi: float = 0.0
    has_large_image: bool = False  # Image covering >50% of page
    
    # Vector signals
    vector_object_count: int = 0
    
    # Overlap signals
    text_image_overlap: bool = False  # Text bounding boxes overlap image bounding boxes
    ocr_layer_detected: bool = False  # Text exists on top of an image
    
    # Layout signals
    whitespace_ratio: float = 0.0
    has_multi_column: bool = False
    has_table_structure: bool = False
    
    # Classification
    page_class: str = "unknown"
    confidence: float = 0.0
    classification_evidence: list = field(default_factory=list)


def classify_page(page, page_number: int) -> PageSignals:
    """
    Classify a single page using multiple independent signals.
    
    This is the core forensic tool. It does NOT rely solely on get_text().
    """
    signals = PageSignals(page_number=page_number)
    page_rect = page.rect
    page_area = page_rect.width * page_rect.height
    
    evidence = []
    
    # ── Signal 1: Text extraction ──
    text = page.get_text("text")
    text_dict = page.get_text("dict")
    
    signals.text_exists = bool(text.strip())
    signals.text_length = len(text.strip())
    
    # ── Signal 2: Text blocks from dict ──
    blocks = text_dict.get("blocks", [])
    text_blocks = [b for b in blocks if b.get("type") == 0]
    image_blocks = [b for b in blocks if b.get("type") == 1]
    
    signals.text_block_count = len(text_blocks)
    signals.image_block_count = len(image_blocks) if hasattr(signals, 'image_block_count') else len(image_blocks)
    signals.image_count = len(image_blocks)
    
    # ── Signal 3: Font analysis ──
    all_fonts = Counter()
    all_sizes = []
    text_chars_total = 0
    
    for block in text_blocks:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                font_name = span.get("font", "")
                font_size = span.get("size", 0)
                span_text = span.get("text", "")
                
                if font_name:
                    all_fonts[font_name] += 1
                if font_size > 0:
                    all_sizes.append(font_size)
                text_chars_total += len(span_text)
    
    signals.font_count = len(all_fonts)
    signals.font_names = list(all_fonts.keys())
    signals.font_sizes = list(set(all_sizes))
    signals.text_line_count = sum(
        len(line.get("spans", []))
        for block in text_blocks
        for line in block.get("lines", [])
    )
    
    # Text character density
    if page_area > 0:
        signals.text_char_density = text_chars_total / (page_area / 10000)  # chars per 10000 sq px
    
    # ── Signal 4: Image analysis ──
    images = page.get_images(full=True)
    signals.image_count = max(len(images), len(image_blocks))
    
    # Calculate image coverage
    total_image_area = 0
    for img_block in image_blocks:
        bbox = img_block.get("bbox", [0, 0, 0, 0])
        img_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
        total_image_area += img_area
    
    signals.image_coverage_pct = (total_image_area / max(1, page_area)) * 100
    signals.has_large_image = signals.image_coverage_pct > 50
    
    # DPI estimation from images
    if images:
        max_dpi = 0
        for img in images:
            xref = img[0]
            try:
                img_info = page.parent.extract_image(xref)
                if img_info:
                    w = img_info.get("width", 0)
                    h = img_info.get("height", 0)
                    # Estimate DPI from image dimensions relative to page size
                    if w > 0 and h > 0:
                        dpi_x = w / (page_rect.width / 72)
                        dpi_y = h / (page_rect.height / 72)
                        avg_dpi = (dpi_x + dpi_y) / 2
                        max_dpi = max(max_dpi, avg_dpi)
            except:
                pass
        signals.raster_dpi = max_dpi
    
    # ── Signal 5: Vector objects ──
    try:
        drawings = page.get_drawings()
        signals.vector_object_count = len(drawings)
    except:
        signals.vector_object_count = 0
    
    # ── Signal 6: Whitespace analysis ──
    # Approximate: non-text, non-image area
    text_area = 0
    for block in text_blocks:
        bbox = block.get("bbox", [0, 0, 0, 0])
        text_area += (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
    
    content_area = text_area + total_image_area
    signals.whitespace_ratio = max(0, 1 - (content_area / max(1, page_area)))
    
    # ── Signal 7: OCR overlay detection ──
    # Check if text bounding boxes significantly overlap image bounding boxes
    if text_blocks and image_blocks:
        overlap_count = 0
        for tb in text_blocks:
            tbbox = tb.get("bbox", [0, 0, 0, 0])
            for ib in image_blocks:
                ibbox = ib.get("bbox", [0, 0, 0, 0])
                # Calculate intersection
                x_overlap = max(0, min(tbbox[2], ibbox[2]) - max(tbbox[0], ibbox[0]))
                y_overlap = max(0, min(tbbox[3], ibbox[3]) - max(tbbox[1], ibbox[1]))
                overlap_area = x_overlap * y_overlap
                text_area_tb = (tbbox[2] - tbbox[0]) * (tbbox[3] - tbbox[1])
                if text_area_tb > 0 and overlap_area / text_area_tb > 0.5:
                    overlap_count += 1
        
        signals.text_image_overlap = overlap_count > 0
        signals.ocr_layer_detected = (
            overlap_count > 0 and
            signals.image_coverage_pct > 30 and
            signals.text_length > 50
        )
    
    # ── MULTI-STAGE CLASSIFICATION ──
    class_result = _classify_with_evidence(signals)
    signals.page_class = class_result["class"]
    signals.confidence = class_result["confidence"]
    signals.classification_evidence = class_result["evidence"]
    
    return signals


def _classify_with_evidence(signals: PageSignals) -> dict:
    """
    Multi-stage classification using all available evidence.
    Returns classification with confidence and evidence list.
    """
    evidence = []
    scores = {
        "native_text": 0.0,
        "scanned_image": 0.0,
        "ocr_overlay": 0.0,
        "mixed_content": 0.0,
        "blank": 0.0,
    }
    
    # ── Evidence: blank page ──
    if signals.text_length < 10 and signals.image_count == 0:
        scores["blank"] = 0.95
        evidence.append(f"Near-empty page: {signals.text_length} chars, 0 images")
    
    # ── Evidence: strong native text ──
    if signals.text_exists and signals.text_length > 100:
        scores["native_text"] += 0.3
        evidence.append(f"Text exists: {signals.text_length} chars")
    
    if signals.font_count >= 2:
        scores["native_text"] += 0.15
        evidence.append(f"Multiple fonts: {signals.font_count} distinct fonts")
    elif signals.font_count == 1:
        scores["native_text"] += 0.1
        evidence.append(f"Single font: {signals.font_names[0] if signals.font_names else 'unknown'}")
    
    if signals.text_char_density > 0.5:
        scores["native_text"] += 0.15
        evidence.append(f"Good text density: {signals.text_char_density:.2f}")
    
    if signals.text_line_count > 5:
        scores["native_text"] += 0.1
        evidence.append(f"Multiple text lines: {signals.text_line_count}")
    
    # ── Evidence: scanned image ──
    if signals.image_count > 0 and signals.image_coverage_pct > 80:
        scores["scanned_image"] += 0.4
        evidence.append(f"High image coverage: {signals.image_coverage_pct:.1f}%")
    
    if signals.has_large_image:
        scores["scanned_image"] += 0.2
        evidence.append("Large image covering >50% of page")
    
    if signals.raster_dpi > 100:
        scores["scanned_image"] += 0.15
        evidence.append(f"High DPI raster: {signals.raster_dpi:.0f}")
    
    if signals.image_count > 0 and signals.text_length < 50:
        scores["scanned_image"] += 0.15
        evidence.append(f"Image present but minimal text: {signals.text_length} chars")
    
    # ── Evidence: OCR overlay ──
    if signals.ocr_layer_detected:
        scores["ocr_overlay"] += 0.5
        evidence.append("OCR overlay detected: text overlapping image")
    
    if signals.image_coverage_pct > 30 and signals.text_length > 100:
        scores["ocr_overlay"] += 0.2
        evidence.append(f"Image + text coexist: {signals.image_coverage_pct:.1f}% image, {signals.text_length} chars")
    
    # ── Evidence: mixed content ──
    if signals.image_count > 0 and signals.text_length > 100:
        scores["mixed_content"] += 0.2
        evidence.append(f"Mixed: {signals.image_count} images + {signals.text_length} chars text")
    
    if 20 < signals.image_coverage_pct < 80:
        scores["mixed_content"] += 0.2
        evidence.append(f"Moderate image coverage: {signals.image_coverage_pct:.1f}%")
    
    # ── Penalize conflicting evidence ──
    if signals.image_coverage_pct > 80 and signals.text_length > 500:
        # High image coverage BUT lots of text — likely OCR overlay
        scores["native_text"] *= 0.3
        scores["scanned_image"] *= 0.5
        scores["ocr_overlay"] += 0.3
        evidence.append("Conflict: high image coverage + lots of text → likely OCR overlay")
    
    if signals.image_coverage_pct < 5 and signals.text_length > 200:
        # Very low image coverage + lots of text — definitely native
        scores["scanned_image"] *= 0.1
        scores["ocr_overlay"] *= 0.1
        scores["native_text"] += 0.2
        evidence.append("Confirmation: low image + high text → native text")
    
    # ── Select highest score ──
    best_class = max(scores, key=scores.get)
    best_score = scores[best_class]
    total_score = sum(scores.values())
    confidence = best_score / max(0.01, total_score)
    
    if best_score < 0.1:
        return {"class": "unknown", "confidence": 0.0, "evidence": evidence}
    
    return {"class": best_class, "confidence": round(confidence, 3), "evidence": evidence}


def classify_document_pages(filepath: Path) -> list[PageSignals]:
    """Classify every page in a document."""
    import pymupdf
    
    results = []
    try:
        doc = pymupdf.open(str(filepath))
        for i in range(len(doc)):
            page = doc[i]
            signals = classify_page(page, i + 1)
            results.append(signals)
        doc.close()
    except Exception as e:
        results.append(PageSignals(
            page_number=0,
            page_class="unknown",
            confidence=0.0,
            classification_evidence=[f"Error: {e}"],
        ))
    
    return results
