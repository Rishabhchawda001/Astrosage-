#!/usr/bin/env python3
"""
Multi-Witness Collation Engine — EBCC Stage 2

Normalizes, aligns, and collates multiple witnesses for a scripture.
Produces variant apparatus and confidence scores.

Usage:
  python3 scripts/collation_engine.py --scripture NAME [--witnesses FILE1 FILE2 ...]
"""

import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict


def normalize_devanagari(text):
    """Normalize Devanagari text for comparison."""
    # NFC normalization
    text = unicodedata.normalize('NFC', text)
    
    # Normalize common OCR substitutions
    replacements = {
        '\u0964': '॥',   # Devanagari danda
        '\u0965': '॥',   # Devanagari double danda
        '\u093C': '',     # Nukta (remove)
        '\u094D': '',     # Virama (remove for comparison)
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Normalize danda
    text = re.sub(r'\।\।+', '॥', text)
    text = re.sub(r'\।(?!\।)', '|', text)
    
    return text.strip()


def normalize_roman(text):
    """Normalize Roman/Sanskrit text for comparison."""
    text = unicodedata.normalize('NFC', text)
    
    # Normalize common diacritics
    text = re.sub(r'\s+', ' ', text)
    
    # Normalize danda
    text = re.sub(r'\|\|+', '॥', text)
    text = re.sub(r'(?<!\|)\|(?!\|)', '|', text)
    
    return text.strip()


def extract_verses_from_text(text, script='devanagari'):
    """Extract individual verses from continuous text."""
    if script == 'devanagari':
        # Split on danda patterns
        verses = re.split(r'॥\s*', text)
    else:
        # Split on || pattern
        verses = re.split(r'॥\s*|\|\|\s*', text)
    
    result = []
    for v in verses:
        v = v.strip()
        if v and len(v) > 5:  # Skip tiny fragments
            result.append(v)
    
    return result


class Witness:
    """Represents a single witness for a scripture."""
    
    def __init__(self, filepath, metadata=None):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.metadata = metadata or {}
        
        # Load text
        with open(filepath, encoding='utf-8', errors='replace') as f:
            self.raw_text = f.read()
        
        # Detect script
        devanagari_chars = sum(1 for c in self.raw_text if '\u0900' <= c <= '\u097F')
        self.script = 'devanagari' if devanagari_chars > len(self.raw_text) * 0.1 else 'roman'
        
        # Normalize
        if self.script == 'devanagari':
            self.normalized = normalize_devanagari(self.raw_text)
        else:
            self.normalized = normalize_roman(self.raw_text)
        
        # Extract verses
        self.verses = extract_verses_from_text(self.normalized, self.script)
        
        # Metadata
        self.publisher = self._detect_publisher()
        self.char_count = len(self.raw_text)
        self.verse_count = len(self.verses)
    
    def _detect_publisher(self):
        """Detect publisher from filename."""
        fn = self.filename.lower()
        publishers = {
            'gita_press': ['gita_press', 'gitapress', 'gp'],
            'chowkhamba': ['chowkhamba', 'chaukhamba'],
            'anandashram': ['anand', 'anandashram'],
            'motilal': ['motilal'],
            'nag': ['nag_publishers', 'nag '],
            'venkateshwar': ['venkateshwar'],
            'nirnaya_sagar': ['nirnaya'],
            'bori': ['bori'],
        }
        for pub, keywords in publishers.items():
            if any(k in fn for k in keywords):
                return pub
        return 'unknown'
    
    def fingerprint(self):
        """Compute a fingerprint for deduplication."""
        # Use first 1000 chars of normalized text
        sample = self.normalized[:1000]
        return hash(sample)


class CollationEngine:
    """Collates multiple witnesses."""
    
    def __init__(self, witnesses):
        self.witnesses = witnesses
        self.n = len(witnesses)
    
    def collate_verses(self):
        """Align and collate verses across witnesses."""
        if self.n < 2:
            return {'error': 'need at least 2 witnesses'}
        
        # Get verse counts
        verse_counts = [w.verse_count for w in self.witnesses]
        max_verses = max(verse_counts)
        
        # Simple alignment: compare verse by position
        aligned = []
        for i in range(max_verses):
            verse_texts = []
            for w in self.witnesses:
                if i < len(w.verses):
                    verse_texts.append(w.verses[i])
                else:
                    verse_texts.append(None)
            
            # Compare across witnesses
            if sum(1 for v in verse_texts if v is not None) >= 2:
                comparison = self._compare_verse_set(verse_texts)
                aligned.append({
                    'position': i,
                    'texts': verse_texts,
                    'comparison': comparison,
                })
        
        return {
            'total_aligned': len(aligned),
            'witnesses': [w.filename for w in self.witnesses],
            'verse_counts': verse_counts,
            'aligned': aligned,
        }
    
    def _compare_verse_set(self, texts):
        """Compare a set of verse texts across witnesses."""
        valid = [(i, t) for i, t in enumerate(texts) if t is not None]
        if len(valid) < 2:
            return {'status': 'insufficient_witnesses'}
        
        # Compare each pair
        agreements = 0
        disagreements = 0
        variants = []
        
        for i in range(len(valid)):
            for j in range(i + 1, len(valid)):
                idx_a, text_a = valid[i]
                idx_b, text_b = valid[j]
                
                if text_a == text_b:
                    agreements += 1
                else:
                    disagreements += 1
                    # Find difference
                    diff = self._find_diff(text_a, text_b)
                    variants.append({
                        'witness_a': self.witnesses[idx_a].filename,
                        'witness_b': self.witnesses[idx_b].filename,
                        'diff_type': diff['type'],
                        'position': diff.get('position'),
                        'a_context': diff.get('a_context'),
                        'b_context': diff.get('b_context'),
                    })
        
        total_pairs = len(valid) * (len(valid) - 1) // 2
        
        return {
            'agreements': agreements,
            'disagreements': disagreements,
            'agreement_rate': round(100 * agreements / max(total_pairs, 1), 1),
            'variants': variants[:5],  # Limit
        }
    
    def _find_diff(self, text_a, text_b):
        """Find first difference between two texts."""
        for i in range(min(len(text_a), len(text_b))):
            if text_a[i] != text_b[i]:
                return {
                    'type': 'character',
                    'position': i,
                    'a_context': text_a[max(0,i-5):i+10],
                    'b_context': text_b[max(0,i-5):i+10],
                }
        
        if len(text_a) != len(text_b):
            return {
                'type': 'length',
                'a_len': len(text_a),
                'b_len': len(text_b),
            }
        
        return {'type': 'identical'}
    
    def compute_witness_agreement(self):
        """Compute pairwise agreement matrix."""
        if self.n < 2:
            return {}
        
        matrix = {}
        for i in range(self.n):
            for j in range(i + 1, self.n):
                w_a = self.witnesses[i]
                w_b = self.witnesses[j]
                
                # Compare verses
                common = min(w_a.verse_count, w_b.verse_count)
                agreements = 0
                for k in range(common):
                    if w_a.verses[k] == w_b.verses[k]:
                        agreements += 1
                
                pair_key = f"{w_a.publisher}:{w_b.publisher}"
                matrix[pair_key] = {
                    'agreements': agreements,
                    'total': common,
                    'rate': round(100 * agreements / max(common, 1), 1),
                }
        
        return matrix
    
    def summary(self):
        """Produce collation summary."""
        return {
            'witness_count': self.n,
            'witnesses': [{
                'filename': w.filename,
                'publisher': w.publisher,
                'script': w.script,
                'char_count': w.char_count,
                'verse_count': w.verse_count,
                'fingerprint': w.fingerprint(),
            } for w in self.witnesses],
        }


def collate_scripture(scripture_name, witness_files):
    """Collate all witnesses for a scripture."""
    
    print(f"\n{'='*60}")
    print(f"COLLATION: {scripture_name}")
    print(f"{'='*60}")
    
    # Load witnesses
    witnesses = []
    for fn in witness_files:
        fp = os.path.join('knowledge/downloads', fn)
        if os.path.exists(fp):
            w = Witness(fp)
            witnesses.append(w)
            print(f"  Loaded: {w.filename} ({w.publisher}, {w.script}, {w.verse_count} verses)")
    
    if len(witnesses) < 2:
        print("  Need at least 2 witnesses for collation")
        return None
    
    # Deduplicate
    fingerprints = {}
    unique = []
    for w in witnesses:
        fp = w.fingerprint()
        if fp not in fingerprints:
            fingerprints[fp] = w
            unique.append(w)
        else:
            print(f"  Duplicate detected: {w.filename} (same as {fingerprints[fp].filename})")
    
    if len(unique) < 2:
        print("  After deduplication, need at least 2 unique witnesses")
        return None
    
    # Collate
    engine = CollationEngine(unique)
    summary = engine.summary()
    
    # Compute agreement
    agreement = engine.compute_witness_agreement()
    summary['agreement_matrix'] = agreement
    
    # Collate verses
    collation = engine.collate_verses()
    summary['collation'] = {
        'total_aligned': collation['total_aligned'],
        'verse_counts': collation['verse_counts'],
    }
    
    # Count agreements/disagreements
    total_agreements = sum(v['agreements'] for v in agreement.values())
    total_comparisons = sum(v['total'] for v in agreement.values())
    
    print(f"\n  Unique witnesses: {len(unique)}")
    print(f"  Total aligned verses: {collation['total_aligned']}")
    print(f"  Overall agreement: {total_agreements}/{total_comparisons} ({100*total_agreements/max(total_comparisons,1):.1f}%)")
    
    print(f"\n  Pairwise agreement:")
    for pair, stats in sorted(agreement.items(), key=lambda x: x[1]['rate']):
        print(f"    {pair:30s} {stats['rate']:5.1f}% ({stats['agreements']}/{stats['total']})")
    
    return summary


if __name__ == '__main__':
    # Collate Agni Purana as example
    agni_witnesses = [
        'agni_puran_gita_press.txt',
        'agni_puran_chowkhamba.txt',
        'agni_puran_anand_ashram.txt',
        'agni_puran_gitapress_old.txt',
        'agni_puran_gita_press_new.txt',
    ]
    
    result = collate_scripture('Agni Purana', agni_witnesses)
    
    if result:
        os.makedirs('knowledge/cuv/collation', exist_ok=True)
        with open('knowledge/cuv/collation/agni_puran.json', 'w') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n  Results saved to knowledge/cuv/collation/agni_puran.json")
