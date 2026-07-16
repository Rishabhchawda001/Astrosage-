#!/usr/bin/env python3
"""
Bhagavad Gita Full Collation — Extracts from all witnesses, deduplicates by source,
compares across sources, builds variant apparatus.
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


def extract_from_xml(filepath, source_name):
    """Extract verses from any GRETIL XML, returning {ref: [(text, source_tag), ...]}"""
    verses = defaultdict(list)
    
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
    except Exception as e:
        print(f"  ERROR: {e}", file=sys.stderr)
        return verses
    
    ns = 'http://www.tei-c.org/ns/1.0'
    
    # Strategy 1: xml:id on <lg> (Ramanuja format)
    for lg in root.iter(f'{{{ns}}}lg'):
        xml_id = lg.get('{http://www.w3.org/XML/1998/namespace}id', '')
        m = re.match(r'BhG_(\d+)\.(\d+)', xml_id)
        if m:
            ch, vs = int(m.group(1)), int(m.group(2))
            ref = f"BG_{ch:02d}.{vs:03d}"
            lines = []
            for l in lg.findall(f'.//{{{ns}}}l'):
                if l.text:
                    t = l.text.strip()
                    if re.match(r'^BhG\s+\d+\.\d+$', t):
                        continue
                    t = re.sub(r'\|\|BhG_\d+\.\d+\|\|', '', t)
                    t = re.sub(r'//\s*BhG_\d+\.\d+\s*//?', '', t)
                    t = re.sub(r'\|\|\d+\|\|', '', t).strip()
                    t = re.sub(r'\s+', ' ', t)
                    if t and len(t) > 2:
                        lines.append(t)
            if lines:
                text = ' '.join(lines)
                fp = hashlib.sha256(text.encode()).hexdigest()[:16]
                verses[ref].append((text, f"{source_name}_lg", fp))
    
    # Strategy 2: ||BhG_X.Y|| in <l> elements
    for l in root.iter(f'{{{ns}}}l'):
        if l.text:
            t = l.text.strip()
            m = re.search(r'\|\|BhG_(\d+)\.(\d+)\|\|', t)
            if m:
                ch, vs = int(m.group(1)), int(m.group(2))
                ref = f"BG_{ch:02d}.{vs:03d}"
                clean = re.sub(r'\|\|BhG_\d+\.\d+\|\|', '', t).strip()
                clean = re.sub(r'\s+', ' ', clean)
                if clean and len(clean) > 2:
                    fp = hashlib.sha256(clean.encode()).hexdigest()[:16]
                    verses[ref].append((clean, f"{source_name}_l", fp))
    
    # Strategy 3: // BhG_X.Y // in <l> elements (Bhaskara)
    for l in root.iter(f'{{{ns}}}l'):
        if l.text:
            t = l.text.strip()
            m = re.search(r'//\s*BhG_(\d+)\.(\d+)\s*//?', t)
            if m:
                ch, vs = int(m.group(1)), int(m.group(2))
                ref = f"BG_{ch:02d}.{vs:03d}"
                clean = re.sub(r'//\s*BhG_\d+\.\d+\s*//?', '', t).strip()
                clean = re.sub(r'//\s*$', '', clean).strip()
                clean = re.sub(r'\s+', ' ', clean)
                if clean and len(clean) > 2:
                    fp = hashlib.sha256(clean.encode()).hexdigest()[:16]
                    verses[ref].append((clean, f"{source_name}_bhaskara", fp))
    
    return verses


def extract_from_4comm(filepath, source_name):
    """Extract from 4-commentary XML (complex structure with commentary interleaved)."""
    verses = defaultdict(list)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find reference positions
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
        
        # Extract <l> lines
        l_lines = re.findall(r'<l>(.*?)</l>', lg_content)
        verse_lines = []
        for line in l_lines:
            line = line.strip()
            if re.match(r'^BhG[_ ]\d+\.\d+$', line):
                continue
            if re.match(r'^(Viśvanātha|Śrīdhara|Baladeva|Rāmānuja|Bhāskara|Caitanya)\s*:', line):
                continue
            clean = re.sub(r'\|\|BhG_\d+\.\d+\|\|', '', line)
            clean = re.sub(r'//\s*BhG_\d+\.\d+\s*//?', '', clean)
            clean = re.sub(r'\|\|\d+\|\|', '', clean).strip()
            clean = re.sub(r'//\s*$', '', clean).strip()
            clean = re.sub(r'\s+', ' ', clean)
            if clean and len(clean) > 3:
                verse_lines.append(clean)
        
        if verse_lines:
            text = ' '.join(verse_lines)
            fp = hashlib.sha256(text.encode()).hexdigest()[:16]
            verses[best_ref].append((text, f"{source_name}_lg", fp))
    
    return verses


def normalize_for_compare(text):
    """Normalize for comparison."""
    t = text.strip()
    t = re.sub(r'\|\|\d+\|\|', '', t)
    t = re.sub(r'//\s*$', '', t).strip()
    t = re.sub(r'\s+', ' ', t)
    # Remove all diacritics for pure content comparison
    # Actually, keep diacritics but normalize whitespace and punctuation
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
        if diffs <= 1:
            return 'single_word_variant'
        elif diffs <= 3:
            return 'few_word_variant'
    
    # Length ratio
    ratio = min(len(norm_a), len(norm_b)) / max(len(norm_a), len(norm_b)) if max(len(norm_a), len(norm_b)) > 0 else 0
    if ratio < 0.6:
        return 'major_difference'
    
    return 'textual_variant'


def main():
    print("=" * 70)
    print("BHAGAVAD GITA FULL COLLATION")
    print("=" * 70)
    
    # Source priority for canonical reading
    source_priority = {
        'gretil_4comm': 1,
        'gretil_shankara': 2,
        'gretil_ramanuja': 3,
        'gretil_bhaskara': 4,
    }
    
    # Collect all witnesses per verse
    all_witnesses = defaultdict(list)  # ref -> [(text, source_tag, fingerprint)]
    
    # 1. 4-commentary XML
    print("\n--- 4-commentary XML ---")
    f4c = os.path.join(DOWNLOADS, "bhagavad_gita_4comm_gretil.xml")
    v4c = extract_from_4comm(f4c, "gretil_4comm")
    for ref, ws in v4c.items():
        all_witnesses[ref].extend(ws)
    print(f"  {len(v4c)} verse refs")
    
    # 2. Shankara XML
    print("\n--- Shankara XML ---")
    fsh = os.path.join(DOWNLOADS, "bhagavad_gita_shankara_gretil.xml")
    vsh = extract_from_xml(fsh, "gretil_shankara")
    for ref, ws in vsh.items():
        all_witnesses[ref].extend(ws)
    print(f"  {len(vsh)} verse refs")
    
    # 3. Comm XML (Shankara 1-17)
    print("\n--- Comm XML ---")
    fco = os.path.join(DOWNLOADS, "bhagavad_gita_comm_gretil.xml")
    vco = extract_from_xml(fco, "gretil_shankara_comm")
    for ref, ws in vco.items():
        all_witnesses[ref].extend(ws)
    print(f"  {len(vco)} verse refs")
    
    # 4. Bhaskara
    print("\n--- Bhaskara bhashya ---")
    fbs = os.path.join(DOWNLOADS, "bhaskara_gita_bhashya_gretil.xml")
    if os.path.exists(fbs):
        vbs = extract_from_xml(fbs, "gretil_bhaskara")
        for ref, ws in vbs.items():
            all_witnesses[ref].extend(ws)
        print(f"  {len(vbs)} verse refs")
    
    # 5. Ramanuja
    print("\n--- Ramanuja bhashya ---")
    frm = os.path.join(DOWNLOADS, "ramanuja_gita_bhashya_gretil.xml")
    if os.path.exists(frm):
        vrm = extract_from_xml(frm, "gretil_ramanuja")
        for ref, ws in vrm.items():
            all_witnesses[ref].extend(ws)
        print(f"  {len(vrm)} verse refs")
    
    # Deduplicate by source group (not individual source_tag)
    # Group by: base source (gretil_4comm, gretil_shankara, etc.)
    def get_base_source(tag):
        for prefix in ['gretil_4comm', 'gretil_shankara', 'gretil_ramanuja', 'gretil_bhaskara', 'gretil_shankara_comm']:
            if tag.startswith(prefix):
                return prefix
        return tag
    
    # Build clean witness list per verse
    clean_witnesses = {}
    for ref, ws in all_witnesses.items():
        by_source = defaultdict(list)
        for text, tag, fp in ws:
            base = get_base_source(tag)
            by_source[base].append((text, tag, fp))
        
        # For each source group, pick the best (first) reading
        deduped = []
        for base_src, readings in by_source.items():
            # Deduplicate within source by fingerprint
            seen_fps = set()
            for text, tag, fp in readings:
                if fp not in seen_fps:
                    deduped.append((text, base_src, tag, fp))
                    seen_fps.add(fp)
        
        clean_witnesses[ref] = deduped
    
    # Build expected list
    expected = []
    for ch in range(1, 19):
        for vs in range(1, EXPECTED[ch] + 1):
            expected.append(f"BG_{ch:02d}.{vs:03d}")
    
    # Build canonical verses and variant apparatus
    canonical = []
    apparatus = {}
    
    stats = {
        'total': 0, 'found': 0, 'missing': 0,
        'unanimous': 0, 'orthographic': 0, 'single_word': 0,
        'few_word': 0, 'textual': 0, 'major': 0, 'single_witness_only': 0
    }
    
    for ref in expected:
        ch = int(ref.split('_')[1].split('.')[0])
        vs = int(ref.split('.')[1])
        stats['total'] += 1
        
        if ref not in clean_witnesses:
            stats['missing'] += 1
            canonical.append({
                'chapter': ch, 'verse': vs, 'ref': ref,
                'text': None, 'source': None, 'witness_count': 0,
                'status': 'missing'
            })
            continue
        
        witnesses = clean_witnesses[ref]
        stats['found'] += 1
        
        # Select canonical reading (highest priority source)
        best_text = None
        best_src = None
        for text, base_src, tag, fp in witnesses:
            if best_src is None or source_priority.get(base_src, 99) < source_priority.get(best_src, 99):
                best_text = text
                best_src = base_src
        
        # Deduplicate by unique text
        unique_texts = {}
        for text, base_src, tag, fp in witnesses:
            norm = normalize_for_compare(text)
            if norm not in unique_texts:
                unique_texts[norm] = {'text': text, 'source': base_src, 'all_sources': []}
            unique_texts[norm]['all_sources'].append(base_src)
        
        witness_count = len(unique_texts)
        
        # Compare unique readings
        variants = []
        unique_list = list(unique_texts.values())
        
        if witness_count == 1:
            stats['single_witness_only'] += 1
            classification = 'single_witness'
            confidence = 0.70
        elif witness_count >= 2:
            classifications = []
            for i in range(len(unique_list)):
                for j in range(i+1, len(unique_list)):
                    c = classify_difference(unique_list[i]['text'], unique_list[j]['text'])
                    classifications.append(c)
                    if c != 'identical':
                        variants.append({
                            'reading_a': unique_list[i]['text'][:300],
                            'reading_b': unique_list[j]['text'][:300],
                            'source_a': unique_list[i]['source'],
                            'source_b': unique_list[j]['source'],
                            'classification': c
                        })
            
            if all(c == 'identical' for c in classifications):
                classification = 'unanimous'
                confidence = 0.95
                stats['unanimous'] += 1
            elif all(c in ('identical', 'orthographic') for c in classifications):
                classification = 'orthographic_variant'
                confidence = 0.90
                stats['orthographic'] += 1
            elif any(c == 'major_difference' for c in classifications):
                classification = 'major_difference'
                confidence = 0.60
                stats['major'] += 1
            elif any(c == 'textual_variant' for c in classifications):
                classification = 'textual_variant'
                confidence = 0.75
                stats['textual'] += 1
            elif any(c == 'few_word_variant' for c in classifications):
                classification = 'few_word_variant'
                confidence = 0.80
                stats['few_word'] += 1
            elif any(c == 'single_word_variant' for c in classifications):
                classification = 'single_word_variant'
                confidence = 0.85
                stats['single_word'] += 1
            else:
                classification = 'minor_variant'
                confidence = 0.80
        else:
            classification = 'unknown'
            confidence = 0.50
        
        canonical.append({
            'chapter': ch, 'verse': vs, 'ref': ref,
            'text': best_text, 'source': best_src,
            'witness_count': witness_count,
            'status': 'multi_witness' if witness_count > 1 else 'single_witness'
        })
        
        apparatus[ref] = {
            'ref': ref, 'chapter': ch, 'verse': vs,
            'canonical_text': best_text,
            'witness_count': witness_count,
            'unique_readings': [{'text': u['text'][:300], 'source': u['source'], 
                                'all_sources': u['all_sources']} for u in unique_list],
            'variants': variants,
            'classification': classification,
            'confidence': confidence
        }
    
    # Print results
    print(f"\n{'=' * 70}")
    print(f"COLLATION RESULTS")
    print(f"{'=' * 70}")
    print(f"Total expected: {stats['total']}")
    print(f"Found: {stats['found']}")
    print(f"Missing: {stats['missing']}")
    print(f"\nClassification:")
    print(f"  Unanimous: {stats['unanimous']}")
    print(f"  Orthographic only: {stats['orthographic']}")
    print(f"  Single-word variant: {stats['single_word']}")
    print(f"  Few-word variant: {stats['few_word']}")
    print(f"  Textual variant: {stats['textual']}")
    print(f"  Major difference: {stats['major']}")
    print(f"  Single witness only: {stats['single_witness_only']}")
    
    # Per-chapter
    print(f"\n{'Ch':<5}{'Exp':<6}{'Fnd':<6}{'Unan':<6}{'Orth':<6}{'1W':<5}{'FW':<5}{'Tex':<5}{'Maj':<5}{'Sing':<6}")
    print("-" * 54)
    for ch in range(1, 19):
        ch_app = {k: v for k, v in apparatus.items() if v['chapter'] == ch}
        n = len(ch_app)
        u = sum(1 for v in ch_app.values() if v['classification'] == 'unanimous')
        o = sum(1 for v in ch_app.values() if v['classification'] == 'orthographic_variant')
        s = sum(1 for v in ch_app.values() if v['classification'] == 'single_word_variant')
        f = sum(1 for v in ch_app.values() if v['classification'] == 'few_word_variant')
        t = sum(1 for v in ch_app.values() if v['classification'] == 'textual_variant')
        m = sum(1 for v in ch_app.values() if v['classification'] == 'major_difference')
        si = sum(1 for v in ch_app.values() if v['classification'] == 'single_witness')
        print(f"{ch:<5}{EXPECTED[ch]:<6}{n:<6}{u:<6}{o:<6}{s:<5}{f:<5}{t:<5}{m:<5}{si:<6}")
    
    # Show some textual variants
    tv = [(k, v) for k, v in apparatus.items() if v['classification'] in ('textual_variant', 'major_difference')]
    if tv:
        print(f"\n--- Textual Variants ({len(tv)} total) ---")
        for ref, v in tv[:15]:
            print(f"\n{ref} ({v['witness_count']} unique readings, {v['classification']}):")
            for r in v['unique_readings']:
                print(f"  [{r['source']}] {r['text'][:120]}...")
    
    # Save
    result = {
        'scripture': 'Bhagavadgita',
        'sources': ['gretil_4comm', 'gretil_shankara', 'gretil_shankara_comm', 'gretil_bhaskara', 'gretil_ramanuja'],
        'total': stats['total'],
        'found': stats['found'],
        'missing_count': stats['missing'],
        'completeness': round(stats['found'] / stats['total'] * 100, 1),
        'multi_witness': stats['found'] - stats['single_witness_only'],
        'single_witness': stats['single_witness_only'],
        'variant_stats': {k: v for k, v in stats.items() if k not in ('total', 'found', 'missing')},
        'missing_verses': [ref for ref in expected if ref not in clean_witnesses],
        'verses': canonical
    }
    
    outpath = os.path.join(DTC_BG, "verses_canonical_v2.json")
    with open(outpath, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    app_out = os.path.join(DTC_BG, "variant_apparatus.json")
    with open(app_out, 'w', encoding='utf-8') as f:
        json.dump({
            'scripture': 'Bhagavadgita',
            'stats': stats,
            'apparatus': apparatus
        }, f, ensure_ascii=False, indent=2)
    
    summary = {
        'scripture': 'Bhagavadgita',
        'analysis': 'Multi-witness collation v2',
        'witnesses': result['sources'],
        'total_verses': stats['total'],
        'found': stats['found'],
        'completeness': result['completeness'],
        'multi_witness': result['multi_witness'],
        'single_witness': result['single_witness'],
        'variant_stats': result['variant_stats'],
        'textual_variant_refs': [k for k, v in apparatus.items() if v['classification'] in ('textual_variant', 'major_difference')],
        'missing_verses': result['missing_verses']
    }
    
    sum_out = os.path.join(DTC_BG, "collation_summary_v2.json")
    with open(sum_out, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\nSaved: {outpath}")
    print(f"Saved: {app_out}")
    print(f"Saved: {sum_out}")


if __name__ == '__main__':
    main()
