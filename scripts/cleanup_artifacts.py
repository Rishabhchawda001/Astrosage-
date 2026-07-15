#!/usr/bin/env python3
"""
Cleanup Artifacts — Remove parser artifacts from prose AKUs

Removes:
- Empty AKUs
- Isolated punctuation (/, ||, ), etc.)
- Whitespace-only AKUs
- Equals patterns
- Short non-alpha strings

Usage:
  python3 scripts/cleanup_artifacts.py [--input DIR] [--output DIR] [--dry-run]
"""

import json
import os
import re
import sys
from collections import Counter


def is_artifact(body):
    """Determine if an AKU body is a parser artifact."""
    body = body.strip()
    
    if not body:
        return True, 'empty'
    
    # Isolated punctuation
    if body in (')', '(', '[', ']', '{', '}', '<', '>', '.', ',', ';', ':', '?', '!', '/', '|', '||'):
        return True, 'isolated_punctuation'
    
    # Short non-alpha (no alphabetic characters)
    if len(body) < 4 and not any(c.isalpha() for c in body):
        return True, 'short_non_alpha'
    
    # Whitespace-only or equals patterns
    if re.match(r'^[\s=]+$', body):
        return True, 'whitespace_pattern'
    
    # Just digits
    if re.match(r'^\d+$', body):
        return True, 'digit_only'
    
    # Just a reference marker
    if re.match(r'^\d+\.\d+', body) and len(body) < 20:
        return True, 'reference_marker'
    
    return False, None


def cleanup_scripture(input_file, output_file=None, dry_run=False):
    """Clean up artifacts in a single scripture file."""
    
    with open(input_file) as f:
        data = json.load(f)
    
    title = data.get('title', '')
    removed = 0
    kept = 0
    removal_types = Counter()
    
    new_chapters = []
    
    for ch in data.get('chapters', []):
        ch_num = ch.get('chapter_num', 0)
        akus = ch.get('akus', [])
        
        new_akus = []
        for aku in akus:
            body = (aku.get('body') or '').strip()
            is_art, art_type = is_artifact(body)
            
            if is_art:
                removed += 1
                removal_types[art_type] += 1
            else:
                new_akus.append(aku)
                kept += 1
        
        if new_akus:  # Only keep chapters with content
            new_chapters.append({
                'chapter_num': ch_num,
                'aku_count': len(new_akus),
                'akus': new_akus,
            })
    
    result = {
        'file': data.get('file', ''),
        'title': title,
        'total_chapters': len(new_chapters),
        'total_akus': kept,
        'chapters': new_chapters,
    }
    
    if output_file and not dry_run:
        os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    
    return {
        'title': title,
        'before': removed + kept,
        'after': kept,
        'removed': removed,
        'types': dict(removal_types),
    }


def cleanup_all(input_dir, output_dir, dry_run=False):
    """Clean up all prose AKU files."""
    
    if not dry_run:
        os.makedirs(output_dir, exist_ok=True)
    
    stats = []
    total_before = 0
    total_after = 0
    total_removed = 0
    
    for fn in sorted(os.listdir(input_dir)):
        if not fn.endswith('.json'):
            continue
        
        input_file = os.path.join(input_dir, fn)
        output_file = os.path.join(output_dir, fn) if not dry_run else None
        
        result = cleanup_scripture(input_file, output_file, dry_run)
        stats.append(result)
        total_before += result['before']
        total_after += result['after']
        total_removed += result['removed']
    
    print(f"\n{'='*60}")
    print(f"ARTIFACT CLEANUP REPORT")
    print(f"{'='*60}")
    print(f"Scriptures processed: {len(stats)}")
    print(f"Total AKUs before: {total_before}")
    print(f"Total AKUs after: {total_after}")
    print(f"Artifacts removed: {total_removed} ({100*total_removed/total_before:.1f}%)")
    
    # Removal type breakdown
    all_types = Counter()
    for s in stats:
        for t, c in s['types'].items():
            all_types[t] += c
    
    print(f"\nRemoval types:")
    for t, c in all_types.most_common():
        print(f"  {t:25s} {c:7d}")
    
    # Top scriptures by removal
    print(f"\nScriptures with most removals:")
    for s in sorted(stats, key=lambda x: -x['removed'])[:10]:
        if s['removed'] > 0:
            pct = 100 * s['removed'] / max(s['before'], 1)
            print(f"  {s['title'][:45]:45s} {s['removed']:6d} removed ({pct:.1f}%)")
    
    return stats


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Cleanup Artifacts')
    parser.add_argument('--input', default='knowledge/gretil_prose')
    parser.add_argument('--output', default='knowledge/cuv/gretil_prose_clean')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    
    cleanup_all(args.input, args.output, args.dry_run)
