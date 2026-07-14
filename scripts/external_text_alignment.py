"""
Phase 20 — External Text Alignment & Atomic Knowledge Recovery.

Processes downloaded texts, discovers new public-domain editions,
downloads them, aligns against canonical layer, and recovers missing fragments.
"""
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.unit_evidence.engine import UnitEvidenceEngine
from core.unit_passports.engine import UnitPassportEngine, PassportStatus
from core.unit_variants.engine import UnitVariantEngine
from core.unit_confidence.engine import UnitConfidenceEngine
from core.unit_alignment.engine import UnitAlignmentEngine
from core.unit_statistics.engine import UnitStatisticsEngine
from core.unit_reconstruction.engine import UnitReconstructionEngine, RecoveryStatus

SILVER_DIR = Path("knowledge/silver/structured_documents")
BRONZE_DIR = Path("knowledge/bronze/extracted_text")
DOWNLOADS_DIR = Path("knowledge/downloads")
DISCOVERIES_DIR = Path("knowledge/discovered_editions")
EXTERNAL_BRONZE_DIR = Path("knowledge/external_bronze")
EXTERNAL_BRONZE_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINT_DIR = Path("knowledge/checkpoints/alignment")
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
PROGRESS_FILE = CHECKPOINT_DIR / "progress.json"
RESULTS_FILE = CHECKPOINT_DIR / "results.json"


def http_get(url, timeout=15, retries=2):
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "AstroSage-KnowledgeEngine/1.0",
                "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(5 * (attempt + 1))
            elif e.code in (404, 403):
                return None
            elif attempt < retries:
                time.sleep(2)
            else:
                return None
        except Exception:
            if attempt < retries:
                time.sleep(2)
            else:
                return None
    return None


def http_download(url, dest, timeout=30):
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "AstroSage-KnowledgeEngine/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            dest.write_bytes(data)
            return True
    except Exception:
        return False


def detect_language(text):
    if not text.strip():
        return "unknown"
    deva = sum(1 for c in text if '\u0900' <= c <= '\u097F')
    total = sum(1 for c in text if c.isalpha())
    if total == 0:
        return "unknown"
    pct = deva / total
    if pct > 0.5:
        return "hindi_sanskrit"
    elif pct > 0.1:
        return "mixed"
    return "english"


def extract_paragraphs(text):
    return [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip() and len(p.strip()) > 20]


def normalize_text(text):
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'[^\w\s\u0900-\u097F।॥\.\,\;\:\!\?]', '', text)
    return text


def compute_text_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def load_progress():
    if PROGRESS_FILE.exists():
        try:
            return json.loads(PROGRESS_FILE.read_text())
        except Exception:
            pass
    return {"processed_downloads": [], "processed_discoveries": [],
            "new_downloads": 0, "recovered_fragments": 0,
            "recovered_chars": 0, "recovered_words": 0,
            "recovered_verses": 0, "recovered_commentary": 0,
            "confidence_improvements": 0, "unknown_remaining": 0,
            "http_requests": 0, "alignments_made": 0}


def save_progress(progress):
    PROGRESS_FILE.write_text(json.dumps(progress, indent=2, default=str))


