#!/usr/bin/env python3
"""
Bhagavad Gita Multi-Witness Verse Extraction & Collation v2
Handles all GRETIL XML formats: 4comm, Shankara, comm, Bhaskara, Ramanuja
"""

import json
import os
import re
import sys
import hashlib
from collections import defaultdict
from xml.etree import ElementTree as ET

REPO = "/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage"
DOWNLOADS = os.path.join(REPO, "knowledge/downloads")
DTC_BG = os.path.join(REPO, "knowledge/dtc/bhagavad_gita")

EXPECTED = {
    1:46, 2:72, 3:43, 4:42, 5:29, 6:47, 7:30, 8:28,
    9:34, 10:42, 11:55, 12:20, 13:35, 14:27, 15:20,
    16:24, 17:28, 18:78
}


def extract_verse_text_from_lg(lg_elem):
    """Extract clean verse text from an <lg> element."""
    lines = []
    for l in lg_elem.findall('.//{http://www.tei-c.org/ns/1.0}l'):
        if l.text:
            text = l.text.strip()
            # Skip reference-only lines
            if re.match(r'^BhG\s+\d+\.\d+$', text):
                continue
            # Skip commentary attribution lines
            if re.match(r'^(Viśvanātha|Śrīdhara|Baladeva|Madhva|Rāmānuja|Bhāskara|Caitanya)\s*:', text):
                continue
            # Clean verse markers
            clean = re.sub(r'\|\|BhG_\d+\.\d+\|\|', '', text)
            clean = re.sub(r'//\s*BhG_\d+\.\d+\s*//?', '', clean)
            clean = re.sub(r'\|\|\d+\|\|', '', clean)
            clean = re.sub(r'//\s*$', '', clean).strip()
            clean = re.sub(r'\s+', ' ', clean)
            if clean and len(clean) > 2:
                lines.append(clean)
    return ' '.join(lines) if lines else None


def parse_gretil_tei(filepath, source_name):
    """Parse any GRETIL TEI XML file for verse references."""
    verses = {}
    
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
    except Exception as e:
        print(f"  ERROR parsing {filepath}: {e}", file=sys.stderr)
        return verses
    
    ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
    
    # Strategy 1: <lg xml:id="BhG_X.Y"> (Ramanuja format)
    for lg in root.iter('{http://www.tei-c.org/ns/1.0}lg'):
        xml_id = lg.get('{http://www.w3.org/XML/1998/namespace}id', '')
        m = re.match(r'BhG_(\d+)\.(\d+)', xml_id)
        if m:
            ch, vs = int(m.group(1)), int(m.group(2))
            ref = f"BG_{ch:02d}.{vs:03d}"
            text = extract_verse_text_from_lg(lg)
            if text:
                if ref not in verses:
                    verses[ref] = []
                verses[ref].append({'text': text, 'source': source_name, 'tag': 'lg'})
    
    # Strategy 2: <l> elements with ||BhG_X.Y|| pattern (Shankara/comm format)
    for elem in root.iter('{http://www.tei-c.org/ns/1.0}l'):
        if elem.text:
            text = elem.text.strip()
            m = re.search(r'\|\|BhG_(\d+)\.(\d+)\|\|', text)
            if m:
                ch, vs = int(m.group(1)), int(m.group(2))
                ref = f"BG_{ch:02d}.{vs:03d}"
                clean = re.sub(r'\|\|BhG_\d+\.\d+\|\|', '', text).strip()
                clean = re.sub(r'\s+', ' ', clean)
                if clean and len(clean) > 2:
                    if ref not in verses:
                        verses[ref] = []
                    # Check for duplicates
                    existing = {w['text'] for w in verses[ref]}
                    if clean not in existing:
                        verses[ref].append({'text': clean, 'source': source_name, 'tag': 'l'})
    
    # Strategy 3: <l> elements with // BhG_X.Y // pattern (Bhaskara format)
    for elem in root.iter('{http://www.tei-c.org/ns/1.0}l'):
        if elem.text:
            text = elem.text.strip()
            m = re.search(r'//\s*BhG_(\d+)\.(\d+)\s*//?', text)
            if m:
                ch, vs = int(m.group(1)), int(m.group(2))
                ref = f"BG_{ch:02d}.{vs:03d}"
                clean = re.sub(r'//\s*BhG_\d+\.\d+\s*//?', '', text).strip()
                clean = re.sub(r'//\s*$', '', clean).strip()
                clean = re.sub(r'\s+', ' ', clean)
                if clean and len(clean) > 2:
                    if ref not in verses:
                        verses[ref] = []
                    existing = {w['text'] for w in verses[ref]}
                    if clean not in existing:
                        verses[ref].append({'text': clean, 'source': source_name, 'tag': 'l_bhaskara'})
    
    return verses


