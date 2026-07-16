#!/usr/bin/env python3
"""
Phase 4: Universal Witness Census Builder
Maps every on-disk resource to scripture canon and builds witness families.
"""
import json
import os
import hashlib
import re
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent
GREtil_DIR = BASE / 'knowledge' / 'gretil_parsed'
DOWNLOADS_DIR = BASE / 'knowledge' / 'downloads'
DTC_DIR = BASE / 'knowledge' / 'dtc'
CONFIG_DIR = DTC_DIR / 'config'

def load_json(path):
    with open(path) as f:
        return json.load(f)

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def file_hash(path, chunk_size=65536):
    h = hashlib.sha256()
    try:
        with open(path, 'rb') as f:
            while True:
                data = f.read(chunk_size)
                if not data:
                    break
                h.update(data)
        return h.hexdigest()[:16]
    except:
        return None

def count_lines(path):
    try:
        with open(path, 'r', errors='replace') as f:
            return sum(1 for _ in f)
    except:
        return 0

def count_nonempty_lines(path):
    try:
        with open(path, 'r', errors='replace') as f:
            return sum(1 for line in f if line.strip())
    except:
        return 0

def detect_script(text_sample):
    """Detect if text is Devanagari, IAST, or mixed."""
    devanagari_chars = sum(1 for c in text_sample if '\u0900' <= c <= '\u097F')
    latin_chars = sum(1 for c in text_sample if c.isalpha() and ord(c) < 128)
    total = max(devanagari_chars + latin_chars, 1)
    deva_pct = devanagari_chars / total
    if deva_pct > 0.3:
        return 'Devanagari'
    elif deva_pct < 0.05 and latin_chars > 10:
        return 'IAST'
    else:
        return 'mixed'

