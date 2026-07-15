#!/usr/bin/env python3
"""
Rigveda Verse Extraction v2 — Fixed text extraction using itertext().
"""

import json
import os
import re
import hashlib
import uuid
from xml.etree import ElementTree as ET

REPO = "/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage"
DOWNLOADS = os.path.join(REPO, "knowledge/downloads")
DTC_RV = os.path.join(REPO, "knowledge/dtc/rigveda")
NS = 'http://www.tei-c.org/ns/1.0'


def clean_vedic_text(text):
    """Remove Vedic accent marks while preserving text."""
    t = text
    # Remove combining accent marks (Unicode combining characters)
    t = re.sub(r'[\u0300-\u036f\u1DC0-\u1DFF\u20D0-\u20FF\uA69C-\uA69F]', '', t)
    # Remove specific Vedic marks
    t = re.sub(r'[̱̍̐̑]', '', t)
    # Normalize whitespace
    t = re.sub(r'\s+', ' ', t)
    return t.strip()


def extract_aufrecht(filepath):
    """Extract all verses from Aufrecht edition using itertext()."""
    verses = {}
    
    tree = ET.parse(filepath)
    root = tree.getroot()
    
    for lg in root.iter(f'{{{NS}}}lg'):
        xml_id = lg.get('{http://www.w3.org/XML/1998/namespace}id', '')
        m = re.match(r'RV_(\d+)\.(\d+)\.(\d+)', xml_id)
        if not m:
            continue
        
        mandala = int(m.group(1))
        sukta = int(m.group(2))
        verse = int(m.group(3))
        ref = f"RV_{mandala}.{sukta:03d}.{verse:02d}"
        
        lines = []
        for l in lg.findall(f'{{{NS}}}l'):
            # Use itertext to get ALL text including from child elements
            full_text = ''.join(l.itertext())
            full_text = clean_vedic_text(full_text)
            # Remove verse markers
            full_text = re.sub(r'\|\|?\s*$', '', full_text).strip()
            if full_text:
                lines.append(full_text)
        
        if lines:
            full_verse = ' | '.join(lines)
            fp = hashlib.sha256(full_verse.encode()).hexdigest()[:16]
            verses[ref] = {
                'ref': ref,
                'mandala': mandala,
                'sukta': sukta,
                'verse': verse,
                'text': full_verse,
                'text_clean': clean_vedic_text(full_verse),
                'source': 'aufrecht',
                'fingerprint': fp
            }
    
    return verses


def extract_khila(filepath):
    """Extract from Khila XML."""
    verses = {}
    
    tree = ET.parse(filepath)
    root = tree.getroot()
    
    for lg in root.iter(f'{{{NS}}}lg'):
        xml_id = lg.get('{http://www.w3.org/XML/1998/namespace}id', '')
        m = re.match(r'RvKh_(\d+)\.(\d+)\.(\d+)', xml_id)
        if not m:
            continue
        
        km = int(m.group(1))
        ks = int(m.group(2))
        kv = int(m.group(3))
        ref = f"RVKh_{km}.{ks:03d}.{kv:02d}"
        
        lines = []
        for l in lg.findall(f'{{{NS}}}l'):
            if l.text:
                text = l.text.strip()
                text = re.sub(r'\s+', ' ', text)
                if text:
                    lines.append(text)
        
        if lines:
            full = ' | '.join(lines)
            verses[ref] = {
                'ref': ref,
                'mandala': km,
                'sukta': ks,
                'verse': kv,
                'text': full,
                'source': 'khila',
                'fingerprint': hashlib.sha256(full.encode()).hexdigest()[:16]
            }
    
    return verses