def parse_4comm_xml(filepath, source_name):
    """Parse the 4-commentary GRETIL XML."""
    verses = {}
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Strategy: Find <lg> blocks and associate with nearest BhG reference
    # First, find all reference positions (both formats)
    ref_positions = []
    for m in re.finditer(r'BhG[_ ](\d+)\.(\d+)', content):
        ch, vs = int(m.group(1)), int(m.group(2))
        ref = f"BG_{ch:02d}.{vs:03d}"
        ref_positions.append((m.start(), ref))
    
    # Find all <lg> blocks
    lg_pattern = re.compile(r'<lg(?:\s[^>]*)?>(.*?)</lg>', re.DOTALL)
    
    for lg_match in lg_pattern.finditer(content):
        lg_start = lg_match.start()
        lg_content = lg_match.group(1)
        
        # Find the closest preceding reference
        best_ref = None
        best_dist = float('inf')
        for pos, ref in ref_positions:
            if pos < lg_start:
                dist = lg_start - pos
                if dist < best_dist:
                    best_dist = dist
                    best_ref = ref
        
        if not best_ref:
            continue
        
        # Extract <l> elements
        l_lines = re.findall(r'<l>(.*?)</l>', lg_content)
        
        verse_lines = []
        for line in l_lines:
            line = line.strip()
            # Skip reference-only lines
            if re.match(r'^BhG[_ ]\d+\.\d+$', line):
                continue
            # Skip commentary attribution
            if re.match(r'^(Viśvanātha|Śrīdhara|Baladeva|Madhva|Rāmānuja|Bhāskara|Caitanya)\s*:', line):
                continue
            # Clean
            clean = re.sub(r'\|\|BhG_\d+\.\d+\|\|', '', line)
            clean = re.sub(r'//\s*BhG_\d+\.\d+\s*//?', '', clean)
            clean = re.sub(r'\|\|\d+\|\|', '', clean).strip()
            clean = re.sub(r'//\s*$', '', clean).strip()
            clean = re.sub(r'\s+', ' ', clean)
            if clean and len(clean) > 3:
                verse_lines.append(clean)
        
        if verse_lines:
            full_verse = ' '.join(verse_lines)
            if best_ref not in verses:
                verses[best_ref] = []
            existing = {w['text'] for w in verses[best_ref]}
            if full_verse not in existing:
                verses[best_ref].append({
                    'text': full_verse,
                    'source': source_name,
                    'tag': 'lg'
                })
    
    return verses


def build_expected_verse_list():
    expected = []
    for ch in range(1, 19):
        for vs in range(1, EXPECTED[ch] + 1):
            expected.append(f"BG_{ch:02d}.{vs:03d}")
    return expected


