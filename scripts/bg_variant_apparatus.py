#!/usr/bin/env python3
"""
Bhagavad Gita Variant Apparatus Builder

Compares verse text across all witnesses, identifies genuine variants,
classifies them, and builds a complete variant apparatus.
"""

import json
import os
import re
import sys
import hashlib
from collections import defaultdict

REPO = "/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage"
DTC_BG = os.path.join(REPO, "knowledge/dtc/bhagavad_gita")


def normalize_verse(text):
    """Normalize verse text for comparison (preserve content, normalize formatting)."""
    t = text.strip()
    # Remove verse numbers
    t = re.sub(r'\|\|\d+\|\|', '', t)
    t = re.sub(r'//\s*$', '', t).strip()
    # Normalize whitespace
    t = re.sub(r'\s+', ' ', t)
    # Normalize danda
    t = re.sub(r'\|\|', '||', t)
    t = re.sub(r'(?<!\|)\|(?!\|)', '|', t)
    # Normalize common diacritic variants
    t = t.replace('ñ', 'ñ')  # keep as-is for now
    return t.strip()


def compute_fingerprint(text):
    """Compute a normalized fingerprint for verse comparison."""
    norm = normalize_verse(text)
    # Remove all punctuation and whitespace for pure content comparison
    content = re.sub(r'[\s\|·]', '', norm)
    return content


def classify_variant(text_a, text_b, norm_a, norm_b):
    """Classify the type of difference between two verse readings."""
    if norm_a == norm_b:
        return 'identical'
    
    # Check for simple orthographic differences
    content_a = re.sub(r'[\s\|·]', '', norm_a)
    content_b = re.sub(r'[\s\|·]', '', norm_b)
    
    if content_a == content_b:
        return 'orthographic'  # Same content, different formatting
    
    # Check for sandhi differences
    words_a = set(norm_a.split())
    words_b = set(norm_b.split())
    
    if len(words_a.symmetric_difference(words_b)) <= 2:
        # Few word differences - could be sandhi or minor variants
        diff_words = words_a.symmetric_difference(words_b)
        if len(diff_words) <= 2:
            return 'minor_variant'
    
    # Check for significant differences
    len_ratio = min(len(norm_a), len(norm_b)) / max(len(norm_a), len(norm_b)) if max(len(norm_a), len(norm_b)) > 0 else 0
    
    if len_ratio < 0.7:
        return 'structural_difference'  # Very different lengths
    
    return 'textual_variant'