def extract_vedaweb(book_path):
    """Extract VedaWeb verses (Lubotsky + VNH)."""
    verses = {}
    
    tree = ET.parse(book_path)
    root = tree.getroot()
    
    for stanza in root.iter(f'{{{NS}}}div'):
        xml_id = stanza.get('{http://www.w3.org/XML/1998/namespace}id', '')
        if stanza.get('type') != 'stanza':
            continue
        
        m = re.match(r'b(\d+)_h(\d+)_(\d+)', xml_id)
        if not m:
            continue
        
        book = int(m.group(1))
        hymn = int(m.group(2))
        verse = int(m.group(3))
        ref = f"RV_{book}.{hymn:03d}.{verse:02d}"
        
        for lg in stanza.findall(f'{{{NS}}}lg'):
            lg_id = lg.get('{http://www.w3.org/XML/1998/namespace}id', '')
            source = 'unknown'
            if 'lubotsky' in lg_id:
                source = 'lubotsky'
            elif 'vnh' in lg_id:
                source = 'vnh'
            else:
                continue
            
            padas = {}
            for l in lg.findall(f'{{{NS}}}l'):
                l_id = l.get('{http://www.w3.org/XML/1998/namespace}id', '')
                if '_tokens' in l_id:
                    continue
                if l.text:
                    text = l.text.strip()
                    pada_match = re.search(r'_([abcd])$', l_id)
                    if pada_match:
                        padas[pada_match.group(1)] = text
            
            if padas:
                full = ' | '.join(padas.get(p, '') for p in ['a', 'b', 'c', 'd'] if p in padas)
                full = re.sub(r'\s+', ' ', full).strip()
                if full:
                    if ref not in verses:
                        verses[ref] = {}
                    verses[ref][source] = {
                        'text': full,
                        'text_clean': clean_vedic_text(full),
                        'fingerprint': hashlib.sha256(full.encode()).hexdigest()[:16]
                    }
    
    return verses


