#!/usr/bin/env python3
"""
Phase 4: Full Corpus Index Builder
Maps ALL on-disk text files to scripture IDs and witness families.
"""
import json
import os
import re
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent
DOWNLOADS_DIR = BASE / 'knowledge' / 'downloads'
GREtil_DIR = BASE / 'knowledge' / 'gretil_parsed'
BRONZE_DIR = BASE / 'knowledge' / 'bronze' / 'extracted_text'
DTC_DIR = BASE / 'knowledge' / 'dtc'
CONFIG_DIR = DTC_DIR / 'config'

def load_json(path):
    with open(path) as f:
        return json.load(f)

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Comprehensive scripture-to-keywords mapping for file detection
SCRIPTURE_KEYWORDS = {
    'RV': ['rigveda', 'rig_veda', 'rig-veda', 'rgveda', 'vedaweb', 'aufrecht', 'sontakke', 'rigveda_muller', 'rigveda_oldenberg'],
    'SV': ['samaveda', 'sama_veda', 'sama-veda', 'jaiminiya'],
    'YVK': ['yajurveda_krishna', 'taittiriya_samhita', 'yajur_krishna'],
    'YVS': ['yajurveda_shukla', 'yajur_shukla', 'shukla_yajurveda', 'madhyandina', 'kathaka'],
    'AV': ['atharvaveda', 'atharva_veda', 'atharva-veda', 'atharva'],
    'BG': ['bhagavad_gita', 'bhagavad-gita', 'bhagavadgita', 'gita_press', 'gitapress', 'gitagovinda', 'gita_bhashya'],
    'MBH': ['mahabharata', 'mbh_', 'bharata'],
    'RM': ['ramayana', 'ramayan', 'valmiki'],
    'HV': ['harivamsa', 'harivamsha', 'harivansh'],
    'BHAG': ['bhagavata', 'bhagwat', 'bhagavat_purana', 'bhagavatam'],
    'VISH': ['vishnu_puran', 'vishnupuran'],
    'SHIV': ['shiv_puran', 'shiva_puran', 'shiva_'],
    'DEVI': ['devi_bhagwat', 'devi_bhaagwat', 'devi_gita'],
    'AGNI': ['agni_puran', 'agnipuran'],
    'BRAH': ['brahma_puran', 'brahmapuran', 'brahma_samhita'],
    'MATS': ['matsya_puran', 'matsyapurana'],
    'KURM': ['kurma_puran', 'kurmapurana'],
    'LING': ['linga_puran', 'lingpuran'],
    'MARK': ['markandeya_puran', 'markandeyapurana'],
    'NARADA': ['narada_puran', 'naradiya_puran'],
    'VAMAN': ['vaman_puran', 'vamana_puran', 'vamanpurana'],
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
    'PRASHNA': ['prashna_upanishad'],
    'MUND': ['mundaka_upanishad'],
    'MAND': ['mandukya_upanishad'],
    'TAITT': ['taittiriya_upanishad'],
    'AITAREYA': ['aitareya_upanishad'],
    'CHAND': ['chandogya_upanishad', 'chandogya_'],
    'BRIHAD': ['brhadaranyaka', 'brihadaranyaka'],
    'SHVET': ['shvetashvatara'],
    'KAUS': ['kaushitaki'],
    'MAITR': ['maitri_upanishad'],
    'MAHAN': ['mahanarayana'],
    'MANU': ['manusmriti', 'manusmruti'],
    'YAJNAV': ['yajnavalkya_smriti', 'yajnavalkya'],
    'VISHNU_SM': ['vishnu_smriti', 'vishnusmriti', 'vishnu_dharma'],
    'NARADA_SM': ['narada_smriti'],
    'PARASHARA': ['parashara_smriti'],
    'VYASA_SM': ['vyasa_smriti'],
    'APASTAMBA_DS': ['apastamba_dharmasutra', 'apastamba_grihya'],
    'BAUDHAYANA_DS': ['baudhayana_dharmasutra', 'baudhayana'],
    'GAUTAMA_DS': ['gautama_dharmasutra', 'gautama_dharma'],
    'VEDANTA_SUTRA': ['brahma_sutra', 'vedanta_sutra', 'brahmasutra'],
    'YOGA_SUTRA': ['yoga_sutra', 'yogasutra'],
    'NYAYA_SUTRA': ['nyaya_sutra', 'nyayasutra'],
    'VAISHESHIKA_SUTRA': ['vaisheshika_sutra', 'vaisheshika'],
    'NIRUKTA': ['nirukta'],
}

