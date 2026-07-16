#!/usr/bin/env python3
"""
Phase 4: CUID Generation for All Scriptures
Build canonical unit IDs for every scripture with available witnesses.
"""
import json
import os
import re
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).parent.parent
DTC_DIR = BASE / 'knowledge' / 'dtc'
DOWNLOAD_DIR = BASE / 'knowledge' / 'downloads'
GREtil_DIR = BASE / 'knowledge' / 'gretil_parsed'
CUID_DIR = DTC_DIR / 'cuid_sets'
CUID_DIR.mkdir(parents=True, exist_ok=True)

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def extract_rv_from_gretil():
    """Extract Rigveda CUIDs from the GRETIL Aufrecht source."""
    # Load the IAST text
    iast_path = GREtil_DIR / 'rigveda_aufrecht_gretil_iast.txt'
    deva_path = GREtil_DIR / 'rigveda_aufrecht_gretil_devanagari.txt'
    
    cuids = {}
    
    if not iast_path.exists():
        print("  Aufrecht IAST not found, trying XML...")
        return extract_rv_from_xml()
    
    # Parse the structured text - look for mandala/sukta/verse patterns
    with open(iast_path, 'r', errors='replace') as f:
        content = f.read()
    
    with open(deva_path, 'r', errors='replace') as f:
        deva_content = f.read()
    
    iast_lines = [l for l in content.split('\n') if l.strip()]
    deva_lines = [l for l in deva_content.split('\n') if l.strip()]
    
    # Track state
    current_mandala = 1
    current_sukta = 1
    verse_counter = 0
    
    for i, line in enumerate(iast_lines):
        # Detect mandala boundaries
        mandala_match = re.match(r'^(?:mandala|MaNDala)\s+(\d+)', line, re.IGNORECASE)
        if mandala_match:
            current_mandala = int(mandala_match.group(1))
            current_sukta = 1
            verse_counter = 0
            continue
        
        # Detect sukta boundaries
        sukta_match = re.match(r'^(?:sukta|sUkta)\s+(\d+)', line, re.IGNORECASE)
        if sukta_match:
            current_sukta = int(sukta_match.group(1))
            verse_counter = 0
            continue
        
        # Skip empty/header lines
        if len(line.strip()) < 10:
            continue
        
        verse_counter += 1
        cuid = f"RV.{current_mandala}.{current_sukta}.{verse_counter}"
        
        deva_line = deva_lines[i] if i < len(deva_lines) else ""
        
        cuids[cuid] = {
            'cuid': cuid,
            'iast': line.strip(),
            'devanagari': deva_line.strip() if deva_line else '',
            'mandala': current_mandala,
            'sukta': current_sukta,
            'verse': verse_counter,
            'witness': 'F-AUFRECHT-GRETIL',
        }
    
    return cuids


def extract_rv_from_xml():
    """Extract Rigveda CUIDs from the XML source."""
    xml_path = DOWNLOAD_DIR / 'rigveda_aufrecht_gretil.xml'
    if not xml_path.exists():
        print("  XML not found")
        return {}
    
    from lxml import etree
    try:
        tree = etree.parse(str(xml_path))
        root = tree.getroot()
    except Exception as e:
        print(f"  XML parse error: {e}")
        return {}
    
    # Get namespace
    ns = {}
    if root.tag.startswith('{'):
        ns_uri = root.tag.split('}')[0][1:]
        ns['tei'] = ns_uri
    
    ns_prefix = f'{{{ns.get("tei", "")}}}' if ns else ''
    
    cuids = {}
    current_mandala = 1
    current_sukta = 1
    
    # Try to find all div elements
    for elem in root.iter(f'{ns_prefix}div', f'div'):
        div_type = elem.get('type', '')
        div_n = elem.get('n', '')
        
        if div_type == 'mandala' or div_type == 'book':
            current_mandala = int(div_n) if div_n.isdigit() else current_mandala
            current_sukta = 1
        elif div_type == 'sukta':
            current_sukta = int(div_n) if div_n.isdigit() else current_sukta
    
    # Find verses (lg elements or l elements)
    verse_count = 0
    for elem in root.iter(f'{ns_prefix}lg', 'lg', f'{ns_prefix}l', 'l'):
        text_parts = []
        for child in elem:
            if child.text:
                text_parts.append(child.text)
            if child.tail:
                text_parts.append(child.tail)
        text = ''.join(text_parts).strip()
        
        verse_n = elem.get('n', '')
        if verse_n and verse_n.isdigit():
            verse_num = int(verse_n)
        else:
            verse_count += 1
            verse_num = verse_count
        
        if text:
            cuid = f"RV.{current_mandala}.{current_sukta}.{verse_num}"
            if cuid not in cuids:
                cuids[cuid] = {
                    'cuid': cuid,
                    'text': text,
                    'mandala': current_mandala,
                    'sukta': current_sukta,
                    'verse': verse_num,
                    'witness': 'F-AUFRECHT-XML',
                }
    
    return cuids


