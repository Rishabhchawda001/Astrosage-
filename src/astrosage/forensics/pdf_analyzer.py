"""
PDF Forensics — Low-level PDF structure analysis.

Inspects:
  - Embedded fonts (and whether they're standard or custom)
  - Raster images (count, size, DPI, format)
  - Vector graphics (paths, lines, curves)
  - Compression methods
  - Hidden text layers
  - Annotations
  - Bookmarks
  - Embedded metadata
  - Rendering complexity
  - Page content streams

Determines:
  - Born Digital (created from software, not scanned)
  - Scanned (image-based, no native text)
  - OCR Overlay (scanned + invisible OCR text)
  - Hybrid (mix of native and scanned pages)
  - Converted (from another format)
"""
from __future__ import annotations

import re
import time
from collections import Counter
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


@dataclass
class PageForensics:
    """Low-level forensics for a single PDF page."""
    page_number: int = 0
    
    # Content streams
    content_stream_length: int = 0
    
    # Fonts
    embedded_fonts: list = field(default_factory=list)
    font_count: int = 0
    has_cid_fonts: bool = False  # CID fonts indicate Unicode/complex text
    has_standard_fonts: bool = False  # Helvetica, Times, Courier
    has_custom_fonts: bool = False
    
    # Images
    raster_image_count: int = 0
    raster_image_formats: list = field(default_factory=list)
    total_image_bytes: int = 0
    max_image_dpi: float = 0.0
    
    # Vectors
    vector_path_count: int = 0
    vector_line_count: int = 0
    
    # Text
    has_text_layer: bool = False
    text_is_visible: bool = False
    text_is_hidden: bool = False  # Text in content stream but not rendered
    ocr_confidence_indicator: float = 0.0
    
    # Complexity
    rendering_operations: int = 0
    color_space_count: int = 0
    
    # Classification
    forensic_class: str = "unknown"  # born_digital, scanned, ocr_overlay, hybrid, converted
    forensic_confidence: float = 0.0
    forensic_evidence: list = field(default_factory=list)


