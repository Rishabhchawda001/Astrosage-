#!/usr/bin/env python3
"""
Extract verses from VedaWeb TEI files for multi-witness comparison.
"""

import json
import os
import re
import hashlib
from xml.etree import ElementTree as ET

REPO = "/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage"
VEDAWEB = os.path.join(REPO, "knowledge/downloads/vedaweb/cceh-c-salt_vedaweb_tei-f975755")
NS = 'http://www.tei-c.org/ns/1.0'


def extract_vedaweb_book(filepath):
    """Extract all verses from a VedaWeb TEI book file."""
    verses = {}
    
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
    except Exception as e:
        print(f"  ERROR: {e}")
        return verses
    
    # Find all stanzas
    for stanza in root.iter(f'{{{NS}}}div'):
        xml_id = stanza.get('{http://www.w3.org/XML/1998/namespace}id', '')
        stanza_type = stanza.get('type', '')
        
        if stanza_type != 'stanza':
            continue
        
        # Parse stanza ID: b01_h001_01 -> book 1, hymn 1, verse 1
        m = re.match(r'b(\d+)_h(\d+)_(\d+)', xml_id)
        if not m:
            continue
        
        book = int(m.group(1))
        hymn = int(m.group(2))
        verse = int(m.group(3))
        ref = f"RV_{book}.{hymn:03d}.{verse:02d}"
        
        # Extract from different sources
        sources = {}
        for lg in stanza.findall(f'{{{NS}}}lg'):
            lg_id = lg.get('{http://www.w3.org/XML/1998/namespace}id', '')
            
            # Determine source
            source = 'unknown'
            if 'zurich' in lg_id:
                source = 'zurich'
            elif 'lubotsky' in lg_id:
                source = 'lubotsky'
            elif 'vnh' in lg_id:
                source = 'vnh'
            
            if source == 'unknown':
                continue
            
            # Extract padas (a, b, c, d)
            padas = {}
            for l in lg.findall(f'{{{NS}}}l'):
                l_id = l.get('{http://www.w3.org/XML/1998/namespace}id', '')
                # Only get text padas, not token pads
                if '_tokens' in l_id:
                    continue
                if l.text:
                    text = l.text.strip()
                    # Determine pada
                    pada_match = re.search(r'_([abcd])$', l_id)
                    if pada_match:
                        padas[pada_match.group(1)] = text
            
            if padas:
                full_text = ' | '.join(padas.get(p, '') for p in ['a', 'b', 'c', 'd'] if p in padas)
                full_text = re.sub(r'\s+', ' ', full_text).strip()
                if full_text:
                    fp = hashlib.sha256(full_text.encode()).hexdigest()[:16]
                    sources[source] = {
                        'text': full_text,
                        'padas': padas,
                        'fingerprint': fp
                    }
        
        if sources:
            verses[ref] = {
                'ref': ref,
                'book': book,
                'hymn': hymn,
                'verse': verse,
                'sources': sources,
                'source_count': len(sources)
            }
    
    return verses


def main():
    print("=" * 70)
    print("VEDAWEB EXTRACTION")
    print("=" * 70)
    
    all_verses = {}
    
    for book in range(1, 11):
        filepath = os.path.join(VEDAWEB, f"rv_book_{book:02d}.tei")
        if os.path.exists(filepath):
            verses = extract_vedaweb_book(filepath)
            print(f"  Book {book}: {len(verses)} verses, {sum(v['source_count'] for v in verses.values())} total readings")
            for ref, v in verses.items():
                if ref not in all_verses:
                    all_verses[ref] = v
                else:
                    # Merge sources
                    for src, data in v['sources'].items():
                        all_verses[ref]['sources'][src] = data
                    all_verses[ref]['source_count'] = len(all_verses[ref]['sources'])
    
    print(f"\nTotal verses: {len(all_verses)}")
    
    # Source coverage
    source_counts = {}
    for v in all_verses.values():
        for src in v['sources']:
            source_counts[src] = source_counts.get(src, 0) + 1
    for src, count in sorted(source_counts.items()):
        print(f"  {src}: {count} verses")
    
    # Compare with Aufrecht
    print("\n--- Comparing with Aufrecht edition ---")
    auf_path = os.path.join(REPO, "knowledge/downloads/rigveda_aufrecht_gretil.xml")
    from xml.etree import ElementTree as ET
    
    auf_verses = {}
    try:
        tree = ET.parse(auf_path)
        root = tree.getroot()
        for lg in root.iter(f'{{{NS}}}lg'):
            xml_id = lg.get('{http://www.w3.org/XML/1998/namespace}id', '')
            m = re.match(r'RV_(\d+)\.(\d+)\.(\d+)', xml_id)
            if m:
                mandala = int(m.group(1))
                sukta = int(m.group(2))
                verse = int(m.group(3))
                ref = f"RV_{mandala}.{sukta:03d}.{verse:02d}"
                
                lines = []
                for l in lg.findall(f'{{{NS}}}l'):
                    if l.text:
                        text = re.sub(r'<orig>.*?</orig>', '', l.text)
                        text = re.sub(r'[̱̍]', '', text).strip()
                        text = re.sub(r'\s+', ' ', text)
                        text = re.sub(r'\|\|?\s*$', '', text).strip()
                        if text:
                            lines.append(text)
                
                if lines:
                    full = ' | '.join(lines)
                    auf_verses[ref] = full
    except Exception as e:
        print(f"  ERROR reading Aufrecht: {e}")
    
    print(f"Aufrecht verses: {len(auf_verses)}")
    
    # Compare VNH with Aufrecht
    if 'vnh' in source_counts:
        identical = 0
        different = 0
        for ref, v in all_verses.items():
            if 'vnh' in v['sources'] and ref in auf_verses:
                vnh_text = v['sources']['vnh']['text']
                auf_text = auf_verses[ref]
                # Normalize for comparison
                vnh_norm = re.sub(r'[_\-]', '', re.sub(r'\s+', ' ', vnh_text)).strip()
                auf_norm = re.sub(r'[_\-]', '', re.sub(r'\s+', ' ', auf_text)).strip()
                if vnh_norm == auf_norm:
                    identical += 1
                else:
                    different += 1
        
        print(f"VNH vs Aufrecht: {identical} identical, {different} different")
    
    # Compare Zurich with Lubotsky
    if 'zurich' in source_counts and 'lubotsky' in source_counts:
        identical = 0
        different = 0
        for ref, v in all_verses.items():
            if 'zurich' in v['sources'] and 'lubotsky' in v['sources']:
                z_text = v['sources']['zurich']['text']
                l_text = v['sources']['lubotsky']['text']
                z_norm = re.sub(r'[_\-]', '', re.sub(r'\s+', ' ', z_text)).strip()
                l_norm = re.sub(r'[_\-]', '', re.sub(r'\s+', ' ', l_text)).strip()
                if z_norm == l_norm:
                    identical += 1
                else:
                    different += 1
        
        print(f"Zurich vs Lubotsky: {identical} identical, {different} different")
    
    # Save
    out = {
        'source': 'vedaweb',
        'total_verses': len(all_verses),
        'sources': source_counts,
        'verses': all_verses
    }
    
    out_path = os.path.join(REPO, "knowledge/dtc/rigveda/vedaweb_extract.json")
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\nSaved: {out_path}")


if __name__ == '__main__':
    main()
