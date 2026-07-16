#!/usr/bin/env python3
"""
Phase 4: Comprehensive Coverage & Confidence Report
Generates the definitive status of every scripture in the corpus.
"""
import json
import os
from pathlib import Path
from collections import defaultdict
from datetime import datetime

BASE = Path(__file__).parent.parent
DTC_DIR = BASE / 'knowledge' / 'dtc'
CONFIG_DIR = DTC_DIR / 'config'
CORPUS_INDEX = DTC_DIR / 'phase4_corpus_index.json'
CENSUS = DTC_DIR / 'phase4_universal_census.json'
CUID_DIR = DTC_DIR / 'cuid_sets'
COLLATION_DIR = DTC_DIR / 'collation'
COVERAGE_DIR = DTC_DIR / 'coverage'
COVERAGE_DIR.mkdir(parents=True, exist_ok=True)

# Expected canonical verse/chapter counts (from scholarly sources)
EXPECTED = {
    'RV': {'chapters': 10, 'verses': 10600, 'name': 'Rigveda Samhita'},
    'SV': {'chapters': 2, 'verses': 1875, 'name': 'Samaveda Samhita'},
    'YVK': {'chapters': 40, 'verses': 2000, 'name': 'Krishna Yajurveda (Taittiriya Samhita)'},
    'YVS': {'chapters': 40, 'verses': 2000, 'name': 'Shukla Yajurveda (Madhyandina)'},
    'AV': {'chapters': 20, 'verses': 6000, 'name': 'Atharvaveda Samhita'},
    'BG': {'chapters': 18, 'verses': 700, 'name': 'Bhagavad Gita'},
    'MBH': {'chapters': 18, 'verses': 100000, 'name': 'Mahabharata'},
    'RM': {'chapters': 7, 'verses': 24000, 'name': 'Ramayana'},
    'HV': {'chapters': 2, 'verses': 16000, 'name': 'Harivamsha'},
    'BHAG': {'chapters': 12, 'verses': 18000, 'name': 'Bhagavata Purana'},
    'VISH': {'chapters': 6, 'verses': 23000, 'name': 'Vishnu Purana'},
    'SHIV': {'chapters': 11, 'verses': 24000, 'name': 'Shiva Purana'},
    'DEVI': {'chapters': 31, 'verses': 18000, 'name': 'Devi Bhagavata Purana'},
    'AGNI': {'chapters': 382, 'verses': 16000, 'name': 'Agni Purana'},
    'BRAH': {'chapters': 268, 'verses': 14000, 'name': 'Brahma Purana'},
    'MATS': {'chapters': 291, 'verses': 13000, 'name': 'Matsya Purana'},
    'KURM': {'chapters': 252, 'verses': 12000, 'name': 'Kurma Purana'},
    'LING': {'chapters': 238, 'verses': 11000, 'name': 'Linga Purana'},
    'MARK': {'chapters': 137, 'verses': 9000, 'name': 'Markandeya Purana'},
    'NARADA': {'chapters': 336, 'verses': 18000, 'name': 'Narada Purana'},
    'VAMAN': {'chapters': 96, 'verses': 10000, 'name': 'Vamana Purana'},
    'VARAH': {'chapters': 218, 'verses': 10000, 'name': 'Varaha Purana'},
    'VYU': {'chapters': 24000, 'verses': 24000, 'name': 'Vayu Purana'},
    'SKAND': {'chapters': 800, 'verses': 24000, 'name': 'Skanda Purana'},
    'BRAHMD': {'chapters': 315, 'verses': 12000, 'name': 'Brahmanda Purana'},
    'KALI': {'chapters': 58, 'verses': 9000, 'name': 'Kalika Purana'},
    'GARUDA': {'chapters': 70, 'verses': 8000, 'name': 'Garuda Purana'},
    'ISHA': {'chapters': 1, 'verses': 18, 'name': 'Isha Upanishad'},
    'KEN': {'chapters': 4, 'verses': 32, 'name': 'Kena Upanishad'},
    'KATH': {'chapters': 3, 'verses': 119, 'name': 'Katha Upanishad'},
    'PRASHNA': {'chapters': 6, 'verses': 64, 'name': 'Prashna Upanishad'},
    'MUND': {'chapters': 3, 'verses': 83, 'name': 'Mundaka Upanishad'},
    'MAND': {'chapters': 1, 'verses': 12, 'name': 'Mandukya Upanishad'},
    'TAITT': {'chapters': 3, 'verses': 104, 'name': 'Taittiriya Upanishad'},
    'AITAREYA': {'chapters': 3, 'verses': 33, 'name': 'Aitareya Upanishad'},
    'CHAND': {'chapters': 10, 'verses': 634, 'name': 'Chandogya Upanishad'},
    'BRIHAD': {'chapters': 6, 'verses': 536, 'name': 'Brihadaranyaka Upanishad'},
    'SHVET': {'chapters': 6, 'verses': 113, 'name': 'Shvetashvatara Upanishad'},
    'KAUS': {'chapters': 4, 'verses': 88, 'name': 'Kaushitaki Upanishad'},
    'MAITR': {'chapters': 7, 'verses': 115, 'name': 'Maitri Upanishad'},
    'MAHAN': {'chapters': 1, 'verses': 84, 'name': 'Mahanarayana Upanishad'},
    'MANU': {'chapters': 12, 'verses': 2694, 'name': 'Manusmriti'},
    'YAJNAV': {'chapters': 3, 'verses': 1054, 'name': 'Yajnavalkya Smriti'},
    'VISHNU_SM': {'chapters': 1, 'verses': 100, 'name': 'Vishnu Smriti'},
    'NARADA_SM': {'chapters': 1, 'verses': 150, 'name': 'Narada Smriti'},
    'PARASHARA': {'chapters': 1, 'verses': 150, 'name': 'Parashara Smriti'},
    'VYASA_SM': {'chapters': 1, 'verses': 100, 'name': 'Vyasa Smriti'},
    'APASTAMBA_DS': {'chapters': 30, 'verses': 1500, 'name': 'Apastamba Dharmasutra'},
    'BAUDHAYANA_DS': {'chapters': 4, 'verses': 500, 'name': 'Baudhayana Dharmasutra'},
    'GAUTAMA_DS': {'chapters': 30, 'verses': 1000, 'name': 'Gautama Dharmasutra'},
    'VEDANTA_SUTRA': {'chapters': 4, 'verses': 555, 'name': 'Vedanta Sutras (Brahma Sutras)'},
    'YOGA_SUTRA': {'chapters': 4, 'verses': 196, 'name': 'Yoga Sutras'},
    'NYAYA_SUTRA': {'chapters': 5, 'verses': 560, 'name': 'Nyaya Sutras'},
    'VAISHESHIKA_SUTRA': {'chapters': 10, 'verses': 370, 'name': 'Vaisheshika Sutras'},
}


