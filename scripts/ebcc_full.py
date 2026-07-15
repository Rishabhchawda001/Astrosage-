#!/usr/bin/env python3
"""
EBCC Full Verification — Compare all GRETIL XML against extracted AKUs.
Handles both <div>-wrapped and direct <p> XML structures.
"""

import json
import os
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter

TEI_NS = 'http://www.tei-c.org/ns/1.0'
NS = {'tei': TEI_NS}


def normalize_text(text):
    text = unicodedata.normalize('NFC', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def strip_ref_markers(text):
    text = re.sub(r'^[A-Z]\w+\d+[\d.,\-/]*\s*/\s*', '', text)
    text = re.sub(r'//\w+_\d+\.\d+//', '', text)
    text = re.sub(r'\([A-Z]\w+_\d+[\d.,\-/]*\)', '', text)
    return text.strip()


def extract_text_from_element(el):
    """Extract all text from an element including children."""
    parts = []
    if el.text:
        parts.append(el.text)
    for child in el:
        if child.text:
            parts.append(child.text)
        if child.tail:
            parts.append(child.tail)
    return ' '.join(parts).strip()


def extract_xml_units(xml_path):
    """Extract text units from TEI XML, handling both div-wrapped and direct-p structures."""
    try:
        tree = ET.parse(xml_path)
    except ET.ParseError as e:
        return [], {'error': str(e)}
    
    root = tree.getroot()
    body = root.find('.//tei:body', NS)
    if body is None:
        return [], {'error': 'no body element'}
    
    # Extract metadata
    title_el = root.find('.//tei:titleStmt/tei:title', NS)
    title = title_el.text.strip() if title_el is not None and title_el.text else ''
    
    editor_els = root.findall('.//tei:respStmt/tei:name', NS)
    editors = [e.text.strip() for e in editor_els if e.text]
    
    source_el = root.find('.//tei:sourceDesc/tei:bibl', NS)
    source = source_el.text.strip() if source_el is not None and source_el.text else ''
    
    units = []
    
    # Collect all <p>, <l>, <lg> elements from body
    # Strategy: find them whether they're in <div> or direct under <body>
    elements_to_process = []
    
    for child in body:
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        
        if tag == 'div':
            # Process div's children
            for gc in child:
                gc_tag = gc.tag.split('}')[-1] if '}' in gc.tag else gc.tag
                if gc_tag in ('p', 'l', 'lg'):
                    elements_to_process.append(gc)
        elif tag in ('p', 'l', 'lg'):
            elements_to_process.append(child)
    
    for el in elements_to_process:
        tag = el.tag.split('}')[-1] if '}' in el.tag else el.tag
        
        if tag == 'p':
            raw_text = extract_text_from_element(el)
            
            ref_match = re.match(r'^([A-Z]\w+\d+[\d.,\-/]*)\s*/\s*', raw_text)
            ref = ref_match.group(1) if ref_match else None
            if ref_match:
                raw_text = raw_text[ref_match.end():]
            
            norm = normalize_text(raw_text)
            clean = normalize_text(strip_ref_markers(raw_text))
            
            if norm and len(clean) > 0:
                units.append({
                    'ref': ref,
                    'norm': norm,
                    'clean': clean,
                })
        
        elif tag == 'lg':
            for line in el.findall('tei:l', NS):
                raw_text = extract_text_from_element(line)
                n = line.get('n', '')
                norm = normalize_text(raw_text)
                if norm:
                    units.append({
                        'ref': n or None,
                        'norm': norm,
                        'clean': normalize_text(strip_ref_markers(raw_text)),
                    })
        
        elif tag == 'l':
            raw_text = extract_text_from_element(el)
            n = el.get('n', '')
            norm = normalize_text(raw_text)
            if norm:
                units.append({
                    'ref': n or None,
                    'norm': norm,
                    'clean': normalize_text(strip_ref_markers(raw_text)),
                })
    
    meta = {
        'title': title,
        'editors': editors,
        'source': source,
        'unit_count': len(units),
    }
    
    return units, meta


def load_aku_units(aku_path):
    with open(aku_path) as f:
        data = json.load(f)
    
    units = []
    for ch in data.get('chapters', []):
        ch_num = ch.get('chapter_num', 0)
        for aku in ch.get('akus', []):
            body = (aku.get('body') or '').strip()
            ref = aku.get('ref')
            norm = normalize_text(body)
            if norm:
                units.append({
                    'ref': ref,
                    'norm': norm,
                    'clean': normalize_text(strip_ref_markers(body)),
                    'chapter': ch_num,
                })
    return units


def verify_scripture(xml_path, aku_path):
    xml_units, xml_meta = extract_xml_units(xml_path)
    aku_units = load_aku_units(aku_path)
    
    if not xml_units:
        return {
            'status': 'error',
            'error': xml_meta.get('error', 'no XML units'),
            'title': xml_meta.get('title', ''),
        }
    
    # Match using clean text
    exact = 0
    contained = 0
    xml_matched = set()
    aku_matched = set()
    
    # Exact match
    for i, x in enumerate(xml_units):
        for j, a in enumerate(aku_units):
            if j not in aku_matched and x['clean'] == a['clean']:
                exact += 1
                xml_matched.add(i)
                aku_matched.add(j)
                break
    
    # Substring containment
    for i, x in enumerate(xml_units):
        if i in xml_matched:
            continue
        for j, a in enumerate(aku_units):
            if j in aku_matched:
                continue
            if x['clean'] and a['clean']:
                if x['clean'] in a['clean'] or a['clean'] in x['clean']:
                    contained += 1
                    xml_matched.add(i)
                    aku_matched.add(j)
                    break
    
    xml_unmatched = [xml_units[i] for i in range(len(xml_units)) if i not in xml_matched]
    aku_unmatched = [aku_units[j] for j in range(len(aku_units)) if j not in aku_matched]
    
    verified = exact + contained
    total_xml = len(xml_units)
    coverage = 100 * verified / max(total_xml, 1)
    
    return {
        'status': 'verified' if coverage > 95 else 'mostly_verified' if coverage > 80 else 'needs_review',
        'title': xml_meta.get('title', ''),
        'editors': xml_meta.get('editors', []),
        'source': xml_meta.get('source', ''),
        'xml_units': total_xml,
        'aku_units': len(aku_units),
        'exact_matches': exact,
        'substring_matches': contained,
        'verified': verified,
        'coverage': round(coverage, 1),
        'xml_unmatched_count': len(xml_unmatched),
        'aku_unmatched_count': len(aku_unmatched),
        'xml_unmatched_samples': [{'ref': u['ref'], 'text': u['clean'][:80]} for u in xml_unmatched[:5]],
        'aku_unmatched_samples': [{'ref': u['ref'], 'text': u['clean'][:80]} for u in aku_unmatched[:5]],
    }


def main():
    xml_dir = 'knowledge/downloads'
    aku_dir = 'knowledge/cuv/gretil_prose_clean'
    output_file = 'knowledge/cuv/ebcc_results.json'
    
    results = []
    total_xml = 0
    total_verified = 0
    
    for xml_fn in sorted(os.listdir(xml_dir)):
        if not xml_fn.endswith('.xml'):
            continue
        
        base = xml_fn.replace('_gretil.xml', '').replace('.xml', '')
        aku_fn = f'{base}_gretil_prose.json'
        aku_path = os.path.join(aku_dir, aku_fn)
        
        if not os.path.exists(aku_path):
            continue
        
        xml_path = os.path.join(xml_dir, xml_fn)
        result = verify_scripture(xml_path, aku_path)
        result['xml_file'] = xml_fn
        result['aku_file'] = aku_fn
        results.append(result)
        
        total_xml += result.get('xml_units', 0)
        total_verified += result.get('verified', 0)
        
        status = result['status']
        coverage = result.get('coverage', 0)
        title = result.get('title', '')[:45]
        print(f"  [{status:18s}] {coverage:5.1f}% {title}")
    
    print(f"\n{'='*60}")
    print(f"EBCC VERIFICATION SUMMARY")
    print(f"{'='*60}")
    print(f"Scriptures verified: {len(results)}")
    print(f"Total XML units: {total_xml}")
    print(f"Total verified: {total_verified} ({100*total_verified/max(total_xml,1):.1f}%)")
    
    status_counts = Counter(r['status'] for r in results)
    print(f"\nStatus distribution:")
    for s, c in status_counts.most_common():
        print(f"  {s:20s} {c:4d}")
    
    os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump({
            'total_scriptures': len(results),
            'total_xml_units': total_xml,
            'total_verified': total_verified,
            'overall_coverage': round(100 * total_verified / max(total_xml, 1), 1),
            'results': results,
        }, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to: {output_file}")


if __name__ == '__main__':
    main()