def detect_encoding(path):
    """Check if file is valid UTF-8 with proper Sanskrit characters."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read(10000)
        
        # Check for replacement characters
        has_replacement = '\ufffd' in content
        has_devanagari = any('\u0900' <= c <= '\u097F' for c in content)
        has_iast = bool(re.search(r'[āīūṛṝḷḹṃḥṣśṇṭḍñḥḥ]', content))
        has_accents = bool(re.search(r'[àáâãäåèéêëìíîïòóôõöùúûü]', content))
        
        return {
            'valid_utf8': True,
            'has_replacement': has_replacement,
            'has_devanagari': has_devanagari,
            'has_iast': has_iast,
            'has_accents': has_accents,
        }
    except:
        return {'valid_utf8': False, 'has_replacement': False, 'has_devanagari': False, 'has_iast': False, 'has_accents': False}

# Explicit mapping: GRETIL text name -> scripture ID
GREtil_MAP = {
    'rigveda_aufrecht': 'RV',
    'rigveda_padapatha': 'RV',
    'rigveda_khila': 'RV',
    'samaveda': 'SV',
    'atharva_prayashchittani': 'AV',
    'atharvashiras_upanishad': 'AV',
    'atharvaveda_parisista': 'AV',
    'bhagavad_gita_4comm': 'BG',
    'bhagavad_gita_shankara': 'BG',
    'madhva_gita_bhashya': 'BG',
    'ramanuja_gita_bhashya': 'BG',
    'bhaskara_gita_bhashya': 'BG',
    'harivamsa': 'HV',
    'harivamsa_app1': 'HV',
    'ramayana': 'RM',
    'agni_puran': 'AGNI',
    'brahma_puran': 'BRAH',
    'bhagavata': 'BHAG',
    'garuda_puran': 'GARUDA',
    'kurma_puran': 'KURM',
    'linga_puran': 'LING',
    'markandeya_puran': 'MARK',
    'narada_puran': 'NARADA',
    'matsya_puran': 'MATS',
    'shiva_puran': 'SHIV',
    'skanda_puran_revakhanda': 'SKAND',
    'vamana_puran': 'VAMAN',
    'vamana_puran_saromahatmya': 'VAMAN',
    'vishnu_puran': 'VISH',
    'revakhanda_vayu_puran': 'VYU',
    'devi_gita': 'DEVI',
    'aitareya_upanishad': 'AITAREYA',
    'isha_upanishad': 'ISHA',
    'shvetashvatara_upanishad': 'SHVET',
    'taittiriya_upanishad_bhashya': 'TAITT',
    'manusmriti': 'MANU',
    'narada_smriti': 'NARADA_SM',
    'vishnu_smriti': 'VISHNU_SM',
    'vishnu_dharma': 'VISHNU_SM',
    'yajnavalkya_smriti': 'YAJNAV',
    'ramanuja_vedartha': 'VISHNU_SM',
    'apastamba_dharmasutra': 'APASTAMBA_DS',
    'apastamba_grihya_sutra': 'APASTAMBA_DS',
    'baudhayana_dharmasutra': 'BAUDHAYANA_DS',
    'gautama_dharmasutra': 'GAUTAMA_DS',
    'gautama_dharmasutra_1_3_comm': 'GAUTAMA_DS',
    'yoga_sutra': 'YOGA_SUTRA',
    'yoga_sutra_bhasya': 'YOGA_SUTRA',
}

# GRETIL texts not in the 54 scripture canon
NON_CANON_GREtil = {
    'abhinavagupta_bhairava_stava', 'abhinavagupta_krama_stotro',
    'astavakra_gita', 'brahma_samhita', 'devi_kalottara_agama',
    'ganapati_stotra', 'gitagovinda', 'hatha_yoga_pradipika',
    'kalidasa_shyamaladandaka', 'kirana tantra', 'kubjikamata tantra',
    'malinivijayottara tantra', 'matrkabhedatantra', 'mrigendra_agama',
    'nadabindi_upanishad', 'namaskaraikavimshati stotra',
    'narasimha_puran', 'nirukta', 'pancavimsha_brahmana',
    'satvatatantra', 'shankhayana_shrauta_sutra', 'shira_upanishad',
    'shiva mahimna stava', 'shiva_sutra_varttika', 'shiva_upanishad',
    'shivasankalpa_upanishad', 'svacchandatantra', 'svayambhu_puran',
    'todala tantra', 'uddamareshvara tantra', 'vaikhanasa_dharmasutra',
    'vasistha_dharmasutra', 'vijJAnabhairava', 'vijnana_bhairava',
    'vinaashikha tantra', 'yama_smriti', 'yamuna stotraratna',
    'yoga_bija', 'gopatha_brahmana', 'kositaki_brahmana',
    'angiras_smriti', 'brihaspati_smriti', 'katyayana_smriti',
    'manava_grihya_sutra', 'ashvalayana_grihya_sutra',
    'ashvalayana_shrauta_sutra', 'sarvadurgatiparishodhana tantra',
}

def build_gretil_witness(text_name, scripture_id=None):
    """Build a witness record for a GRETIL-parsed text."""
    iast_path = GREtil_DIR / f'{text_name}_gretil_iast.txt'
    deva_path = GREtil_DIR / f'{text_name}_gretil_devanagari.txt'
    struct_path = GREtil_DIR / f'{text_name}_gretil_structure.json'
    
    # Determine witness family
    if 'aufrecht' in text_name:
        family = 'F-AUFRECHT'
    elif 'padapatha' in text_name:
        family = 'F-PADAPATHA'
    elif 'khila' in text_name:
        family = 'F-KHILA'
    elif '4comm' in text_name or 'shankara' in text_name or 'madhva' in text_name or 'ramanuja' in text_name or 'bhaskara' in text_name:
        family = 'F-COMMENTARY'
    else:
        family = 'F-GRETIL'
    
    # Detect encoding
    enc_info = {'valid_utf8': False}
    if iast_path.exists():
        enc_info = detect_encoding(iast_path)
    
    # Count lines
    iast_lines = count_lines(iast_path) if iast_path.exists() else 0
    deva_lines = count_lines(deva_path) if deva_path.exists() else 0
    
    # Load structure
    structure = {}
    if struct_path.exists():
        try:
            structure = load_json(struct_path)
        except:
            pass
    
    witness = {
        'witness_id': f'GREtil-{text_name}',
        'family_id': family,
        'scripture_id': scripture_id,
        'source': 'GRETIL',
        'text_name': text_name,
        'editor': 'GRETIL (Salomon et al.)',
        'institution': 'University of Cologne',
        'language': 'Sanskrit',
        'script': enc_info.get('has_devanagari', False) and 'Devanagari' or 'IAST',
        'encoding': {
            'native_unicode': True,
            'ocr': False,
            'valid_utf8': enc_info.get('valid_utf8', False),
            'has_replacement': enc_info.get('has_replacement', False),
            'has_devanagari': enc_info.get('has_devanagari', False),
            'has_iast': enc_info.get('has_iast', False),
        },
        'critical_edition': False,
        'diplomatic_edition': False,
        'commentary': family == 'F-COMMENTARY',
        'completion': {
            'iast_lines': iast_lines,
            'deva_lines': deva_lines,
            'has_structure': bool(structure),
            'structure_keys': list(structure.keys()) if isinstance(structure, dict) else [],
        },
        'files': {
            'iast': str(iast_path.relative_to(BASE)) if iast_path.exists() else None,
            'devanagari': str(deva_path.relative_to(BASE)) if deva_path.exists() else None,
            'structure': str(struct_path.relative_to(BASE)) if struct_path.exists() else None,
        },
        'acquisition_status': 'ACQUIRED',
        'license': 'Academic use (GRETIL)',
        'is_derivative': False,
    }
    
    return witness

def build_other_witnesses():
    """Build witness records for non-GRETIL files on disk."""
    witnesses = []
    
    # Check downloads directory for additional witnesses
    downloads_files = list(DOWNLOADS_DIR.glob('*.xml')) + list(DOWNLOADS_DIR.glob('*.txt')) + list(DOWNLOADS_DIR.glob('*.pdf'))
    
    for f in downloads_files:
        name = f.name.lower()
        
        # RV-related
        if 'rigveda' in name or 'vedaweb' in name.lower():
            # These are already counted in RV census
            continue
        
        # BG-related
        if 'bg_' in name and 'gitapress' in name:
            witnesses.append({
                'witness_id': f'DOWNLOAD-{f.stem}',
                'family_id': 'F-GITAPRESS',
                'scripture_id': 'BG',
                'source': 'Archive.org (DjVuTXT)',
                'text_name': f.stem,
                'publisher': 'Gita Press',
                'ocr': True,
                'files': {'local': str(f.relative_to(BASE))},
                'acquisition_status': 'ACQUIRED',
            })
    
    return witnesses

def main():
    print("=" * 70)
    print("PHASE 4: UNIVERSAL WITNESS CENSUS BUILDER")
    print("=" * 70)
    
    # Load scripture canon
    canon = load_json(CONFIG_DIR / 'scripture_canon.json')
    scriptures = {s['id']: s for s in canon['scriptures']}
    
    # Initialize census
    census = {}
    for sid, s in scriptures.items():
        census[sid] = {
            'scripture_id': sid,
            'canonical_name': s.get('canonical_name', ''),
            'iast': s.get('iast', ''),
            'devanagari': s.get('devanagari', ''),
            'category': s.get('category', ''),
            'priority': s.get('priority', 99),
            'witnesses': [],
            'families': {},
            'gretil_texts': [],
            'total_witnesses': 0,
            'independent_families': 0,
        }
    
    # Process all GRETIL texts
    gretil_dir = GREtil_DIR
    gretil_texts = sorted([f.stem.replace('_gretil_iast', '') 
                          for f in gretil_dir.glob('*_gretil_iast.txt')])
    
    print(f"\nProcessing {len(gretil_texts)} GRETIL texts...")
    
    for text_name in gretil_texts:
        scripture_id = GREtil_MAP.get(text_name)
        witness = build_gretil_witness(text_name, scripture_id)
        
        if scripture_id and scripture_id in census:
            census[scripture_id]['witnesses'].append(witness)
            census[scripture_id]['gretil_texts'].append(text_name)
            fam = witness['family_id']
            if fam not in census[scripture_id]['families']:
                census[scripture_id]['families'][fam] = []
            census[scripture_id]['families'][fam].append(witness['witness_id'])
        elif text_name in NON_CANON_GREtil:
            # Store in a special non-canon bucket
            if 'NON_CANON' not in census:
                census['NON_CANON'] = {
                    'scripture_id': 'NON_CANON',
                    'canonical_name': 'Non-canon GRETIL texts',
                    'category': 'Other',
                    'witnesses': [],
                    'families': {},
                }
            census['NON_CANON']['witnesses'].append(witness)
            fam = witness['family_id']
            if fam not in census['NON_CANON']['families']:
                census['NON_CANON']['families'][fam] = []
            census['NON_CANON']['families'][fam].append(witness['witness_id'])
        else:
            print(f"  WARNING: {text_name} not mapped to any scripture and not in non-canon list")
    
    # Add additional witnesses from downloads
    other_witnesses = build_other_witnesses()
    for w in other_witnesses:
        sid = w.get('scripture_id')
        if sid and sid in census:
            census[sid]['witnesses'].append(w)
            fam = w.get('family_id', 'F-UNKNOWN')
            if fam not in census[sid]['families']:
                census[sid]['families'][fam] = []
            census[sid]['families'][fam].append(w['witness_id'])
    
    # Add VedaWeb/Lubotsky witnesses for RV
    vedaweb_dir = DOWNLOADS_DIR / 'vedaweb'
    if vedaweb_dir.exists():
        vedaweb_files = list(vedaweb_dir.rglob('rv_book_*.tei'))
        if vedaweb_files:
            witness = {
                'witness_id': 'VedaWeb-Lubotsky',
                'family_id': 'F-LUBOTSKY',
                'scripture_id': 'RV',
                'source': 'VedaWeb / Zenodo (Lubotsky)',
                'editor': 'Alexei Lubotsky',
                'institution': 'Leiden University',
                'language': 'Sanskrit',
                'script': 'IAST',
                'encoding': {'native_unicode': True, 'ocr': False},
                'files': [str(f.relative_to(BASE)) for f in vedaweb_files[:5]],
                'total_files': len(vedaweb_files),
                'acquisition_status': 'ACQUIRED',
                'license': 'Academic',
                'is_derivative': False,
            }
            census['RV']['witnesses'].append(witness)
            census['RV']['families'].setdefault('F-LUBOTSKY', []).append('VedaWeb-Lubotsky')
    
    # Compute summary stats
    for sid, entry in census.items():
        entry['total_witnesses'] = len(entry['witnesses'])
        entry['independent_families'] = len(entry['families'])
    
    # Save census
    save_json(DTC_DIR / 'phase4_universal_census.json', census)
    
    # Print summary
    print("\n" + "=" * 70)
    print("UNIVERSAL WITNESS CENSUS SUMMARY")
    print("=" * 70)
    
    total_witnesses = 0
    total_families = 0
    scriptures_with_witnesses = 0
    
    for sid in sorted(census.keys(), key=lambda x: scriptures.get(x, {}).get('priority', 99)):
        entry = census[sid]
        tw = entry['total_witnesses']
        tf = entry['independent_families']
        total_witnesses += tw
        total_families += tf
        if tw > 0:
            scriptures_with_witnesses += 1
        status = 'VERIFIED' if tf >= 2 else ('EVIDENCE_INCOMPLETE' if tw > 0 else 'NO_WITNESSES')
        print(f"{sid:15s} {tw:3d} witnesses, {tf:2d} families [{status}]")
    
    print(f"\nTotal: {total_witnesses} witnesses, {total_families} families")
    print(f"Scriptures with witnesses: {scriptures_with_witnesses}/{len(scriptures)}")
    print(f"\nCensus saved to: {DTC_DIR / 'phase4_universal_census.json'}")

if __name__ == '__main__':
    main()
