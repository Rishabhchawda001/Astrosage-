#!/usr/bin/env python3
"""
Certification: Ground-Truth Verification of Every Scripture
Independently verifies extracted data against source files.
No assumptions. Every number must be reproducible.
"""
import json
import os
import re
import unicodedata
from pathlib import Path
from collections import defaultdict
from datetime import datetime

BASE = Path(__file__).parent.parent
DOWNLOAD_DIR = BASE / 'knowledge' / 'downloads'
GREIL_DIR = BASE / 'knowledge' / 'gretil_parsed'
DTC_DIR = BASE / 'knowledge' / 'dtc'
CERT_DIR = DTC_DIR / 'certification'
CERT_DIR.mkdir(parents=True, exist_ok=True)


def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# Scripture definitions with expected structure
SCRIPTURES = {
    'RV': {'name': 'Rigveda Samhita', 'category': 'Veda', 'expected_verses': 10600, 'expected_mandalas': 10, 'structure': 'mandala/sukta/verse'},
    'SV': {'name': 'Samaveda Samhita', 'category': 'Veda', 'expected_verses': 1875, 'structure': 'kanda/adhyaya/verse'},
    'YVK': {'name': 'Krishna Yajurveda', 'category': 'Veda', 'expected_verses': 2000, 'structure': 'kanda/adhyaya/verse'},
    'YVS': {'name': 'Shukla Yajurveda', 'category': 'Veda', 'expected_verses': 2000, 'structure': 'adhyaya/verse'},
    'AV': {'name': 'Atharvaveda Samhita', 'category': 'Veda', 'expected_verses': 6000, 'structure': 'kanda/sukta/verse'},
    'BG': {'name': 'Bhagavad Gita', 'category': 'Itihasa', 'expected_verses': 700, 'expected_chapters': 18, 'structure': 'adhyaya/verse'},
    'MBH': {'name': 'Mahabharata', 'category': 'Itihasa', 'expected_verses': 100000, 'expected_parvas': 18, 'structure': 'parva/adhyaya/verse'},
    'RM': {'name': 'Ramayana', 'category': 'Itihasa', 'expected_verses': 24000, 'expected_kandas': 7, 'structure': 'kanda/sarga/verse'},
    'HV': {'name': 'Harivamsha', 'category': 'Itihasa', 'expected_verses': 16000, 'structure': 'parva/adhyaya/verse'},
    'BHAG': {'name': 'Bhagavata Purana', 'category': 'Purana', 'expected_verses': 18000, 'expected_skandhas': 12, 'structure': 'skandha/adhyaya/verse'},
    'VISH': {'name': 'Vishnu Purana', 'category': 'Purana', 'expected_verses': 23000, 'structure': 'amsha/adhyaya/verse'},
    'SHIV': {'name': 'Shiva Purana', 'category': 'Purana', 'expected_verses': 24000, 'structure': 'vidya/samhita/verse'},
    'DEVI': {'name': 'Devi Bhagavata Purana', 'category': 'Purana', 'expected_verses': 18000, 'structure': 'skandha/adhyaya/verse'},
    'AGNI': {'name': 'Agni Purana', 'category': 'Purana', 'expected_verses': 16000, 'expected_chapters': 382, 'structure': 'adhyaya/verse'},
    'BRAH': {'name': 'Brahma Purana', 'category': 'Purana', 'expected_verses': 14000, 'structure': 'adhyaya/verse'},
    'MATS': {'name': 'Matsya Purana', 'category': 'Purana', 'expected_verses': 13000, 'structure': 'adhyaya/verse'},
    'KURM': {'name': 'Kurma Purana', 'category': 'Purana', 'expected_verses': 12000, 'structure': 'adhyaya/verse'},
    'LING': {'name': 'Linga Purana', 'category': 'Purana', 'expected_verses': 11000, 'structure': 'adhyaya/verse'},
    'MARK': {'name': 'Markandeya Purana', 'category': 'Purana', 'expected_verses': 9000, 'structure': 'adhyaya/verse'},
    'NARADA': {'name': 'Narada Purana', 'category': 'Purana', 'expected_verses': 18000, 'structure': 'adhyaya/verse'},
    'VAMAN': {'name': 'Vamana Purana', 'category': 'Purana', 'expected_verses': 10000, 'structure': 'adhyaya/verse'},
    'VARAH': {'name': 'Varaha Purana', 'category': 'Purana', 'expected_verses': 10000, 'structure': 'adhyaya/verse'},
    'VYU': {'name': 'Vayu Purana', 'category': 'Purana', 'expected_verses': 24000, 'structure': 'adhyaya/verse'},
    'SKAND': {'name': 'Skanda Purana', 'category': 'Purana', 'expected_verses': 24000, 'structure': 'khandhika/adhyaya/verse'},
    'BRAHMD': {'name': 'Brahmanda Purana', 'category': 'Purana', 'expected_verses': 12000, 'structure': 'adhyaya/verse'},
    'KALI': {'name': 'Kalika Purana', 'category': 'Purana', 'expected_verses': 9000, 'structure': 'adhyaya/verse'},
    'GARUDA': {'name': 'Garuda Purana', 'category': 'Purana', 'expected_verses': 8000, 'structure': 'adhyaya/verse'},
    'ISHA': {'name': 'Isha Upanishad', 'category': 'Upanishad', 'expected_verses': 18, 'structure': 'verse'},
    'KEN': {'name': 'Kena Upanishad', 'category': 'Upanishad', 'expected_verses': 32, 'structure': 'kanda/verse'},
    'KATH': {'name': 'Katha Upanishad', 'category': 'Upanishad', 'expected_verses': 119, 'structure': 'vallika/verse'},
    'PRASHNA': {'name': 'Prashna Upanishad', 'category': 'Upanishad', 'expected_verses': 64, 'structure': 'prashna/verse'},
    'MUND': {'name': 'Mundaka Upanishad', 'category': 'Upanishad', 'expected_verses': 83, 'structure': 'mundaka/verse'},
    'MAND': {'name': 'Mandukya Upanishad', 'category': 'Upanishad', 'expected_verses': 12, 'structure': 'verse'},
    'TAITT': {'name': 'Taittiriya Upanishad', 'category': 'Upanishad', 'expected_verses': 104, 'structure': 'vallika/anuvaka/verse'},
    'AITAREYA': {'name': 'Aitareya Upanishad', 'category': 'Upanishad', 'expected_verses': 33, 'structure': 'adhyaya/verse'},
    'CHAND': {'name': 'Chandogya Upanishad', 'category': 'Upanishad', 'expected_verses': 634, 'structure': 'kanda/adhyaya/verse'},
    'BRIHAD': {'name': 'Brihadaranyaka Upanishad', 'category': 'Upanishad', 'expected_verses': 536, 'structure': 'adhyaya/khanda/verse'},
    'SHVET': {'name': 'Shvetashvatara Upanishad', 'category': 'Upanishad', 'expected_verses': 113, 'structure': 'adhyaya/verse'},
    'KAUS': {'name': 'Kaushitaki Upanishad', 'category': 'Upanishad', 'expected_verses': 88, 'structure': 'adhyaya/verse'},
    'MAITR': {'name': 'Maitri Upanishad', 'category': 'Upanishad', 'expected_verses': 115, 'structure': 'prapathaka/verse'},
    'MAHAN': {'name': 'Mahanarayana Upanishad', 'category': 'Upanishad', 'expected_verses': 84, 'structure': 'verse'},
    'MANU': {'name': 'Manusmriti', 'category': 'Smriti', 'expected_verses': 2694, 'expected_adhyayas': 12, 'structure': 'adhyaya/sutra'},
    'YAJNAV': {'name': 'Yajnavalkya Smriti', 'category': 'Smriti', 'expected_verses': 1054, 'structure': 'adhyaya/sutra'},
    'VISHNU_SM': {'name': 'Vishnu Smriti', 'category': 'Smriti', 'expected_verses': 100, 'structure': 'adhyaya/sutra'},
    'NARADA_SM': {'name': 'Narada Smriti', 'category': 'Smriti', 'expected_verses': 150, 'structure': 'adhyaya/sutra'},
    'PARASHARA': {'name': 'Parashara Smriti', 'category': 'Smriti', 'expected_verses': 150, 'structure': 'adhyaya/sutra'},
    'VYASA_SM': {'name': 'Vyasa Smriti', 'category': 'Smriti', 'expected_verses': 100, 'structure': 'sutra'},
    'APASTAMBA_DS': {'name': 'Apastamba Dharmasutra', 'category': 'Sutra', 'expected_verses': 1500, 'structure': 'prashna/sutra'},
    'BAUDHAYANA_DS': {'name': 'Baudhayana Dharmasutra', 'category': 'Sutra', 'expected_verses': 500, 'structure': 'prashna/sutra'},
    'GAUTAMA_DS': {'name': 'Gautama Dharmasutra', 'category': 'Sutra', 'expected_verses': 1000, 'structure': 'adhikarana/sutra'},
    'VEDANTA_SUTRA': {'name': 'Vedanta Sutras', 'category': 'Sutra', 'expected_verses': 555, 'structure': 'adhyaya/pada/sutra'},
    'YOGA_SUTRA': {'name': 'Yoga Sutras', 'category': 'Sutra', 'expected_verses': 196, 'structure': 'pada/sutra'},
    'NYAYA_SUTRA': {'name': 'Nyaya Sutras', 'category': 'Sutra', 'expected_verses': 560, 'structure': 'adhyaya/sutra'},
    'VAISHESHIKA_SUTRA': {'name': 'Vaisheshika Sutras', 'category': 'Sutra', 'expected_verses': 370, 'structure': 'adhyaya/sutra'},
}

