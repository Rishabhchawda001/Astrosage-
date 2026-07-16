#!/usr/bin/env python3
"""
Phase 4: Targeted Acquisition for CRITICAL Gap Scriptures
Searches Archive.org for scriptures with no witnesses on disk.
"""
import json
import os
import re
import time
import hashlib
from pathlib import Path
import requests

BASE = Path(__file__).parent.parent
DOWNLOAD_DIR = BASE / 'knowledge' / 'downloads'
DTC_DIR = BASE / 'knowledge' / 'dtc'
ACQUISITION_DIR = DTC_DIR / 'acquisition'
ACQUISITION_DIR.mkdir(parents=True, exist_ok=True)


def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# Scriptures needing acquisition
CRITICAL_SCRIPTURES = {
    'YVK': {
        'name': 'Krishna Yajurveda (Taittiriya Samhita)',
        'search_terms': [
            'Taittiriya Samhita sanskrit',
            'Krishna Yajurveda sanskrit text',
            'Taittiriya Samhita Devanagari',
        ],
        'gretil_file': 'taittiriya_samhita',
    },
    'PRASHNA': {
        'name': 'Prashna Upanishad',
        'search_terms': [
            'Prashna Upanishad sanskrit',
            'Prashnopanishad sanskrit text',
            'Six Upanishads sanskrit',
        ],
        'gretil_file': 'prashna_upanishad',
    },
    'MAITR': {
        'name': 'Maitri Upanishad',
        'search_terms': [
            'Maitri Upanishad sanskrit',
            'Maitrayaniya Upanishad sanskrit',
        ],
        'gretil_file': 'maitri_upanishad',
    },
    'MAHAN': {
        'name': 'Mahanarayana Upanishad',
        'search_terms': [
            'Mahanarayana Upanishad sanskrit',
            'Mahanarayana Upanishad text',
        ],
        'gretil_file': 'mahanarayana_upanishad',
    },
    'PARASHARA': {
        'name': 'Parashara Smriti',
        'search_terms': [
            'Parashara Smriti sanskrit',
            'Parashara Smriti text',
        ],
        'gretil_file': 'parashara_smriti',
    },
    'VYASA_SM': {
        'name': 'Vyasa Smriti',
        'search_terms': [
            'Vyasa Smriti sanskrit',
            'Vyasasmriti text',
        ],
        'gretil_file': 'vyasa_smriti',
    },
    'NYAYA_SUTRA': {
        'name': 'Nyaya Sutras',
        'search_terms': [
            'Nyaya Sutra Gautama sanskrit',
            'Nyayasutras sanskrit text',
            'Nyaya Bhashya sanskrit',
        ],
        'gretil_file': 'nyaya_sutra',
    },
    'VAISHESHIKA_SUTRA': {
        'name': 'Vaisheshika Sutras',
        'search_terms': [
            'Vaisheshika Sutra Kanada sanskrit',
            'Vaisheshikasutras sanskrit text',
        ],
        'gretil_file': 'vaisheshika_sutra',
    },
}


def search_archive_org(query, max_results=5):
    """Search Archive.org for Sanskrit texts."""
    url = 'https://archive.org/advancedsearch.php'
    params = {
        'q': f'{query} AND mediatexts AND language:sanskrit',
        'fl[]': ['identifier', 'title', 'description', 'year', 'language', 'subject'],
        'sort[]': 'downloads desc',
        'rows': max_results,
        'page': 1,
        'output': 'json',
    }
    
    try:
        resp = requests.get(url, params=params, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            docs = data.get('response', {}).get('docs', [])
            return docs
        else:
            print(f"    HTTP {resp.status_code}")
            return []
    except Exception as e:
        print(f"    Error: {e}")
        return []


def check_gretil_accessibility(filename):
    """Check if a file exists on GRETIL (known to be 404)."""
    url = f'https://www.sub.uni-goettingen.de/ebc/wrzvoe/tmp/gretil/1_sanskr/4_epic/{filename}.htm'
    try:
        resp = requests.head(url, timeout=10)
        return resp.status_code == 200
    except:
        return False


def main():
    print("=" * 70)
    print("PHASE 4: TARGETED ACQUISITION — CRITICAL GAPS")
    print("=" * 70)
    
    results = {}
    
    for sid, info in CRITICAL_SCRIPTURES.items():
        print(f"\n--- {sid}: {info['name']} ---")
        
        scripture_result = {
            'scripture': sid,
            'name': info['name'],
            'search_results': [],
            'acquired': False,
            'notes': [],
        }
        
        # Search Archive.org
        for term in info['search_terms']:
            print(f"  Searching: '{term}'")
            docs = search_archive_org(term, max_results=3)
            
            for doc in docs:
                result = {
                    'identifier': doc.get('identifier', ''),
                    'title': doc.get('title', ''),
                    'year': doc.get('year', ''),
                    'language': doc.get('language', []),
                    'subjects': doc.get('subject', []),
                    'url': f"https://archive.org/details/{doc.get('identifier', '')}",
                }
                scripture_result['search_results'].append(result)
                print(f"    Found: {result['title'][:60]} ({result['year']})")
            
            time.sleep(1)  # Rate limit
        
        # Check GRETIL
        gretil_name = info.get('gretil_file', '')
        if gretil_name:
            print(f"  Checking GRETIL: {gretil_name}")
            accessible = check_gretil_accessibility(gretil_name)
            if accessible:
                scripture_result['notes'].append(f'GRETIL accessible: {gretil_name}')
                print(f"    GRETIL accessible!")
            else:
                scripture_result['notes'].append(f'GRETIL not accessible (404)')
                print(f"    GRETIL not accessible")
        
        results[sid] = scripture_result
    
    # Save results
    save_json(ACQUISITION_DIR / 'critical_gap_acquisition_results.json', results)
    
    # Summary
    print(f"\n{'='*70}")
    print("ACQUISITION RESULTS SUMMARY")
    print(f"{'='*70}")
    
    for sid, r in results.items():
        n_results = len(r['search_results'])
        print(f"  {sid:15s} {n_results} Archive.org results found")
        for note in r['notes']:
            print(f"    {note}")
    
    print(f"\nResults saved to: {ACQUISITION_DIR / 'critical_gap_acquisition_results.json'}")


if __name__ == '__main__':
    main()
