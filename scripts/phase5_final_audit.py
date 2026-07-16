#!/usr/bin/env python3
"""
Phase 5: Final Corpus Audit & Freeze Candidate Report
Generates the definitive status of every resource in the corpus.
"""
import json
import os
import hashlib
from pathlib import Path
from collections import defaultdict
from datetime import datetime

BASE = Path(__file__).parent.parent
DTC_DIR = BASE / 'knowledge' / 'dtc'
EXTRACT_DIR = DTC_DIR / 'extractions'

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    print("=" * 70)
    print("PHASE 5: FINAL CORPUS AUDIT")
    print("=" * 70)
    
    # Load all data
    inventory = json.load(open(EXTRACT_DIR / 'complete_inventory.json'))
    extraction = json.load(open(EXTRACT_DIR / 'extraction_results.json'))
    
    # === WITNESS INVENTORY ===
    witness_inventory = defaultdict(lambda: {
        'files': [],
        'families': set(),
        'total_verses': 0,
        'sources': set(),
        'encodings': set(),
    })
    
    for path, record in inventory.items():
        sid = record.get('scripture')
        if not sid:
            continue
        
        w = witness_inventory[sid]
        w['files'].append(path)
        w['families'].add(record.get('family', 'F-UNKNOWN'))
        w['sources'].add(record.get('source', 'unknown'))
        enc = record.get('encoding', {})
        if enc.get('quality'):
            w['encodings'].add(enc['quality'])
    
    # Add extraction data
    for sid, ext in extraction.items():
        if sid in witness_inventory:
            witness_inventory[sid]['total_verses'] = ext.get('best_verses', 0)
    
    # === FAMILY ANALYSIS ===
    all_families = defaultdict(lambda: {'scriptures': [], 'files': []})
    for path, record in inventory.items():
        fam = record.get('family', 'F-UNKNOWN')
        sid = record.get('scripture', 'NONE')
        all_families[fam]['scriptures'].append(sid)
        all_families[fam]['files'].append(path)
    
    # === UNICODE AUDIT ===
    unicode_issues = []
    for path, record in inventory.items():
        enc = record.get('encoding', {})
        if enc.get('has_replacement'):
            unicode_issues.append({'file': path, 'issue': 'replacement_characters'})
        if enc.get('quality') == 'GARBLED':
            unicode_issues.append({'file': path, 'issue': 'garbled_encoding'})
    
    # === GENERATE REPORTS ===
    
    # 1. Scripture Inventory
    scripture_inventory = {}
    for sid, ext in extraction.items():
        w = witness_inventory[sid]
        scripture_inventory[sid] = {
            'scripture': sid,
            'files_count': len(w['files']),
            'families': sorted(w['families']),
            'independent_families': len([f for f in w['families'] if not f.endswith('_UNKNOWN')]),
            'sources': sorted(w['sources']),
            'total_verses_extracted': ext.get('best_verses', 0),
            'expected_verses': ext.get('expected_verses', 0),
            'coverage_pct': ext.get('coverage_pct', 0),
            'best_file': ext.get('best_file'),
            'encoding_quality': sorted(w['encodings']),
            'status': 'VERIFIED' if ext.get('coverage_pct', 0) >= 80 else 'PARTIAL',
        }
    
    save_json(EXTRACT_DIR / 'scripture_inventory.json', scripture_inventory)
    
    # 2. Witness Family Registry
    family_registry = {}
    for fam, data in all_families.items():
        family_registry[fam] = {
            'family_id': fam,
            'scriptures': sorted(set(s for s in data['scriptures'] if s)),
            'file_count': len(data['files']),
            'files': data['files'][:50],  # Cap for file size
        }
    
    save_json(EXTRACT_DIR / 'family_registry.json', family_registry)
    
    # 3. Unicode Audit
    unicode_audit = {
        'total_files_checked': len(inventory),
        'issues_found': len(unicode_issues),
        'issues': unicode_issues[:100],
        'garbled_files': sum(1 for r in inventory.values() if r.get('encoding', {}).get('quality') == 'GARBLED'),
        'good_files': sum(1 for r in inventory.values() if r.get('encoding', {}).get('quality') == 'GOOD'),
    }
    
    save_json(EXTRACT_DIR / 'unicode_audit.json', unicode_audit)
    
    # 4. Gap Report
    gaps = []
    for sid, ext in extraction.items():
        cov = ext.get('coverage_pct', 0)
        if cov < 80:
            gaps.append({
                'scripture': sid,
                'coverage': cov,
                'verses': ext.get('best_verses', 0),
                'expected': ext.get('expected_verses', 0),
                'files_available': ext.get('files_processed', 0),
                'reason': 'Insufficient data in available files' if ext.get('best_verses', 0) > 0 else 'No files found',
            })
    gaps.sort(key=lambda x: x['coverage'])
    
    save_json(EXTRACT_DIR / 'gap_report.json', {
        'total_gaps': len(gaps),
        'gaps': gaps,
    })
    
    # === FINAL SUMMARY ===
    print(f"\n{'='*70}")
    print("FINAL CORPUS AUDIT SUMMARY")
    print(f"{'='*70}")
    
    total_files = len(inventory)
    total_scriptures = len(extraction)
    total_verses = sum(ext.get('best_verses', 0) for ext in extraction.values())
    verified = sum(1 for s in scripture_inventory.values() if s['status'] == 'VERIFIED')
    total_families = len(all_families)
    independent_families = len([f for f in all_families if not f.startswith('F-UNKNOWN')])
    
    print(f"\n  CORPUS STATISTICS:")
    print(f"  Total files indexed:        {total_files:,}")
    print(f"  Total scriptures:           {total_scriptures}")
    print(f"  Total verses extracted:     {total_verses:,}")
    print(f"  Verified scriptures:        {verified}/{total_scriptures}")
    print(f"  Witness families:           {total_families}")
    print(f"  Independent families:       {independent_families}")
    print(f"  Unicode issues:             {unicode_audit['issues_found']}")
    print(f"  Coverage gaps:              {gaps.__len__()}")
    
    print(f"\n  SCRIPTURE STATUS:")
    for sid in sorted(scripture_inventory.keys()):
        s = scripture_inventory[sid]
        icon = '✅' if s['status'] == 'VERIFIED' else '⚠️'
        print(f"  {icon} {sid:15s} {s['total_verses_extracted']:7d} verses ({s['coverage_pct']:5.1f}%) [{s['independent_families']} families]")
    
    print(f"\n  REMAINING GAPS:")
    for gap in gaps:
        print(f"  ⚠️ {gap['scripture']:15s} {gap['coverage']:5.1f}% — {gap['reason']}")
    
    if not gaps:
        print(f"  None! All scriptures at 80%+ coverage.")
    
    # === CORPUS FREEZE CANDIDATE ===
    print(f"\n{'='*70}")
    print("CORPUS FREEZE CANDIDATE ASSESSMENT")
    print(f"{'='*70}")
    
    freeze_ready = True
    conditions = []
    
    # Check conditions
    unparsed = sum(1 for r in inventory.values() if r.get('status') == 'ACQUIRED' and r.get('scripture'))
    conditions.append(('Acquired-but-unparsed = 0', unparsed == 0, f'{unparsed} files'))
    
    parser_failures = sum(1 for ext in extraction.values() if ext.get('best_verses', 0) == 0)
    conditions.append(('Parser failures = 0', parser_failures == 0, f'{parser_failures} failures'))
    
    unicode_ok = unicode_audit['garbled_files'] == 0
    conditions.append(('No garbled Unicode', unicode_ok, f'{unicode_audit["garbled_files"]} garbled'))
    
    all_verified = verified == total_scriptures
    conditions.append(('All scriptures verified', all_verified, f'{verified}/{total_scriptures}'))
    
    for name, met, detail in conditions:
        icon = '✅' if met else '❌'
        print(f"  {icon} {name}: {detail}")
        if not met:
            freeze_ready = False
    
    if freeze_ready:
        print(f"\n  🟢 CORPUS FREEZE CANDIDATE: READY")
    else:
        print(f"\n  🔴 CORPUS FREEZE CANDIDATE: NOT READY")
        print(f"  Continue recovery until all conditions met.")
    
    # Save freeze report
    freeze_report = {
        'generated': datetime.now().isoformat(),
        'freeze_ready': freeze_ready,
        'conditions': [{'name': n, 'met': m, 'detail': d} for n, m, d in conditions],
        'summary': {
            'total_files': total_files,
            'total_scriptures': total_scriptures,
            'total_verses': total_verses,
            'verified': verified,
            'independent_families': independent_families,
            'unicode_issues': unicode_audit['issues_found'],
            'coverage_gaps': len(gaps),
        },
    }
    save_json(EXTRACT_DIR / 'freeze_candidate_report.json', freeze_report)
    
    print(f"\nReports saved to: {EXTRACT_DIR}")


if __name__ == '__main__':
    main()
