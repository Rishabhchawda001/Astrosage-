#!/usr/bin/env python3
"""
Robust forensic analysis runner with timeouts and batch saves.
"""
import sys
import os
import json
import time
import signal
import traceback
from pathlib import Path
from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import Optional

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

import pymupdf

BASE = Path("/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage")
FORENSICS_DIR = BASE / "knowledge" / "benchmarks" / "forensics"
FORENSICS_DIR.mkdir(parents=True, exist_ok=True)

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Page classification timed out")

# ── Import the page classifier ──
sys.path.insert(0, str(BASE / "src"))
from astrosage.forensics.page_classifier import classify_page, PageSignals

def classify_with_timeout(page, page_number, timeout_sec=30):
    """Classify a page with a per-page timeout."""
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_sec)
    try:
        signals = classify_page(page, page_number)
        signal.alarm(0)
        return signals
    except TimeoutError:
        return PageSignals(
            page_number=page_number,
            page_class="unknown",
            confidence=0.0,
            classification_evidence=["Classification timed out"],
        )
    except Exception as e:
        return PageSignals(
            page_number=page_number,
            page_class="unknown",
            confidence=0.0,
            classification_evidence=[f"Error: {e}"],
        )
    finally:
        signal.signal(signal.SIGALRM, old_handler)
        signal.alarm(0)


def classify_document(filepath, doc_timeout=120):
    """Classify all pages in a document with timeout handling."""
    result = {
        "filename": filepath.name,
        "relative_path": str(filepath.relative_to(BASE / "knowledge" / "raw" / "source_library")),
        "total_pages": 0,
        "page_signals": [],
        "page_classes": [],
        "timed_out_pages": 0,
        "error_pages": 0,
        "error": None,
    }
    
    try:
        doc = pymupdf.open(str(filepath))
        result["total_pages"] = len(doc)
        
        doc_start = time.time()
        for i in range(len(doc)):
            # Check document-level timeout
            if time.time() - doc_start > doc_timeout:
                result["error"] = f"Document timeout after {doc_timeout}s at page {i+1}/{len(doc)}"
                break
            
            page = doc[i]
            signals = classify_with_timeout(page, i + 1, timeout_sec=10)
            result["page_signals"].append(asdict(signals))
            result["page_classes"].append(signals.page_class)
            
            if "timed out" in " ".join(signals.classification_evidence):
                result["timed_out_pages"] += 1
            elif "Error" in " ".join(signals.classification_evidence):
                result["error_pages"] += 1
        
        doc.close()
    except Exception as e:
        result["error"] = str(e)
    
    # Document-level classification
    if result["page_classes"]:
        class_counts = Counter(result["page_classes"])
        most_common = class_counts.most_common(1)[0]
        result["document_class"] = most_common[0]
        result["document_confidence"] = most_common[1] / len(result["page_classes"])
        result["page_class_counts"] = dict(class_counts)
    else:
        result["document_class"] = "error"
        result["document_confidence"] = 0.0
        result["page_class_counts"] = {}
    
    return result