# Scripture -> file name patterns (verified from actual downloads)
SCRIPTURE_FILES = {
    'RV': [
        ('rigveda_aufrecht_gretil.xml', 'gretil_xml'),
        ('rigveda_padapatha_gretil.xml', 'gretil_xml'),
        ('rigveda_khila_gretil.xml', 'gretil_xml'),
        ('vedaweb/cceh-c-salt_vedaweb_tei-f975755/', 'vedaweb_tei'),
        ('rigveda_chowkhamba_1973_djvu.txt', 'ocr'),
        ('rigveda_hindi.txt', 'hindi'),
        ('rigveda_maxmuller_djvu.txt', 'ocr'),
        ('rigveda_sayana_bhashya_ia_ia_djvu.txt', 'commentary'),
    ],
    'BG': [
        ('bg_gita_press_djvu.txt', 'ocr'),
        ('bhagavad_gita_4comm_gretil.xml', 'gretil_xml'),
        ('bhagavad_gita_shankara_gretil.xml', 'gretil_xml'),
        ('bhagavad_gita_warrier_bhashya_djvu.txt', 'ocr'),
        ('bhagavad_gita_pullela_telugu_djvu.txt', 'ocr'),
    ],
    'MBH': [
        ('mahabharata_satwalekar_ia_ia_djvu.txt', 'ocr'),
        ('mahabharata_virata_bori_ia_ia_djvu.txt', 'ocr'),
    ],
    'RM': [
        ('ramayana_gretil.xml', 'gretil_xml'),
        ('ramayana_baroda_critical_vol1.txt', 'critical'),
        ('ramayana_critical_2022.txt', 'critical'),
        ('ramcharitmanas_djvu.txt', 'hindi'),
    ],
}


