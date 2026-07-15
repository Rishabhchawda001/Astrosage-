#!/usr/bin/env python3
"""
AKU Classifier — Canonical Unit Validation (CUV) Step 1

Classifies every prose AKU into exactly one canonical class:
  verse, sutra, mantra, prose, commentary, translation,
  metadata, heading, colophon, footnote, critical_apparatus,
  index, publisher_material, ocr_artifact, empty, unknown

Usage:
  python3 scripts/aku_classifier.py [--input DIR] [--output FILE] [--dry-run]
"""

import json
import os
import re
import sys
import hashlib
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

# Canonical classes (exactly one per AKU)
CLASSES = [
    "verse",           # Metered verse with danda markers
    "sutra",           # Sutra with numbered references
    "mantra",          # Ritual mantra (oṃ, svāhā, namaḥ)
    "prose",           # General prose passage
    "commentary",      # Commentary (bhāṣya,ṭīkā,vṛtti)
    "translation",     # Translation text
    "metadata",        # Title, catalog, edition info
    "heading",         # Chapter/section heading
    "colophon",        # Closing/subscription marker
    "footnote",        # Footnote or editorial note
    "critical_apparatus",  # Critical apparatus entries
    "index",           # Table of contents or index
    "publisher_material",  # Publisher boilerplate
    "ocr_artifact",    # Detected OCR garbage
    "empty",           # Empty or whitespace-only
    "unknown",         # Cannot classify
]


