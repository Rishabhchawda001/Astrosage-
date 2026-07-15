#!/usr/bin/env python3
"""
Verse Splitter — CUV Step 2 (Boundary Repair)

Splits multi-verse AKUs into individual verses.
Handles:
- Double danda (||) delimited verses
- Embedded verse references (//BhP_1.1.1//)
- Multi-line verse blocks

Usage:
  python3 scripts/verse_splitter.py [--input DIR] [--output DIR] [--dry-run]
"""

import json
import os
import re
import sys
from collections import Counter


def split_by_danda(body):
    """Split text on double danda into individual verses."""
    # Split on || but keep the danda marker
    parts = re.split(r'\|\|', body)
    verses = []
    for part in parts:
        text = part.strip()
        if text:
            # Remove trailing single danda if present
            text = re.sub(r'\|\s*$', '', text).strip()
            if text:
                verses.append(text + ' ||')
    return verses


def split_by_embedded_refs(body):
    """Split text with embedded verse references."""
    # Pattern: //Ref_Text// or //Ref//
    parts = re.split(r'//(\w+_\d+\.\d+)//', body)
    verses = []
    i = 1
    while i < len(parts) - 1:
        ref = parts[i]
        text = parts[i + 1].strip() if i + 1 < len(parts) else ''
        if text:
            verses.append({'ref': ref, 'text': text})
        i += 2
    return verses


def split_multi_verse_aku(aku, chapter_num):
    """
    Split a multi-verse AKU into individual verse AKUs.
    Returns list of new AKU dicts.
    """
    body = (aku.get('body') or '').strip()
    ref = aku.get('ref')
    
    if not body:
        return [aku]
    
    # Check for embedded references first
    embedded = re.findall(r'//(\w+_\d+\.\d+)//', body)
    if len(embedded) > 1:
        # Has embedded verse references
        parts = split_by_embedded_refs(body)
        if len(parts) > 1:
            result = []
            for part in parts:
                result.append({
                    'ref': part['ref'],
                    'body': part['text'],
                })
            return result
    
    # Check for double danda splitting
    if body.count('||') > 1:
        verses = split_by_danda(body)
        if len(verses) > 1:
            return [{'ref': ref, 'body': v} for v in verses]
    
    # No split needed
    return [aku]


def process_scripture(input_file, output_file=None, dry_run=False):
    """Process a single scripture file, splitting multi-verse AKUs."""
    
    with open(input_file) as f:
        data = json.load(f)
    
    title = data.get('title', '')
    total_before = 0
    total_after = 0
    splits_made = 0
    
    new_chapters = []
    
    for ch in data.get('chapters', []):
        ch_num = ch.get('chapter_num', 0)
        akus = ch.get('akus', [])
        total_before += len(akus)
        
        new_akus = []
        for aku in akus:
            body = (aku.get('body') or '').strip()
            
            # Check if this is a multi-verse AKU
            is_multi = False
            if '||' in body and body.count('||') > 1:
                is_multi = True
            embedded = re.findall(r'//(\w+_\d+\.\d+)//', body)
            if len(embedded) > 1:
                is_multi = True
            
            if is_multi:
                split_akus = split_multi_verse_aku(aku, ch_num)
                new_akus.extend(split_akus)
                splits_made += 1
            else:
                new_akus.append(aku)
        
        total_after += len(new_akus)
        new_chapters.append({
            'chapter_num': ch_num,
            'aku_count': len(new_akus),
            'akus': new_akus,
        })
    
    result = {
        'file': data.get('file', ''),
        'title': title,
        'total_chapters': data.get('total_chapters', len(new_chapters)),
        'total_akus': total_after,
        'chapters': new_chapters,
    }
    
    if output_file and not dry_run:
        os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    
    return {
        'title': title,
        'before': total_before,
        'after': total_after,
        'splits': splits_made,
    }


def process_all(input_dir, output_dir, dry_run=False):
    """Process all prose AKU files."""
    
    stats = []
    total_before = 0
    total_after = 0
    total_splits = 0
    
    for fn in sorted(os.listdir(input_dir)):
        if not fn.endswith('.json'):
            continue
        
        input_file = os.path.join(input_dir, fn)
        output_file = os.path.join(output_dir, fn) if output_dir else None
        
        result = process_scripture(input_file, output_file, dry_run)
        stats.append(result)
        total_before += result['before']
        total_after += result['after']
        total_splits += result['splits']
    
    print(f"\n{'='*60}")
    print(f"VERSE SPLITTING REPORT")
    print(f"{'='*60}")
    print(f"Scriptures processed: {len(stats)}")
    print(f"Total AKUs before: {total_before}")
    print(f"Total AKUs after: {total_after}")
    print(f"Net change: +{total_after - total_before}")
    print(f"Multi-verse AKUs split: {total_splits}")
    
    # Top scriptures by splits
    print(f"\nScriptures with most splits:")
    for s in sorted(stats, key=lambda x: -x['splits'])[:10]:
        if s['splits'] > 0:
            print(f"  {s['title'][:45]:45s} {s['splits']:5d} splits ({s['before']}→{s['after']})")
    
    return stats


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Verse Splitter for CUV')
    parser.add_argument('--input', default='knowledge/gretil_prose')
    parser.add_argument('--output', default='knowledge/cuv/gretil_prose_split')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    
    if not args.dry_run:
        os.makedirs(args.output, exist_ok=True)
    
    process_all(args.input, args.output if not args.dry_run else None, args.dry_run)
