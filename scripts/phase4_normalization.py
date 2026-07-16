#!/usr/bin/env python3
"""
Phase 4: Text Normalization Engine
Unicode normalization, transliteration validation, verse normalization.
"""
import json
import os
import re
import unicodedata
from pathlib import Path

BASE = Path(__file__).parent.parent
GREtil_DIR = BASE / 'knowledge' / 'gretil_parsed'
DTC_DIR = BASE / 'knowledge' / 'dtc'
NORM_DIR = DTC_DIR / 'normalization'
NORM_DIR.mkdir(parents=True, exist_ok=True)


def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def analyze_unicode(text):
    """Analyze Unicode composition of text."""
    stats = {
        'total_codepoints': len(text),
        'devanagari': 0,
        'iast_latin': 0,
        'vowels': 0,
        'consonants': 0,
        'visarga': 0,
        'anusvara': 0,
        'candrabindu': 0,
        'vedic_accents': 0,
        'half_letters': 0,
        'conjuncts': 0,
        'danda': 0,
        'double_danda': 0,
        'space': 0,
        'other': 0,
        'replacement_chars': 0,
        'combining_marks': 0,
        'nfc_form': unicodedata.normalize('NFC', text) == text,
        'nfd_form': unicodedata.normalize('NFD', text) == text,
        'unique_codepoints': len(set(text)),
    }
    
    for cp in text:
        cp_int = ord(cp)
        
        if cp == '\ufffd':
            stats['replacement_chars'] += 1
        elif 0x0900 <= cp_int <= 0x097F:  # Devanagari
            stats['devanagari'] += 1
            if cp in 'अआइईउऊऋॠऌ':
                stats['vowels'] += 1
            elif cp in 'कखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह':
                stats['consonants'] += 1
            elif cp == '\u0903':  # Visarga
                stats['visarga'] += 1
            elif cp == '\u0902':  # Anusvara
                stats['anusvara'] += 1
            elif cp == '\u0901':  # Candrabindu
                stats['candrabindu'] += 1
            elif cp_int in range(0x093A, 0x094F):  # Matras
                stats['combining_marks'] += 1
            elif cp == '॥':
                stats['double_danda'] += 1
            elif cp == '।':
                stats['danda'] += 1
        elif 0x0041 <= cp_int <= 0x007A:  # Basic Latin
            stats['iast_latin'] += 1
        elif cp in 'āīūṛṝḷḹṃḥṣśṇṭḍñḥṭḍ':
            stats['iast_latin'] += 1
        elif cp == ' ':
            stats['space'] += 1
        elif cp in '॥।':
            stats['danda'] += 1
        elif 0x10A0 <= cp_int <= 0x10FF:  # Vedic accents
            stats['vedic_accents'] += 1
        else:
            stats['other'] += 1
    
    # Check for half-letters (virama)
    stats['half_letters'] = text.count('\u094D')
    
    return stats


def detect_transliteration_scheme(text):
    """Detect which transliteration scheme is used."""
    schemes = {
        'DEVANAGARI': 0,
        'IAST': 0,
        'ISO_15919': 0,
        'SLP1': 0,
        'ITRANS': 0,
        'VELTHUIS': 0,
        'HK': 0,
    }
    
    # Devanagari
    if any('\u0900' <= c <= '\u097F' for c in text):
        schemes['DEVANAGARI'] += 10
    
    # IAST indicators
    iast_chars = set('āīūṛṝḷḹṃḥṣśṇṭḍñḥṭḍ')
    if any(c in iast_chars for c in text):
        schemes['IAST'] += 5
    
    # SLP1 indicators
    if re.search(r'[fFxXqEiI]', text) and not any(c in iast_chars for c in text):
        schemes['SLP1'] += 3
    
    # ITRANS indicators
    if re.search(r'\\d|\\D|\\N|\\T|\\S|\\Z', text):
        schemes['ITRANS'] += 3
    
    # Velthuis indicators
    if re.search(r'\.\.aa|\.ii|\.uu|\.RR|\.LL', text):
        schemes['VELTHUIS'] += 3
    
    best = max(schemes, key=schemes.get)
    return best if schemes[best] > 0 else 'UNKNOWN'


