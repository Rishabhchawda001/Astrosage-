#!/usr/bin/env python3
"""
Classify witness files into families based on family_collapse_rules.json
"""
import json
import re
from pathlib import Path
from datetime import datetime, timezone

RULES_FILE = "/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage/knowledge/dtc/config/family_collapse_rules.json"
MANIFEST_FILE = "/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage/knowledge/dtc/downloads_manifest.json"
OUTPUT_FILE = "/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage/knowledge/dtc/witness_classification.json"

def load_rules():
    with open(RULES_FILE) as f:
        return json.load(f)

def load_manifest():
    with open(MANIFEST_FILE) as f:
        return json.load(f)

def classify_file(file_info, rules):
    """Classify a file into a witness family"""
    filename = file_info.get('filename', '')
    rel_path = file_info.get('relative_path', '')
    scripture = file_info.get('scripture_id', 'UNKNOWN')
    text = f"{filename} {rel_path}".lower()
    
    # Special case: VedaWeb TEI files (rv_book_XX.tei)
    if scripture == 'RV' and 'vedaweb' in text and filename.startswith('rv_book_') and filename.endswith('.tei'):
        return {
            "family_id": "F-LUBOTSKY",
            "base_edition": "Lubotsky independent transcription (VedaWeb/Zenodo 4601264)",
            "relationship": "original",
            "notes": "VedaWeb TEI book file, contains Lubotsky layer",
            "matched_pattern": "vedaweb_rv_book_tei"
        }
    
    # Special case: VedaWeb corpus file
    if scripture == 'RV' and 'vedaweb' in text and 'vedaweb_corpus' in text:
        return {
            "family_id": "F-LUBOTSKY",
            "base_edition": "VedaWeb corpus TEI",
            "relationship": "original",
            "notes": "VedaWeb corpus TEI file",
            "matched_pattern": "vedaweb_corpus"
        }
    
    # Regular pattern matching
    for rule in rules.get('rules', []):
        pattern = rule.get('pattern', '')
        if not pattern:
            continue
        
        alternatives = pattern.split('|')
        for alt in alternatives:
            alt = alt.strip().lower()
            if re.search(alt, text):
                return {
                    "family_id": rule['family_id'],
                    "base_edition": rule.get('base_edition', ''),
                    "relationship": rule.get('relationship', 'unknown'),
                    "notes": rule.get('notes', ''),
                    "matched_pattern": alt
                }
    
    return {
        "family_id": "F-UNCLASSIFIED",
        "base_edition": "Unknown",
        "relationship": "unknown",
        "notes": "No family collapse rule matched",
        "matched_pattern": "none"
    }

def main():
    rules = load_rules()
    manifest = load_manifest()
    
    results = {
        "generated": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "total_files": 0,
        "by_family": {},
        "by_scripture": {},
        "unclassified": []
    }
    
    for file_info in manifest.get('files', []):
        scripture = file_info.get('scripture_id', 'UNKNOWN')
        if scripture == 'UNKNOWN':
            continue
            
        classification = classify_file(file_info, rules)
        family_id = classification['family_id']
        
        file_entry = {
            "relative_path": file_info['relative_path'],
            "filename": file_info['filename'],
            "scripture": scripture,
            "format": file_info['file_type'],
            "size_bytes": file_info['size_bytes'],
            "checksum": file_info['checksum_sha256'][:16],
            "classification": classification
        }
        
        if family_id not in results['by_family']:
            results['by_family'][family_id] = {
                "files": [],
                "scriptures": set(),
                "count": 0,
                "total_bytes": 0
            }
        
        results['by_family'][family_id]['files'].append(file_entry)
        results['by_family'][family_id]['scriptures'].add(scripture)
        results['by_family'][family_id]['count'] += 1
        results['by_family'][family_id]['total_bytes'] += file_info['size_bytes']
        
        if scripture not in results['by_scripture']:
            results['by_scripture'][scripture] = {}
        if family_id not in results['by_scripture'][scripture]:
            results['by_scripture'][scripture][family_id] = 0
        results['by_scripture'][scripture][family_id] += 1
        
        if family_id == 'F-UNCLASSIFIED':
            results['unclassified'].append(file_entry)
        
        results['total_files'] += 1
    
    # Convert sets to lists for JSON
    for fam in results['by_family'].values():
        fam['scriptures'] = list(fam['scriptures'])
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Classification complete. Total files: {results['total_files']}")
    print(f"Families: {len(results['by_family'])}")
    print(f"Unclassified: {len(results['unclassified'])}")
    
    for fam_id, fam in results['by_family'].items():
        if fam_id != 'F-UNCLASSIFIED':
            print(f"  {fam_id}: {fam['count']} files, scriptures: {fam['scriptures']}")

if __name__ == '__main__':
    main()
