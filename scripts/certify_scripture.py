#!/usr/bin/env python3
"""
Scripture Certifier — CUV Step 10

Certifies a single scripture by:
1. Classifying all AKUs
2. Validating boundaries
3. Checking Unicode integrity
4. Verifying numbering sequences
5. Producing a certification report

Usage:
  python3 scripts/certify_scripture.py --scripture FILE [--output DIR]
"""

import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

# Import classifiers
sys.path.insert(0, os.path.dirname(__file__))
from aku_classifier import AKUClassifier


class ScriptureCertifier:
    """Certifies a single scripture's canonical units."""
    
    def __init__(self, scripture_file, title=None):
        self.file = scripture_file
        self.title = title or scripture_file
        self.classifier = AKUClassifier({'title': title or '', 'file': scripture_file})
        
        self.results = {
            'file': scripture_file,
            'title': self.title,
            'status': 'pending',
            'total_akus': 0,
            'certified_akus': 0,
            'issues': [],
            'class_distribution': Counter(),
            'chapter_stats': [],
            'numbering_issues': [],
            'unicode_issues': [],
            'boundary_issues': [],
        }
    
    def certify(self, data):
        """Run full certification on loaded scripture data."""
        
        total_akus = 0
        certified = 0
        
        for ch in data.get('chapters', []):
            ch_num = ch.get('chapter_num', 0)
            akus = ch.get('akus', [])
            ch_result = {
                'chapter': ch_num,
                'total': len(akus),
                'certified': 0,
                'issues': [],
            }
            
            # Classify all AKUs
            classified = []
            for aku in akus:
                body = (aku.get('body') or '').strip()
                ref = aku.get('ref')
                cls, confidence, reasons = self.classifier.classify(ref, body)
                classified.append({
                    'ref': ref,
                    'body': body,
                    'class': cls,
                    'confidence': confidence,
                    'reasons': reasons,
                    'body_len': len(body),
                })
                self.results['class_distribution'][cls] += 1
                total_akus += 1
            
            # Validate numbering
            numbering_issues = self._validate_numbering(classified, ch_num)
            ch_result['issues'].extend(numbering_issues)
            self.results['numbering_issues'].extend(numbering_issues)
            
            # Validate boundaries
            boundary_issues = self._validate_boundaries(classified, ch_num)
            ch_result['issues'].extend(boundary_issues)
            self.results['boundary_issues'].extend(boundary_issues)
            
            # Validate Unicode
            unicode_issues = self._validate_unicode_batch(classified, ch_num)
            ch_result['issues'].extend(unicode_issues)
            self.results['unicode_issues'].extend(unicode_issues)
            
            # Count certified (no issues = certified)
            if not ch_result['issues']:
                ch_result['certified'] = len(akus)
                certified += len(akus)
            else:
                # Some AKUs may still be certified
                for aku in classified:
                    if aku['confidence'] >= 80 and not any(
                        i.get('aku_ref') == aku['ref'] for i in ch_result['issues']
                    ):
                        ch_result['certified'] += 1
                        certified += 1
            
            self.results['chapter_stats'].append(ch_result)
        
        self.results['total_akus'] = total_akus
        self.results['certified_akus'] = certified
        
        # Determine status
        if certified == total_akus:
            self.results['status'] = 'certified'
        elif certified > total_akus * 0.9:
            self.results['status'] = 'mostly_certified'
        elif certified > total_akus * 0.5:
            self.results['status'] = 'partially_certified'
        else:
            self.results['status'] = 'needs_work'
        
        return self.results
    
    def _validate_numbering(self, classified, ch_num):
        """Validate reference numbering sequence."""
        issues = []
        prev_num = None
        
        for aku in classified:
            ref = aku['ref']
            if ref is None:
                continue
            
            # Extract numeric parts
            nums = re.findall(r'(\d+)', ref)
            if not nums:
                continue
            
            # Try to get the last number as sequence
            try:
                current_num = int(nums[-1])
                if prev_num is not None and current_num < prev_num and current_num != 1:
                    issues.append({
                        'type': 'numbering_regression',
                        'severity': 'medium',
                        'chapter': ch_num,
                        'aku_ref': ref,
                        'from': prev_num,
                        'to': current_num,
                    })
                prev_num = current_num
            except ValueError:
                pass
        
        return issues
    
    def _validate_boundaries(self, classified, ch_num):
        """Validate AKU boundaries."""
        issues = []
        
        for i, aku in enumerate(classified):
            body = aku['body']
            
            # Empty AKU
            if not body:
                issues.append({
                    'type': 'empty_aku',
                    'severity': 'low',
                    'chapter': ch_num,
                    'aku_ref': aku['ref'],
                })
            
            # OCR artifact (just punctuation/brackets)
            elif len(body) < 3 and not any(c.isalpha() for c in body):
                issues.append({
                    'type': 'ocr_artifact',
                    'severity': 'medium',
                    'chapter': ch_num,
                    'aku_ref': aku['ref'],
                    'body': body,
                })
            
            # Mid-word split detection
            if body and body[-1].isalpha() and i + 1 < len(classified):
                next_body = classified[i + 1]['body']
                if next_body and next_body[0].islower():
                    # Check if this is a real split vs sentence boundary
                    end_word = body.split()[-1] if body.split() else ''
                    start_word = next_body.split()[0] if next_body.split() else ''
                    if len(end_word) > 5 and len(start_word) > 4:
                        issues.append({
                            'type': 'potential_mid_word_split',
                            'severity': 'low',
                            'chapter': ch_num,
                            'aku_ref': aku['ref'],
                            'end': end_word[-10:],
                            'start': start_word[:10],
                        })
        
        return issues
    
    def _validate_unicode_batch(self, classified, ch_num):
        """Validate Unicode for a batch of AKUs."""
        issues = []
        
        for aku in classified:
            body = aku['body']
            if not body:
                continue
            
            # Check for replacement characters
            if '\ufffd' in body:
                issues.append({
                    'type': 'replacement_char',
                    'severity': 'high',
                    'chapter': ch_num,
                    'aku_ref': aku['ref'],
                    'count': body.count('\ufffd'),
                })
            
            # Check normalization
            nfc = unicodedata.normalize('NFC', body)
            if body != nfc:
                issues.append({
                    'type': 'normalization',
                    'severity': 'medium',
                    'chapter': ch_num,
                    'aku_ref': aku['ref'],
                })
        
        return issues


