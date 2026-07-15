#!/usr/bin/env python3
"""
Certify All Scriptures — Global CUV Report

Runs certification on all prose AKU files and produces a global report.
"""

import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(__file__))
from certify_scripture import ScriptureCertifier


def certify_all(input_dir, output_dir):
    """Certify all scriptures and produce global report."""
    
    os.makedirs(output_dir, exist_ok=True)
    
    all_results = []
    global_stats = {
        'total_scriptures': 0,
        'total_akus': 0,
        'total_certified': 0,
        'total_issues': 0,
        'by_status': Counter(),
        'by_class': Counter(),
        'issue_types': Counter(),
    }
    
    for fn in sorted(os.listdir(input_dir)):
        if not fn.endswith('.json'):
            continue
        
        filepath = os.path.join(input_dir, fn)
        with open(filepath) as f:
            data = json.load(f)
        
        title = data.get('title', fn)
        certifier = ScriptureCertifier(fn, title)
        results = certifier.certify(data)
        
        # Save individual results
        out_file = os.path.join(output_dir, fn.replace('.json', '_cert.json'))
        results['class_distribution'] = dict(results['class_distribution'])
        with open(out_file, 'w') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        all_results.append(results)
        global_stats['total_scriptures'] += 1
        global_stats['total_akus'] += results['total_akus']
        global_stats['total_certified'] += results['certified_akus']
        global_stats['by_status'][results['status']] += 1
        
        for cls, count in results['class_distribution'].items():
            global_stats['by_class'][cls] += count
        
        for issue in results['numbering_issues'] + results['boundary_issues'] + results['unicode_issues']:
            global_stats['issue_types'][issue['type']] += 1
            global_stats['total_issues'] += 1
    
    # Print global report
    print(f"\n{'='*70}")
    print(f"GLOBAL CERTIFICATION REPORT")
    print(f"{'='*70}")
    print(f"Total scriptures: {global_stats['total_scriptures']}")
    print(f"Total AKUs: {global_stats['total_akus']}")
    print(f"Total certified: {global_stats['total_certified']} ({100*global_stats['total_certified']/max(global_stats['total_akus'],1):.1f}%)")
    print(f"Total issues: {global_stats['total_issues']}")
    
    print(f"\nStatus distribution:")
    for status, count in global_stats['by_status'].most_common():
        print(f"  {status:25s} {count:4d} scriptures")
    
    print(f"\nGlobal class distribution:")
    for cls, count in global_stats['by_class'].most_common():
        pct = 100 * count / max(global_stats['total_akus'], 1)
        print(f"  {cls:25s} {count:7d} ({pct:5.1f}%)")
    
    print(f"\nGlobal issue types:")
    for itype, count in global_stats['issue_types'].most_common():
        print(f"  {itype:30s} {count:7d}")
    
    # Find scriptures needing most work
    print(f"\nScriptures needing most work:")
    needs_work = sorted(all_results, key=lambda x: x['certified_akus'] / max(x['total_akus'], 1))
    for r in needs_work[:10]:
        pct = 100 * r['certified_akus'] / max(r['total_akus'], 1)
        print(f"  {r['title'][:50]:50s} {pct:5.1f}% ({r['certified_akus']}/{r['total_akus']})")
    
    # Save global report
    global_stats['by_status'] = dict(global_stats['by_status'])
    global_stats['by_class'] = dict(global_stats['by_class'])
    global_stats['issue_types'] = dict(global_stats['issue_types'])
    
    report_file = os.path.join(output_dir, '_global_report.json')
    with open(report_file, 'w') as f:
        json.dump(global_stats, f, indent=2, ensure_ascii=False)
    print(f"\nGlobal report saved to: {report_file}")
    
    return global_stats


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default='knowledge/gretil_prose')
    parser.add_argument('--output', default='knowledge/cuv/certified')
    args = parser.parse_args()
    
    certify_all(args.input, args.output)