def classify_file(filename):
    """Classify a file into a scripture and witness family."""
    fn = filename.lower().replace('-', '_').replace(' ', '_')
    
    # Find best scripture match
    best_scripture = None
    best_score = 0
    
    for sid, keywords in SCRIPTURE_KEYWORDS.items():
        for kw in keywords:
            kw_norm = kw.lower().replace('-', '_').replace(' ', '_')
            if kw_norm in fn:
                # Longer keyword match = more specific
                if len(kw_norm) > best_score:
                    best_score = len(kw_norm)
                    best_scripture = sid
    
    # Detect witness family
    family = 'F-UNKNOWN'
    if 'aufrecht' in fn:
        family = 'F-AUFRECHT'
    elif 'padapatha' in fn:
        family = 'F-PADAPATHA'
    elif 'khila' in fn and 'rv' in fn:
        family = 'F-KHILA'
    elif 'vedaweb' in fn:
        family = 'F-LUBOTSKY'
    elif 'sontakke' in fn or 'vsm' in fn:
        family = 'F-SONTAKKE'
    elif 'gretil' in fn:
        family = 'F-GRETIL'
    elif 'gita_press' in fn or 'gitapress' in fn:
        family = 'F-GITAPRESS'
    elif 'anand' in fn or 'anandashram' in fn:
        family = 'F-ANANDASHRAM'
    elif 'chowkhamba' in fn or 'chaukhamba' in fn:
        family = 'F-CHOWKHAMBA'
    elif 'motilal' in fn:
        family = 'F-MOTILAL'
    elif 'khemraj' in fn:
        family = 'F-KHEMRAJ'
    elif 'bori' in fn:
        family = 'F-BORI'
    elif 'muller' in fn or 'mueller' in fn:
        family = 'F-MAXMULLER'
    elif 'oldenberg' in fn:
        family = 'F-OLDENBERG'
    elif 'sayana' in fn or 'sayanacharya' in fn:
        family = 'F-SAYANA'
    elif 'ramtek' in fn or 'kksu' in fn:
        family = 'F-RAMTEK'
    elif 'satavalekar' in fn or 'satwalekar' in fn:
        family = 'F-SATAVALEKAR'
    elif 'jayadev' in fn:
        family = 'F-JAYADEV'
    elif 'dli' in fn:
        family = 'F-DLI'
    elif 'djvu' in fn:
        family = 'F-DJVU_OCR'
    elif 'critical' in fn:
        family = 'F-CRITICAL'
    elif 'nirnaya' in fn:
        family = 'F-NIRNAYA_SAGAR'
    elif 'edgerton' in fn:
        family = 'F-EDGERTON'
    elif 'shankara' in fn or 'sankara' in fn:
        family = 'F-SHANKARA_COMMENTARY'
    elif 'ramanuja' in fn:
        family = 'F-RAMANUJA_COMMENTARY'
    elif 'madhva' in fn:
        family = 'F-MADHVA_COMMENTARY'
    elif 'venkateshwar' in fn:
        family = 'F-VENKATESHWAR'
    elif 'gita_press' in fn or 'gp_' in fn:
        family = 'F-GITAPRESS'
    
    # Detect OCR
    is_ocr = any(x in fn for x in ['djvu', 'ocr', 'djvutxt'])
    
    # Detect script
    script = 'IAST'  # default assumption for downloaded Sanskrit
    if any(x in fn for x in ['devanagari', 'hindi', 'sanskrit_hindi']):
        script = 'Devanagari'
    
    return {
        'scripture': best_scripture,
        'family': family,
        'ocr': is_ocr,
        'script': script,
        'confidence': best_score,
    }