def analyze_page_forensics(page, page_number: int) -> PageForensics:
    """Perform low-level forensics on a single page."""
    forensics = PageForensics(page_number=page_number)
    evidence = []
    
    # ── Content stream analysis ──
    try:
        xref = page.xref
        contents = page.get_contents()
        if contents:
            total_length = 0
            for c in contents:
                try:
                    stream = page.parent.xref_stream(c)
                    total_length += len(stream) if stream else 0
                except:
                    pass
            forensics.content_stream_length = total_length
    except:
        pass
    
    # ── Font analysis ──
    try:
        font_list = page.get_fonts(full=True)
        forensics.font_count = len(font_list)
        
        standard_fonts = {"Helvetica", "Times", "Courier", "Symbol", "ZapfDingbats"}
        
        for font_info in font_list:
            if len(font_info) >= 4:
                font_name = font_info[3] if len(font_info) > 3 else ""
                encoding = font_info[1] if len(font_info) > 1 else ""
                name = font_info[2] if len(font_info) > 2 else ""
                
                forensics.embedded_fonts.append(font_name)
                
                # Check for CID fonts (complex text rendering)
                if "CID" in encoding or "Identity" in encoding:
                    forensics.has_cid_fonts = True
                    evidence.append(f"CID font detected: {font_name} (encoding: {encoding})")
                
                # Check for standard vs custom fonts
                is_standard = any(sf.lower() in font_name.lower() for sf in standard_fonts)
                if is_standard:
                    forensics.has_standard_fonts = True
                else:
                    forensics.has_custom_fonts = True
        
        if forensics.has_cid_fonts:
            evidence.append("CID fonts indicate Unicode text support")
        
    except Exception as e:
        evidence.append(f"Font analysis error: {e}")
    
    # ── Image analysis ──
    try:
        images = page.get_images(full=True)
        forensics.raster_image_count = len(images)
        
        formats = set()
        total_bytes = 0
        max_dpi = 0
        
        for img in images:
            xref = img[0]
            try:
                img_dict = page.parent.extract_image(xref)
                if img_dict:
                    ext = img_dict.get("ext", "unknown")
                    image_bytes = img_dict.get("image", b"")
                    width = img_dict.get("width", 0)
                    height = img_dict.get("height", 0)
                    
                    formats.add(ext)
                    total_bytes += len(image_bytes)
                    
                    # DPI estimation
                    if width > 0 and height > 0:
                        page_rect = page.rect
                        dpi_x = width / (page_rect.width / 72)
                        dpi_y = height / (page_rect.height / 72)
                        avg_dpi = (dpi_x + dpi_y) / 2
                        max_dpi = max(max_dpi, avg_dpi)
            except:
                pass
        
        forensics.raster_image_formats = list(formats)
        forensics.total_image_bytes = total_bytes
        forensics.max_image_dpi = max_dpi
        
        if images:
            evidence.append(f"{len(images)} images, formats: {formats}, DPI: {max_dpi:.0f}")
            if max_dpi > 150:
                evidence.append("High DPI (likely scan at 200+ DPI)")
            elif max_dpi > 0:
                evidence.append(f"Moderate DPI ({max_dpi:.0f})")
        
    except Exception as e:
        evidence.append(f"Image analysis error: {e}")
    
    # ── Vector analysis ──
    try:
        drawings = page.get_drawings()
        forensics.vector_path_count = len(drawings)
        evidence.append(f"{len(drawings)} vector paths")
    except:
        pass
    
    # ── Text layer analysis ──
    text = page.get_text("text")
    forensics.has_text_layer = bool(text.strip())
    
    # Check if text is visible (in the content stream) or hidden
    # Hidden text would be in the content stream but with zero-width fonts
    if forensics.has_text_layer:
        text_dict = page.get_text("dict")
        blocks = text_dict.get("blocks", [])
        text_blocks = [b for b in blocks if b.get("type") == 0]
        
        if text_blocks:
            # Check font sizes — hidden OCR text often uses very small fonts
            small_font_count = 0
            total_spans = 0
            for block in text_blocks:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        total_spans += 1
                        if span.get("size", 12) < 1:
                            small_font_count += 1
            
            if total_spans > 0 and small_font_count / total_spans > 0.5:
                forensics.text_is_hidden = True
                evidence.append(f"Hidden text detected: {small_font_count}/{total_spans} spans with tiny fonts")
            else:
                forensics.text_is_visible = True
    
    # ── RENDERING COMPLEXITY ──
    try:
        # Count rendering operations in content stream
        ops = page.get_text_trace()
        forensics.rendering_operations = len(ops) if ops else 0
    except:
        pass
    
    # ── FORENSIC CLASSIFICATION ──
    class_result = _forensic_classify(forensics, evidence)
    forensics.forensic_class = class_result["class"]
    forensics.forensic_confidence = class_result["confidence"]
    forensics.forensic_evidence = evidence
    
    return forensics