class AKUClassifier:
    """Rule-based classifier for GRETIL prose AKUs."""
    
    def __init__(self, scripture_context=None):
        """
        scripture_context: dict with keys like 'title', 'file' to help
        classify based on scripture type (sutra vs purana vs upanishad).
        """
        self.ctx = scripture_context or {}
        self.title_lower = self.ctx.get('title', '').lower()
        self.file_lower = self.ctx.get('file', '').lower()
        
        # Detect scripture genre from title/file
        self.is_sutra = any(k in self.title_lower for k in [
            'sūtra', 'sutra', 'dharmasūtra', 'gṛhyasūtra', 'śrautasūtra',
            'mīmāṃsā', 'nyāya', 'vaiśeṣika', 'yoga', 'brahmasūtra'
        ])
        self.is_purana = any(k in self.title_lower for k in [
            'purāṇa', 'purana'
        ])
        self.is_upanishad = any(k in self.title_lower for k in [
            'upaniṣad', 'upanishad'
        ])
        self.is_brahmana = any(k in self.title_lower for k in [
            'brāhmaṇa', 'brahmana'
        ])
        self.is_smriti = any(k in self.title_lower for k in [
            'smṛti', 'smriti', 'dharmaśāstra', 'dharmasastra'
        ])
        self.is_stotra = any(k in self.title_lower for k in [
            'stotra', 'stava', 'stuti', 'śānti'
        ])
        self.is_commentary = any(k in self.title_lower for k in [
            'bhāṣya', 'bhashya', 'ṭīkā', 'tika', 'vṛtti', 'vrtti',
            'commentary', 'vyākhyā', 'vyakhya'
        ])
        self.is_aveda = any(k in self.file_lower for k in [
            'veda', 'vedic', 'rigveda', 'yajurveda', 'samaveda', 'atharvaveda'
        ])
    
    def classify(self, ref, body):
        """
        Classify a single AKU. Returns (class_name, confidence, reasons).
        
        Args:
            ref: Reference string (may be None)
            body: Body text string (may be empty)
        
        Returns:
            tuple: (class_name, confidence 0-100, list of reason strings)
        """
        body = (body or '').strip()
        ref = (ref or '').strip() if ref else None
        reasons = []
        
        # === EMPTY ===
        if not body:
            return ('empty', 100, ['empty body'])
        
        # === OCR ARTIFACTS ===
        # Detect garbled text patterns
        if self._is_ocr_artifact(body):
            reasons.append('OCR artifact patterns detected')
            return ('ocr_artifact', 85, reasons)
        
        # === METADATA ===
        if self._is_metadata(body, ref):
            reasons.append('metadata pattern')
            return ('metadata', 90, reasons)
        
        # === HEADING ===
        if self._is_heading(body, ref):
            reasons.append('heading pattern')
            return ('heading', 85, reasons)
        
        # === COLOPHON ===
        if self._is_colophon(body):
            reasons.append('colophon marker')
            return ('colophon', 95, reasons)
        
        # === INDEX ===
        if self._is_index(body, ref):
            reasons.append('index/TOC pattern')
            return ('index', 80, reasons)
        
        # === CRITICAL APPARATUS ===
        if self._is_critical_apparatus(body, ref):
            reasons.append('critical apparatus pattern')
            return ('critical_apparatus', 85, reasons)
        
        # === FOOTNOTE ===
        if self._is_footnote(body):
            reasons.append('footnote pattern')
            return ('footnote', 80, reasons)
        
        # === PUBLISHER MATERIAL ===
        if self._is_publisher_material(body):
            reasons.append('publisher material')
            return ('publisher_material', 75, reasons)
        
        # === TRANSLATION ===
        if self._is_translation(body):
            reasons.append('translation pattern')
            return ('translation', 70, reasons)
        
        # === COMMENTARY ===
        if self._is_commentary(body, ref):
            reasons.append('commentary pattern')
            return ('commentary', 80, reasons)
        
        # === MANTRA ===
        if self._is_mantra(body):
            reasons.append('mantra pattern')
            return ('mantra', 85, reasons)
        
        # === VERSE ===
        if self._is_verse(body, ref):
            reasons.append('verse pattern')
            return ('verse', 90, reasons)
        
        # === SUTRA ===
        if self._is_sutra(body, ref):
            reasons.append('sutra pattern')
            return ('sutra', 85, reasons)
        
        # === PROSE (fallback) ===
        if len(body) > 20:
            reasons.append('substantial text, no verse/sutra markers')
            return ('prose', 60, reasons)
        
        # Short text that doesn't match anything specific
        return ('unknown', 40, ['short text, no clear markers'])
    
    def _is_ocr_artifact(self, body):
        """Detect OCR garbage."""
        if len(body) < 3:
            return False
        # High ratio of special characters
        alpha = sum(1 for c in body if c.isalpha() or unicodedata.category(c).startswith('L'))
        if len(body) > 5 and alpha / len(body) < 0.3:
            return True
        # Repeated = or - patterns (common OCR artifacts)
        if re.search(r'={3,}', body):
            return True
        # Random digit clusters
        if re.search(r'\d{5,}', body):
            return True
        return False
    
    def _is_metadata(self, body, ref):
        """Detect title/catalog/edition metadata."""
        patterns = [
            r'^(agnipurāṇam|bhagavadgītā|veda|purāṇam)',
            r'^(atha|evam|tatra)\s+\S+\s+ukta',
            r'^(vyāsa|vaiśampāyana|jaimini)',
            r'(nāma|saṃhitā|khaṇḍa)\s*$',
            r'^(1\.|2\.|3\.)\s*\S',  # numbered list items
            r'^(sūtrāṇi|sūtram)\s*$',
        ]
        for p in patterns:
            if re.search(p, body, re.IGNORECASE):
                return True
        # Very short text that is just a title
        if len(body) < 30 and not any(c in body for c in '|/'):
            # Check if it looks like a title (capitalized, no verbs)
            words = body.split()
            if len(words) <= 4 and not any(w in body for w in ['ca', 'vā', 'tu', 'hi', 'eva']):
                return True
        return False
    
    def _is_heading(self, body, ref):
        """Detect chapter/section headings."""
        patterns = [
            r'^(prathamo|dvitīya|tṛtīya|caturtha|pañcama|ṣaṣṭha|saptama|aṣṭama|navama|daśama)',
            r'(adhyāya|paṭala|khaṇḍa|prasna|pīṭhika|anuvāka)\s*$',
            r'^athāto\b',
            r'^(prathamaḥ|dvitīyaḥ|tṛtīyaḥ)\s+(adhyāya|paṭala|khaṇḍa)',
            r'^(vyākhyāsyāmaḥ|vakṣyāmaḥ|āhariṣyāmaḥ)\b',
            r'^(oṃ|om)\s+namo\s+',
        ]
        for p in patterns:
            if re.search(p, body, re.IGNORECASE):
                return True
        # Short text with chapter-like reference
        if ref and len(body) < 50:
            if re.search(r'\d+\.\d+$', ref):
                return True
        return False
    
    def _is_colophon(self, body):
        """Detect colophon/subscription markers."""
        patterns = [
            r'samāpta',
            r'samāptam',
            r'sampūrṇam',
            r'iti\s+\S+\s+namo\s+',
            r'iti\s+\S+\s+stotram\s+samāpta',
            r'iti\s+śrī',
            r'iti\s+\S+\s+saṃhitā',
            r'iti\s+\S+\s+purāṇam',
            r'iti\s+\S+\s+upaniṣat',
            r'iti\s+\S+\s+brāhmaṇam',
            r'iti\s+\S+\s+mantra',
            r'iti\s+\S+\s+prokta',
        ]
        for p in patterns:
            if re.search(p, body, re.IGNORECASE):
                return True
        return False
    
    def _is_index(self, body, ref):
        """Detect table of contents / index entries."""
        patterns = [
            r'^(viniyoga|anukramaṇikā|anukramaṇi|pariśiṣṭa)',
            r'^(kāṇḍa|aṣṭaka|adhyāya|paṭala)\s+\d',
            r'^\d+\.\s+\S+.*\d+\s*$',  # "1. Chapter name ... page"
        ]
        for p in patterns:
            if re.search(p, body, re.IGNORECASE):
                return True
        # TOC-style: short lines with numbers
        if len(body) < 60 and re.match(r'^\d', body):
            return True
        return False
    
    def _is_critical_apparatus(self, body, ref):
        """Detect critical apparatus entries."""
        patterns = [
            r'\*\s*\S+\s*→\s*\S+',  # asterisk corrections
            r' reading ',  # "reading" in apparatus
            r' om\.?\s',   # omission marker
            r' add\.?\s',  # addition marker
            r' conj\.?\s',  # conjecture
            r' fort\.?\s',  # "for"
            r' \d+\.\d+\s*[:/]\s*\d+',  # manuscript folio refs
        ]
        for p in patterns:
            if re.search(p, body, re.IGNORECASE):
                return True
        # Very short with brackets (editorial)
        if len(body) < 40 and '[' in body and ']' in body:
            return True
        return False
    
    def _is_footnote(self, body):
        """Detect footnote-like content."""
        patterns = [
            r'^\d+\.\s*\S',  # numbered footnote
            r'^\[\d+\]',     # bracketed number
            r'^\(\d+\)',     # parenthesized number
            r'cf\.\s',       # cross-reference
            r'vid\.\s',      # "see"
            r'v\.\s+\d',     # "verse X"
        ]
        for p in patterns:
            if re.search(p, body, re.IGNORECASE):
                return True
        return False
    
    def _is_publisher_material(self, body):
        """Detect publisher boilerplate."""
        patterns = [
            r'(printed|published|edition|copyright|press)',
            r'(motilal|banarsidass|chowkhamba|nirnaya|nag\s)',
            r'(gita\s*press|anandashram|venkateshwar)',
            r'(isbn|oclc|doi:|http)',
        ]
        for p in patterns:
            if re.search(p, body, re.IGNORECASE):
                return True
        return False
    
    def _is_translation(self, body):
        """Detect translation text."""
        # Translations tend to be in English or have English words
        english_words = len(re.findall(r'\b[a-z]{3,}\b', body))
        total_words = len(body.split())
        if total_words > 5 and english_words / max(total_words, 1) > 0.4:
            return True
        return False
    
    def _is_commentary(self, body, ref):
        """Detect commentary text."""
        patterns = [
            r'\biti\s+\S+\s+ukta',  # "thus says X"
            r'\bucyate\b',
            r'\bvadati\b',
            r'\bāha\b',
            r'\bbrūyāt\b',
            r'\bbhāṣye\b',
            r'\bṭīkāyām\b',
            r'\bvṛttau\b',
            r'\bvyākhyānām\b',
            r'\bmantrasya\s+',
            r'\bsūtrasya\s+',
            r'\basya\s+mantrasya\s+',
            r'\byathā\s+',
            r'\btathā\s+ca\s+',
            r'\bparibhāṣā\b',
            r'\bpramāṇam\b',
            r'\bhetuḥ\b',
            r'\bpūrvapakṣa\b',
            r'\bsiddhānta\b',
        ]
        for p in patterns:
            if re.search(p, body, re.IGNORECASE):
                return True
        # Commentary is typically long prose
        if len(body) > 200 and self.is_commentary:
            return True
        return False
    
    def _is_mantra(self, body):
        """Detect ritual mantra."""
        patterns = [
            r'^oṃ\b',
            r'\bsvāhā\b',
            r'\bnamaḥ\b',
            r'\bnamaskāra\b',
            r'\bhūm\b',
            r'\bphat\b',
            r'\bsvadhā\b',
            r'\bhaiṃ\b',
            r'\bhraṃ\b',
            r'\bhkṃ\b',
            r'\bhrīṃ\b',
        ]
        for p in patterns:
            if re.search(p, body, re.IGNORECASE):
                return True
        return False
    
    def _is_verse(self, body, ref):
        """Detect verse text."""
        # Double danda is strongest verse marker
        if '||' in body:
            return True
        # Reference patterns that indicate verse
        if ref and re.search(r'_\d+\.\d+\d*/?\d*', ref):
            # Check body for verse-like content
            if '|' in body or len(body) > 30:
                return True
        # Single danda with substantial text (likely verse line)
        if '|' in body and len(body) > 20:
            # But not if it's clearly prose (has many sandhi markers)
            words = body.split()
            if len(words) < 20:  # verses tend to be shorter
                return True
        return False
    
    def _is_sutra(self, body, ref):
        """Detect sutra text."""
        # Sutra reference patterns
        if ref and re.search(r'[A-Z][a-z]+\d+\.\d+', ref):
            return True
        # Sutra-style: short, pithy statements
        if len(body) < 80 and self.is_sutra:
            # Check for sutra语言 characteristics
            if any(w in body for w in ['ca', 'vā', 'tu', 'eva', 'hi', 'iti']):
                return True
        # Numbered sutra with dots
        if re.search(r'\d+\.\d+\.\d+', body):
            return True
        return False