def main():
    print("=" * 70)
    print("PHASE 4: FULL CORPUS INDEX BUILDER")
    print("=" * 70)
    
    # Load scripture canon
    canon = load_json(CONFIG_DIR / 'scripture_canon.json')
    scriptures = {s['id']: s for s in canon['scriptures']}
    
    corpus_index = {}
    
    # Index all text files in downloads
    print("\n--- Indexing downloads/ ---")
    download_files = []
    for f in sorted(DOWNLOADS_DIR.glob('*.txt')):
        info = classify_file(f.name)
        record = {
            'path': str(f.relative_to(BASE)),
            'name': f.name,
            'size': f.stat().st_size,
            'type': 'downloads_txt',
            **info,
        }
        download_files.append(record)
        if info['scripture']:
            if info['scripture'] not in corpus_index:
                corpus_index[info['scripture']] = []
            corpus_index[info['scripture']].append(record)
    
    print(f"  {len(download_files)} text files indexed")
    
    # Index GRETIL XML files in downloads
    print("\n--- Indexing downloads/*.xml ---")
    for f in sorted(DOWNLOADS_DIR.glob('*.xml')):
        info = classify_file(f.name)
        record = {
            'path': str(f.relative_to(BASE)),
            'name': f.name,
            'size': f.stat().st_size,
            'type': 'downloads_xml',
            **info,
        }
        if info['scripture']:
            if info['scripture'] not in corpus_index:
                corpus_index[info['scripture']] = []
            corpus_index[info['scripture']].append(record)
    
    # Index subdirectories
    print("\n--- Indexing downloads/ subdirectories ---")
    for subdir in sorted(DOWNLOADS_DIR.iterdir()):
        if subdir.is_dir():
            for f in sorted(subdir.glob('*')):
                if f.is_file():
                    info = classify_file(f.name)
                    record = {
                        'path': str(f.relative_to(BASE)),
                        'name': f.name,
                        'size': f.stat().st_size,
                        'type': f'downloads_{subdir.name}',
                        **info,
                    }
                    if info['scripture']:
                        if info['scripture'] not in corpus_index:
                            corpus_index[info['scripture']] = []
                        corpus_index[info['scripture']].append(record)
    
    # Index GRETIL parsed texts
    print("\n--- Indexing gretil_parsed/ ---")
    for f in sorted(GREtil_DIR.glob('*_gretil_iast.txt')):
        text_name = f.stem.replace('_gretil_iast', '')
        info = classify_file(text_name)
        record = {
            'path': str(f.relative_to(BASE)),
            'name': f.name,
            'size': f.stat().st_size,
            'type': 'gretil_parsed',
            **info,
            'family': 'F-GRETIL',  # Override: all gretil parsed are one family
        }
        if info['scripture']:
            if info['scripture'] not in corpus_index:
                corpus_index[info['scripture']] = []
            corpus_index[info['scripture']].append(record)
    
    # Index bronze extracted text
    if BRONZE_DIR.exists():
        print("\n--- Indexing bronze/extracted_text/ ---")
        bronze_files = list(BRONZE_DIR.glob('*.txt'))
        for f in sorted(bronze_files):
            info = classify_file(f.name)
            record = {
                'path': str(f.relative_to(BASE)),
                'name': f.name,
                'size': f.stat().st_size,
                'type': 'bronze_ocr',
                **info,
            }
            if info['scripture']:
                if info['scripture'] not in corpus_index:
                    corpus_index[info['scripture']] = []
                corpus_index[info['scripture']].append(record)
        print(f"  {len(bronze_files)} bronze files indexed")
    
    # Save corpus index
    save_json(DTC_DIR / 'phase4_corpus_index.json', corpus_index)
    
    # Print summary
    print("\n" + "=" * 70)
    print("CORPUS INDEX SUMMARY")
    print("=" * 70)
    
    total_files = 0
    for sid in sorted(corpus_index.keys(), key=lambda x: scriptures.get(x, {}).get('priority', 99)):
        files = corpus_index[sid]
        total_files += len(files)
        families = set(f.get('family', 'F-UNKNOWN') for f in files)
        ocr_count = sum(1 for f in files if f.get('ocr'))
        print(f"{sid:15s} {len(files):3d} files, {len(families)} families, {ocr_count} OCR [{', '.join(sorted(families)[:3])}]")
    
    print(f"\nTotal indexed: {total_files} files across {len(corpus_index)} scriptures")

if __name__ == '__main__':
    main()
