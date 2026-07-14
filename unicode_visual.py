"""Generate visual validation samples and Unicode quality analysis."""
import json, sys, random, re
from pathlib import Path
from collections import Counter
import pymupdf

sys.stdout.reconfigure(line_buffering=True)

BASE = Path(".")
FORENSICS_DIR = BASE / "knowledge" / "benchmarks" / "forensics"
VISUAL_DIR = FORENSICS_DIR / "visual_samples"
VISUAL_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR = BASE / "knowledge" / "raw" / "source_library"

data = json.loads(open(FORENSICS_DIR / "forensic_results.json").read())

# ══════════════════════════════════════════════════════════════════
# 1. VISUAL VALIDATION
# ══════════════════════════════════════════════════════════════════
print("Generating visual validation samples...", flush=True)

by_class = {}
for r in data:
    cls = r.get("document_class", "error")
    if cls not in by_class:
        by_class[cls] = []
    by_class[cls].append(r)

all_samples = []
for cls, docs in by_class.items():
    if cls in ("timeout", "error"):
        continue
    sampled = random.sample(docs, min(3, len(docs)))
    for doc in sampled:
        fp = RAW_DIR / doc.get("relative_path", "")
        if not fp.exists():
            continue
        try:
            pdf_doc = pymupdf.open(str(fp))
            total_pages = len(pdf_doc)
            pages_to_sample = [0]
            if total_pages > 10:
                pages_to_sample.append(total_pages // 2)
            elif total_pages > 1:
                pages_to_sample.append(1)
            
            for page_idx in pages_to_sample:
                if page_idx >= total_pages:
                    continue
                page = pdf_doc[page_idx]
                pix = page.get_pixmap(dpi=150)
                img_name = f"{cls}_{doc['filename'][:40]}_p{page_idx+1}.png"
                img_name = re.sub(r'[^\w\-_\.]', '_', img_name)
                img_path = VISUAL_DIR / img_name
                pix.save(str(img_path))
                
                text = page.get_text("text")
                all_samples.append({
                    "document": doc["filename"],
                    "document_class": cls,
                    "page": page_idx + 1,
                    "text_length": len(text.strip()),
                    "text_preview": text[:500].strip(),
                    "image_path": str(img_path),
                    "total_pages": total_pages,
                })
            pdf_doc.close()
        except Exception as e:
            print(f"  Warning: {doc['filename']}: {e}", flush=True)

with open(VISUAL_DIR / "visual_validation.json", "w", encoding="utf-8") as f:
    json.dump(all_samples, f, indent=2, ensure_ascii=False)

lines = ["# Visual Validation Report\n"]
lines.append(f"Total samples: {len(all_samples)}\n")

by_cls = {}
for s in all_samples:
    cls = s["document_class"]
    if cls not in by_cls:
        by_cls[cls] = []
    by_cls[cls].append(s)

for cls, samples in sorted(by_cls.items()):
    lines.append(f"\n## {cls.upper()} ({len(samples)} samples)\n")
    for s in samples:
        lines.append(f"### {s['document'][:50]} — Page {s['page']}/{s['total_pages']}\n")
        lines.append(f"- **Text length:** {s['text_length']} chars")
        lines.append(f"- **Image:** `{s['image_path']}`")
        if s['text_preview']:
            lines.append(f"- **Text preview:** `{s['text_preview'][:200]}...`")
        else:
            lines.append("- **Text preview:** (no text)")
        lines.append("")

with open(VISUAL_DIR / "VISUAL_VALIDATION.md", "w") as f:
    f.write("\n".join(lines))

print(f"  Generated {len(all_samples)} visual samples", flush=True)

# ══════════════════════════════════════════════════════════════════
# 2. UNICODE QUALITY ANALYSIS
# ══════════════════════════════════════════════════════════════════
print("\nRunning Unicode quality analysis...", flush=True)

sampled_pdfs = random.sample([r for r in data if r.get("document_class") != "timeout"], min(50, len(data)))

unicode_issues = []
encoding_errors = 0
total_chars = 0
devanagari_chars = 0
latin_chars = 0
other_chars = 0

for r in sampled_pdfs:
    fp = RAW_DIR / r.get("relative_path", "")
    if not fp.exists():
        continue
    try:
        doc = pymupdf.open(str(fp))
        pages = random.sample(range(len(doc)), min(5, len(doc)))
        for pi in pages:
            text = doc[pi].get_text("text")
            total_chars += len(text)
            
            for ch in text:
                cp = ord(ch)
                if 0x0900 <= cp <= 0x097F:
                    devanagari_chars += 1
                elif 0x0020 <= cp <= 0x007E:
                    latin_chars += 1
                elif cp > 127:
                    other_chars += 1
            
            if '\ufffd' in text:
                encoding_errors += 1
                unicode_issues.append({
                    "file": r["filename"],
                    "page": pi + 1,
                    "issue": "Replacement character (U+FFFD) detected",
                    "count": text.count('\ufffd')
                })
        doc.close()
    except Exception as e:
        encoding_errors += 1

unicode_report = {
    "total_characters_analyzed": total_chars,
    "devanagari_characters": devanagari_chars,
    "latin_characters": latin_chars,
    "other_characters": other_chars,
    "devanagari_pct": round(devanagari_chars / max(1, total_chars) * 100, 2),
    "latin_pct": round(latin_chars / max(1, total_chars) * 100, 2),
    "other_pct": round(other_chars / max(1, total_chars) * 100, 2),
    "encoding_errors": encoding_errors,
    "replacement_characters": sum(i.get("count", 0) for i in unicode_issues),
    "issues": unicode_issues[:20],
    "samples_analyzed": len(sampled_pdfs),
}

with open(FORENSICS_DIR / "unicode_quality.json", "w") as f:
    json.dump(unicode_report, f, indent=2, ensure_ascii=False)
print(f"  Unicode: {total_chars:,} chars, Devanagari: {devanagari_chars:,}, Latin: {latin_chars:,}", flush=True)
print(f"  Encoding errors: {encoding_errors}, Replacement chars: {unicode_report['replacement_characters']}", flush=True)

print("\nDone.", flush=True)
