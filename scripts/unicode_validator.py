#!/usr/bin/env python3
"""
Unicode Validator — Canonical Unit Validation (CUV) Step 6-7

Validates Unicode integrity of every AKU:
- NFC/NFD normalization
- Replacement characters (U+FFFD)
- Sanskrit-specific: ligatures, visarga, anusvara, matras
- Broken UTF-8 patterns
- Invisible corruption

Usage:
  python3 scripts/unicode_validator.py [--input DIR] [--output FILE]
"""

import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict


# Sanskrit/Devanagari Unicode ranges
DEVANAGARI_RANGE = (0x0900, 0x097F)
DEVANAGARI_EXT_RANGE = (0xA8E0, 0xA8FF)
VEDIC_EXTENSIONS = (0x1CD0, 0x1CFF)

# Common Sanskrit diacritics (IAST)
IAST_MARKS = {
    'ā', 'ī', 'ū', 'ṛ', 'ṝ', 'ḷ', 'ṃ', 'ḥ', 'ś', 'ṣ', 'ṇ',
    'ṅ', 'ñ', 'ṭ', 'ḍ', 'ḍh', 'ṇh', 'th', 'ph', 'bh', 'ch', 'jh',
}

# Vedic accent markers
VEDIC_ACCENTS = set(range(0x1CD0, 0x1CFF + 1))

# Combining marks
COMBINING_CATEGORIES = {'Mn', 'Mc', 'Me'}


class UnicodeValidator:
    """Validates Unicode integrity of Sanskrit text."""
    
    def __init__(self):
        self.stats = Counter()
    
    def validate_text(self, text, ref=None):
        """
        Validate Unicode of a single text string.
        Returns list of issues found.
        """
        issues = []
        
        if not text:
            self.stats['empty'] += 1
            return issues
        
        # 1. Normalization check
        nfc = unicodedata.normalize('NFC', text)
        nfd = unicodedata.normalize('NFD', text)
        
        if text != nfc:
            self.stats['normalization_needed'] += 1
            issues.append({
                'type': 'normalization',
                'severity': 'medium',
                'detail': 'Text is not NFC normalized',
                'ref': ref,
            })
        
        # 2. Replacement characters
        if '\ufffd' in text:
            count = text.count('\ufffd')
            self.stats['replacement_chars'] += count
            issues.append({
                'type': 'replacement_char',
                'severity': 'high',
                'count': count,
                'ref': ref,
            })
        
        # 3. Character-by-character analysis
        for i, ch in enumerate(text):
            cp = ord(ch)
            cat = unicodedata.category(ch)
            
            # Invisible characters
            if cat == 'Cn':  # unassigned
                self.stats['unassigned'] += 1
                issues.append({
                    'type': 'unassigned_codepoint',
                    'severity': 'high',
                    'position': i,
                    'codepoint': f'U+{cp:04X}',
                    'ref': ref,
                })
            
            # Private use area
            if cat == 'Co':
                self.stats['private_use'] += 1
                issues.append({
                    'type': 'private_use',
                    'severity': 'high',
                    'position': i,
                    'codepoint': f'U+{cp:04X}',
                    'ref': ref,
                })
            
            # Control characters (except common ones)
            if cat.startswith('C') and cat not in ('Cn', 'Cc') and cp not in (0x200B, 0x200C, 0x200D, 0xFEFF):
                self.stats['control_chars'] += 1
                issues.append({
                    'type': 'control_char',
                    'severity': 'medium',
                    'position': i,
                    'codepoint': f'U+{cp:04X}',
                    'category': cat,
                    'ref': ref,
                })
        
        # 4. Sanskrit-specific checks
        # Check for broken combining sequences
        prev_was_consonant = False
        for i, ch in enumerate(text):
            cp = ord(ch)
            cat = unicodedata.category(ch)
            
            # Devanagari consonant check
            if 0x0915 <= cp <= 0x0939:  # Ka to Ha
                prev_was_consonant = True
            elif cat in COMBINING_CATEGORIES:
                if prev_was_consonant:
                    # Combining mark after consonant is normal (matra)
                    prev_was_consonant = False
                else:
                    # Orphan combining mark
                    self.stats['orphan_combining'] += 1
                    if issues is not None and len(issues) < 100:  # Limit
                        issues.append({
                            'type': 'orphan_combining',
                            'severity': 'low',
                            'position': i,
                            'codepoint': f'U+{cp:04X}',
                            'ref': ref,
                        })
            else:
                prev_was_consonant = False
        
        # 5. Visarga without preceding vowel/consonant
        for m in re.finditer(r'ḥ', text):
            pos = m.start()
            if pos > 0:
                prev_ch = text[pos - 1]
                prev_cat = unicodedata.category(prev_ch)
                if prev_cat == 'Zs':  # space before visarga
                    self.stats['spaced_visarga'] += 1
        
        # 6. Check for common OCR substitutions in Sanskrit
        # e.g., 'aa' instead of 'ā', 'ii' instead of 'ī'
        ocr_patterns = [
            (r'(?<!\w)aa(?!\w)', 'possible_ocr_aa'),
            (r'(?<!\w)ii(?!\w)', 'possible_ocr_ii'),
            (r'(?<!\w)uu(?!\w)', 'possible_ocr_uu'),
            (r'(?<!\w)RR(?!\w)', 'possible_ocr_RR'),
        ]
        for pattern, issue_type in ocr_patterns:
            matches = re.findall(pattern, text)
            if matches:
                self.stats[issue_type] += len(matches)
        
        self.stats['total_texts'] += 1
        self.stats['total_chars'] += len(text)
        self.stats['total_issues'] += len(issues)
        
        return issues
    
    def get_summary(self):
        """Return validation summary."""
        return {
            'total_texts': self.stats['total_texts'],
            'total_chars': self.stats['total_chars'],
            'total_issues': self.stats['total_issues'],
            'normalization_needed': self.stats['normalization_needed'],
            'replacement_chars': self.stats['replacement_chars'],
            'unassigned': self.stats['unassigned'],
            'private_use': self.stats['private_use'],
            'control_chars': self.stats['control_chars'],
            'orphan_combining': self.stats['orphan_combining'],
            'spaced_visarga': self.stats['spaced_visarga'],
        }