def classify_all_prose_akus(input_dir, output_file=None, dry_run=False):
    """Classify all prose AKUs and produce classification report."""
    
    classifier_cache = {}  # scripture-specific classifiers
    results = []
    class_counts = Counter()
    total = 0
    per_scripture = {}
    
    for fn in sorted(os.listdir(input_dir)):
        if not fn.endswith('.json'):
            continue
        
        filepath = os.path.join(input_dir, fn)
        with open(filepath) as f:
            data = json.load(f)
        
        title = data.get('title', fn)
        ctx = {'title': title, 'file': fn}
        classifier = AKUClassifier(ctx)
        
        scripture_stats = Counter()
        
        for ch in data.get('chapters', []):
            ch_num = ch.get('chapter_num', 0)
            for aku in ch.get('akus', []):
                total += 1
                ref = aku.get('ref')
                body = aku.get('body', '')
                
                cls, confidence, reasons = classifier.classify(ref, body)
                class_counts[cls] += 1
                scripture_stats[cls] += 1
                
                results.append({
                    'scripture': fn.replace('_gretil_prose.json', ''),
                    'chapter': ch_num,
                    'ref': ref,
                    'class': cls,
                    'confidence': confidence,
                    'reasons': reasons,
                    'body_len': len(body),
                })
        
        per_scripture[fn] = {
            'title': title,
            'total': sum(scripture_stats.values()),
            'classes': dict(scripture_stats),
        }
    
    # Report
    print(f"\\n{'='*60}")
    print(f"AKU CLASSIFICATION REPORT")
    print(f"{'='*60}")
    print(f"Total AKUs classified: {total}")
    print(f"\\nClass distribution:")
    for cls, count in class_counts.most_common():
        pct = 100 * count / total
        bar = '#' * int(pct / 2)
        print(f"  {cls:25s} {count:7d} ({pct:5.1f}%) {bar}")
    
    # Per-scripture summary
    print(f"\\nPer-scripture breakdown (top 10 by complexity):")
    sorted_sciptures = sorted(per_scripture.items(), 
                              key=lambda x: len(x[1]['classes']), reverse=True)
    for fn, stats in sorted_sciptures[:10]:
        print(f"  {stats['title'][:40]:40s} ({stats['total']:5d} AKUs):")
        for cls, count in sorted(stats['classes'].items(), key=lambda x: -x[1]):
            print(f"    {cls:20s} {count:5d}")
    
    # Save results
    if output_file and not dry_run:
        os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump({
                'total': total,
                'class_counts': dict(class_counts),
                'per_scripture': per_scripture,
                'details': results,
            }, f, indent=2, ensure_ascii=False)
        print(f"\\nResults saved to: {output_file}")
    
    return results, class_counts, per_scripture


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='AKU Classifier for CUV')
    parser.add_argument('--input', default='knowledge/gretil_prose',
                        help='Directory with prose JSON files')
    parser.add_argument('--output', default='knowledge/cuv/classification.json',
                        help='Output file for classification results')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print report without saving')
    args = parser.parse_args()
    
    classify_all_prose_akus(args.input, args.output, args.dry_run)