def certify_scripture(input_file, output_file=None):
    """Certify a single scripture file."""
    
    with open(input_file) as f:
        data = json.load(f)
    
    title = data.get('title', os.path.basename(input_file))
    certifier = ScriptureCertifier(os.path.basename(input_file), title)
    results = certifier.certify(data)
    
    # Print report
    print(f"\n{'='*60}")
    print(f"CERTIFICATION REPORT: {title}")
    print(f"{'='*60}")
    print(f"Status: {results['status'].upper()}")
    print(f"Total AKUs: {results['total_akus']}")
    print(f"Certified: {results['certified_akus']} ({100*results['certified_akus']/max(results['total_akus'],1):.1f}%)")
    
    print(f"\nClass distribution:")
    for cls, count in results['class_distribution'].most_common():
        print(f"  {cls:25s} {count:6d}")
    
    print(f"\nIssues by type:")
    issue_types = Counter()
    for issue in results['numbering_issues'] + results['boundary_issues'] + results['unicode_issues']:
        issue_types[issue['type']] += 1
    for itype, count in issue_types.most_common():
        print(f"  {itype:30s} {count:6d}")
    
    if output_file:
        os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
        # Convert Counter to dict for JSON
        results['class_distribution'] = dict(results['class_distribution'])
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to: {output_file}")
    
    return results


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Scripture Certifier for CUV')
    parser.add_argument('--scripture', required=True, help='Path to prose JSON file')
    parser.add_argument('--output', help='Output file for certification results')
    args = parser.parse_args()
    
    certify_scripture(args.scripture, args.output)
