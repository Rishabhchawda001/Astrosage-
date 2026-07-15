#!/usr/bin/env python3
"""
Bhagavad Gita Collation v3 — Proper verse extraction from all GRETIL XML formats.
Extracts FULL verse text from <lg> blocks, not just individual <l> lines.
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

EXPECTED = {i+1: v for i, v in enumerate([46,72,43,42,29,47,30,28,34,42,55,20,35,27,20,24,28,78])}
NS = 'http://www.tei-c.org/ns/1.0'


def clean_verse_line(text):
    """Clean a single verse line."""
    t = text.strip()
    t = re.sub(r'\|\|BhG_\d+\.\d+\|\|', '', t)
    t = re.sub(r'//\s*BhG_\d+\.\d+\s*//?', '', t)
    t = re.sub(r'\|\|\d+\|\|', '', t).strip()
    t = re.sub(r'//\s*$', '', t).strip()
    # Remove footnote numbers
    t = re.sub(r'\d+$', '', t).strip()
    t = re.sub(r'\s+', ' ', t)
    return t


def extract_from_tei(filepath, source_name):
    """Extract verses from any GRETIL TEI XML."""
    verses = {}
    
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
    except Exception as e:
        print(f"  ERROR: {e}", file=sys.stderr)
        return verses
    
    # Strategy 1: <lg xml:id="BhG_X.Y"> (Ramanuja format)
    for lg in root.iter(f'{{{NS}}}lg'):
        xml_id = lg.get('{http://www.w3.org/XML/1998/namespace}id', '')
        m = re.match(r'BhG_(\d+)\.(\d+)', xml_id)
        if m:
            ch, vs = int(m.group(1)), int(m.group(2))
            ref = f"BG_{ch:02d}.{vs:03d}"
            lines = []
            for l in lg.findall(f'{{{NS}}}l'):
                if l.text:
                    cleaned = clean_verse_line(l.text)
                    # Skip non-verse lines
                    if re.match(r'^(sañjaya|dhṛtarāṣṭra|arjuna|kṛṣṇa)\s+uvāca$', cleaned, re.IGNORECASE):
                        lines.append(cleaned)
                        continue
                    if cleaned and len(cleaned) > 1:
                        lines.append(cleaned)
            if lines:
                text = ' | '.join(lines) if len(lines) > 1 else lines[0]
                verses[ref] = text
    
    # Strategy 2: <lg> blocks containing ||BhG_X.Y|| in <l> elements
    # This handles Shankara, comm, and 4comm formats
    for lg in root.iter(f'{{{NS}}}lg'):
        # Check if any <l> in this <lg> contains a BhG reference
        ref_in_lg = None
        for l in lg.findall(f'{{{NS}}}l'):
            if l.text:
                m = re.search(r'\|\|BhG_(\d+)\.(\d+)\|\|', l.text)
                if m:
                    ch, vs = int(m.group(1)), int(m.group(2))
                    ref_in_lg = f"BG_{ch:02d}.{vs:03d}"
                    break
        
        if ref_in_lg:
            lines = []
            for l in lg.findall(f'{{{NS}}}l'):
                if l.text:
                    cleaned = clean_verse_line(l.text)
                    if cleaned and len(cleaned) > 1:
                        lines.append(cleaned)
            if lines:
                text = ' | '.join(lines) if len(lines) > 1 else lines[0]
                if ref_in_lg not in verses:
                    verses[ref_in_lg] = text
    
    # Strategy 3: <l> elements with // BhG_X.Y // (Bhaskara format)
    for lg in root.iter(f'{{{NS}}}lg'):
        ref_in_lg = None
        for l in lg.findall(f'{{{NS}}}l'):
            if l.text:
                m = re.search(r'//\s*BhG_(\d+)\.(\d+)\s*//?', l.text)
                if m:
                    ch, vs = int(m.group(1)), int(m.group(2))
                    ref_in_lg = f"BG_{ch:02d}.{vs:03d}"
                    break
        
        if ref_in_lg and ref_in_lg not in verses:
            lines = []
            for l in lg.findall(f'{{{NS}}}l'):
                if l.text:
                    cleaned = clean_verse_line(l.text)
                    if cleaned and len(cleaned) > 1:
                        lines.append(cleaned)
            if lines:
                text = ' | '.join(lines) if len(lines) > 1 else lines[0]
                verses[ref_in_lg] = text
    
    return verses


def extract_from_4comm(filepath, source_name):
    """Extract from 4-commentary XML (complex structure)."""
    verses = {}
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find reference positions (both formats)
    ref_positions = []
    for m in re.finditer(r'BhG[_ ](\d+)\.(\d+)', content):
        ch, vs = int(m.group(1)), int(m.group(2))
        ref = f"BG_{ch:02d}.{vs:03d}"
        ref_positions.append((m.start(), ref))
    
    # Find <lg> blocks
    for lg_match in re.finditer(r'<lg(?:\s[^>]*)?>(.*?)</lg>', content, re.DOTALL):
        lg_start = lg_match.start()
        lg_content = lg_match.group(1)
        
        # Find nearest preceding reference
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
        
        # Skip if we already have this verse from a better source
        if best_ref in verses:
            continue
        
        # Extract <l> elements
        l_lines = re.findall(r'<l>(.*?)</l>', lg_content)
        verse_lines = []
        for line in l_lines:
            line = line.strip()
            if re.match(r'^BhG[_ ]\d+\.\d+$', line):
                continue
            # Skip commentary attribution
            if re.match(r'^(Viśvanātha|Śrīdhara|Baladeva|Rāmānuja|Bhāskara|Caitanya)\s*:', line):
                continue
            cleaned = clean_verse_line(line)
            if cleaned and len(cleaned) > 3:
                verse_lines.append(cleaned)
        
        if verse_lines:
            text = ' | '.join(verse_lines) if len(verse_lines) > 1 else verse_lines[0]
            verses[best_ref] = text
    
    return verses


def normalize_for_compare(text):
    """Normalize for comparison."""
    t = text.strip()
    t = re.sub(r'\|\|\d+\|\|', '', t)
    t = re.sub(r'//\s*$', '', t).strip()
    t = re.sub(r'\s+', ' ', t)
    return t


def classify_difference(text_a, text_b):
    """Classify the difference between two verse readings."""
    norm_a = normalize_for_compare(text_a)
    norm_b = normalize_for_compare(text_b)
    
    if norm_a == norm_b:
        return 'identical'
    
    # Pure content (no spaces/punctuation)
    content_a = re.sub(r'[\s\|·/]', '', norm_a)
    content_b = re.sub(r'[\s\|·/]', '', norm_b)
    
    if content_a == content_b:
        return 'orthographic'
    
    # Word-level comparison
    words_a = norm_a.split()
    words_b = norm_b.split()
    
    if len(words_a) == len(words_b):
        diffs = sum(1 for a, b in zip(words_a, words_b) if a != b)
        if diffs == 0:
            return 'identical'
        elif diffs == 1:
            return 'single_word_variant'
        elif diffs <= 3:
            return 'few_word_variant'
    
    # Length ratio
    ratio = min(len(norm_a), len(norm_b)) / max(len(norm_a), len(norm_b)) if max(len(norm_a), len(norm_b)) > 0 else 0
    if ratio < 0.5:
        return 'major_difference'
    elif ratio < 0.8:
        return 'significant_variant'
    
    return 'textual_variant'


def main():
    print("=" * 70)
    print("BHAGAVAD GITA COLLATION v3 — Full Verse Extraction")
    print("=" * 70)
    
    # Source priority
    source_priority = {
        'gretil_ramanuja': 1,
        'gretil_4comm': 2,
        'gretil_shankara': 3,
        'gretil_shankara_comm': 4,
        'gretil_bhaskara': 5,
    }
    
    all_witnesses = defaultdict(dict)  # ref -> {source: text}
    
    # 1. Ramanuja (most complete, cleanest extraction)
    print("\n--- Ramanuja bhashya ---")
    frm = os.path.join(DOWNLOADS, "ramanuja_gita_bhashya_gretil.xml")
    vrm = extract_from_tei(frm, "gretil_ramanuja")
    for ref, text in vrm.items():
        all_witnesses[ref]['gretil_ramanuja'] = text
    print(f"  {len(vrm)} verses")
    
    # 2. Shankara XML
    print("\n--- Shankara XML ---")
    fsh = os.path.join(DOWNLOADS, "bhagavad_gita_shankara_gretil.xml")
    vsh = extract_from_tei(fsh, "gretil_shankara")
    for ref, text in vsh.items():
        all_witnesses[ref]['gretil_shankara'] = text
    print(f"  {len(vsh)} verses")
    
    # 3. Comm XML (Shankara 1-17)
    print("\n--- Comm XML (Shankara 1-17) ---")
    fco = os.path.join(DOWNLOADS, "bhagavad_gita_comm_gretil.xml")
    vco = extract_from_tei(fco, "gretil_shankara_comm")
    for ref, text in vco.items():
        all_witnesses[ref]['gretil_shankara_comm'] = text
    print(f"  {len(vco)} verses")
    
    # 4. 4-commentary XML
    print("\n--- 4-commentary XML ---")
    f4c = os.path.join(DOWNLOADS, "bhagavad_gita_4comm_gretil.xml")
    v4c = extract_from_4comm(f4c, "gretil_4comm")
    for ref, text in v4c.items():
        all_witnesses[ref]['gretil_4comm'] = text
    print(f"  {len(v4c)} verses")
    
    # 5. Bhaskara
    print("\n--- Bhaskara bhashya ---")
    fbs = os.path.join(DOWNLOADS, "bhaskara_gita_bhashya_gretil.xml")
    vbs = extract_from_tei(fbs, "gretil_bhaskara")
    for ref, text in vbs.items():
        all_witnesses[ref]['gretil_bhaskara'] = text
    print(f"  {len(vbs)} verses")
    
    # Build expected list
    expected = []
    for ch in range(1, 19):
        for vs in range(1, EXPECTED[ch] + 1):
            expected.append(f"BG_{ch:02d}.{vs:03d}")
    
    # Analyze
    stats = {
        'total': 0, 'found': 0, 'missing': 0,
        'unanimous': 0, 'orthographic': 0, 'single_word': 0,
        'few_word': 0, 'textual': 0, 'significant': 0,
        'major': 0, 'single_witness_only': 0
    }
    
    canonical = []
    apparatus = {}
    
    for ref in expected:
        ch = int(ref.split('_')[1].split('.')[0])
        vs = int(ref.split('.')[1])
        stats['total'] += 1
        
        witnesses = all_witnesses.get(ref, {})
        
        if not witnesses:
            stats['missing'] += 1
            canonical.append({
                'chapter': ch, 'verse': vs, 'ref': ref,
                'text': None, 'source': None, 'witness_count': 0,
                'witnesses': {}, 'status': 'missing'
            })
            continue
        
        stats['found'] += 1
        
        # Select canonical reading
        best_src = min(witnesses.keys(), key=lambda s: source_priority.get(s, 99))
        best_text = witnesses[best_src]
        
        # Get unique readings
        unique = {}
        for src, text in witnesses.items():
            norm = normalize_for_compare(text)
            if norm not in unique:
                unique[norm] = {'text': text, 'sources': []}
            unique[norm]['sources'].append(src)
        
        witness_count = len(unique)
        
        if witness_count == 1:
            stats['single_witness_only'] += 1
            classification = 'single_witness'
            confidence = 0.70
            variants = []
        else:
            # Compare all pairs
            unique_list = list(unique.values())
            pair_classifications = []
            variants = []
            
            for i in range(len(unique_list)):
                for j in range(i+1, len(unique_list)):
                    c = classify_difference(unique_list[i]['text'], unique_list[j]['text'])
                    pair_classifications.append(c)
                    if c != 'identical':
                        variants.append({
                            'reading_a': unique_list[i]['text'][:300],
                            'reading_b': unique_list[j]['text'][:300],
                            'sources_a': unique_list[i]['sources'],
                            'sources_b': unique_list[j]['sources'],
                            'classification': c
                        })
            
            if all(c == 'identical' for c in pair_classifications):
                classification = 'unanimous'
                confidence = 0.95
                stats['unanimous'] += 1
            elif all(c in ('identical', 'orthographic') for c in pair_classifications):
                classification = 'orthographic_variant'
                confidence = 0.92
                stats['orthographic'] += 1
            elif any(c == 'major_difference' for c in pair_classifications):
                classification = 'major_difference'
                confidence = 0.60
                stats['major'] += 1
            elif any(c == 'significant_variant' for c in pair_classifications):
                classification = 'significant_variant'
                confidence = 0.72
                stats['significant'] += 1
            elif any(c == 'textual_variant' for c in pair_classifications):
                classification = 'textual_variant'
                confidence = 0.78
                stats['textual'] += 1
            elif any(c == 'few_word_variant' for c in pair_classifications):
                classification = 'few_word_variant'
                confidence = 0.82
                stats['few_word'] += 1
            elif any(c == 'single_word_variant' for c in pair_classifications):
                classification = 'single_word_variant'
                confidence = 0.87
                stats['single_word'] += 1
            else:
                classification = 'minor_variant'
                confidence = 0.80
        
        canonical.append({
            'chapter': ch, 'verse': vs, 'ref': ref,
            'text': best_text, 'source': best_src,
            'witness_count': witness_count,
            'witnesses': {src: text[:200] for src, text in witnesses.items()},
            'status': 'multi_witness' if witness_count > 1 else 'single_witness'
        })
        
        apparatus[ref] = {
            'ref': ref, 'chapter': ch, 'verse': vs,
            'canonical_text': best_text,
            'witness_count': witness_count,
            'variants': variants,
            'classification': classification,
            'confidence': confidence
        }
    
    # Print results
    print(f"\n{'=' * 70}")
    print(f"COLLATION RESULTS")
    print(f"{'=' * 70}")
    print(f"Total: {stats['total']}  Found: {stats['found']}  Missing: {stats['missing']}")
    print(f"\nClassification:")
    for k in ['unanimous', 'orthographic', 'single_word', 'few_word', 'textual', 'significant', 'major', 'single_witness_only']:
        print(f"  {k}: {stats[k]}")
    
    # Per-chapter
    print(f"\n{'Ch':<5}{'Exp':<6}{'Fnd':<6}{'Unan':<6}{'Orth':<6}{'1Wd':<5}{'FW':<5}{'Tex':<5}{'Sig':<5}{'Maj':<5}{'Sing':<6}")
    print("-" * 60)
    for ch in range(1, 19):
        ch_app = {k: v for k, v in apparatus.items() if v['chapter'] == ch}
        n = len(ch_app)
        u = sum(1 for v in ch_app.values() if v['classification'] == 'unanimous')
        o = sum(1 for v in ch_app.values() if v['classification'] == 'orthographic_variant')
        s = sum(1 for v in ch_app.values() if v['classification'] == 'single_word_variant')
        f = sum(1 for v in ch_app.values() if v['classification'] == 'few_word_variant')
        t = sum(1 for v in ch_app.values() if v['classification'] == 'textual_variant')
        sg = sum(1 for v in ch_app.values() if v['classification'] == 'significant_variant')
        m = sum(1 for v in ch_app.values() if v['classification'] == 'major_difference')
        si = sum(1 for v in ch_app.values() if v['classification'] == 'single_witness')
        print(f"{ch:<5}{EXPECTED[ch]:<6}{n:<6}{u:<6}{o:<6}{s:<5}{f:<5}{t:<5}{sg:<5}{m:<5}{si:<6}")
    
    # Show sample variants
    tv = [(k, v) for k, v in apparatus.items() 
          if v['classification'] in ('textual_variant', 'significant_variant', 'single_word_variant', 'few_word_variant')]
    if tv:
        print(f"\n--- Non-identical Variants ({len(tv)} total) ---")
        for ref, v in tv[:20]:
            print(f"\n{ref} ({v['witness_count']} witnesses, {v['classification']}):")
            for var in v['variants'][:2]:
                print(f"  [{','.join(var['sources_a'])}] {var['reading_a'][:100]}")
                print(f"  [{','.join(var['sources_b'])}] {var['reading_b'][:100]}")
                print(f"  => {var['classification']}")
    
    # Save
    result = {
        'scripture': 'Bhagavadgita',
        'sources': list(source_priority.keys()),
        'total': stats['total'],
        'found': stats['found'],
        'missing_count': stats['missing'],
        'completeness': round(stats['found'] / stats['total'] * 100, 1),
        'multi_witness': stats['found'] - stats['single_witness_only'],
        'single_witness': stats['single_witness_only'],
        'variant_stats': {k: v for k, v in stats.items() if k not in ('total', 'found', 'missing')},
        'missing_verses': [ref for ref in expected if ref not in all_witnesses],
        'verses': canonical
    }
    
    with open(os.path.join(DTC_BG, "verses_canonical_v3.json"), 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    with open(os.path.join(DTC_BG, "variant_apparatus.json"), 'w', encoding='utf-8') as f:
        json.dump({'scripture': 'Bhagavadgita', 'stats': stats, 'apparatus': apparatus}, f, ensure_ascii=False, indent=2)
    
    summary = {
        'scripture': 'Bhagavadgita',
        'analysis': 'Multi-witness collation v3',
        'witnesses': result['sources'],
        'total_verses': stats['total'],
        'found': stats['found'],
        'completeness': result['completeness'],
        'multi_witness': result['multi_witness'],
        'single_witness': result['single_witness'],
        'variant_stats': result['variant_stats'],
        'textual_variant_refs': [k for k, v in apparatus.items() 
                                 if v['classification'] in ('textual_variant', 'significant_variant', 'major_difference')],
        'missing_verses': result['missing_verses']
    }
    
    with open(os.path.join(DTC_BG, "collation_summary_v3.json"), 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\nSaved: verses_canonical_v3.json, variant_apparatus.json, collation_summary_v3.json")


if __name__ == '__main__':
    main()
