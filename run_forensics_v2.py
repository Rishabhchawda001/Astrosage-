#!/usr/bin/env python3
"""
Forensic analysis v2: multiprocessing-based with proper timeout isolation.
"""
import sys
import os
import json
import time
import traceback
from pathlib import Path
from collections import Counter
from dataclasses import asdict
from multiprocessing import Pool, TimeoutError as MPTimeoutError

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

BASE = Path("/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage")
RAW_DIR = BASE / "knowledge" / "raw" / "source_library"
FORENSICS_DIR = BASE / "knowledge" / "benchmarks" / "forensics"
FORENSICS_DIR.mkdir(parents=True, exist_ok=True)


def classify_single_doc(filepath_str):
    """Classify a single document. Runs in a subprocess."""
    import pymupdf
    import signal
    from collections import Counter
    from dataclasses import asdict
    from pathlib import Path
    
    filepath = Path(filepath_str)
    sys.path.insert(0, str(BASE / "src"))
    from astrosage.forensics.page_classifier import classify_page, PageSignals
    
    result = {
        "filename": filepath.name,
        "relative_path": str(filepath.relative_to(RAW_DIR)),
        "total_pages": 0,
        "page_classes": [],
        "page_class_counts": {},
        "document_class": "error",
        "document_confidence": 0.0,
        "error": None,
        "timed_out_pages": 0,
    }
    
    try:
        doc = pymupdf.open(str(filepath))
        num_pages = len(doc)
        result["total_pages"] = num_pages
        
        # Limit to 200 pages per doc for efficiency (sample if larger)
        step = max(1, num_pages // 200) if num_pages > 200 else 1
        pages_to_classify = list(range(0, num_pages, step))
        
        page_classes = []
        for idx in pages_to_classify:
            page = doc[idx]
            try:
                signals = classify_page(page, idx + 1)
                page_classes.append(signals.page_class)
            except Exception:
                page_classes.append("unknown")
        
        doc.close()
        
        result["page_classes"] = page_classes
        class_counts = Counter(page_classes)
        result["page_class_counts"] = dict(class_counts)
        
        if class_counts:
            most_common = class_counts.most_common(1)[0]
            result["document_class"] = most_common[0]
            result["document_confidence"] = round(most_common[1] / len(page_classes), 3)
        
        # Detect hybrid documents
        if len(class_counts) > 1:
            top_class, top_count = most_common
            if top_count < len(page_classes) * 0.8:
                result["document_class"] = "hybrid"
                result["document_confidence"] = round(top_count / len(page_classes), 3)
        
    except Exception as e:
        result["error"] = str(e)[:200]
    
    return result


def main():
    print("=" * 70, flush=True)
    print("PHASE 3.1 — DOCUMENT FORENSICS v2 (Multiprocessing)", flush=True)
    print("=" * 70, flush=True)
    
    pdfs = sorted(RAW_DIR.rglob("*.pdf"))
    print(f"Found {len(pdfs)} PDFs", flush=True)
    
    results_file = FORENSICS_DIR / "forensic_results.json"
    
    # Load existing progress
    existing = {}
    if results_file.exists():
        try:
            existing_data = json.loads(results_file.read_text())
            existing = {r["filename"]: r for r in existing_data}
            print(f"Resuming: {len(existing)} already processed", flush=True)
        except:
            pass
    
    # Filter out already-processed PDFs
    remaining = [fp for fp in pdfs if fp.name not in existing]
    print(f"Remaining: {len(remaining)} to process", flush=True)
    
    all_results = list(existing.values())
    start_time = time.time()
    
    # Process in parallel with timeout
    DOC_TIMEOUT = 60  # seconds per document
    
    if remaining:
        with Pool(processes=4) as pool:
            async_results = {}
            for fp in remaining:
                ar = pool.apply_async(classify_single_doc, (str(fp),))
                async_results[fp.name] = (ar, fp)
            
            completed = 0
            total = len(remaining)
            
            for name, (ar, fp) in list(async_results.items()):
                try:
                    result = ar.get(timeout=DOC_TIMEOUT)
                    all_results.append(result)
                    completed += 1
                    
                    if completed % 20 == 0:
                        elapsed = time.time() - start_time
                        print(f"  [{completed}/{total}] Elapsed: {elapsed:.0f}s", flush=True)
                        # Save checkpoint
                        save_results(all_results, results_file)
                        
                except MPTimeoutError:
                    print(f"  TIMEOUT: {name} ({DOC_TIMEOUT}s)", flush=True)
                    all_results.append({
                        "filename": name,
                        "relative_path": str(fp.relative_to(RAW_DIR)),
                        "total_pages": 0,
                        "page_classes": [],
                        "document_class": "timeout",
                        "error": f"Timeout after {DOC_TIMEOUT}s",
                    })
                    completed += 1
                    
                except Exception as e:
                    print(f"  ERROR: {name}: {str(e)[:80]}", flush=True)
                    all_results.append({
                        "filename": name,
                        "relative_path": str(fp.relative_to(RAW_DIR)),
                        "total_pages": 0,
                        "page_classes": [],
                        "document_class": "error",
                        "error": str(e)[:200],
                    })
                    completed += 1
        
        pool.close()
        pool.join()
    
    # Final save
    save_results(all_results, results_file)
    
    # ── Compute statistics ──
    all_page_classes = []
    for r in all_results:
        all_page_classes.extend(r.get("page_classes", []))
    
    total_pages = len(all_page_classes)
    page_class_counts = Counter(all_page_classes)
    doc_class_counts = Counter(r.get("document_class", "error") for r in all_results)
    
    print("\n" + "=" * 70, flush=True)
    print("RESULTS", flush=True)
    print("=" * 70, flush=True)
    print(f"Total PDFs: {len(pdfs)}", flush=True)
    print(f"Documents processed: {len(all_results)}", flush=True)
    print(f"Total pages sampled: {total_pages}", flush=True)
    print(f"Processing time: {time.time() - start_time:.0f}s", flush=True)
    
    print("\nPage-level classifications:", flush=True)
    for cls, count in page_class_counts.most_common():
        pct = count / max(1, total_pages) * 100
        print(f"  {cls}: {count} ({pct:.1f}%)", flush=True)
    
    print("\nDocument-level classifications:", flush=True)
    for cls, count in doc_class_counts.most_common():
        print(f"  {cls}: {count}", flush=True)
    
    # ── Evidence summary ──
    evidence = {
        "total_pdfs": len(pdfs),
        "total_documents_processed": len(all_results),
        "total_pages_sampled": total_pages,
        "page_class_distribution": {cls: {"count": count, "pct": round(count/max(1,total_pages)*100, 2)} for cls, count in page_class_counts.most_common()},
        "document_class_distribution": dict(doc_class_counts),
        "native_text_pct": round(page_class_counts.get("native_text", 0) / max(1, total_pages) * 100, 2),
        "scanned_pct": round(page_class_counts.get("scanned_image", 0) / max(1, total_pages) * 100, 2),
        "ocr_overlay_pct": round(page_class_counts.get("ocr_overlay", 0) / max(1, total_pages) * 100, 2),
        "mixed_pct": round(page_class_counts.get("mixed_content", 0) / max(1, total_pages) * 100, 2),
        "blank_pct": round(page_class_counts.get("blank", 0) / max(1, total_pages) * 100, 2),
        "processing_time_sec": round(time.time() - start_time, 1),
    }
    
    native_pct = evidence["native_text_pct"]
    scanned_total = evidence["scanned_pct"] + evidence["ocr_overlay_pct"]
    
    if native_pct > 95:
        evidence["conclusion"] = "CORROBORATED: >95% native text pages. The claim of 'zero scanned' is approximately correct."
        evidence["verdict"] = "corroborated"
    elif native_pct > 80:
        evidence["conclusion"] = "PARTIALLY CORROBORATED: Majority native text but meaningful scanned content exists."
        evidence["verdict"] = "partially_corroborated"
    elif native_pct > 50:
        evidence["conclusion"] = "PARTIALLY CORROBORATED: ~Half native, half scanned/OCR. The 'zero scanned' claim is FALSE."
        evidence["verdict"] = "partially_corroborated"
    else:
        evidence["conclusion"] = "DISPROVED: Significant scanned content. The 'zero scanned' claim is FALSE."
        evidence["verdict"] = "disproved"
    
    (FORENSICS_DIR / "evidence_summary.json").write_text(json.dumps(evidence, indent=2, ensure_ascii=False))
    print(f"\nConclusion: {evidence['conclusion']}", flush=True)
    print(f"Verdict: {evidence['verdict']}", flush=True)
    
    # Save page class distribution
    (FORENSICS_DIR / "page_class_distribution.json").write_text(json.dumps(dict(page_class_counts), indent=2))


def save_results(all_results, results_file):
    """Save intermediate results."""
    lightweight = []
    for r in all_results:
        lr = {k: v for k, v in r.items() if k != "page_signals"}
        lightweight.append(lr)
    results_file.write_text(json.dumps(lightweight, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