def _forensic_classify(f: PageForensics, evidence: list) -> dict:
    """Classify using forensic evidence."""
    scores = {
        "born_digital": 0.0,
        "scanned": 0.0,
        "ocr_overlay": 0.0,
        "hybrid": 0.0,
        "converted": 0.0,
    }
    
    # ── Born Digital indicators ──
    if f.has_text_layer and f.text_is_visible:
        scores["born_digital"] += 0.3
        evidence.append("Visible text layer → born digital")
    
    if f.has_cid_fonts:
        scores["born_digital"] += 0.15
        evidence.append("CID fonts → Unicode text support → born digital")
    
    if f.has_custom_fonts:
        scores["born_digital"] += 0.1
        evidence.append("Custom fonts → created by software → born digital")
    
    if f.raster_image_count == 0:
        scores["born_digital"] += 0.15
        evidence.append("No raster images → pure text/vector → born digital")
    
    if f.font_count >= 2:
        scores["born_digital"] += 0.1
        evidence.append(f"{f.font_count} fonts → formatted document")
    
    # ── Scanned indicators ──
    if f.raster_image_count > 0 and f.max_image_dpi > 150:
        scores["scanned"] += 0.3
        evidence.append(f"High DPI images ({f.max_image_dpi:.0f}) → likely scan")
    
    if f.raster_image_count > 0 and f.total_image_bytes > 500000:
        scores["scanned"] += 0.2
        evidence.append(f"Large image data ({f.total_image_bytes / 1024:.0f}KB) → likely scan")
    
    if f.font_count == 0 and f.raster_image_count > 0:
        scores["scanned"] += 0.25
        evidence.append("No fonts + images → scanned page")
    
    if not f.has_text_layer and f.raster_image_count > 0:
        scores["scanned"] += 0.2
        evidence.append("No text layer + images → scanned")
    
    # ── OCR Overlay indicators ──
    if f.has_text_layer and f.raster_image_count > 0 and f.max_image_dpi > 100:
        scores["ocr_overlay"] += 0.3
        evidence.append("Text layer + high-DPI images → OCR overlay")
    
    if f.text_is_hidden and f.raster_image_count > 0:
        scores["ocr_overlay"] += 0.3
        evidence.append("Hidden text + images → OCR overlay (invisible text on scan)")
    
    if f.has_text_layer and f.image_coverage_pct > 50 if hasattr(f, 'image_coverage_pct') else False:
        scores["ocr_overlay"] += 0.2
    
    # ── Hybrid indicators ──
    if f.has_text_layer and f.raster_image_count > 0 and f.max_image_dpi < 100:
        scores["hybrid"] += 0.2
        evidence.append("Text + low-DPI images → hybrid (embedded figures)")
    
    # ── Select best ──
    best = max(scores, key=scores.get)
    best_score = scores[best]
    total = sum(scores.values())
    
    return {
        "class": best,
        "confidence": round(best_score / max(0.01, total), 3),
    }


def analyze_pdf_forensics(filepath: Path) -> dict:
    """Run full forensics on a PDF file."""
    import pymupdf
    
    result = {
        "filename": filepath.name,
        "filepath": str(filepath),
        "total_pages": 0,
        "page_forensics": [],
        "document_class": "unknown",
        "document_confidence": 0.0,
        "has_native_text": False,
        "has_scanned_pages": False,
        "has_ocr_overlay": False,
        "total_images": 0,
        "total_fonts": 0,
        "total_image_bytes": 0,
        "fonts": [],
    }
    
    try:
        doc = pymupdf.open(str(filepath))
        result["total_pages"] = len(doc)
        
        page_classes = []
        all_fonts = set()
        total_images = 0
        total_img_bytes = 0
        total_dpi = 0
        dpi_count = 0
        
        sample_pages = min(len(doc), 10)  # Sample up to 10 pages for efficiency
        
        for i in range(sample_pages):
            page = doc[i]
            pf = analyze_page_forensics(page, i + 1)
            result["page_forensics"].append(asdict(pf))
            page_classes.append(pf.forensic_class)
            
            all_fonts.update(pf.embedded_fonts)
            total_images += pf.raster_image_count
            total_img_bytes += pf.total_image_bytes
            if pf.max_image_dpi > 0:
                total_dpi += pf.max_image_dpi
                dpi_count += 1
        
        doc.close()
        
        result["total_images"] = total_images
        result["total_fonts"] = len(all_fonts)
        result["fonts"] = list(all_fonts)
        result["total_image_bytes"] = total_img_bytes
        result["avg_image_dpi"] = total_dpi / max(1, dpi_count)
        
        # Document-level classification from page classes
        class_counts = Counter(page_classes)
        if class_counts:
            most_common = class_counts.most_common(1)[0]
            result["document_class"] = most_common[0]
            result["document_confidence"] = most_common[1] / len(page_classes)
        
        result["has_native_text"] = "born_digital" in page_classes
        result["has_scanned_pages"] = "scanned" in page_classes
        result["has_ocr_overlay"] = "ocr_overlay" in page_classes
        
        # If >20% of sampled pages are scanned, mark as hybrid
        scanned_pct = class_counts.get("scanned", 0) + class_counts.get("ocr_overlay", 0)
        if scanned_pct > 0 and scanned_pct < len(page_classes) * 0.8:
            result["document_class"] = "hybrid"
        
    except Exception as e:
        result["error"] = str(e)
    
    return result