def normalize_verse_number(text):
    """Extract and normalize verse numbers from text lines."""
    # Common verse number patterns
    patterns = [
        r'(\d+)\.\.(\d+)\.\.(\d+)',  # book.chapter.verse
        r'(\d+)\.(\d+)',  # chapter.verse
        r'(\d+)',  # just verse number
    ]
    
    for pattern in patterns:
        match = re.match(pattern, text.strip())
        if match:
            return match.groups()
    return None


def process_gretil_text(name):
    """Process a single GRETIL text for normalization analysis."""
    iast_path = GREtil_DIR / f'{name}_gretil_iast.txt'
    deva_path = GREtil_DIR / f'{name}_gretil_devanagari.txt'
    
    result = {'name': name}
    
    for lang, path in [('iast', iast_path), ('devanagari', deva_path)]:
        if not path.exists():
            continue
        
        with open(path, 'r', errors='replace') as f:
            text = f.read()
        
        lines = [l for l in text.split('\n') if l.strip()]
        
        stats = analyze_unicode(text)
        scheme = detect_transliteration_scheme(text)
        
        result[lang] = {
            'line_count': len(lines),
            'char_count': len(text),
            'unicode_stats': stats,
            'transliteration_scheme': scheme,
            'nfc_normalized': stats['nfc_form'],
            'has_replacement_chars': stats['replacement_chars'] > 0,
        }
    
    return result


def main():
    print("=" * 70)
    print("PHASE 4: TEXT NORMALIZATION ANALYSIS")
    print("=" * 70)
    
    # Process all GRETIL texts
    gretil_texts = sorted([f.stem.replace('_gretil_iast', '') 
                          for f in GREtil_DIR.glob('*_gretil_iast.txt')])
    
    results = {}
    total_lines = 0
    total_codepoints = 0
    
    for name in gretil_texts:
        result = process_gretil_text(name)
        results[name] = result
        
        for lang in ['iast', 'devanagari']:
            if lang in result:
                lines = result[lang]['line_count']
                cps = result[lang]['char_count']
                total_lines += lines
                total_codepoints += cps
                stats = result[lang]['unicode_stats']
                scheme = result[lang]['transliteration_scheme']
                repl = '⚠️' if stats['replacement_chars'] > 0 else '✓'
                
                print(f"  {name:40s} {lang:12s} {lines:5d} lines {cps:8d} cp {scheme:12s} {repl}")
    
    # Save results
    save_json(NORM_DIR / 'normalization_analysis.json', results)
    
    # Summary
    print(f"\n{'='*70}")
    print("NORMALIZATION SUMMARY")
    print(f"{'='*70}")
    print(f"Texts processed: {len(results)}")
    print(f"Total lines: {total_lines:,}")
    print(f"Total codepoints: {total_codepoints:,}")
    
    # Scheme distribution
    schemes = defaultdict(int)
    for r in results.values():
        for lang in ['iast', 'devanagari']:
            if lang in r:
                schemes[r[lang]['transliteration_scheme']] += 1
    
    print(f"\nScript/scheme distribution:")
    for scheme, count in sorted(schemes.items(), key=lambda x: -x[1]):
        print(f"  {scheme:15s} {count} files")
    
    # Issues found
    issues = []
    for name, r in results.items():
        for lang in ['iast', 'devanagari']:
            if lang in r:
                stats = r[lang]['unicode_stats']
                if stats['replacement_chars'] > 0:
                    issues.append(f"{name}/{lang}: {stats['replacement_chars']} replacement characters")
                if not stats['nfc_form']:
                    issues.append(f"{name}/{lang}: Not NFC normalized")
    
    print(f"\nIssues found: {len(issues)}")
    for issue in issues[:10]:
        print(f"  ⚠ {issue}")
    
    return results


if __name__ == '__main__':
    from collections import defaultdict
    main()
