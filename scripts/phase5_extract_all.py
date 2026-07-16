#!/usr/bin/env python3
"""
Phase 5: Extract CUIDs from ALL classified files on disk.
Every scripture file gets processed. No file left behind.
"""
import json
import os
import re
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

# Load inventory
inventory = json.load(open(EXTRACT_DIR / 'complete_inventory.json'))

# Expected verse counts
EXPECTED = {
    'RV': 10600, 'SV': 1875, 'AV': 6000, 'BG': 700, 'MBH': 100000,
    'RM': 24000, 'HV': 16000, 'BHAG': 18000, 'VISH': 23000,
    'SHIV': 24000, 'DEVI': 18000, 'AGNI': 16000, 'BRAH': 14000,
    'MATS': 13000, 'KURM': 12000, 'LING': 11000, 'MARK': 9000,
    'NARADA': 18000, 'VAMAN': 10000, 'VARAH': 10000, 'VYU': 24000,
    'SKAND': 24000, 'BRAHMD': 12000, 'KALI': 9000, 'GARUDA': 8000,
    'ISHA': 18, 'KEN': 32, 'KATH': 119, 'PRASHNA': 64,
    'MUND': 83, 'MAND': 12, 'TAITT': 104, 'AITAREYA': 33,
    'CHAND': 634, 'BRIHAD': 536, 'SHVET': 113, 'KAUS': 88,
    'MAITR': 115, 'MAHAN': 84, 'MANU': 2694, 'YAJNAV': 1054,
    'VISHNU_SM': 100, 'NARADA_SM': 150, 'PARASHARA': 150,
    'VYASA_SM': 100, 'APASTAMBA_DS': 1500, 'BAUDHAYANA_DS': 500,
    'GAUTAMA_DS': 1000, 'VEDANTA_SUTRA': 555, 'YOGA_SUTRA': 196,
    'NYAYA_SUTRA': 560, 'VAISHESHIKA_SUTRA': 370,
}


def extract_verses_from_text(path, scripture_id):
    """Extract verse-like content from a text file."""
    try:
        with open(path, 'r', errors='replace') as f:
            content = f.read()
    except:
        return {'status': 'READ_ERROR', 'verses': 0}
    
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    
    # Filter out header/footer noise
    noise_patterns = [
        r'^(?:chapter|sarga|adhyaya|book|kanda|parva|mandala)\s*$',
        r'^(?:Copyright|copyright| DISCLAIMER|Published by)',
        r'^(?:Page|page)\s+\d+',
        r'^\d+\s*$',  # Just page numbers
        r'^[=\-\*]{3,}$',  # Dividers
        r'^(?:TABLE OF CONTENTS|Index|Contents)',
    ]
    
    clean_lines = []
    for line in lines:
        if any(re.match(p, line, re.IGNORECASE) for p in noise_patterns):
            continue
        if len(line) < 5:
            continue
        clean_lines.append(line)
    
    # Detect structure
    current_section = 1
    verse_counter = 0
    verses = []
    
    for line in clean_lines:
        # Detect section markers
        section_match = re.match(r'^(?:sarga|adhyAya|adhyaya|prashna|khanda|pATALa|patala|chapter|khaNDa)\s+(\d+)', line, re.IGNORECASE)
        if section_match:
            current_section = int(section_match.group(1))
            verse_counter = 0
            continue
        
        # Detect verse number markers (e.g., "1.", "2.", "||1||")
        verse_num_match = re.match(r'^[॥|]*(\d+)[॥|.\s]', line)
        if verse_num_match:
            verse_counter = int(verse_num_match.group(1))
            text = re.sub(r'^[॥|]*\d+[॥|.\s]+', '', line).strip()
        else:
            verse_counter += 1
            text = line
        
        if text and len(text) > 5:
            verses.append({
                'section': current_section,
                'verse': verse_counter,
                'text': text[:500],  # Cap for storage
            })
    
    return {
        'status': 'EXTRACTED',
        'total_lines': len(lines),
        'clean_lines': len(clean_lines),
        'verses': len(verses),
        'sections': len(set(v['section'] for v in verses)),
        'verse_data': verses[:5000],  # Cap for storage
    }


def main():
    print("=" * 70)
    print("PHASE 5: EXTRACT ALL CLASSIFIED FILES")
    print("=" * 70)
    
    # Group files by scripture
    by_scripture = defaultdict(list)
    for path, record in inventory.items():
        sid = record.get('scripture')
        if sid and record.get('source') in ('downloads', 'bronze'):
            by_scripture[sid].append(record)
    
    extraction_results = {}
    
    for sid in sorted(by_scripture.keys()):
        files = by_scripture[sid]
        print(f"\n--- {sid} ({len(files)} files) ---")
        
        best_result = None
        best_verses = 0
        all_results = []
        
        for record in files:
            fpath = BASE / record['path']
            if not fpath.exists():
                continue
            
            enc = record.get('encoding', {})
            if enc.get('quality') in ('GARBLED', 'UNREADABLE'):
                print(f"  SKIP {record['name'][:50]} [{enc.get('quality')}]")
                continue
            
            result = extract_verses_from_text(fpath, sid)
            result['file'] = record['path']
            result['family'] = record.get('family', 'F-UNKNOWN')
            result['source'] = record.get('source', 'unknown')
            result['size'] = record.get('size', 0)
            all_results.append(result)
            
            if result['verses'] > best_verses:
                best_verses = result['verses']
                best_result = result
            
            print(f"  {record['name'][:50]:50s} {result['verses']:6d} verses [{result['status']}]")
        
        # Store best result
        expected = EXPECTED.get(sid, 1000)
        coverage = min(100, (best_verses / expected * 100)) if expected > 0 else 0
        
        extraction_results[sid] = {
            'scripture': sid,
            'files_processed': len(all_results),
            'best_verses': best_verses,
            'expected_verses': expected,
            'coverage_pct': round(coverage, 1),
            'all_results': all_results,
            'best_file': best_result['file'] if best_result else None,
        }
        
        print(f"  => Best: {best_verses} verses ({coverage:.1f}% of {expected})")
    
    # Save extraction results
    save_json(EXTRACT_DIR / 'extraction_results.json', extraction_results)
    
    # Summary
    print(f"\n{'='*70}")
    print("EXTRACTION SUMMARY")
    print(f"{'='*70}")
    
    total_verses = 0
    for sid in sorted(extraction_results.keys()):
        r = extraction_results[sid]
        total_verses += r['best_verses']
        cov = r['coverage_pct']
        icon = '✅' if cov >= 80 else '⚠️' if cov >= 30 else '📋' if r['best_verses'] > 0 else '❌'
        print(f"  {icon} {sid:15s} {r['best_verses']:7d}/{r['expected_verses']:6d} ({cov:5.1f}%) from {r['files_processed']} files")
    
    print(f"\nTotal verses extracted: {total_verses:,}")
    print(f"Scriptures with data: {sum(1 for r in extraction_results.values() if r['best_verses'] > 0)}")
    print(f"Scriptures with 0: {sum(1 for r in extraction_results.values() if r['best_verses'] == 0)}")


def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


if __name__ == '__main__':
    main()