def main():
    print("=" * 70)
    print("BHAGAVAD GITA MULTI-WITNESS VERSE EXTRACTION v2")
    print("=" * 70)
    
    all_witnesses = {}
    
    # 1. 4-commentary XML
    print("\n--- GRETIL 4-commentary XML ---")
    f4c = os.path.join(DOWNLOADS, "bhagavad_gita_4comm_gretil.xml")
    v4c = parse_4comm_xml(f4c, "gretil_4comm")
    v4c_direct = parse_gretil_tei(f4c, "gretil_4comm_direct")
    # Merge
    for ref, ws in {**v4c, **v4c_direct}.items():
        if ref not in all_witnesses:
            all_witnesses[ref] = []
        existing = {w['text'] for w in all_witnesses[ref]}
        for w in ws:
            if w['text'] not in existing:
                all_witnesses[ref].append(w)
                existing.add(w['text'])
    print(f"  Total unique verse refs: {sum(1 for r in all_witnesses if any(w['source'].startswith('gretil_4comm') for w in all_witnesses[r]))}")
    
    # 2. Shankara XML
    print("\n--- GRETIL Shankara XML ---")
    fsh = os.path.join(DOWNLOADS, "bhagavad_gita_shankara_gretil.xml")
    vsh = parse_gretil_tei(fsh, "gretil_shankara")
    for ref, ws in vsh.items():
        if ref not in all_witnesses:
            all_witnesses[ref] = []
        existing = {w['text'] for w in all_witnesses[ref]}
        for w in ws:
            if w['text'] not in existing:
                all_witnesses[ref].append(w)
                existing.add(w['text'])
    print(f"  Unique verse refs from Shankara: {len(vsh)}")
    
    # 3. Comm XML (Shankara 1-17)
    print("\n--- GRETIL comm XML (Shankara 1-17) ---")
    fco = os.path.join(DOWNLOADS, "bhagavad_gita_comm_gretil.xml")
    vco = parse_gretil_tei(fco, "gretil_shankara_comm")
    for ref, ws in vco.items():
        if ref not in all_witnesses:
            all_witnesses[ref] = []
        existing = {w['text'] for w in all_witnesses[ref]}
        for w in ws:
            if w['text'] not in existing:
                all_witnesses[ref].append(w)
                existing.add(w['text'])
    print(f"  Unique verse refs from comm: {len(vco)}")
    
    # 4. Bhaskara bhashya
    print("\n--- GRETIL Bhaskara bhashya ---")
    fbs = os.path.join(DOWNLOADS, "bhaskara_gita_bhashya_gretil.xml")
    if os.path.exists(fbs):
        vbs = parse_gretil_tei(fbs, "gretil_bhaskara")
        for ref, ws in vbs.items():
            if ref not in all_witnesses:
                all_witnesses[ref] = []
            existing = {w['text'] for w in all_witnesses[ref]}
            for w in ws:
                if w['text'] not in existing:
                    all_witnesses[ref].append(w)
                    existing.add(w['text'])
        print(f"  Unique verse refs from Bhaskara: {len(vbs)}")
    else:
        print("  File not found")
    
    # 5. Ramanuja bhashya
    print("\n--- GRETIL Ramanuja bhashya ---")
    frm = os.path.join(DOWNLOADS, "ramanuja_gita_bhashya_gretil.xml")
    if os.path.exists(frm):
        vrm = parse_gretil_tei(frm, "gretil_ramanuja")
        for ref, ws in vrm.items():
            if ref not in all_witnesses:
                all_witnesses[ref] = []
            existing = {w['text'] for w in all_witnesses[ref]}
            for w in ws:
                if w['text'] not in existing:
                    all_witnesses[ref].append(w)
                    existing.add(w['text'])
        print(f"  Unique verse refs from Ramanuja: {len(vrm)}")
    else:
        print("  File not found")
    
    expected = build_expected_verse_list()
    
    print(f"\n{'=' * 70}")
    print(f"EXTRACTION SUMMARY")
    print(f"{'=' * 70}")
    print(f"Expected: {len(expected)}")
    print(f"With witnesses: {len(all_witnesses)}")
    
    missing = [v for v in expected if v not in all_witnesses]
    print(f"Missing: {len(missing)}")
    if missing:
        print(f"  {missing}")
    
    # Build canonical verses
    canonical = []
    for ref in expected:
        ch = int(ref.split('_')[1].split('.')[0])
        vs = int(ref.split('.')[1])
        
        if ref in all_witnesses:
            witnesses = all_witnesses[ref]
            # Select best canonical text
            priority = ['gretil_4comm', 'gretil_shankara', 'gretil_shankara_comm',
                       'gretil_bhaskara', 'gretil_ramanuja']
            canon_text = None
            canon_src = None
            for p in priority:
                for w in witnesses:
                    if w['source'] == p:
                        canon_text = w['text']
                        canon_src = w['source']
                        break
                if canon_text:
                    break
            if not canon_text:
                canon_text = witnesses[0]['text']
                canon_src = witnesses[0]['source']
            
            canonical.append({
                'chapter': ch, 'verse': vs, 'ref': ref,
                'text': canon_text, 'source': canon_src,
                'witness_count': len(witnesses),
                'witnesses': [{'source': w['source'],
                              'text_hash': hashlib.sha256(w['text'].encode()).hexdigest()[:16]}
                             for w in witnesses],
                'status': 'multi_witness' if len(witnesses) > 1 else 'single_witness'
            })
        else:
            canonical.append({
                'chapter': ch, 'verse': vs, 'ref': ref,
                'text': None, 'source': None,
                'witness_count': 0, 'witnesses': [],
                'status': 'missing'
            })
    
    multi = sum(1 for v in canonical if v['status'] == 'multi_witness')
    single = sum(1 for v in canonical if v['status'] == 'single_witness')
    miss = sum(1 for v in canonical if v['status'] == 'missing')
    
    print(f"\nMulti-witness: {multi}")
    print(f"Single-witness: {single}")
    print(f"Missing: {miss}")
    
    # Per-chapter
    print(f"\n{'Ch':<5}{'Exp':<6}{'Fnd':<6}{'Multi':<7}{'Sgl':<6}{'Miss':<6}")
    print("-" * 36)
    for ch in range(1, 19):
        exp = EXPECTED[ch]
        cv = [v for v in canonical if v['chapter'] == ch]
        fnd = sum(1 for v in cv if v['status'] != 'missing')
        m = sum(1 for v in cv if v['status'] == 'multi_witness')
        s = sum(1 for v in cv if v['status'] == 'single_witness')
        mi = sum(1 for v in cv if v['status'] == 'missing')
        print(f"{ch:<5}{exp:<6}{fnd:<6}{m:<7}{s:<6}{mi:<6}")
    
    # Source analysis
    print(f"\n--- Source Coverage ---")
    source_counts = defaultdict(int)
    for ref, ws in all_witnesses.items():
        for w in ws:
            source_counts[w['source']] += 1
    for src, count in sorted(source_counts.items()):
        print(f"  {src}: {count} verses")
    
    # Save
    result = {
        'scripture': 'Bhagavadgita',
        'sources': list(source_counts.keys()),
        'total': len(expected),
        'found': multi + single,
        'missing_count': miss,
        'multi_witness': multi,
        'single_witness': single,
        'completeness': round((multi + single) / len(expected) * 100, 1),
        'missing_verses': [v['ref'] for v in canonical if v['status'] == 'missing'],
        'verses': canonical
    }
    
    outpath = os.path.join(DTC_BG, "verses_canonical_v2.json")
    with open(outpath, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\nSaved: {outpath}")
    
    # Collation summary
    collation = {
        'scripture': 'Bhagavadgita',
        'total_canonical_verses': multi + single,
        'expected': len(expected),
        'completeness': result['completeness'],
        'missing_verses': result['missing_verses'],
        'multi_witness_verses': multi,
        'single_witness_verses': single,
        'sources': result['sources'],
        'per_chapter': {}
    }
    for ch in range(1, 19):
        cv = [v for v in canonical if v['chapter'] == ch]
        collation['per_chapter'][str(ch)] = {
            'expected': EXPECTED[ch],
            'found': sum(1 for v in cv if v['status'] != 'missing'),
            'multi_witness': sum(1 for v in cv if v['status'] == 'multi_witness'),
            'single_witness': sum(1 for v in cv if v['status'] == 'single_witness'),
            'missing': [v['ref'] for v in cv if v['status'] == 'missing']
        }
    
    coll_out = os.path.join(DTC_BG, "collation_summary_v2.json")
    with open(coll_out, 'w', encoding='utf-8') as f:
        json.dump(collation, f, ensure_ascii=False, indent=2)
    print(f"Saved: {coll_out}")
    
    return result


if __name__ == '__main__':
    main()
