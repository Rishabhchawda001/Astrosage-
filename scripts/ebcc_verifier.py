#!/usr/bin/env python3
"""
EBCC Verifier — Evidence-Based Canonical Certification

Extracts canonical units directly from authoritative TEI XML,
compares against extracted AKUs, and produces evidence-backed
certification with character-level diff.

Usage:
  python3 scripts/ebcc_verifier.py --xml FILE --aku FILE [--output FILE]
"""

import json
import os
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict


TEI_NS = 'http://www.tei-c.org/ns/1.0'


class TEIExtractor:
    """Extracts text directly from TEI XML."""
    
    def __init__(self, xml_path):
        self.xml_path = xml_path
        self.tree = ET.parse(xml_path)
        self.root = self.tree.getroot()
        self.ns = {'tei': TEI_NS}
        
        # Extract header metadata
        self.title = self._extract_title()
        self.editor = self._extract_editor()
        self.source = self._extract_source()
        self.license = self._extract_license()
    
    def _extract_title(self):
        el = self.root.find('.//tei:titleStmt/tei:title', self.ns)
        return el.text.strip() if el is not None and el.text else ''
    
    def _extract_editor(self):
        els = self.root.findall('.//tei:respStmt/tei:name', self.ns)
        return [e.text.strip() for e in els if e.text]
    
    def _extract_source(self):
        el = self.root.find('.//tei:sourceDesc/tei:bibl', self.ns)
        return el.text.strip() if el is not None and el.text else ''
    
    def _extract_license(self):
        el = self.root.find('.//tei:availability/tei:licence', self.ns)
        if el is not None:
            return el.get('target', '') or (el.text or '').strip()
        return ''
    
    def extract_body_units(self):
        """
        Extract all text units from the TEI body.
        Returns list of dicts with: type, ref, text, raw_xml
        """
        body = self.root.find('.//tei:body', self.ns)
        if body is None:
            return []
        
        units = []
        
        for div in body.findall('tei:div', self.ns):
            div_type = div.get('type', '')
            div_id = div.get('{http://www.w3.org/XML/1998/namespace}id', '')
            
            for child in div:
                tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                
                if tag == 'p':
                    text = self._extract_text_content(child)
                    if text.strip():
                        # Check for embedded reference markers
                        ref_match = re.match(r'^([A-Z]\w+\d+[\d.,\-/]*)\s*/\s*', text)
                        if ref_match:
                            ref = ref_match.group(1)
                            text = text[ref_match.end():]
                        else:
                            ref = None
                        
                        units.append({
                            'type': 'prose',
                            'ref': ref,
                            'text': text.strip(),
                            'div_type': div_type,
                            'div_id': div_id,
                        })
                
                elif tag == 'lg':
                    # Verse group
                    for line in child.findall('tei:l', self.ns):
                        text = self._extract_text_content(line)
                        n = line.get('n', '')
                        if text.strip():
                            units.append({
                                'type': 'verse',
                                'ref': n or None,
                                'text': text.strip(),
                                'div_type': div_type,
                                'div_id': div_id,
                            })
                
                elif tag == 'l':
                    text = self._extract_text_content(child)
                    n = child.get('n', '')
                    if text.strip():
                        units.append({
                            'type': 'verse_line',
                            'ref': n or None,
                            'text': text.strip(),
                            'div_type': div_type,
                            'div_id': div_id,
                        })
        
        return units
    
    def _extract_text_content(self, element):
        """Extract all text content from an element, including children."""
        parts = []
        if element.text:
            parts.append(element.text)
        for child in element:
            # Include child text
            if child.text:
                parts.append(child.text)
            if child.tail:
                parts.append(child.tail)
        return ' '.join(parts).strip()


class AKULoader:
    """Loads extracted AKU data."""
    
    def __init__(self, aku_path):
        self aku_path = aku_path
        with open(aku_path) as f:
            self.data = json.load(f)
    
    def get_all_akus(self):
        """Return flat list of all AKUs with chapter info."""
        akus = []
        for ch in self.data.get('chapters', []):
            ch_num = ch.get('chapter_num', 0)
            for aku in ch.get('akus', []):
                akus.append({
                    'chapter': ch_num,
                    'ref': aku.get('ref'),
                    'body': (aku.get('body') or '').strip(),
                })
        return akus