def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return {}


def build_coverage_report():
    """Build comprehensive coverage report for all 54 scriptures."""
    canon = load_json(CONFIG_DIR / 'scripture_canon.json')
    scriptures = {s['id']: s for s in canon['scriptures']}
    
    corpus_index = load_json(CORPUS_INDEX)
    census = load_json(CENSUS)
    collation = load_json(COLLATION_DIR / 'collation_results.json')
    
    report = {
        'generated': datetime.now().isoformat(),
        'phase': 'Phase 4: Digital Critical Edition',
        'total_scriptures': len(scriptures),
        'scriptures': {},
        'summary': {},
    }
    
    for sid, s in scriptures.items():
        exp = EXPECTED.get(sid, {'chapters': 0, 'verses': 0, 'name': s.get('canonical_name', sid)})
        
        # Get corpus files
        files = corpus_index.get(sid, [])
        families = set(f.get('family', 'F-UNKNOWN') for f in files)
        ocr_files = [f for f in files if f.get('ocr')]
        unicode_files = [f for f in files if not f.get('ocr')]
        
        # Get CUIDs
        cuid_path = CUID_DIR / f'{sid}_cuids.json'
        cuids = load_json(cuid_path)
        cuid_count = len(cuids)
        
        # Get collation
        collation_data = collation.get(sid, {})
        collation_status = collation_data.get('status', 'NOT_COLLATED')
        variant_count = collation_data.get('total_variants', 0)
        avg_agreement = collation_data.get('average_agreement', 0)
        
        # Calculate coverage
        verse_coverage = min(100, (cuid_count / exp['verses'] * 100)) if exp['verses'] > 0 else 0
        
        # Determine verification status
        independent_families = len([f for f in families if not f.endswith('_UNKNOWN')])
        if independent_families >= 2 and verse_coverage > 80:
            status = 'VERIFIED'
        elif cuid_count > 0:
            status = 'EVIDENCE_INCOMPLETE'
        elif len(files) > 0:
            status = 'ACQUIRED_NOT_PARSED'
        else:
            status = 'NO_WITNESSES'
        
        # Confidence score (0-100)
        conf = 0
        conf += min(30, independent_families * 15)  # Up to 30 for witnesses
        conf += min(30, verse_coverage * 0.3)  # Up to 30 for coverage
        conf += min(20, avg_agreement * 0.2) if avg_agreement > 0 else 0  # Up to 20 for agreement
        conf += 10 if collation_status == 'COLLATED' else 0  # 10 for collation
        conf += 10 if cuid_count > 0 else 0  # 10 for having CUIDs
        
        report['scriptures'][sid] = {
            'name': exp['name'],
            'category': s.get('category', ''),
            'priority': s.get('priority', 99),
            'status': status,
            'confidence': min(100, round(conf)),
            'expected_verses': exp['verses'],
            'expected_chapters': exp['chapters'],
            'extracted_cuids': cuid_count,
            'verse_coverage_pct': round(verse_coverage, 1),
            'total_files': len(files),
            'families': sorted(families),
            'independent_families': independent_families,
            'ocr_files': len(ocr_files),
            'unicode_files': len(unicode_files),
            'collation_status': collation_status,
            'variant_count': variant_count,
            'average_agreement': round(avg_agreement, 2),
        }
    
    # Summary
    statuses = defaultdict(int)
    conf_scores = []
    for sid, data in report['scriptures'].items():
        statuses[data['status']] += 1
        conf_scores.append(data['confidence'])
    
    report['summary'] = {
        'total': len(report['scriptures']),
        'verified': statuses.get('VERIFIED', 0),
        'evidence_incomplete': statuses.get('EVIDENCE_INCOMPLETE', 0),
        'acquired_not_parsed': statuses.get('ACQUIRED_NOT_PARSED', 0),
        'no_witnesses': statuses.get('NO_WITNESSES', 0),
        'average_confidence': round(sum(conf_scores) / len(conf_scores), 1) if conf_scores else 0,
        'max_confidence': max(conf_scores) if conf_scores else 0,
        'min_confidence': min(conf_scores) if conf_scores else 0,
    }
    
    # Save
    with open(COVERAGE_DIR / 'phase4_coverage_report.json', 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    return report


def build_gap_report(report):
    """Build gap analysis and acquisition queue."""
    gaps = []
    
    for sid, data in report['scriptures'].items():
        if data['status'] == 'NO_WITNESSES':
            gaps.append({
                'scripture': sid,
                'name': data['name'],
                'priority': 'CRITICAL',
                'reason': 'No witnesses on disk',
                'expected_verses': data['expected_verses'],
                'needed': 'Full text from GRETIL or Archive.org',
            })
        elif data['status'] == 'ACQUIRED_NOT_PARSED':
            gaps.append({
                'scripture': sid,
                'name': data['name'],
                'priority': 'HIGH',
                'reason': 'Files acquired but not parsed',
                'files_available': data['total_files'],
                'needed': 'Parse and extract CUIDs',
            })
        elif data['status'] == 'EVIDENCE_INCOMPLETE':
            # Check what's missing
            missing = []
            if data['verse_coverage_pct'] < 50:
                missing.append(f"Verse coverage only {data['verse_coverage_pct']}%")
            if data['independent_families'] < 2:
                missing.append(f"Only {data['independent_families']} independent family")
            if data['collation_status'] != 'COLLATED':
                missing.append('Not yet collated')
            
            gaps.append({
                'scripture': sid,
                'name': data['name'],
                'priority': 'MEDIUM',
                'reason': '; '.join(missing),
                'current_coverage': f"{data['verse_coverage_pct']}%",
                'needed': f"Additional witnesses and/or better extraction",
            })
    
    # Sort by priority
    priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
    gaps.sort(key=lambda x: priority_order.get(x['priority'], 99))
    
    gap_report = {
        'generated': datetime.now().isoformat(),
        'total_gaps': len(gaps),
        'critical': sum(1 for g in gaps if g['priority'] == 'CRITICAL'),
        'high': sum(1 for g in gaps if g['priority'] == 'HIGH'),
        'medium': sum(1 for g in gaps if g['priority'] == 'MEDIUM'),
        'gaps': gaps,
    }
    
    with open(COVERAGE_DIR / 'phase4_gap_report.json', 'w') as f:
        json.dump(gap_report, f, indent=2, ensure_ascii=False)
    
    return gap_report


def print_report(report, gap_report):
    """Print formatted coverage report."""
    print("=" * 80)
    print("PHASE 4: COMPREHENSIVE COVERAGE REPORT")
    print(f"Generated: {report['generated']}")
    print("=" * 80)
    
    # Group by category
    categories = defaultdict(list)
    for sid, data in report['scriptures'].items():
        cat = data.get('category', 'Other')
        categories[cat].append((sid, data))
    
    for cat in ['Veda', 'Itihasa', 'Purana', 'Upanishad', 'Smriti', 'Sutra', 'Darshana']:
        if cat not in categories:
            continue
        
        items = categories[cat]
        print(f"\n{'─'*80}")
        print(f"  {cat.upper()} ({len(items)} scriptures)")
        print(f"{'─'*80}")
        
        for sid, data in sorted(items, key=lambda x: x[1].get('priority', 99)):
            status_icon = {
                'VERIFIED': '✅',
                'EVIDENCE_INCOMPLETE': '⚠️',
                'ACQUIRED_NOT_PARSED': '📋',
                'NO_WITNESSES': '❌',
            }.get(data['status'], '?')
            
            conf = data['confidence']
            cov = data['verse_coverage_pct']
            fams = data['independent_families']
            cuds = data['extracted_cuids']
            exp = data['expected_verses']
            
            print(f"  {status_icon} {sid:15s} {data['name'][:35]:35s} "
                  f"Conf:{conf:3d}% Cov:{cov:5.1f}% "
                  f"Fams:{fams:2d} CUIDs:{cuds:6d}/{exp:6d}")
    
    # Summary
    s = report['summary']
    print(f"\n{'='*80}")
    print(f"  SUMMARY")
    print(f"{'='*80}")
    print(f"  Total scriptures:   {s['total']}")
    print(f"  Verified:           {s['verified']}")
    print(f"  Evidence incomplete: {s['evidence_incomplete']}")
    print(f"  Acquired not parsed: {s['acquired_not_parsed']}")
    print(f"  No witnesses:       {s['no_witnesses']}")
    print(f"  Average confidence: {s['average_confidence']}%")
    
    print(f"\n{'='*80}")
    print(f"  GAP ANALYSIS")
    print(f"{'='*80}")
    print(f"  Total gaps: {gap_report['total_gaps']}")
    print(f"  Critical: {gap_report['critical']}")
    print(f"  High: {gap_report['high']}")
    print(f"  Medium: {gap_report['medium']}")
    
    print(f"\n  Top acquisition priorities:")
    for gap in gap_report['gaps'][:10]:
        print(f"    [{gap['priority']:8s}] {gap['scripture']:15s} {gap['name'][:30]:30s} — {gap['reason']}")


def main():
    report = build_coverage_report()
    gap_report = build_gap_report(report)
    print_report(report, gap_report)


if __name__ == '__main__':
    main()
