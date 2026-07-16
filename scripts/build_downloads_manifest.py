#!/usr/bin/env python3
"""
Build manifest of all files in downloads/
"""
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime

DOWNLOADS = "/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage/knowledge/downloads"
OUTPUT = "/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage/knowledge/dtc/downloads_manifest.json"

def sha256_file(path):
    h = hashlib.sha256()
    try:
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
        return h.hexdigest()
    except:
        return None

def detect_scripture(name):
    name_lower = name.lower()
    mapping = {
        'rigveda': 'RV', 'rgveda': 'RV',
        'samaveda': 'SV',
        'yajurveda': 'YVK', 'yajur': 'YVK',
        'atharvaveda': 'AV', 'atharva': 'AV',
        'bhagavad': 'BG', 'gita': 'BG', 'geeta': 'BG',
        'mahabharat': 'MBH', 'mahabharata': 'MBH',
        'ramayan': 'RM', 'ramayana': 'RM',
        'harivamsh': 'HV', 'harivamsa': 'HV',
        'bhagavat': 'BHAG', 'bhagavata': 'BHAG',
        'vishnu': 'VISH', 'shiv': 'SHIV', 'shiva': 'SHIV',
        'devi': 'DEVI', 'agni': 'AGNI', 'brahma': 'BRAH',
        'matsya': 'MATS', 'kurma': 'KURM', 'linga': 'LING',
        'markandeya': 'MARK', 'narada': 'NARADA', 'vamana': 'VAMAN',
        'varaha': 'VARAH', 'vayu': 'VYU', 'skanda': 'SKAND',
        'brahmanda': 'BRAHMD', 'kalika': 'KALI', 'garuda': 'GARUDA',
        'isha': 'ISHA', 'kena': 'KEN', 'katha': 'KATH',
        'prashna': 'PRASHNA', 'mundaka': 'MUND', 'mandukya': 'MAND',
        'taittiriya': 'TAITT', 'aitareya': 'AITAREYA',
        'chandogya': 'CHAND', 'brihadaranyaka': 'BRIHAD',
        'shvetashvatara': 'SHVET', 'kaushitaki': 'KAUS',
        'maitri': 'MAITR', 'mahanarayana': 'MAHAN',
        'manusmriti': 'MANU', 'manu': 'MANU',
        'yajnavalkya': 'YAJNAV', 'parashara': 'PARASHARA',
        'vyasa': 'VYASA_SM', 'apastamba': 'APASTAMBA_DS',
        'baudhayana': 'BAUDHAYANA_DS', 'gautama': 'GAUTAMA_DS',
        'vedanta': 'VEDANTA_SUTRA', 'yoga_sutra': 'YOGA_SUTRA',
        'nyaya': 'NYAYA_SUTRA', 'vaisheshika': 'VAISHESHIKA_SUTRA',
        'padapatha': 'RV', 'khila': 'RV', 'sayana': 'RV',
        'sontakke': 'RV', 'maxmuller': 'RV', 'max_muller': 'RV',
        'chowkhamba': 'RV', 'ramtek': 'RV',
        'vedaweb': 'RV', 'vnh': 'RV', 'lubotsky': 'RV',
    }
    for key, sid in mapping.items():
        if key in name_lower:
            return sid
    return 'UNKNOWN'

def classify_file(fname):
    fname_lower = fname.lower()
    if fname_lower.endswith('.xml') or fname_lower.endswith('.tei'):
        return 'tei_xml'
    elif fname_lower.endswith('.pdf'):
        return 'pdf'
    elif fname_lower.endswith('.djvu') or fname_lower.endswith('.djv'):
        return 'djvu'
    elif fname_lower.endswith('.txt'):
        return 'text'
    elif fname_lower.endswith('.zip'):
        return 'archive'
    return 'unknown'

def main():
    files = []
    for dirpath, dirnames, filenames in os.walk(DOWNLOADS):
        dirnames[:] = [d for d in dirnames if not d.startswith('.')]
        for fname in filenames:
            if fname.startswith('.'):
                continue
            fpath = os.path.join(dirpath, fname)
            try:
                stat = os.stat(fpath)
                size = stat.st_size
                if size == 0:
                    continue
                rel = os.path.relpath(fpath, DOWNLOADS)
                scripture = detect_scripture(fname)
                ftype = classify_file(fname)
                
                files.append({
                    "relative_path": rel,
                    "absolute_path": fpath,
                    "filename": fname,
                    "size_bytes": size,
                    "checksum_sha256": sha256_file(fpath),
                    "scripture_id": scripture,
                    "file_type": ftype,
                    "extension": Path(fname).suffix.lower(),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            except Exception as e:
                print(f"Error: {fpath}: {e}")
    
    total_bytes = sum(f["size_bytes"] for f in files)
    by_type = {}
    by_scripture = {}
    for f in files:
        t = f["file_type"]
        s = f["scripture_id"]
        by_type[t] = by_type.get(t, 0) + 1
        by_scripture[s] = by_scripture.get(s, {"count": 0, "bytes": 0})
        by_scripture[s]["count"] += 1
        by_scripture[s]["bytes"] += f["size_bytes"]
    
    manifest = {
        "generated": datetime.utcnow().isoformat() + 'Z',
        "downloads_root": DOWNLOADS,
        "total_files": len(files),
        "total_bytes": total_bytes,
        "by_file_type": by_type,
        "by_scripture": by_scripture,
        "files": files
    }
    
    with open(OUTPUT, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"Manifest written to {OUTPUT}")
    print(f"Total files: {len(files)}")
    print(f"Total bytes: {total_bytes:,}")
    print(f"By type: {by_type}")
    print(f"By scripture: {json.dumps(by_scripture, indent=2)}")

if __name__ == '__main__':
    main()