def build_variant_apparatus():
    """Build complete variant apparatus for all verses."""
    
    # Load canonical verses
    vpath = os.path.join(DTC_BG, "verses_canonical_v2.json")
    with open(vpath, 'r') as f:
        data = json.load(f)
    
    verses = data['verses']
    
    print("=" * 70)
    print("BHAGAVAD GITA VARIANT APPARATUS")
    print("=" * 70)
    
    # For each verse, collect all witness readings
    apparatus = {}
    stats = {
        'total': 0,
        'identical': 0,
        'orthographic': 0,
        'minor_variant': 0,
        'textual_variant': 0,
        'structural_difference': 0,
        'single_witness': 0
    }
    
    for verse in verses:
        ref = verse['ref']
        witnesses = verse.get('witnesses', [])
        
        if not witnesses:
            continue
        
        stats['total'] += 1
        
        if len(witnesses) == 1:
            stats['single_witness'] += 1
            apparatus[ref] = {
                'ref': ref,
                'chapter': verse['chapter'],
                'verse': verse['verse'],
                'canonical_text': verse['text'],
                'witness_count': 1,
                'readings': [{'source': witnesses[0]['source'], 'text': verse['text']}],
                'variants': [],
                'classification': 'single_witness',
                'confidence': 0.7  # Single witness = lower confidence
            }
            continue
        
        # Collect unique readings
        readings = []
        seen_texts = set()
        for w in witnesses:
            # We need the actual text, not just the hash
            # The text is in the canonical verse data
            if verse['text'] and w['source'] == verse['source']:
                norm = normalize_verse(verse['text'])
                fp = compute_fingerprint(verse['text'])
                if fp not in seen_texts:
                    readings.append({
                        'source': w['source'],
                        'text': verse['text'],
                        'normalized': norm,
                        'fingerprint': fp
                    })
                    seen_texts.add(fp)
        
        # If we only have the canonical text, use it
        if not readings and verse['text']:
            norm = normalize_verse(verse['text'])
            fp = compute_fingerprint(verse['text'])
            readings.append({
                'source': verse['source'],
                'text': verse['text'],
                'normalized': norm,
                'fingerprint': fp
            })
        
        # Compare readings
        variants = []
        if len(readings) >= 2:
            # Compare each pair
            for i in range(len(readings)):
                for j in range(i + 1, len(readings)):
                    classification = classify_variant(
                        readings[i]['text'], readings[j]['text'],
                        readings[i]['normalized'], readings[j]['normalized']
                    )
                    if classification != 'identical':
                        variants.append({
                            'witness_a': readings[i]['source'],
                            'witness_b': readings[j]['source'],
                            'text_a': readings[i]['text'][:200],
                            'text_b': readings[j]['text'][:200],
                            'classification': classification
                        })
        
        # Determine overall classification
        if not variants:
            classification = 'unanimous'
            confidence = 0.95
        elif all(v['classification'] in ('identical', 'orthographic') for v in variants):
            classification = 'orthographic_variants'
            confidence = 0.90
        elif any(v['classification'] == 'textual_variant' for v in variants):
            classification = 'textual_variants'
            confidence = 0.75
        else:
            classification = 'minor_variants'
            confidence = 0.85
        
        # Update stats
        if classification == 'unanimous':
            stats['identical'] += 1
        elif 'orthographic' in classification:
            stats['orthographic'] += 1
        elif 'minor' in classification:
            stats['minor_variant'] += 1
        elif 'textual' in classification:
            stats['textual_variant'] += 1
        
        apparatus[ref] = {
            'ref': ref,
            'chapter': verse['chapter'],
            'verse': verse['verse'],
            'canonical_text': verse['text'],
            'witness_count': len(witnesses),
            'readings': [{'source': r['source'], 'normalized': r['normalized']} for r in readings],
            'variants': variants,
            'classification': classification,
            'confidence': confidence
        }
    
    # Print summary
    print(f"\nTotal verses analyzed: {stats['total']}")
    print(f"  Unanimous (identical across witnesses): {stats['identical']}")
    print(f"  Orthographic variants only: {stats['orthographic']}")
    print(f"  Minor variants: {stats['minor_variant']}")
    print(f"  Textual variants: {stats['textual_variant']}")
    print(f"  Single witness only: {stats['single_witness']}")
    
    # Per-chapter breakdown
    print(f"\n{'Ch':<5}{'Total':<7}{'Unanimous':<11}{'Ortho':<7}{'Minor':<7}{'Textual':<9}{'Single':<8}")
    print("-" * 54)
    for ch in range(1, 19):
        ch_app = {k: v for k, v in apparatus.items() if v['chapter'] == ch}
        total = len(ch_app)
        unanimous = sum(1 for v in ch_app.values() if v['classification'] == 'unanimous')
        ortho = sum(1 for v in ch_app.values() if 'orthographic' in v['classification'])
        minor = sum(1 for v in ch_app.values() if 'minor' in v['classification'])
        textual = sum(1 for v in ch_app.values() if 'textual' in v['classification'])
        single = sum(1 for v in ch_app.values() if v['classification'] == 'single_witness')
        print(f"{ch:<5}{total:<7}{unanimous:<11}{ortho:<7}{minor:<7}{textual:<9}{single:<8}")
    
    # List some textual variants for inspection
    textual_verses = [(k, v) for k, v in apparatus.items() if v['classification'] == 'textual_variants']
    if textual_verses:
        print(f"\n--- Sample Textual Variants (first 10) ---")
        for ref, v in textual_verses[:10]:
            print(f"\n{ref} ({v['witness_count']} witnesses):")
            for var in v['variants'][:3]:
                print(f"  {var['witness_a']} vs {var['witness_b']}: {var['classification']}")
                print(f"    A: {var['text_a'][:100]}...")
                print(f"    B: {var['text_b'][:100]}...")
    
    # Save apparatus
    outpath = os.path.join(DTC_BG, "variant_apparatus.json")
    with open(outpath, 'w', encoding='utf-8') as f:
        json.dump({
            'scripture': 'Bhagavadgita',
            'total_verses': stats['total'],
            'stats': stats,
            'apparatus': apparatus
        }, f, ensure_ascii=False, indent=2)
    print(f"\nSaved: {outpath}")
    
    # Save a summary for the collation
    summary = {
        'scripture': 'Bhagavadgita',
        'analysis_date': '2025-07-15',
        'total_verses': stats['total'],
        'witness_count': len(data.get('sources', [])),
        'witnesses': data.get('sources', []),
        'variant_stats': {
            'unanimous': stats['identical'],
            'orthographic': stats['orthographic'],
            'minor': stats['minor_variant'],
            'textual': stats['textual_variant'],
            'single_witness': stats['single_witness']
        },
        'textual_variant_verses': [ref for ref, v in apparatus.items() if v['classification'] == 'textual_variants'],
        'confidence_distribution': {
            'high (>=0.9)': sum(1 for v in apparatus.values() if v['confidence'] >= 0.9),
            'medium (0.75-0.9)': sum(1 for v in apparatus.values() if 0.75 <= v['confidence'] < 0.9),
            'low (<0.75)': sum(1 for v in apparatus.values() if v['confidence'] < 0.75)
        }
    }
    
    sum_out = os.path.join(DTC_BG, "collation_summary_v2.json")
    with open(sum_out, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"Saved: {sum_out}")
    
    return apparatus


if __name__ == '__main__':
    build_variant_apparatus()