def main():
    print("=" * 70)
    print("RIGVEDA EXTRACTION v2 — Fixed text extraction")
    print("=" * 70)
    
    # 1. Aufrecht
    print("\n--- Aufrecht Edition ---")
    auf_path = os.path.join(DOWNLOADS, "rigveda_aufrecht_gretil.xml")
    auf = extract_aufrecht(auf_path)
    print(f"  Extracted {len(auf)} verses")
    
    # Show sample
    sample = auf.get('RV_1.001.01', {})
    print(f"  Sample RV_1.001.01: {sample.get('text', 'N/A')[:100]}")
    
    # 2. VedaWeb
    print("\n--- VedaWeb ---")
    vw_dir = os.path.join(DOWNLOADS, "vedaweb/cceh-c-salt_vedaweb_tei-f975755")
    vw_all = {}
    for book in range(1, 11):
        bp = os.path.join(vw_dir, f"rv_book_{book:02d}.tei")
        if os.path.exists(bp):
            vw = extract_vedaweb(bp)
            vw_all.update(vw)
    print(f"  Extracted {len(vw_all)} verses")
    
    # Source counts
    vw_sources = {}
    for v in vw_all.values():
        for s in v:
            vw_sources[s] = vw_sources.get(s, 0) + 1
    for s, c in vw_sources.items():
        print(f"    {s}: {c} verses")
    
    # 3. Khilas
    print("\n--- Khilas ---")
    kh_path = os.path.join(DOWNLOADS, "rigveda_khila_gretil.xml")
    kh = extract_khila(kh_path)
    print(f"  Extracted {len(kh)} khila verses")
    
    # Compare sources
    print("\n--- Cross-source comparison ---")
    
    # Aufrecht vs VNH
    auf_match = 0
    auf_diff = 0
    for ref, auf_data in auf.items():
        if ref in vw_all and 'vnh' in vw_all[ref]:
            auf_clean = auf_data['text_clean']
            vnh_clean = vw_all[ref]['vnh']['text_clean']
            if auf_clean == vnh_clean:
                auf_match += 1
            else:
                auf_diff += 1
                if auf_diff <= 3:
                    print(f"  DIFF {ref}:")
                    print(f"    Aufrecht: {auf_clean[:80]}")
                    print(f"    VNH:      {vnh_clean[:80]}")
    print(f"Aufrecht vs VNH: {auf_match} identical, {auf_diff} different")
    
    # Aufrecht vs Lubotsky
    lub_match = 0
    lub_diff = 0
    for ref, auf_data in auf.items():
        if ref in vw_all and 'lubotsky' in vw_all[ref]:
            auf_clean = auf_data['text_clean']
            lub_clean = vw_all[ref]['lubotsky']['text_clean']
            if auf_clean == lub_clean:
                lub_match += 1
            else:
                lub_diff += 1
                if lub_diff <= 3:
                    print(f"  DIFF {ref}:")
                    print(f"    Aufrecht: {auf_clean[:80]}")
                    print(f"    Lubotsky: {lub_clean[:80]}")
    print(f"Aufrecht vs Lubotsky: {lub_match} identical, {lub_diff} different")
    
    # Build canonical units with multi-witness data
    print("\n--- Building multi-witness canonical units ---")
    units = []
    for ref in sorted(auf.keys()):
        auf_data = auf[ref]
        witnesses = {'aufrecht': auf_data['text_clean']}
        
        if ref in vw_all:
            for src in ['lubotsky', 'vnh']:
                if src in vw_all[ref]:
                    witnesses[src] = vw_all[ref][src]['text_clean']
        
        # Deduplicate by normalized text
        unique = {}
        for src, text in witnesses.items():
            norm = re.sub(r'\s+', ' ', text).strip()
            if norm not in unique:
                unique[norm] = []
            unique[norm].append(src)
        
        wc = len(unique)
        if wc >= 3:
            status = 'verified_strong'
            conf = 0.95
        elif wc >= 2:
            status = 'verified'
            conf = 0.88
        else:
            status = 'single_witness'
            conf = 0.70
        
        # Canonical reading (prefer Aufrecht)
        canon = witnesses.get('aufrecht', list(witnesses.values())[0])
        
        units.append({
            'uuid': str(uuid.uuid4()),
            'canonical_ref': ref,
            'scripture': 'Ṛgveda-Saṃhitā',
            'mandala': auf_data['mandala'],
            'sukta': auf_data['sukta'],
            'verse': auf_data['verse'],
            'type': 'verse',
            'text': canon,
            'source': 'aufrecht',
            'witness_count': wc,
            'witnesses': list(witnesses.keys()),
            'unique_readings': wc,
            'status': status,
            'confidence': conf
        })
    
    # Add khila units
    for ref in sorted(kh.keys()):
        v = kh[ref]
        units.append({
            'uuid': str(uuid.uuid4()),
            'canonical_ref': ref,
            'scripture': 'Ṛgveda-Saṃhitā (Khila)',
            'mandala': v['mandala'],
            'sukta': v['sukta'],
            'verse': v['verse'],
            'type': 'khila_verse',
            'text': v['text'],
            'source': 'khila_gretil',
            'witness_count': 1,
            'witnesses': ['khila_gretil'],
            'status': 'single_witness',
            'confidence': 0.65
        })
    
    # Stats
    vs = sum(1 for u in units if u['status'] == 'verified_strong')
    v = sum(1 for u in units if u['status'] == 'verified')
    sw = sum(1 for u in units if u['status'] == 'single_witness')
    
    print(f"\nTotal units: {len(units)}")
    print(f"  Verified strong (3+ unique readings): {vs}")
    print(f"  Verified (2 unique readings): {v}")
    print(f"  Single witness: {sw}")
    
    # Save
    registry = {
        'scripture': 'Ṛgveda-Saṃhitā',
        'total_units': len(units),
        'samhita_verses': len(auf),
        'khila_verses': len(kh),
        'mandalas': 10,
        'verification_stats': {
            'verified_strong': vs,
            'verified': v,
            'single_witness': sw,
            'unverified': 0
        },
        'witnesses_used': ['aufrecht_gretil', 'vedaweb_lubotsky', 'vedaweb_vnh', 'khila_gretil'],
        'units': units
    }
    
    out_path = os.path.join(DTC_RV, "canonical_units_v2.json")
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)
    print(f"\nSaved: {out_path}")
    
    # Update summary
    summary = {
        'scripture': 'Ṛgveda-Saṃhitā',
        'samhita_verses': len(auf),
        'khila_verses': len(kh),
        'total': len(units),
        'sources': ['aufrecht_gretil', 'vedaweb_lubotsky', 'vedaweb_vnh'],
        'multi_witness': v + vs,
        'single_witness': sw,
        'aufrecht_vs_vnh_identical': auf_match,
        'aufrecht_vs_vnh_different': auf_diff,
        'aufrecht_vs_lubotsky_identical': lub_match,
        'aufrecht_vs_lubotsky_different': lub_diff
    }
    
    sum_path = os.path.join(DTC_RV, "extraction_summary_v2.json")
    with open(sum_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"Saved: {sum_path}")


if __name__ == '__main__':
    main()