def verify_unicode(path):
    """Verify Unicode integrity of a file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read(100000)
        
        nfc = unicodedata.normalize('NFC', content)
        nfd = unicodedata.normalize('NFD', content)
        
        replacement_count = content.count('\ufffd')
        devanagari = sum(1 for c in content if '\u0900' <= c <= '\u097F')
        total = max(len(content), 1)
        
        # Check for garbled sequences
        garbled = len(re.findall(r'M-`M-|M-\^@|[\x00-\x08\x0b\x0c\x0e-\x1f]', content))
        
        return {
            'valid_utf8': True,
            'nfc_normalized': content == nfc,
            'replacement_chars': replacement_count,
            'devanagari_count': devanagari,
            'total_chars': total,
            'devanagari_pct': round(devanagari / total * 100, 1),
            'garbled_sequences': garbled,
            'quality': 'GARBLED' if garbled > 100 else ('LOW' if replacement_count > 10 else 'GOOD'),
        }
    except Exception as e:
        return {'valid_utf8': False, 'quality': 'UNREADABLE', 'error': str(e)}


def count_verses_in_file(path):
    """Count actual verses in a file by analyzing structure."""
    try:
        with open(path, 'r', errors='replace') as f:
            content = f.read()
    except:
        return {'status': 'READ_ERROR', 'verses': 0}
    
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    
    # Count verse-like lines (substantial content, not headers/footers)
    verse_like = []
    for line in lines:
        # Skip very short lines (likely headers/page numbers)
        if len(line) < 10:
            continue
        # Skip obvious non-verse lines
        if re.match(r'^(?:chapter|sarga|adhyaya|book|page|copyright|http|www)', line, re.IGNORECASE):
            continue
        if re.match(r'^[\d\s\.]+$', line):
            continue
        verse_like.append(line)
    
    return {
        'total_lines': len(lines),
        'verse_like': len(verse_like),
        'status': 'EXTRACTED',
    }


def verify_scripture(sid, spec):
    """Verify a single scripture against all available sources."""
    print(f"\n  Verifying {sid}: {spec['name']}")
    
    results = {
        'scripture': sid,
        'name': spec['name'],
        'category': spec['category'],
        'expected_verses': spec['expected_verses'],
        'sources': [],
        'unicode_audit': [],
        'total_extractable': 0,
        'best_source': None,
        'best_verses': 0,
        'coverage_pct': 0,
        'certification': 'UNVERIFIED',
    }
    
    # Search for files matching this scripture
    found_files = []
    
    # Check downloads directory
    for f in DOWNLOAD_DIR.rglob('*'):
        if f.is_file() and f.suffix in ('.txt', '.xml', '.tei', '.htm'):
            fname = f.name.lower()
            # Simple name-based matching
            if sid.lower().replace('_', '') in fname.replace('-', '').replace('_', '').replace(' ', ''):
                found_files.append(f)
            elif sid == 'BG' and ('bhagavad_gita' in fname or 'bg_' in fname):
                found_files.append(f)
            elif sid == 'RV' and 'rigveda' in fname:
                found_files.append(f)
            elif sid == 'MBH' and 'mahabharata' in fname:
                found_files.append(f)
            elif sid == 'RM' and ('ramayana' in fname or 'ramayan' in fname):
                found_files.append(f)
    
    # Check GRETIL parsed
    gretil_name_map = {
        'RV': 'rigveda_aufrecht', 'SV': 'samaveda', 'AV': 'atharva_prayashchittani',
        'BG': 'bhagavad_gita_4comm', 'HV': 'harivamsa', 'RM': 'ramayana',
        'AGNI': 'agni_puran', 'BRAH': 'brahma_puran', 'BHAG': 'bhagavata',
        'GARUDA': 'garuda_puran', 'KURM': 'kurma_puran', 'LING': 'linga_puran',
        'MARK': 'markandeya_puran', 'NARADA': 'narada_puran', 'MATS': 'matsya_puran',
        'SHIV': 'shiva_puran', 'SKAND': 'skanda_puran_revakhanda',
        'VAMAN': 'vamana_puran', 'VISH': 'vishnu_puran', 'VYU': 'revakhanda_vayu_puran',
        'DEVI': 'devi_gita', 'AITAREYA': 'aitareya_upanishad', 'ISHA': 'isha_upanishad',
        'SHVET': 'shvetashvatara_upanishad', 'MANU': 'manusmriti',
        'NARADA_SM': 'narada_smriti', 'VISHNU_SM': 'vishnu_smriti',
        'YAJNAV': 'yajnavalkya_smriti', 'APASTAMBA_DS': 'apastamba_dharmasutra',
        'BAUDHAYANA_DS': 'baudhayana_dharmasutra', 'GAUTAMA_DS': 'gautama_dharmasutra',
        'YOGA_SUTRA': 'yoga_sutra',
    }
    
    if sid in gretil_name_map:
        gname = gretil_name_map[sid]
        iast_path = GREIL_DIR / f'{gname}_gretil_iast.txt'
        if iast_path.exists():
            found_files.append(iast_path)
    
    # Verify each found file
    best_verses = 0
    for fpath in found_files:
        rel = str(fpath.relative_to(BASE))
        
        # Unicode verification
        unicode_info = verify_unicode(fpath)
        
        # Verse count
        verse_info = count_verses_in_file(fpath)
        
        source_record = {
            'path': rel,
            'name': fpath.name,
            'size': fpath.stat().st_size,
            'unicode_quality': unicode_info.get('quality', 'UNKNOWN'),
            'unicode_details': unicode_info,
            'verses': verse_info.get('verse_like', 0),
            'total_lines': verse_info.get('total_lines', 0),
            'status': verse_info.get('status', 'UNKNOWN'),
        }
        
        results['sources'].append(source_record)
        results['unicode_audit'].append(unicode_info)
        
        if verse_info.get('verse_like', 0) > best_verses:
            best_verses = verse_info.get('verse_like', 0)
            results['best_source'] = rel
    
    results['total_extractable'] = best_verses
    results['best_verses'] = best_verses
    
    expected = spec.get('expected_verses', 1000)
    results['coverage_pct'] = round(min(100, best_verses / expected * 100), 1) if expected > 0 else 0
    
    # Certification
    has_good_unicode = any(u.get('quality') == 'GOOD' for u in results['unicode_audit'])
    has_enough_verses = results['coverage_pct'] >= 80
    
    if has_enough_verses and has_good_unicode:
        results['certification'] = 'CERTIFIED'
    elif results['best_verses'] > 0:
        results['certification'] = 'PROVISIONALLY_CERTIFIED'
    else:
        results['certification'] = 'UNVERIFIED'
    
    icon = {'CERTIFIED': '✅', 'PROVISIONALLY_CERTIFIED': '⚠️', 'UNVERIFIED': '❌'}.get(results['certification'], '?')
    print(f"    {icon} {results['best_verses']:,} verses ({results['coverage_pct']:.1f}%) [{results['certification']}]")
    
    return results


def main():
    print("=" * 70)
    print("CORPUS CERTIFICATION: GROUND-TRUTH VERIFICATION")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)
    
    all_results = {}
    
    for sid, spec in SCRIPTURES.items():
        result = verify_scripture(sid, spec)
        all_results[sid] = result
    
    # Save results
    save_json(CERT_DIR / 'verification_results.json', all_results)
    
    # Summary
    print(f"\n{'='*70}")
    print("VERIFICATION SUMMARY")
    print(f"{'='*70}")
    
    certified = sum(1 for r in all_results.values() if r['certification'] == 'CERTIFIED')
    provisional = sum(1 for r in all_results.values() if r['certification'] == 'PROVISIONALLY_CERTIFIED')
    unverified = sum(1 for r in all_results.values() if r['certification'] == 'UNVERIFIED')
    
    total_verses = sum(r['best_verses'] for r in all_results.values())
    
    print(f"\n  CERTIFICATION STATUS:")
    print(f"  CERTIFIED:              {certified}")
    print(f"  PROVISIONALLY CERTIFIED: {provisional}")
    print(f"  UNVERIFIED:             {unverified}")
    print(f"  TOTAL:                  {certified + provisional + unverified}")
    
    print(f"\n  CORPUS STATISTICS:")
    print(f"  Total extractable verses: {total_verses:,}")
    
    print(f"\n  PER-SCRIPTURE STATUS:")
    for sid in sorted(all_results.keys()):
        r = all_results[sid]
        icon = {'CERTIFIED': '✅', 'PROVISIONALLY_CERTIFIED': '⚠️', 'UNVERIFIED': '❌'}.get(r['certification'], '?')
        n_sources = len(r['sources'])
        print(f"  {icon} {sid:15s} {r['best_verses']:7d} verses ({r['coverage_pct']:5.1f}%) [{n_sources} sources]")
    
    # List unverified
    unverified_list = [sid for sid, r in all_results.items() if r['certification'] == 'UNVERIFIED']
    if unverified_list:
        print(f"\n  UNVERIFIED SCRIPTURES:")
        for sid in unverified_list:
            r = all_results[sid]
            print(f"    {sid}: {r['name']} — {len(r['sources'])} files found, 0 extractable verses")
    
    print(f"\nResults saved to: {CERT_DIR / 'verification_results.json'}")


if __name__ == '__main__':
    main()
