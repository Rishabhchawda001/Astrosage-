#!/usr/bin/env python3
"""
Phase 4: Update census with newly acquired files.
"""
import json
import os
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent
DTC_DIR = BASE / 'knowledge' / 'dtc'
DOWNLOAD_DIR = BASE / 'knowledge' / 'downloads'

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    print("Updating census with newly acquired files...")
    
    # Load existing census
    census_path = DTC_DIR / 'phase4_universal_census.json'
    if census_path.exists():
        with open(census_path) as f:
            census = json.load(f)
    else:
        census = {}
    
    # Map new acquisitions to scriptures
    NEW_ACQUISITIONS = {
        'MAHAN': [
            {'file': 'mahan_archive_Mahanarayanopanishad_djvu.txt', 'source': 'Archive.org', 'family': 'F-ARCHIVE_DJVU', 'type': 'Sanskrit OCR'},
            {'file': 'mahan_archive_themahanarayana00jacouoft_djvu.txt', 'source': 'Archive.org', 'family': 'F-ARCHIVE_DJVU', 'type': 'English+Sanskrit'},
        ],
        'MAITR': [
            {'file': 'maitr_archive_maitriormaitrya00cowegoog_djvu.txt', 'source': 'Archive.org (Google scan)', 'family': 'F-ARCHIVE_DJVU', 'type': 'English translation'},
        ],
        'PARASHARA': [
            {'file': 'parashara_archive_SriParasharaSmrithiPdf_djvu.txt', 'source': 'Archive.org', 'family': 'F-ARCHIVE_DJVU', 'type': 'English+Sanskrit'},
            {'file': 'parashara_archive_Parashara Smriti + Madhaviya Vritti+++ _djvu.txt', 'source': 'Archive.org', 'family': 'F-ARCHIVE_DJVU', 'type': 'Sanskrit+Hindi'},
        ],
        'PRASHNA': [
            {'file': 'prashna_archive_108 Upanishad Part-1_djvu.txt', 'source': 'Archive.org', 'family': 'F-ARCHIVE_DJVU', 'type': 'Hindi Bhashya'},
        ],
        'YVK': [
            {'file': 'yvk_archive_TaittiriyaAitareyaSwetaswataraUpanishadsWithTika-ERoer1874bis_djvu.txt', 'source': 'Archive.org (Bibliotheca Indica)', 'family': 'F-ARCHIVE_DJVU', 'type': 'English+Sanskrit'},
        ],
        'NYAYA_SUTRA': [
            {'file': 'nyaya_sutra_archive_A Bilingual Index of Nyaya Bindu - Satish Chandra Vidyabhushana 1917 (BIS)_djvu.txt', 'source': 'Archive.org (Bibliotheca Indica)', 'family': 'F-ARCHIVE_DJVU', 'type': 'English index'},
        ],
    }
    
    for sid, acquisitions in NEW_ACQUISITIONS.items():
        if sid not in census:
            census[sid] = {
                'scripture_id': sid,
                'witnesses': [],
                'families': {},
                'total_witnesses': 0,
                'independent_families': 0,
            }
        
        for acc in acquisitions:
            file_path = DOWNLOAD_DIR / acc['file']
            if file_path.exists():
                witness = {
                    'witness_id': f"ARCHIVE-{sid}-{acc['family']}",
                    'family_id': acc['family'],
                    'scripture_id': sid,
                    'source': acc['source'],
                    'text_name': acc['file'],
                    'type': acc['type'],
                    'acquisition_status': 'ACQUIRED',
                    'ocr': True,
                    'files': {'local': str(file_path.relative_to(BASE))},
                }
                
                # Check if already in census
                existing_ids = [w.get('witness_id') for w in census[sid].get('witnesses', [])]
                if witness['witness_id'] not in existing_ids:
                    census[sid]['witnesses'].append(witness)
                    fam = acc['family']
                    if fam not in census[sid].get('families', {}):
                        census[sid].setdefault('families', {})[fam] = []
                    census[sid]['families'][fam].append(witness['witness_id'])
                    print(f"  Added: {sid} <- {acc['file']} ({acc['family']})")
    
    # Recompute stats
    for sid, entry in census.items():
        entry['total_witnesses'] = len(entry.get('witnesses', []))
        entry['independent_families'] = len(entry.get('families', {}))
    
    # Save updated census
    save_json(census_path, census)
    
    # Summary
    print(f"\nUpdated census for {len(census)} scriptures")
    for sid in sorted(census.keys()):
        e = census[sid]
        print(f"  {sid:15s} {e['total_witnesses']:3d} witnesses, {e['independent_families']:2d} families")

if __name__ == '__main__':
    main()