def extract_bg_cuids():
    """Extract Bhagavad Gita CUIDs from available sources."""
    cuids = {}
    
    # Try Gita Press OCR first (we know it has 1251 verses)
    gp_path = BASE / 'knowledge' / 'dtc' / 'bg_gitapress' / 'bg_gitapress_ocr_verses.json'
    if gp_path.exists():
        with open(gp_path) as f:
            gp_data = json.load(f)
        
        for verse in gp_data.get('verses', []):
            chapter = verse.get('chapter', 0)
            verse_num = verse.get('verse', 0)
            text = verse.get('text', '')
            cuid = f"BG.{chapter}.{verse_num}"
            if cuid not in cuids:
                cuids[cuid] = {
                    'cuid': cuid,
                    'text': text,
                    'chapter': chapter,
                    'verse': verse_num,
                    'witness': 'F-GITAPRESS',
                }
    
    # Try GRETIL Gita sources
    for suffix in ['bhagavad_gita_4comm', 'bhagavad_gita_shankara']:
        iast_path = GREtil_DIR / f'{suffix}_gretil_iast.txt'
        if not iast_path.exists():
            continue
        
        with open(iast_path, 'r', errors='replace') as f:
            content = f.read()
        
        # For commentaries, extract verse text (skip commentary)
        # Simple heuristic: lines that look like verse (short, no commentary markers)
        lines = [l.strip() for l in content.split('\n') if l.strip()]
        
        # Try to find chapter markers
        current_chapter = 0
        verse_counter = 0
        
        for line in lines:
            # Detect chapter markers
            chap_match = re.match(r'^(?:AdhyAya|chapter|sarga)\s+(\d+)', line, re.IGNORECASE)
            if chap_match:
                current_chapter = int(chap_match.group(1))
                verse_counter = 0
                continue
            
            if current_chapter == 0:
                # Try to detect from verse numbering
                verse_match = re.match(r'^(\d+)\.\.(\d+)\.\.(\d+)', line)
                if verse_match:
                    current_chapter = int(verse_match.group(1))
                    verse_counter = 0
            
            if current_chapter > 0 and len(line) > 20 and len(line) < 300:
                verse_counter += 1
                cuid = f"BG.{current_chapter}.{verse_counter}"
                if cuid not in cuids:
                    cuids[cuid] = {
                        'cuid': cuid,
                        'iast': line,
                        'chapter': current_chapter,
                        'verse': verse_counter,
                        'witness': f'F-GRETIL-{suffix}',
                    }
    
    return cuids


def extract_generic_cuids(scripture_id, gretil_name):
    """Extract CUIDs for any scripture from its GRETIL source."""
    iast_path = GREtil_DIR / f'{gretil_name}_gretil_iast.txt'
    deva_path = GREtil_DIR / f'{gretil_name}_gretil_devanagari.txt'
    struct_path = GREtil_DIR / f'{gretil_name}_gretil_structure.json'
    
    if not iast_path.exists():
        return {}
    
    # Load structure if available
    structure = {}
    if struct_path.exists():
        try:
            with open(struct_path) as f:
                structure = json.load(f)
        except:
            pass
    
    with open(iast_path, 'r', errors='replace') as f:
        iast_content = f.read()
    
    with open(deva_path, 'r', errors='replace') as f:
        deva_content = f.read()
    
    iast_lines = [l for l in iast_content.split('\n') if l.strip()]
    deva_lines = [l for l in deva_content.split('\n') if l.strip()]
    
    cuids = {}
    
    # If structure JSON has chapter/verse info, use it
    if structure and isinstance(structure, dict):
        chapters = structure.get('chapters', structure.get('sections', []))
        if isinstance(chapters, list):
            for ch in chapters:
                ch_num = ch.get('number', ch.get('n', 0))
                verses = ch.get('verses', ch.get('lines', []))
                if isinstance(verses, list):
                    for v in verses:
                        v_num = v.get('number', v.get('n', 0))
                        text = v.get('text', v.get('iast', ''))
                        cuid = f"{scripture_id}.{ch_num}.{v_num}"
                        if text:
                            cuids[cuid] = {
                                'cuid': cuid,
                                'text': text,
                                'chapter': ch_num,
                                'verse': v_num,
                                'witness': f'F-GRETIL-{gretil_name}',
                            }
    
    # Fallback: enumerate all lines with sequential numbering
    if not cuids:
        current_section = 1
        verse_counter = 0
        
        for i, line in enumerate(iast_lines):
            # Detect section/chapter markers
            if len(line) < 15:
                section_match = re.match(r'^(?:sarga|adhyAya|prashna|khanda|patala)\s+(\d+)', line, re.IGNORECASE)
                if section_match:
                    current_section = int(section_match.group(1))
                    verse_counter = 0
                    continue
            
            verse_counter += 1
            deva_line = deva_lines[i] if i < len(deva_lines) else ""
            
            cuid = f"{scripture_id}.{current_section}.{verse_counter}"
            cuids[cuid] = {
                'cuid': cuid,
                'iast': line.strip(),
                'devanagari': deva_line.strip() if deva_line else '',
                'section': current_section,
                'verse': verse_counter,
                'witness': f'F-GRETIL-{gretil_name}',
            }
    
    return cuids


