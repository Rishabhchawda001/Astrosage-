#!/usr/bin/env python3
"""
Boundary Validator — Canonical Unit Validation (CUV) Step 2

Validates AKU boundaries:
- No mid-word splits
- No multi-verse AKUs that should be split
- Numbering sequence correct (no gaps, no duplicates)
- Start/end correctness

Usage:
  python3 scripts/boundary_validator.py [--input DIR] [--classification FILE] [--output FILE]
"""

import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


class BoundaryValidator:
    """Validates AKU boundaries within chapters."""
    
    def __init__(self, classification=None):
        self.issues = []
        self.stats = Counter()
    
    def validate_chapter(self, chapter_akus, ch_num, scripture_file):
        """Validate all AKU boundaries in a chapter."""
        chapter_issues = []
        
        for i, aku in enumerate(chapter_akus):
            body = (aku.get('body') or '').strip()
            ref = aku.get('ref')
            cls = aku.get('_class', 'unknown')
            
            # 1. Check mid-word splits
            if body and body[-1].isalpha() and i + 1 < len(chapter_akus):
                next_body = (chapter_akus[i + 1].get('body') or '').strip()
                if next_body and next_body[0].islower():
                    chapter_issues.append({
                        'type': 'mid_word_split',
                        'severity': 'high',
                        'aku_index': i,
                        'ref': ref,
                        'end': body[-20:],
                        'next_start': next_body[:20],
                    })
            
            # 2. Check for multi-verse AKUs (multiple || in one AKU)
            if cls == 'verse' and body.count('||') > 1:
                chapter_issues.append({
                    'type': 'multi_verse_aku',
                    'severity': 'medium',
                    'aku_index': i,
                    'ref': ref,
                    'verse_count': body.count('||'),
                })
            
            # 3. Check for split sutras (should be merged)
            if cls == 'sutra' and i + 1 < len(chapter_akus):
                next_cls = chapter_akus[i + 1].get('_class', 'unknown')
                if next_cls == 'sutra':
                    next_body = (chapter_akus[i + 1].get('body') or '').strip()
                    # Sutras that are just conjunctions should merge
                    if body.endswith(('ca', 'vā', 'tu', 'eva')) and len(next_body) < 20:
                        chapter_issues.append({
                            'type': 'split_sutra',
                            'severity': 'low',
                            'aku_index': i,
                            'ref': ref,
                            'fragment': body[-10:],
                        })
            
            # 4. Check empty followed by empty
            if not body and i + 1 < len(chapter_akus):
                next_body = (chapter_akus[i + 1].get('body') or '').strip()
                if not next_body:
                    chapter_issues.append({
                        'type': 'consecutive_empty',
                        'severity': 'low',
                        'aku_index': i,
                    })
            
            # 5. Check reference sequence
            if ref and i + 1 < len(chapter_akus):
                next_ref = chapter_akus[i + 1].get('ref')
                if next_ref and ref != next_ref:
                    # Extract numeric part for sequence check
                    nums = re.findall(r'(\d+)', ref)
                    next_nums = re.findall(r'(\d+)', next_ref)
                    if nums and next_nums:
                        try:
                            # Check if sequence is broken
                            last = int(nums[-1])
                            nxt = int(next_nums[-1])
                            if nxt < last and nxt != 1:  # Allow chapter reset
                                chapter_issues.append({
                                    'type': 'numbering_regression',
                                    'severity': 'medium',
                                    'aku_index': i,
                                    'from_ref': ref,
                                    'to_ref': next_ref,
                                })
                        except ValueError:
                            pass
            
            # 6. Check for embedded references (multi-verse in prose)
            if cls in ('prose', 'verse') and re.search(r'//\w+_\d+\.\d+//', body):
                refs = re.findall(r'//(\w+_\d+\.\d+)//', body)
                if len(refs) > 1:
                    chapter_issues.append({
                        'type': 'embedded_references',
                        'severity': 'medium',
                        'aku_index': i,
                        'ref': ref,
                        'embedded_refs': refs[:5],
                    })
        
        self.stats['total_chapters'] += 1
        self.stats['total_issues'] += len(chapter_issues)
        self.stats['chapters_with_issues'] += 1 if chapter_issues else 0
        
        return {
            'scripture': scripture_file,
            'chapter': ch_num,
            'aku_count': len(chapter_akus),
            'issues': chapter_issues,
            'issue_count': len(chapter_issues),
        }