def main():
    progress = load_progress()
    print("Phase 20: External Text Alignment & Atomic Knowledge Recovery")
    print("=" * 60)

    # Step 1: Build canonical index
    print("\nStep 1: Building canonical index...")
    start = time.time()
    canonical = {}
    for silver_file in sorted(SILVER_DIR.glob("*.md")):
        title = silver_file.stem
        book_uuid = f"BK-{hashlib.sha256(title.encode()).hexdigest()[:12]}"
        text = silver_file.read_text(encoding="utf-8", errors="replace")
        paragraphs = extract_paragraphs(text)
        para_hashes = set()
        all_words = set()
        for p in paragraphs:
            h = compute_text_hash(p)
            para_hashes.add(h)
            all_words.update(re.findall(r'\b\w+\b', p.lower()))
        canonical[book_uuid] = {
            "title": title, "paragraphs": paragraphs,
            "para_hashes": para_hashes, "word_set": all_words,
            "language": detect_language(text), "text": text}
    print(f"  {len(canonical)} books indexed in {time.time()-start:.1f}s")

    # Step 2: Process existing downloads
    print("\nStep 2: Processing downloaded texts...")
    evidence = UnitEvidenceEngine()
    passports = UnitPassportEngine()
    variants = UnitVariantEngine()
    confidence = UnitConfidenceEngine()
    alignment = UnitAlignmentEngine()
    statistics = UnitStatisticsEngine()
    reconstruction = UnitReconstructionEngine()

    downloads = list(DOWNLOADS_DIR.glob("*.txt"))
    processed_dl = set(progress.get("processed_downloads", []))
    new_dl = 0
    recovered_frags = 0
    recovered_chars = 0
    recovered_words = 0
    recovered_verses = 0
    recovered_commentary = 0
    conf_improvements = 0
    unknown_remaining = 0
    alignments_made = 0

    for dl_file in downloads:
        dl_name = dl_file.name
        if dl_name in processed_dl:
            continue

        ext_text = dl_file.read_text(encoding="utf-8", errors="replace")
        ext_paragraphs = extract_paragraphs(ext_text)
        ext_hashes = set()
        ext_words = set()
        for p in ext_paragraphs:
            ext_hashes.add(compute_text_hash(p))
            ext_words.update(re.findall(r'\b\w+\b', p.lower()))

        lang = detect_language(ext_text)
        ext_id = f"EXT-{hashlib.sha256(dl_name.encode()).hexdigest()[:12]}"

        # Store as external bronze
        ext_bronze = EXTERNAL_BRONZE_DIR / dl_file.name
        if not ext_bronze.exists():
            ext_bronze.write_text(ext_text, encoding="utf-8")

        best_matches = []
        for book_uuid, cdata in canonical.items():
            common_hashes = ext_hashes & cdata["para_hashes"]
            if common_hashes:
                best_matches.append((book_uuid, cdata["title"], len(common_hashes),
                                    len(common_hashes) / max(len(ext_hashes), 1)))

            common_words = ext_words & cdata["word_set"]
            word_overlap = len(common_words) / max(len(ext_words | cdata["word_set"]), 1)
            if word_overlap > 0.3:
                alignment.align(
                    source_unit_id=f"{ext_id}-text",
                    target_unit_id=f"{book_uuid}-text",
                    alignment_type="external_edition",
                    source_language=lang, target_language=cdata["language"],
                    similarity=word_overlap, confidence=word_overlap * 0.9)
                alignments_made += 1

                evidence.add(unit_id=f"{book_uuid}-external",
                           source_type="external_edition",
                           content=f"Match from {dl_name}: {len(common_words)} common words",
                           confidence=min(word_overlap + 0.2, 1.0), trust=0.8)

        # Recovery: find paragraphs in external text not in canonical
        for ext_p in ext_paragraphs:
            ext_h = compute_text_hash(ext_p)
            found_in_canonical = False
            for book_uuid, cdata in canonical.items():
                if ext_h in cdata["para_hashes"]:
                    found_in_canonical = True
                    break

            if not found_in_canonical and best_matches:
                recovered_frags += 1
                recovered_chars += len(ext_p)
                recovered_words += len(ext_p.split())
                verse_matches = re.findall(r'(?:Verse|Sloka)\s+\d+', ext_p, re.IGNORECASE)
                recovered_verses += len(verse_matches)

                if any(kw in ext_p.lower() for kw in ["commentary", "bhashya", "tika", "gloss", "note"]):
                    recovered_commentary += 1

                for book_uuid, title, _, _ in best_matches[:1]:
                    reconstruction.create_candidate(
                        unit_id=f"{book_uuid}-ext-{hashlib.sha256(ext_p[:50].encode()).hexdigest()[:8]}",
                        original_text="", recovered_text=ext_p[:200],
                        confidence=0.7, sources=[dl_name],
                        reason=f"Found in external edition {dl_name}, not in canonical")

                    evidence.add(unit_id=f"{book_uuid}-recovered",
                               source_type="recovery_from_external",
                               content=ext_p[:200], confidence=0.7, trust=0.75)

        progress["processed_downloads"].append(dl_name)
        processed_dl.add(dl_name)
        new_dl += 1
        print(f"  Processed: {dl_name} ({len(ext_paragraphs)} paragraphs, {len(best_matches)} matches)")

    # Step 3: Discover and download more public-domain editions
    print("\nStep 3: Discovering additional public-domain editions...")
    http_requests = progress.get("http_requests", 0)
    processed_disc = set(progress.get("processed_discoveries", []))

    disc_files = list(DISCOVERIES_DIR.glob("*.json"))
    new_downloads = 0

    for disc_file in disc_files:
        if disc_file.stem in processed_disc:
            continue
        try:
            disc_data = json.loads(disc_file.read_text())
        except Exception:
            continue

        for edition in disc_data.get("editions", []):
            is_pd = edition.get("public_domain", False) or edition.get("is_oa", False)
            if not is_pd:
                continue

            ia_ids = edition.get("ia_identifiers", [])
            if ia_ids:
                for ia_id in ia_ids[:1]:
                    text_url = f"https://archive.org/stream/{ia_id}/{ia_id}_djvu.txt"
                    dest = DOWNLOADS_DIR / f"{ia_id}.txt"
                    if dest.exists():
                        continue
                    time.sleep(1)
                    if http_download(text_url, dest):
                        http_requests += 1
                        new_downloads += 1
                        progress["new_downloads"] = progress.get("new_downloads", 0) + 1
                        print(f"  Downloaded: {ia_id}.txt")
                    http_requests += 1

            oa_url = edition.get("oa_url")
            if oa_url and oa_url.endswith(".pdf"):
                dest = DOWNLOADS_DIR / f"{hashlib.sha256(oa_url.encode()).hexdigest()[:12]}.pdf"
                if not dest.exists():
                    time.sleep(1)
                    http_download(oa_url, dest)
                    http_requests += 1

        processed_disc.add(disc_file.stem)

    progress["processed_discoveries"] = list(processed_disc)
    progress["http_requests"] = http_requests

    # Step 4: Process any new downloads
    new_files = [f for f in DOWNLOADS_DIR.glob("*.txt") if f.name not in processed_dl]
    for dl_file in new_files:
        dl_name = dl_file.name
        ext_text = dl_file.read_text(encoding="utf-8", errors="replace")
        ext_paragraphs = extract_paragraphs(ext_text)
        ext_words = set()
        for p in ext_paragraphs:
            ext_words.update(re.findall(r'\b\w+\b', p.lower()))

        lang = detect_language(ext_text)
        ext_id = f"EXT-{hashlib.sha256(dl_name.encode()).hexdigest()[:12]}"

        ext_bronze = EXTERNAL_BRONZE_DIR / dl_file.name
        if not ext_bronze.exists():
            ext_bronze.write_text(ext_text, encoding="utf-8")

        for book_uuid, cdata in canonical.items():
            common_words = ext_words & cdata["word_set"]
            word_overlap = len(common_words) / max(len(ext_words | cdata["word_set"]), 1)
            if word_overlap > 0.3:
                alignment.align(f"{ext_id}-text", f"{book_uuid}-text",
                               "external_edition", source_language=lang,
                               target_language=cdata["language"],
                               similarity=word_overlap, confidence=word_overlap * 0.9)
                alignments_made += 1
                evidence.add(unit_id=f"{book_uuid}-external",
                           source_type="external_edition",
                           content=f"Match from {dl_name}: {len(common_words)} common words",
                           confidence=min(word_overlap + 0.2, 1.0), trust=0.8)

        for ext_p in ext_paragraphs:
            ext_h = compute_text_hash(ext_p)
            found = any(ext_h in cdata["para_hashes"] for cdata in canonical.values())
            if not found:
                recovered_frags += 1
                recovered_chars += len(ext_p)
                recovered_words += len(ext_p.split())

        progress["processed_downloads"].append(dl_name)
        processed_dl.add(dl_name)
        new_dl += 1
        print(f"  Processed new: {dl_name} ({len(ext_paragraphs)} paragraphs)")

    # Step 5: Compute unknown remaining
    for book_uuid, cdata in canonical.items():
        total_p = len(cdata["paragraphs"])
        matched_p = sum(1 for p in cdata["paragraphs"] if compute_text_hash(p) in cdata["para_hashes"])
        if total_p > matched_p:
            unknown_remaining += total_p - matched_p

    elapsed = time.time() - start

    # Save progress
    progress["processed_downloads"] = list(processed_dl)
    progress["recovered_fragments"] = recovered_frags
    progress["recovered_chars"] = recovered_chars
    progress["recovered_words"] = recovered_words
    progress["recovered_verses"] = recovered_verses
    progress["recovered_commentary"] = recovered_commentary
    progress["confidence_improvements"] = conf_improvements
    progress["unknown_remaining"] = unknown_remaining
    progress["alignments_made"] = alignments_made
    save_progress(progress)

    # Results
    results = {
        "external_editions_processed": new_dl,
        "new_public_domain_downloads": new_downloads,
        "atomic_fragments_recovered": recovered_frags,
        "characters_recovered": recovered_chars,
        "words_recovered": recovered_words,
        "verses_recovered": recovered_verses,
        "commentary_recovered": recovered_commentary,
        "unknown_units_remaining": unknown_remaining,
        "alignments_made": alignments_made,
        "http_requests": http_requests,
        "execution_time": round(elapsed, 1),
        "evidence": evidence.summary(),
        "alignment": alignment.summary(),
        "reconstruction": reconstruction.summary(),
        "statistics": statistics.corpus_summary()}
    RESULTS_FILE.write_text(json.dumps(results, indent=2, default=str))

    print(f"\n{'='*60}")
    print(f"EXTERNAL TEXT ALIGNMENT & RECOVERY COMPLETE")
    print(f"{'='*60}")
    print(f"External editions processed: {new_dl}")
    print(f"New public-domain downloads: {new_downloads}")
    print(f"Atomic fragments recovered: {recovered_frags}")
    print(f"Characters recovered: {recovered_chars}")
    print(f"Words recovered: {recovered_words}")
    print(f"Verses recovered: {recovered_verses}")
    print(f"Commentary fragments: {recovered_commentary}")
    print(f"Alignments made: {alignments_made}")
    print(f"UNKNOWN units remaining: {unknown_remaining}")
    print(f"HTTP requests: {http_requests}")
    print(f"Time: {elapsed:.1f}s")
    print(f"\nAlignment: {json.dumps(alignment.summary(), indent=2)}")
    print(f"Evidence: {json.dumps(evidence.summary(), indent=2)}")
    print(f"Reconstruction: {json.dumps(reconstruction.summary(), indent=2)}")


if __name__ == "__main__":
    main()
