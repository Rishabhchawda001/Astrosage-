#!/usr/bin/env python3
"""
Index all files in source_library/ and bronze/extracted_text/
"""
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime

SOURCE_LIB = "/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage/knowledge/source_library"
BRONZE = "/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage/knowledge/bronze/extracted_text"
OUTPUT = "/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage/knowledge/dtc/source_library_index.json"

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
        'samaveda': 'SV', 'yajurveda': 'YVK', 'yajur': 'YVK',
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
    }
    for key, sid in mapping.items():
        if key in name_lower:
            return sid
    return 'UNKNOWN'

def index_directory(root, name):
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip hidden
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
                rel = os.path.relpath(fpath, root)
                scripture = detect_scripture(fname)
                ext = Path(fname).suffix.lower()
                
                files.append({
                    "source": name,
                    "relative_path": rel,
                    "absolute_path": fpath,
                    "filename": fname,
                    "size_bytes": size,
                    "checksum_sha256": sha256_file(fpath),
                    "scripture_id": scripture,
                    "extension": ext,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            except Exception as e:
                print(f"Error: {fpath}: {e}")
    return files

def main():
    index = {
        "generated": datetime.utcnow().isoformat() + 'Z',
        "source_library": index_directory(SOURCE_LIB, "source_library"),
        "bronze_extracted": index_directory(BRONZE, "bronze_extracted_text"),
        "summary": {}
    }
    
    total_files = len(index["source_library"]) + len(index["bronze_extracted"])
    total_bytes = sum(f["size_bytes"] for f in index["source_library"]) + sum(f["size_bytes"] for f in index["bronze_extracted"])
    
    by_scripture = {}
    for f in index["source_library"] + index["bronze_extracted"]:
        sid = f["scripture_id"]
        if sid not in by_scripture:
            by_scripture[sid] = {"count": 0, "bytes": 0}
        by_scripture[sid]["count"] += 1
        by_scripture[sid]["bytes"] += f["size_bytes"]
    
    index["summary"] = {
        "total_files": total_files,
        "total_bytes": total_bytes,
        "source_library_files": len(index["source_library"]),
        "bronze_extracted_files": len(index["bronze_extracted"]),
        "by_scripture": by_scripture
    }
    
    with open(OUTPUT, 'w') as f:
        json.dump(index, f, indent=2)
    
    print(f"Index written to {OUTPUT}")
    print(f"Total files: {total_files}")
    print(f"Total bytes: {total_bytes:,}")
    print(f"By scripture: {json.dumps(by_scripture, indent=2)}")

if __name__ == '__main__':
    main()
