#!/usr/bin/env python3
"""
Phase 4: Multi-Witness Collation Engine
Compares independent witness families for each scripture.
Produces: Agreement matrices, variant apparatus, confidence scores.
"""
import json
import os
import re
from pathlib import Path
from collections import defaultdict
from difflib import SequenceMatcher

BASE = Path(__file__).parent.parent
GREtil_DIR = BASE / 'knowledge' / 'gretil_parsed'
DTC_DIR = BASE / 'knowledge' / 'dtc'
CUID_DIR = DTC_DIR / 'cuid_sets'
COLLATION_DIR = DTC_DIR / 'collation'
COLLATION_DIR.mkdir(parents=True, exist_ok=True)


def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def normalize_text(text):
    """Basic normalization for comparison."""
    if not text:
        return ''
    text = text.strip()
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove common punctuation for comparison
    text = re.sub(r'[।॥,\.\?\!]', '', text)
    return text


def text_similarity(a, b):
    """Compute similarity between two texts."""
    na = normalize_text(a)
    nb = normalize_text(b)
    if not na or not nb:
        return 0.0
    return SequenceMatcher(None, na, nb).ratio()


def classify_difference(a, b):
    """Classify the type of difference between two texts."""
    na = normalize_text(a)
    nb = normalize_text(b)
    
    if na == nb:
        return 'IDENTICAL'
    
    # Check if identical after removing all diacritics
    def strip_diacritics(s):
        replacements = {
            'ā': 'a', 'ī': 'i', 'ū': 'u', 'ṛ': 'r', 'ṝ': 'r',
            'ḷ': 'l', 'ṃ': 'm', 'ḥ': 'h', 'ṇ': 'n', 'ṇ': 'n',
            'ṭ': 't', 'ḍ': 'd', 'ñ': 'n', 'ś': 's', 'ṣ': 's',
        }
        for k, v in replacements.items():
            s = s.replace(k, v)
        return s
    
    sa = strip_diacritics(na)
    sb = strip_diacritics(nb)
    if sa == sb:
        return 'DIACRITIC_ONLY'
    
    # Check if difference is just word order/sandhi
    words_a = set(na.split())
    words_b = set(nb.split())
    if words_a == words_b:
        return 'WORD_ORDER'
    
    # Check if difference is minor (high similarity)
    sim = text_similarity(a, b)
    if sim > 0.95:
        return 'ORTHOGRAPHIC'
    elif sim > 0.85:
        return 'SEGMENTATION'
    elif sim > 0.70:
        return 'EDITORIAL'
    else:
        return 'SIGNIFICANT'


def collate_scripture(scripture_id, gretil_names):
    """Collate all GRETIL witnesses for a scripture."""
    witnesses = {}
    
    for name in gretil_names:
        iast_path = GREtil_DIR / f'{name}_gretil_iast.txt'
        if not iast_path.exists():
            continue
        
        with open(iast_path, 'r', errors='replace') as f:
            lines = [l.strip() for l in f if l.strip()]
        
        witnesses[name] = lines
    
    if len(witnesses) < 2:
        return {
            'scripture': scripture_id,
            'status': 'SINGLE_WITNESS',
            'witness_count': len(witnesses),
            'variants': [],
            'confidence': 'LOW' if len(witnesses) == 0 else 'MEDIUM',
        }
    
    # Pairwise collation
    names = sorted(witnesses.keys())
    variant_apparatus = []
    agreement_matrix = {}
    
    for i, name_a in enumerate(names):
        agreement_matrix[name_a] = {}
        lines_a = witnesses[name_a]
        
        for name_b in names[i+1:]:
            lines_b = witnesses[name_b]
            
            # Align by minimum length
            min_len = min(len(lines_a), len(lines_b))
            max_len = max(len(lines_a), len(lines_b))
            
            agree = 0
            disagree = 0
            missing = max_len - min_len
            variants = []
            
            for j in range(min_len):
                sim = text_similarity(lines_a[j], lines_b[j])
                if sim >= 0.98:
                    agree += 1
                elif sim >= 0.80:
                    disagree += 1
                    diff_type = classify_difference(lines_a[j], lines_b[j])
                    variants.append({
                        'position': j + 1,
                        'type': diff_type,
                        'similarity': round(sim, 4),
                    })
                else:
                    disagree += 1
                    variants.append({
                        'position': j + 1,
                        'type': 'MAJOR_DIFF',
                        'similarity': round(sim, 4),
                    })
            
            total = agree + disagree + missing
            agreement_pct = (agree / total * 100) if total > 0 else 0
            
            agreement_matrix[name_a][name_b] = {
                'agree': agree,
                'disagree': disagree,
                'missing': missing,
                'agreement_pct': round(agreement_pct, 2),
            }
            
            variant_apparatus.extend(variants)
    
    # Classify variant types
    variant_types = defaultdict(int)
    for v in variant_apparatus:
        variant_types[v['type']] += 1
    
    # Overall confidence
    if agreement_matrix:
        all_pcts = []
        for row in agreement_matrix.values():
            for col_data in row.values():
                all_pcts.append(col_data['agreement_pct'])
        avg_agreement = sum(all_pcts) / len(all_pcts) if all_pcts else 0
    else:
        avg_agreement = 0
    
    if avg_agreement > 95:
        confidence = 'HIGH'
    elif avg_agreement > 85:
        confidence = 'MEDIUM'
    else:
        confidence = 'LOW'
    
    return {
        'scripture': scripture_id,
        'status': 'COLLATED',
        'witness_count': len(witnesses),
        'witness_names': names,
        'agreement_matrix': agreement_matrix,
        'variant_apparatus': variant_apparatus[:100],  # Cap for file size
        'variant_type_counts': dict(variant_types),
        'total_variants': len(variant_apparatus),
        'average_agreement': round(avg_agreement, 2),
        'confidence': confidence,
    }