def validate_all_unicode(input_dir, output_file=None):
    """Validate Unicode for all prose AKUs."""
    
    validator = UnicodeValidator()
    per_scripture = {}
    
    for fn in sorted(os.listdir(input_dir)):
        if not fn.endswith('.json'):
            continue
        
        filepath = os.path.join(input_dir, fn)
        with open(filepath) as f:
            data = json.load(f)
        
        title = data.get('title', fn)
        scripture_issues = []
        
        for ch in data.get('chapters', []):
            ch_num = ch.get('chapter_num', 0)
            for aku in ch.get('akus', []):
                body = aku.get('body', '')
                ref = aku.get('ref')
                issues = validator.validate_text(body, ref)
                if issues:
                    scripture_issues.extend(issues)
        
        per_scripture[fn] = {
            'title': title,
            'issue_count': len(scripture_issues),
        }
    
    summary = validator.get_summary()
    
    print(f"\n{'='*60}")
    print(f"UNICODE VALIDATION REPORT")
    print(f"{'='*60}")
    print(f"Total texts validated: {summary['total_texts']}")
    print(f"Total characters: {summary['total_chars']}")
    print(f"Total issues: {summary['total_issues']}")
    print(f"\nIssue breakdown:")
    for key, val in sorted(summary.items()):
        if val > 0 and key not in ('total_texts', 'total_chars', 'total_issues'):
            print(f"  {key:30s} {val:8d}")
    
    # Top scriptures with issues
    print(f"\nScriptures with most Unicode issues:")
    sorted_sciptures = sorted(per_scripture.items(), key=lambda x: -x[1]['issue_count'])
    for fn, stats in sorted_sciptures[:10]:
        if stats['issue_count'] > 0:
            print(f"  {stats['title'][:45]:45s} {stats['issue_count']:6d} issues")
    
    if output_file:
        os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump({
                'summary': summary,
                'per_scripture': per_scripture,
            }, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to: {output_file}")
    
    return summary, per_scripture


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Unicode Validator for CUV')
    parser.add_argument('--input', default='knowledge/gretil_prose')
    parser.add_argument('--output', default='knowledge/cuv/unicode_validation.json')
    args = parser.parse_args()
    
    validate_all_unicode(args.input, args.output)
