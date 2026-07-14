#!/usr/bin/env python3
"""
Phase 4 Smart Runner — Process native PDFs first for maximum throughput.
Then process scanned/OCR documents in batches.
"""
import logging
import sys
import json
from pathlib import Path

sys.stdout.reconfigure(line_buffering=True)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s', stream=sys.stdout)

from src.astrosage.production.run_corpus import CorpusProcessor

processor = CorpusProcessor(".")

# Load forensics data for ordering
forensics = json.loads(open("knowledge/benchmarks/forensics/forensic_results.json").read())
forensics_map = {r["filename"]: r for r in forensics}

# Get all PDFs
all_pdfs = sorted(processor.raw_dir.rglob("*.pdf"))
state = processor.load_checkpoint()
processed_set = set(state.get("processed", []))
quarantined_set = set(state.get("quarantined", []))

# Partition by type
native_pdfs = []
scanned_pdfs = []
other_pdfs = []
for fp in all_pdfs:
    if fp.name in processed_set or fp.name.replace(".pdf", "") in [q.replace(".txt","") for q in quarantined_set]:
        continue
    # Check bronze
    bronze = processor.bronze_dir / f"{fp.stem}.txt"
    if bronze.exists() and bronze.stat().st_size > 10:
        continue
    qf = processor.quarantine_dir / f"{fp.stem}.json"
    if qf.exists():
        continue
    
    f_info = forensics_map.get(fp.name, {})
    doc_class = f_info.get("document_class", "unknown")
    
    if doc_class == "native_text":
        native_pdfs.append(fp)
    elif doc_class in ("scanned_image", "ocr_overlay"):
        scanned_pdfs.append(fp)
    else:
        other_pdfs.append(fp)

total_remaining = len(native_pdfs) + len(scanned_pdfs) + len(other_pdfs)
print(f"\n=== PHASE 4 SMART PROCESSING ===")
print(f"Native PDFs (fast): {len(native_pdfs)}")
print(f"Scanned PDFs (OCR): {len(scanned_pdfs)}")
print(f"Other PDFs: {len(other_pdfs)}")
print(f"Total remaining: {total_remaining}")
print()

# Phase A: Process native PDFs (fast — no OCR needed)
if native_pdfs:
    print(f"=== PHASE A: Processing {len(native_pdfs)} native PDFs ===")
    results_a = []
    for i, fp in enumerate(native_pdfs):
        if (i+1) % 20 == 0:
            print(f"  [A: {i+1}/{len(native_pdfs)}] {fp.name[:50]}")
        try:
            result = processor.process_single_document(fp)
            results_a.append(result)
            # Update checkpoint
            if result["status"] == "complete":
                state["processed"].append(fp.name)
            elif result["status"] == "quarantined":
                state["quarantined"].append(fp.name)
            else:
                state["failed"].append(fp.name)
        except Exception as e:
            print(f"  ERROR: {fp.name}: {e}")
            state["failed"].append(fp.name)
        
        if (i+1) % 25 == 0:
            processor.save_checkpoint(state)
    
    processor.save_checkpoint(state)
    complete_a = sum(1 for r in results_a if r["status"] == "complete")
    print(f"  Phase A complete: {complete_a}/{len(native_pdfs)} native PDFs processed")

# Phase B: Process scanned/OCR PDFs (slow)
if scanned_pdfs:
    print(f"\n=== PHASE B: Processing {len(scanned_pdfs)} scanned PDFs (OCR) ===")
    results_b = []
    for i, fp in enumerate(scanned_pdfs):
        if (i+1) % 10 == 0:
            print(f"  [B: {i+1}/{len(scanned_pdfs)}] {fp.name[:50]}")
        try:
            result = processor.process_single_document(fp)
            results_b.append(result)
            if result["status"] == "complete":
                state["processed"].append(fp.name)
            elif result["status"] == "quarantined":
                state["quarantined"].append(fp.name)
            else:
                state["failed"].append(fp.name)
        except Exception as e:
            print(f"  ERROR: {fp.name}: {e}")
            state["failed"].append(fp.name)
        
        if (i+1) % 10 == 0:
            processor.save_checkpoint(state)
    
    processor.save_checkpoint(state)
    complete_b = sum(1 for r in results_b if r["status"] == "complete")
    print(f"  Phase B complete: {complete_b}/{len(scanned_pdfs)} scanned PDFs processed")

# Phase C: Process other/hybrid PDFs
if other_pdfs:
    print(f"\n=== PHASE C: Processing {len(other_pdfs)} other PDFs ===")
    results_c = []
    for i, fp in enumerate(other_pdfs):
        try:
            result = processor.process_single_document(fp)
            results_c.append(result)
            if result["status"] == "complete":
                state["processed"].append(fp.name)
            elif result["status"] == "quarantined":
                state["quarantined"].append(fp.name)
            else:
                state["failed"].append(fp.name)
        except Exception as e:
            print(f"  ERROR: {fp.name}: {e}")
            state["failed"].append(fp.name)
    
    processor.save_checkpoint(state)
    complete_c = sum(1 for r in results_c if r["status"] == "complete")
    print(f"  Phase C complete: {complete_c}/{len(other_pdfs)} other PDFs processed")

# Final summary
processor.save_checkpoint(state)
bronze_count = len(list(processor.bronze_dir.glob("*.txt")))
silver_count = len(list(processor.silver_dir.glob("*.md")))
quarantine_count = len(list(processor.quarantine_dir.glob("*.json")))

print(f"\n=== FINAL SUMMARY ===")
print(f"Bronze files: {bronze_count}")
print(f"Silver files: {silver_count}")
print(f"Quarantined: {quarantine_count}")
print(f"Checkpoint processed: {len(state.get('processed', []))}")
print(f"Checkpoint failed: {len(state.get('failed', []))}")