# Scriptures with 2+ GRETIL witnesses (eligible for collation)
COLLATABLE = {
    'RV': ['rigveda_aufrecht', 'rigveda_padapatha'],
    'BG': ['bhagavad_gita_4comm', 'bhagavad_gita_shankara', 'madhva_gita_bhashya', 'ramanuja_gita_bhashya'],
    'AV': ['atharva_prayashchittani', 'atharvashiras_upanishad'],
    'HV': ['harivamsa', 'harivamsa_app1'],
    'VAMAN': ['vamana_puran', 'vamana_puran_saromahatmya'],
    'VISHNU_SM': ['vishnu_smriti', 'ramanuja_vedartha'],
    'APASTAMBA_DS': ['apastamba_dharmasutra', 'apastamba_grihya_sutra'],
    'GAUTAMA_DS': ['gautama_dharmasutra', 'gautama_dharmasutra_1_3_comm'],
    'YOGA_SUTRA': ['yoga_sutra', 'yoga_sutra_bhasya'],
}

# Single-witness scriptures (no collation possible)
SINGLE_WITNESS = {
    'SV': ['samaveda'],
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
    'VISH': ['vishnu_puran'],
    'VYU': ['revakhanda_vayu_puran'],
    'DEVI': ['devi_gita'],
    'AITAREYA': ['aitareya_upanishad'],
    'ISHA': ['isha_upanishad'],
    'SHVET': ['shvetashvatara_upanishad'],
    'TAITT': ['taittiriya_upanishad_bhashya'],
    'MANU': ['manusmriti'],
    'NARADA_SM': ['narada_smriti'],
    'YAJNAV': ['yajnavalkya_smriti'],
    'BAUDHAYANA_DS': ['baudhayana_dharmasutra'],
}


def main():
    print("=" * 70)
    print("PHASE 4: MULTI-WITNESS COLLATION ENGINE")
    print("=" * 70)
    
    all_results = {}
    
    # Collate scriptures with 2+ witnesses
    print(f"\n--- Collating {len(COLLATABLE)} multi-witness scriptures ---")
    for sid, names in COLLATABLE.items():
        result = collate_scripture(sid, names)
        all_results[sid] = result
        
        status = result['status']
        wc = result['witness_count']
        variants = result.get('total_variants', 0)
        conf = result['confidence']
        avg = result.get('average_agreement', 0)
        
        if status == 'COLLATED':
            print(f"  {sid:15s} {wc} witnesses, {variants:5d} variants, {avg:.1f}% agreement [{conf}]")
            
            # Print variant type breakdown
            vtc = result.get('variant_type_counts', {})
            if vtc:
                types_str = ', '.join(f"{k}={v}" for k, v in sorted(vtc.items(), key=lambda x: -x[1])[:4])
                print(f"  {'':15s} Types: {types_str}")
        else:
            print(f"  {sid:15s} {status}")
    
    # Record single-witness scriptures
    for sid, names in SINGLE_WITNESS.items():
        all_results[sid] = {
            'scripture': sid,
            'status': 'SINGLE_WITNESS',
            'witness_count': len(names),
            'confidence': 'MEDIUM',
            'note': 'Only one GRETIL witness available. Additional witnesses from other sources needed.',
        }
        print(f"  {sid:15s} {len(names)} witnesses [SINGLE_WITNESS]")
    
    # Save collation results
    save_json(COLLATION_DIR / 'collation_results.json', all_results)
    
    # Summary
    print(f"\n{'='*70}")
    print("COLLATION SUMMARY")
    print(f"{'='*70}")
    
    total_variants = 0
    high_conf = 0
    med_conf = 0
    low_conf = 0
    
    for sid, result in all_results.items():
        total_variants += result.get('total_variants', 0)
        conf = result.get('confidence', 'LOW')
        if conf == 'HIGH':
            high_conf += 1
        elif conf == 'MEDIUM':
            med_conf += 1
        else:
            low_conf += 1
    
    print(f"Scriptures collated: {sum(1 for r in all_results.values() if r['status'] == 'COLLATED')}")
    print(f"Single-witness: {sum(1 for r in all_results.values() if r['status'] == 'SINGLE_WITNESS')}")
    print(f"Total variants found: {total_variants}")
    print(f"Confidence: HIGH={high_conf}, MEDIUM={med_conf}, LOW={low_conf}")
    print(f"\nResults saved to: {COLLATION_DIR / 'collation_results.json'}")


if __name__ == '__main__':
    main()