class EBCCVerifier:
    """Verifies AKUs against authoritative TEI XML."""
    
    def __init__(self, xml_extractor, aku_loader):
        self.xml = xml_extractor
        self.akus = aku_loader
        self.results = {
            'title': xml_extractor.title,
            'editor': xml_extractor.editor,
            'source': xml_extractor.source,
            'license': xml_extractor.license,
            'xml_path': xml_extractor.xml_path,
            'aku_path': aku_loader.aku_path,
        }
    
    def verify(self):
        """Run full verification."""
        
        # Extract from XML
        xml_units = self.xml.extract_body_units()
        aku_units = self.akus.get_all_akus()
        
        self.results['xml_unit_count'] = len(xml_units)
        self.results['aku_unit_count'] = len(aku_units)
        
        # Classify XML units
        xml_verses = [u for u in xml_units if u['type'] in ('verse', 'verse_line')]
        xml_prose = [u for u in xml_units if u['type'] == 'prose']
        
        self.results['xml_verses'] = len(xml_verses)
        self.results['xml_prose'] = len(xml_prose)
        
        # Character-level comparison
        char_issues = self._compare_characters(xml_units, aku_units)
        self.results['char_issues'] = char_issues
        self.results['char_issue_count'] = len(char_issues)
        
        # Boundary comparison
        boundary_issues = self._compare_boundaries(xml_units, aku_units)
        self.results['boundary_issues'] = boundary_issues
        self.results['boundary_issue_count'] = len(boundary_issues)
        
        # Reference comparison
        ref_issues = self._compare_references(xml_units, aku_units)
        self.results['ref_issues'] = ref_issues
        self.results['ref_issue_count'] = len(ref_issues)
        
        # Overall score
        total = max(len(aku_units), 1)
        issues = (len(char_issues) + len(boundary_issues) + len(ref_issues))
        self.results['accuracy'] = max(0, 100 * (total - issues) / total)
        self.results['status'] = (
            'verified' if issues == 0 else
            'mostly_verified' if issues < total * 0.05 else
            'needs_review' if issues < total * 0.2 else
            'significant_issues'
        )
        
        return self.results
    
    def _compare_characters(self, xml_units, aku_units):
        """Compare text at character level."""
        issues = []
        
        # Build a mapping: try to match XML units to AKU units
        xml_texts = [u['text'] for u in xml_units if u['text']]
        aku_texts = [u['body'] for u in aku_units if u['body']]
        
        # Simple comparison: check if XML text is contained in AKU text or vice versa
        for i, xml_text in enumerate(xml_texts[:min(len(xml_texts), len(aku_texts))]):
            if i < len(aku_texts):
                aku_text = aku_texts[i]
                
                # Normalize for comparison
                xml_norm = unicodedata.normalize('NFC', xml_text)
                aku_norm = unicodedata.normalize('NFC', aku_text)
                
                if xml_norm != aku_norm:
                    # Find first difference
                    diff_pos = -1
                    for j in range(min(len(xml_norm), len(aku_norm))):
                        if xml_norm[j] != aku_norm[j]:
                            diff_pos = j
                            break
                    
                    if diff_pos == -1 and len(xml_norm) != len(aku_norm):
                        diff_pos = min(len(xml_norm), len(aku_norm))
                    
                    issues.append({
                        'unit_index': i,
                        'xml_preview': xml_norm[max(0,diff_pos-10):diff_pos+20],
                        'aku_preview': aku_norm[max(0,diff_pos-10):diff_pos+20],
                        'diff_pos': diff_pos,
                        'xml_len': len(xml_norm),
                        'aku_len': len(aku_norm),
                    })
        
        return issues
    
    def _compare_boundaries(self, xml_units, aku_units):
        """Compare unit boundaries."""
        issues = []
        
        xml_count = len([u for u in xml_units if u['text']])
        aku_count = len([u for u in aku_units if u['body']])
        
        if xml_count != aku_count:
            issues.append({
                'type': 'count_mismatch',
                'xml_count': xml_count,
                'aku_count': aku_count,
                'diff': xml_count - aku_count,
            })
        
        return issues
    
    def _compare_references(self, xml_units, aku_units):
        """Compare reference numbering."""
        issues = []
        
        xml_refs = [u['ref'] for u in xml_units if u['ref']]
        aku_refs = [u['ref'] for u in aku_units if u['ref']]
        
        # Check if references match
        if len(xml_refs) != len(aku_refs):
            issues.append({
                'type': 'ref_count_mismatch',
                'xml_refs': len(xml_refs),
                'aku_refs': len(aku_refs),
            })
        
        # Check for reference mismatches
        for i in range(min(len(xml_refs), len(aku_refs))):
            if xml_refs[i] != aku_refs[i]:
                issues.append({
                    'type': 'ref_mismatch',
                    'index': i,
                    'xml_ref': xml_refs[i],
                    'aku_ref': aku_refs[i],
                })
        
        return issues


def verify_scripture(xml_path, aku_path, output_path=None):
    """Verify a single scripture."""
    
    xml_ext = TEIExtractor(xml_path)
    aku_load = AKULoader(aku_path)
    
    verifier = EBCCVerifier(xml_ext, aku_load)
    results = verifier.verify()
    
    # Print report
    print(f"\n{'='*60}")
    print(f"EBCC VERIFICATION: {results['title']}")
    print(f"{'='*60}")
    print(f"Source: {results['source'][:80]}")
    print(f"Editor: {', '.join(results['editor'][:3])}")
    print(f"\nXML units: {results['xml_unit_count']} (verses: {results['xml_verses']}, prose: {results['xml_prose']})")
    print(f"AKU units: {results['aku_unit_count']}")
    print(f"\nCharacter issues: {results['char_issue_count']}")
    print(f"Boundary issues: {results['boundary_issue_count']}")
    print(f"Reference issues: {results['ref_issue_count']}")
    print(f"\nAccuracy: {results['accuracy']:.1f}%")
    print(f"Status: {results['status'].upper()}")
    
    if results['char_issues']:
        print(f"\nSample character diffs:")
        for issue in results['char_issues'][:5]:
            print(f"  Unit {issue['unit_index']}:")
            print(f"    XML: ...{issue['xml_preview']}...")
            print(f"    AKU: ...{issue['aku_preview']}...")
    
    if output_path:
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to: {output_path}")
    
    return results


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='EBCC Verifier')
    parser.add_argument('--xml', required=True, help='Path to TEI XML file')
    parser.add_argument('--aku', required=True, help='Path to extracted AKU JSON')
    parser.add_argument('--output', help='Output path for results')
    args = parser.parse_args()
    
    verify_scripture(args.xml, args.aku, args.output)
