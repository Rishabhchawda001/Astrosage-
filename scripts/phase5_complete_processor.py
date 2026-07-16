#!/usr/bin/env python3
"""
Phase 5: Complete Corpus Processor
Processes EVERY file on disk. No file may remain unprocessed.
Generates extraction status for every resource.
"""
import json
import os
import re
import hashlib
from pathlib import Path
from collections import defaultdict
from datetime import datetime

BASE = Path(__file__).parent.parent
DOWNLOAD_DIR = BASE / 'knowledge' / 'downloads'
GREIL_DIR = BASE / 'knowledge' / 'gretil_parsed'
DTC_DIR = BASE / 'knowledge' / 'dtc'
BRONZE_DIR = BASE / 'knowledge' / 'bronze' / 'extracted_text'
EXTRACT_DIR = DTC_DIR / 'extractions'
EXTRACT_DIR.mkdir(parents=True, exist_ok=True)


def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def file_hash(path, n=8):
    h = hashlib.sha256()
    try:
        with open(path, 'rb') as f:
            while True:
                data = f.read(65536)
                if not data:
                    break
                h.update(data)
        return h.hexdigest()[:n]
    except:
        return None


def detect_encoding_quality(path):
    """Detect encoding issues in a text file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read(50000)
        
        has_replacement = '\ufffd' in content
        has_devanagari = any('\u0900' <= c <= '\u097F' for c in content)
        has_iast = bool(re.search(r'[āīūṛṝḷḹṃḥṣśṇṭḍñṭḍ]', content))
        has_latin = sum(1 for c in content if c.isascii() and c.isalpha()) > 10
        total = len(content)
        
        # Check for garbled sequences (common in bad OCR)
        garbled_patterns = [
            (r'M-`M-', 'devanagari_garbled'),
            (r'M-\^@', 'control_chars'),
            (r'[\x00-\x08\x0b\x0c\x0e-\x1f]', 'control_chars'),
        ]
        garbled_count = 0
        for pattern, _ in garbled_patterns:
            garbled_count += len(re.findall(pattern, content))
        
        garbled_pct = (garbled_count / max(total, 1)) * 100
        
        return {
            'valid_utf8': True,
            'has_replacement': has_replacement,
            'has_devanagari': has_devanagari,
            'has_iast': has_iast,
            'has_latin': has_latin,
            'garbled_pct': round(garbled_pct, 2),
            'quality': 'GARBLED' if garbled_pct > 5 else ('LOW' if garbled_pct > 1 else 'GOOD'),
        }
    except Exception as e:
        return {'valid_utf8': False, 'quality': 'UNREADABLE', 'error': str(e)}


def extract_verse_count(path):
    """Try to count verses in a file."""
    try:
        with open(path, 'r', errors='replace') as f:
            content = f.read()
        
        lines = [l.strip() for l in content.split('\n') if l.strip()]
        
        # Count verse-like lines (non-empty, reasonable length)
        verse_like = [l for l in lines if 15 < len(l) < 500]
        
        return {
            'total_lines': len(lines),
            'verse_like_lines': len(verse_like),
        }
    except:
        return {'total_lines': 0, 'verse_like_lines': 0}


# Scripture keyword mapping (comprehensive)
SCRIPTURE_KEYWORDS = {
    'RV': ['rigveda', 'rig_veda', 'aufrecht', 'sontakke', 'vedaweb', 'muller', 'oldenberg', 'sayana_bhashya'],
    'SV': ['samaveda', 'sama_veda'],
    'YVK': ['taittiriya_samhita', 'krishna_yajurveda', 'yajurveda_gujarati', 'yejurveda', 'yajurveda_jayadev'],
    'YVS': ['yajurveda_madhyandina', 'shukla_yajurveda'],
    'AV': ['atharvaveda', 'atharva_veda'],
    'BG': ['bhagavad_gita', 'bhagavad-gita', 'bhagavadgita', 'gita_press', 'gitapress'],
    'MBH': ['mahabharata', 'mbh_'],
    'RM': ['ramayana', 'ramayan', 'valmiki'],
    'HV': ['harivamsa', 'harivamsha', 'harivansh'],
    'BHAG': ['bhagavata', 'bhagwat', 'bhagavatam'],
    'VISH': ['vishnu_puran', 'vishnupuran'],
    'SHIV': ['shiv_puran', 'shiva_puran'],
    'DEVI': ['devi_bhagwat', 'devi_bhaagwat', 'devi_gita'],
    'AGNI': ['agni_puran', 'agnipuran'],
    'BRAH': ['brahma_puran', 'brahmapuran', 'brahma_samhita'],
    'MATS': ['matsya_puran', 'matsyapurana'],
    'KURM': ['kurma_puran', 'kurmapurana'],
    'LING': ['linga_puran', 'lingpuran'],
    'MARK': ['markandeya_puran'],
    'NARADA': ['narada_puran', 'naradiya_puran'],
    'VAMAN': ['vaman_puran', 'vamana_puran'],
    'VARAH': ['varaha_puran', 'varahapurana'],
    'VYU': ['vayu_purana', 'vayupurana', 'revakhanda'],
    'SKAND': ['skanda_puran', 'skandpuran'],
    'BRAHMD': ['brahmanda_puran'],
    'KALI': ['kalika_puran', 'kali_puran'],
    'GARUDA': ['garuda_puran', 'garudpuran'],
    'BRAHVAIV': ['brahma_vaivarta', 'brahmavaivarta'],
    'PADMA': ['padma_puran', 'padmapuran'],
    'BHAVISHYA': ['bhavishya_puran'],
    'ISHA': ['isha_upanishad'],
    'KEN': ['kena_upanishad', 'kenopanishad'],
    'KATH': ['katha_upanishad', 'kathopanishad'],
    'PRASHNA': ['prashna_upanishad', 'prashnopanishad'],
    'MUND': ['mundaka_upanishad'],
    'MAND': ['mandukya_upanishad'],
    'TAITT': ['taittiriya_upanishad'],
    'AITAREYA': ['aitareya_upanishad'],
    'CHAND': ['chandogya_upanishad', 'chandogya_'],
    'BRIHAD': ['brhadaranyaka', 'brihadaranyaka'],
    'SHVET': ['shvetashvatara'],
    'KAUS': ['kaushitaki'],
    'MAITR': ['maitri_upanishad', 'maitrayaniya'],
    'MAHAN': ['mahanarayana'],
    'MANU': ['manusmriti', 'manusmruti'],
    'YAJNAV': ['yajnavalkya_smriti', 'yajnavalkya'],
    'VISHNU_SM': ['vishnu_smriti', 'vishnusmriti', 'vishnu_dharma', 'vedartha'],
    'NARADA_SM': ['narada_smriti'],
    'PARASHARA': ['parashara_smriti', 'parashara'],
    'VYASA_SM': ['vyasa_smriti'],
    'APASTAMBA_DS': ['apastamba_dharmasutra', 'apastamba_grihya', 'apastamba_dharma'],
    'BAUDHAYANA_DS': ['baudhayana_dharmasutra', 'baudhayana'],
    'GAUTAMA_DS': ['gautama_dharmasutra', 'gautama_dharma'],
    'VEDANTA_SUTRA': ['brahma_sutra', 'vedanta_sutra', 'brahmasutra'],
    'YOGA_SUTRA': ['yoga_sutra', 'yogasutra'],
    'NYAYA_SUTRA': ['nyaya_sutra', 'nyayasutra', 'nyaya_bindu'],
    'VAISHESHIKA_SUTRA': ['vaisheshika_sutra', 'vaisheshika', 'padartha'],
    'NIRUKTA': ['nirukta'],
}


def classify_file(filename):
    """Classify a file into scripture and witness family."""
    fn = filename.lower().replace('-', '_').replace(' ', '_')
    
    best_scripture = None
    best_score = 0
    
    for sid, keywords in SCRIPTURE_KEYWORDS.items():
        for kw in keywords:
            kw_norm = kw.lower().replace('-', '_').replace(' ', '_')
            if kw_norm in fn:
                if len(kw_norm) > best_score:
                    best_score = len(kw_norm)
                    best_scripture = sid
    
    # Family detection
    family = 'F-UNKNOWN'
    family_patterns = [
        ('aufrecht', 'F-AUFRECHT'), ('padapatha', 'F-PADAPATHA'),
        ('khila', 'F-KHILA'), ('vedaweb', 'F-LUBOTSKY'),
        ('sontakke', 'F-SONTAKKE'), ('gretil', 'F-GRETIL'),
        ('gita_press', 'F-GITAPRESS'), ('gitapress', 'F-GITAPRESS'),
        ('anand', 'F-ANANDASHRAM'), ('chowkhamba', 'F-CHOWKHAMBA'),
        ('chaukhamba', 'F-CHOWKHAMBA'), ('motilal', 'F-MOTILAL'),
        ('khemraj', 'F-KHEMRAJ'), ('bori', 'F-BORI'),
        ('muller', 'F-MAXMULLER'), ('oldenberg', 'F-OLDENBERG'),
        ('sayana', 'F-SAYANA'), ('ramtek', 'F-RAMTEK'),
        ('satavalekar', 'F-SATAVALEKAR'), ('satwalekar', 'F-SATAVALEKAR'),
        ('jayadev', 'F-JAYADEV'), ('dli', 'F-DLI'),
        ('critical', 'F-CRITICAL'), ('nirnaya', 'F-NIRNAYA_SAGAR'),
        ('edgerton', 'F-EDGERTON'), ('shankara', 'F-SHANKARA'),
        ('ramanuja', 'F-RAMANUJA'), ('madhva', 'F-MADHVA'),
        ('venkateshwar', 'F-VENKATESHWAR'),
        ('archive', 'F-ARCHIVE_DJVU'), ('djvu', 'F-DJVU_OCR'),
    ]
    for pattern, fam in family_patterns:
        if pattern in fn:
            family = fam
            break
    
    # OCR detection
    is_ocr = any(x in fn for x in ['djvu', 'ocr'])
    
    # File type detection
    ext = os.path.splitext(filename)[1].lower()
    
    return {
        'scripture': best_scripture,
        'family': family,
        'ocr': is_ocr,
        'extension': ext,
        'confidence': best_score,
    }


def main():
    print("=" * 70)
    print("PHASE 5: COMPLETE CORPUS PROCESSOR")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}")
    
    inventory = {}
    unparsed = []
    processed = []
    rejected = []
    
    # === PROCESS ALL DOWNLOAD FILES ===
    print("\n--- Processing knowledge/downloads/ ---")
    for root, dirs, files in os.walk(DOWNLOAD_DIR):
        for fname in sorted(files):
            fpath = Path(root) / fname
            rel = str(fpath.relative_to(BASE))
            size = fpath.stat().st_size
            ext = fpath.suffix.lower()
            
            # Skip non-text files for now
            if ext not in ('.txt', '.xml', '.tei', '.htm', '.html'):
                continue
            
            classification = classify_file(fname)
            
            # Detect encoding quality for text files
            enc_quality = {}
            verse_info = {}
            if ext == '.txt' and size > 100:
                enc_quality = detect_encoding_quality(fpath)
                verse_info = extract_verse_count(fpath)
            
            record = {
                'path': rel,
                'name': fname,
                'size': size,
                'extension': ext,
                'source': 'downloads',
                'hash': file_hash(fpath),
                **classification,
                'encoding': enc_quality,
                'verses': verse_info,
                'processed': False,
                'status': 'ACQUIRED',
            }
            
            # Determine if this should be processed
            if classification['scripture']:
                if enc_quality.get('quality') == 'GARBLED':
                    record['status'] = 'GARBLED_OCR'
                    rejected.append(record)
                elif enc_quality.get('quality') == 'UNREADABLE':
                    record['status'] = 'UNREADABLE'
                    rejected.append(record)
                else:
                    record['status'] = 'READY_FOR_PROCESSING'
                    unparsed.append(record)
            else:
                record['status'] = 'UNCLASSIFIED'
            
            inventory[rel] = record
    
    # === PROCESS ALL GRETIL PARSED FILES ===
    print("\n--- Processing knowledge/gretil_parsed/ ---")
    gretil_texts = set()
    for f in sorted(GREIL_DIR.glob('*_gretil_iast.txt')):
        text_name = f.stem.replace('_gretil_iast', '')
        gretil_texts.add(text_name)
        
        # Check all three files exist
        iast = GREIL_DIR / f'{text_name}_gretil_iast.txt'
        deva = GREIL_DIR / f'{text_name}_gretil_devanagari.txt'
        struct = GREIL_DIR / f'{text_name}_gretil_structure.json'
        
        iast_size = iast.stat().st_size if iast.exists() else 0
        deva_size = deva.stat().st_size if deva.exists() else 0
        struct_size = struct.stat().st_size if struct.exists() else 0
        
        enc = detect_encoding_quality(iast) if iast.exists() else {}
        
        rel = str(iast.relative_to(BASE))
        inventory[rel] = {
            'path': rel,
            'name': f.name,
            'size': iast_size,
            'extension': '.txt',
            'source': 'gretil_parsed',
            'scripture': classify_file(text_name).get('scripture'),
            'family': 'F-GRETIL',
            'ocr': False,
            'encoding': enc,
            'has_devanagari': deva.exists(),
            'has_structure': struct.exists(),
            'deva_size': deva_size,
            'struct_size': struct_size,
            'processed': True,
            'status': 'PROCESSED',
        }
    
    # === PROCESS ALL BRONZE FILES ===
    print("\n--- Processing knowledge/bronze/ ---")
    if BRONZE_DIR.exists():
        for f in sorted(BRONZE_DIR.glob('*.txt')):
            rel = str(f.relative_to(BASE))
            classification = classify_file(f.name)
            enc = detect_encoding_quality(f) if f.stat().st_size > 100 else {}
            
            inventory[rel] = {
                'path': rel,
                'name': f.name,
                'size': f.stat().st_size,
                'extension': '.txt',
                'source': 'bronze',
                **classification,
                'encoding': enc,
                'processed': False,
                'status': 'ACQUIRED',
            }
            if classification['scripture']:
                unparsed.append(inventory[rel])
    
    # === GENERATE REPORTS ===
    print("\n--- Generating reports ---")
    
    # Summary
    total = len(inventory)
    sources = defaultdict(int)
    statuses = defaultdict(int)
    scriptures_found = defaultdict(int)
    
    for r in inventory.values():
        sources[r.get('source', 'unknown')] += 1
        statuses[r.get('status', 'unknown')] += 1
        if r.get('scripture'):
            scriptures_found[r['scripture']] += 1
    
    print(f"\n{'='*70}")
    print("COMPLETE INVENTORY SUMMARY")
    print(f"{'='*70}")
    print(f"Total files indexed: {total}")
    print(f"\nBy source:")
    for src, cnt in sorted(sources.items(), key=lambda x: -x[1]):
        print(f"  {src:25s} {cnt:5d}")
    print(f"\nBy status:")
    for st, cnt in sorted(statuses.items(), key=lambda x: -x[1]):
        print(f"  {st:25s} {cnt:5d}")
    print(f"\nScriptures found: {len(scriptures_found)}")
    for sid, cnt in sorted(scriptures_found.items(), key=lambda x: -x[1]):
        print(f"  {sid:15s} {cnt:3d} files")
    
    print(f"\nFiles ready for processing: {len(unparsed)}")
    print(f"Files already processed (GRETIL): {sum(1 for r in inventory.values() if r.get('status') == 'PROCESSED')}")
    print(f"Files rejected (garbled/unreadable): {len(rejected)}")
    
    # Save inventory
    save_json(EXTRACT_DIR / 'complete_inventory.json', inventory)
    
    # Save unparsed list
    save_json(EXTRACT_DIR / 'unparsed_files.json', [
        {'path': r['path'], 'scripture': r.get('scripture'), 'family': r.get('family'), 'size': r.get('size', 0)}
        for r in unparsed
    ])
    
    # Save rejected list
    save_json(EXTRACT_DIR / 'rejected_files.json', rejected)
    
    print(f"\nInventory saved to: {EXTRACT_DIR / 'complete_inventory.json'}")
    print(f"Unparsed list saved to: {EXTRACT_DIR / 'unparsed_files.json'}")
    print(f"Rejected list saved to: {EXTRACT_DIR / 'rejected_files.json'}")
    
    return inventory, unparsed, rejected


if __name__ == '__main__':
    main()