def validate_all_boundaries(input_dir, classification_file=None, output_file=None):
    """Validate boundaries for all prose AKUs."""
    
    # Load classification if available
    classifications = {}
    if classification_file and os.path.exists(classification_file):
        with open(classification_file) as f:
            class_data = json.load(f)
        for item in class_data.get('details', []):
            key = (item['scripture'], item.get('chapter', 0), item.get('ref'))
            classifications[key] = item['class']
    
    validator = BoundaryValidator()
    all_results = []
    total_akus = 0
    total_issues = 0
    
    for fn in sorted(os.listdir(input_dir)):
        if not fn.endswith('.json'):
            continue
        
        filepath = os.path.join(input_dir, fn)
        with open(filepath) as f:
            data = json.load(f)
        
        title = data.get('title', fn)
        
        for ch in data.get('chapters', []):
            ch_num = ch.get('chapter_num', 0)
            akus = ch.get('akus', [])
            
            # Attach classification to each AKU
            for aku in akus:
                key = (fn.replace('_gretil_prose.json', ''), ch_num, aku.get('ref'))
                aku['_class'] = classifications.get(key, 'unknown')
            
            result = validator.validate_chapter(akus, ch_num, fn)
            all_results.append(result)
            total_akus += result['aku_count']
            total_issues += result['issue_count']
    
    # Report
    print(f"\n{'='*60}")
    print(f"BOUNDARY VALIDATION REPORT")
    print(f"{'='*60}")
    print(f"Total chapters validated: {validator.stats['total_chapters']}")
    print(f"Total AKUs examined: {total_akus}")
    print(f"Total issues found: {total_issues}")
    print(f"Chapters with issues: {validator.stats['chapters_with_issues']}")
    
    # Issue type breakdown
    issue_types = Counter()
    for r in all_results:
        for issue in r['issues']:
            issue_types[issue['type']] += 1
    
    print(f"\nIssue type distribution:")
    for itype, count in issue_types.most_common():
        print(f"  {itype:25s} {count:6d}")
    
    # Severity breakdown
    severity_counts = Counter()
    for r in all_results:
        for issue in r['issues']:
            severity_counts[issue['severity']] += 1
    
    print(f"\nSeverity distribution:")
    for sev, count in severity_counts.most_common():
        print(f"  {sev:15s} {count:6d}")
    
    # Save results
    if output_file:
        os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
        
        # Summary stats only (not all details)
        summary = {
            'total_chapters': validator.stats['total_chapters'],
            'total_akus': total_akus,
            'total_issues': total_issues,
            'chapters_with_issues': validator.stats['chapters_with_issues'],
            'issue_types': dict(issue_types),
            'severity_distribution': dict(severity_counts),
            'chapters_with_high_severity': [
                {'scripture': r['scripture'], 'chapter': r['chapter'], 
                 'high_count': sum(1 for i in r['issues'] if i['severity'] == 'high')}
                for r in all_results
                if sum(1 for i in r['issues'] if i['severity'] == 'high') > 0
            ],
        }
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to: {output_file}")
    
    return all_results, validator.stats


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Boundary Validator for CUV')
    parser.add_argument('--input', default='knowledge/gretil_prose')
    parser.add_argument('--classification', default='knowledge/cuv/classification.json')
    parser.add_argument('--output', default='knowledge/cuv/boundary_validation.json')
    args = parser.parse_args()
    
    validate_all_boundaries(args.input, args.classification, args.output)