def main():
    print("=" * 70)
    print("PHASE 4: CRITICAL EXTRACTION & CUID GENERATION")
    print("=" * 70)
    
    # Scripture -> GRETIL text name mapping
    SCRIPTURE_GREIL_MAP = {
        'RV': ['rigveda_aufrecht', 'rigveda_padapatha', 'rigveda_khila'],
        'BG': ['bhagavad_gita_4comm', 'bhagavad_gita_shankara', 'madhva_gita_bhashya', 'ramanuja_gita_bhashya', 'bhaskara_gita_bhashya'],
        'SV': ['samaveda'],
        'AV': ['atharva_prayashchittani', 'atharvashiras_upanishad', 'atharvaveda_parisista'],
        'HV': ['harivamsa', 'harivamsa_app1'],
        'RM': ['ramayana'],
        'AGNI': ['agni_puran'],
        'BRAH': ['brahma_puran'],
        'BHAG': ['bhagavata'],
        'GARUDA': ['garuda_puran'],
        'KURM': ['kurma_puran'],
        'LING': ['linga_puran'],
        'MARK': ['markandeya_puran'],
        'NARADA': ['narada_puran'],
        'MATS': ['matsya_puran'],
        'SHIV': ['shiva_puran'],
        'SKAND': ['skanda_puran_revakhanda'],
        'VAMAN': ['vamana_puran', 'vamana_puran_saromahatmya'],
        'VISH': ['vishnu_puran'],
        'VYU': ['revakhanda_vayu_puran'],
        'DEVI': ['devi_gita'],
        'AITAREYA': ['aitareya_upanishad'],
        'ISHA': ['isha_upanishad'],
        'SHVET': ['shvetashvatara_upanishad'],
        'TAITT': ['taittiriya_upanishad_bhashya'],
        'MANU': ['manusmriti'],
        'NARADA_SM': ['narada_smriti'],
        'VISHNU_SM': ['vishnu_smriti', 'ramanuja_vedartha'],
        'YAJNAV': ['yajnavalkya_smriti'],
        'APASTAMBA_DS': ['apastamba_dharmasutra', 'apastamba_grihya_sutra'],
        'BAUDHAYANA_DS': ['baudhayana_dharmasutra'],
        'GAUTAMA_DS': ['gautama_dharmasutra', 'gautama_dharmasutra_1_3_comm'],
        'YOGA_SUTRA': ['yoga_sutra', 'yoga_sutra_bhasya'],
    }
    
    all_cuids = {}
    summary = {}
    
    for scripture_id, gretil_names in SCRIPTURE_GREIL_MAP.items():
        scripture_cuids = {}
        
        for gretil_name in gretil_names:
            if scripture_id == 'RV' and gretil_name == 'rigveda_aufrecht':
                # Use specialized RV extractor
                extracted = extract_rv_from_gretil()
            else:
                extracted = extract_generic_cuids(scripture_id, gretil_name)
            
            scripture_cuids.update(extracted)
        
        all_cuids[scripture_id] = scripture_cuids
        summary[scripture_id] = len(scripture_cuids)
        
        # Save per-scripture CUIDs
        save_json(CUID_DIR / f'{scripture_id}_cuids.json', scripture_cuids)
        print(f"  {scripture_id}: {len(scripture_cuids)} CUIDs generated")
    
    # Save combined CUIDs
    save_json(CUID_DIR / 'all_cuids.json', all_cuids)
    
    # Summary
    total = sum(summary.values())
    print(f"\n{'='*70}")
    print(f"TOTAL CUIDs GENERATED: {total}")
    print(f"Scriptures with CUIDs: {len(summary)}")
    print(f"CUIDs saved to: {CUID_DIR}")
    
    # Coverage analysis
    print(f"\n{'='*70}")
    print("COVERAGE ANALYSIS")
    print(f"{'='*70}")
    
    for sid in sorted(summary.keys()):
        count = summary[sid]
        # Expected counts from scripture canon
        EXPECTED = {
            'RV': 10600, 'SV': 1875, 'AV': 6000,
            'BG': 700, 'MBH': 100000, 'RM': 24000,
            'BHAG': 18000, 'SHIV': 24000,
        }
        expected = EXPECTED.get(sid, 1000)
        pct = min(100, (count / expected) * 100) if expected > 0 else 0
        print(f"  {sid:15s} {count:7d} CUIDs / ~{expected:6d} expected ({pct:.1f}%)")

if __name__ == '__main__':
    main()