def main():
    print("=" * 70, flush=True)
    print("PHASE 3.1 — DOCUMENT FORENSICS & CLASSIFIER VALIDATION", flush=True)
    print("=" * 70, flush=True)
    
    # Discover PDFs
    pdfs = sorted((BASE / "knowledge" / "raw" / "source_library").rglob("*.pdf"))
    print(f"Found {len(pdfs)} PDFs", flush=True)
    
    results_file = FORENSICS_DIR / "forensic_results.json"
    
    # Check for existing progress
    existing = {}
    if results_file.exists():
        try:
            existing_data = json.loads(results_file.read_text())
            existing = {r["filename"]: r for r in existing_data}
            print(f"Resuming: {len(existing)} already processed", flush=True)
        except:
            existing = {}
    
    all_results = list(existing.values()) if existing else []
    processed_names = set(r["filename"] for r in all_results)
    
    all_page_classes = []
    all_page_signals = []
    errors = []
    start_time = time.time()
    
    for i, fp in enumerate(pdfs):
        if fp.name in processed_names:
            # Count pages from existing results
            existing_r = next(r for r in all_results if r["filename"] == fp.name)
            all_page_classes.extend(existing_r.get("page_classes", []))
            continue
        
        elapsed = time.time() - start_time
        if (i + 1) % 10 == 0 or i == 0:
            print(f"  [{i+1}/{len(pdfs)}] Elapsed: {elapsed:.0f}s | {fp.name[:50]}", flush=True)
        
        result = classify_document(fp, doc_timeout=120)
        all_results.append(result)
        all_page_classes.extend(result.get("page_classes", []))
        all_page_signals.extend(result.get("page_signals", []))
        
        if result.get("error"):
            errors.append({"file": fp.name, "error": result["error"]})
        
        # Save every 20 files
        if (i + 1) % 20 == 0:
            save_results(all_results, all_page_classes, errors, results_file)
            print(f"    Saved checkpoint: {len(all_results)} files", flush=True)
    
    # Final save
    save_results(all_results, all_page_classes, errors, results_file)
    
    # Compute statistics
    total_pages = len(all_page_classes)
    class_counts = Counter(all_page_classes)
    
    print("\n" + "=" * 70, flush=True)
    print("RESULTS", flush=True)
    print("=" * 70, flush=True)
    print(f"Total PDFs: {len(pdfs)}", flush=True)
    print(f"Total pages analyzed: {total_pages}", flush=True)
    print(f"Processing time: {time.time() - start_time:.0f}s", flush=True)
    print(f"Errors: {len(errors)}", flush=True)
    print()
    
    for cls, count in class_counts.most_common():
        pct = count / max(1, total_pages) * 100
        print(f"  {cls}: {count} ({pct:.1f}%)", flush=True)
    
    # Document-level classes
    doc_classes = Counter(r.get("document_class", "error") for r in all_results)
    print("\nDocument-level classifications:", flush=True)
    for cls, count in doc_classes.most_common():
        print(f"  {cls}: {count}", flush=True)
    
    # Fully scanned docs
    scanned_docs = [r for r in all_results if r.get("document_class") == "scanned_image"]
    ocr_docs = [r for r in all_results if r.get("document_class") == "ocr_overlay"]
    mixed_docs = [r for r in all_results if r.get("document_class") == "hybrid"]
    native_docs = [r for r in all_results if r.get("document_class") == "native_text"]
    
    print(f"\nFully scanned documents: {len(scanned_docs)}", flush=True)
    print(f"OCR overlay documents: {len(ocr_docs)}", flush=True)
    print(f"Hybrid documents: {len(mixed_docs)}", flush=True)
    print(f"Native text documents: {len(native_docs)}", flush=True)
    
    # Save evidence summary
    evidence = {
        "total_pdfs": len(pdfs),
        "total_pages": total_pages,
        "page_class_distribution": {cls: {"count": count, "pct": round(count/max(1,total_pages)*100, 2)} for cls, count in class_counts.most_common()},
        "document_class_distribution": dict(doc_classes),
        "fully_scanned_docs": len(scanned_docs),
        "ocr_overlay_docs": len(ocr_docs),
        "hybrid_docs": len(mixed_docs),
        "native_text_docs": len(native_docs),
        "native_text_pct": round(class_counts.get("native_text", 0) / max(1, total_pages) * 100, 2),
        "scanned_pct": round(class_counts.get("scanned_image", 0) / max(1, total_pages) * 100, 2),
        "ocr_overlay_pct": round(class_counts.get("ocr_overlay", 0) / max(1, total_pages) * 100, 2),
        "mixed_pct": round(class_counts.get("mixed_content", 0) / max(1, total_pages) * 100, 2),
        "blank_pct": round(class_counts.get("blank", 0) / max(1, total_pages) * 100, 2),
        "errors": len(errors),
        "processing_time_sec": round(time.time() - start_time, 1),
    }
    
    # Determine conclusion
    native_pct = evidence["native_text_pct"]
    scanned_total = evidence["scanned_pct"] + evidence["ocr_overlay_pct"]
    
    if native_pct > 95:
        evidence["conclusion"] = "CORROBORATED: The corpus is overwhelmingly native text (>95% native pages)."
        evidence["verdict"] = "corroborated"
    elif native_pct > 80:
        evidence["conclusion"] = "PARTIALLY CORROBORATED: Majority native text but significant scanned content exists."
        evidence["verdict"] = "partially_corroborated"
    elif native_pct > 50:
        evidence["conclusion"] = "PARTIALLY CORROBORATED: ~Half native, half scanned/OCR. Original claim of 'zero scanned' is FALSE."
        evidence["verdict"] = "partially_corroborated"
    else:
        evidence["conclusion"] = "DISPROVED: The corpus contains significant scanned content. Original 'zero scanned' claim is FALSE."
        evidence["verdict"] = "disproved"
    
    (FORENSICS_DIR / "evidence_summary.json").write_text(json.dumps(evidence, indent=2, ensure_ascii=False))
    print(f"\nConclusion: {evidence['conclusion']}", flush=True)
    print(f"Saved: {FORENSICS_DIR / 'evidence_summary.json'}", flush=True)
    
    if errors:
        print(f"\nErrors ({len(errors)}):", flush=True)
        for e in errors[:10]:
            print(f"  {e['file']}: {e['error'][:100]}", flush=True)


def save_results(all_results, all_page_classes, errors, results_file):
    """Save intermediate results."""
    # Save per-document results (without full page_signals to save space)
    lightweight = []
    for r in all_results:
        lr = {k: v for k, v in r.items() if k != "page_signals"}
        lightweight.append(lr)
    
    results_file.write_text(json.dumps(lightweight, indent=1, ensure_ascii=False))
    
    # Save page class distribution
    class_dist = dict(Counter(all_page_classes))
    (FORENSICS_DIR / "page_class_distribution.json").write_text(
        json.dumps(class_dist, indent=2)
    )
    
    # Save errors
    if errors:
        (FORENSICS_DIR / "classification_errors.json").write_text(
            json.dumps(errors, indent=2)
        )


if __name__ == "__main__":
    main()
