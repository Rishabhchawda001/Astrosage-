#!/usr/bin/env python3
"""Update canonical structures and witness graph with GRETIL evidence."""

import json
import os
import glob
from pathlib import Path

def main():
    base_dir = Path(__file__).parent.parent
    parsed_dir = base_dir / 'knowledge' / 'gretil_parsed'
    cku_dir = base_dir / 'knowledge' / 'cku_registry'

    # Load GRETIL summary
    summary_path = parsed_dir / 'gretil_summary.json'
    if not summary_path.exists():
        print("No GRETIL summary found. Run gretil_parser.py first.")
        return

    with open(summary_path) as f:
        summary = json.load(f)

    print(f"Loaded {len(summary)} GRETIL entries")

    # Map GRETIL files to scripture names
    gretil_to_scripture = {
        'agni_puran_gretil.xml': 'Agni Purana',
        'bhagavata_gretil.xml': 'Bhagavata Purana',
        'brahma_puran_gretil.xml': 'Brahma Purana',
        'garuda_puran_gretil.xml': 'Garuda Purana',
        'kurma_puran_gretil.xml': 'Kurma Purana',
        'linga_puran_gretil.xml': 'Linga Purana',
        'matsya_puran_gretil.xml': 'Matsya Purana',
        'narada_puran_gretil.xml': 'Naradiya Purana',
        'ramayana_gretil.xml': 'Valmiki Ramayana',
        'vamana_puran_gretil.xml': 'Vamana Purana',
        'vishnu_puran_gretil.xml': 'Vishnu Purana',
        'vishnu_puran_gretil_critical.xml': 'Vishnu Purana',
        'sa_brahmANDapurANa.xml': 'Brahmanda Purana',
        'sa_bAdarAyaNa-brahmasUtra.xml': 'Brahma Sutra',
    }

    # Update canonical structures
    canonical_path = cku_dir / 'canonical_structures.json'
    if canonical_path.exists():
        with open(canonical_path) as f:
            canonical = json.load(f)
    else:
        canonical = {}

    updated = 0
    for entry in summary:
        fname = entry['file']
        scripture = gretil_to_scripture.get(fname)
        if not scripture:
            continue

        # Create or update canonical structure
        if scripture not in canonical:
            canonical[scripture] = {
                'editions': {},
                'total_chapters': 0,
                'total_verses': 0,
            }

        canonical[scripture]['editions'][f'gretil_{fname}'] = {
            'title': entry['title'],
            'chapters': entry['chapters'],
            'verses': entry['verses'],
            'source': 'GRETIL',
            'quality': 'TEI_XML_scholarly',
            'witness_type': 'native_digital',
        }

        # Update totals (use max across editions)
        if entry['chapters'] > canonical[scripture]['total_chapters']:
            canonical[scripture]['total_chapters'] = entry['chapters']
        if entry['verses'] > canonical[scripture]['total_verses']:
            canonical[scripture]['total_verses'] = entry['verses']

        updated += 1

    with open(canonical_path, 'w', encoding='utf-8') as f:
        json.dump(canonical, f, ensure_ascii=False, indent=2)

    print(f"Updated canonical structures for {updated} scriptures")

    # Update witness graph
    witness_path = cku_dir / 'witness_graph.json'
    if witness_path.exists():
        with open(witness_path) as f:
            witness = json.load(f)
    else:
        witness = {'metadata': {}, 'scriptures': {}}

    for entry in summary:
        fname = entry['file']
        scripture = gretil_to_scripture.get(fname)
        if not scripture:
            continue

        if scripture not in witness.get('scriptures', {}):
            witness.setdefault('scriptures', {})[scripture] = {'witnesses': []}

        # Check if GRETIL witness already exists
        existing = [w for w in witness['scriptures'][scripture]['witnesses']
                    if w.get('source') == 'GRETIL' and w.get('file') == fname]
        if not existing:
            witness['scriptures'][scripture]['witnesses'].append({
                'source': 'GRETIL',
                'file': fname,
                'title': entry['title'],
                'chapters': entry['chapters'],
                'verses': entry['verses'],
                'witness_type': 'native_digital',
                'authority': 'high',
                'quality': 'TEI_XML_scholarly',
                'script': 'IAST',
                'license': 'CC_BY-NC-SA_4.0',
            })

    with open(witness_path, 'w', encoding='utf-8') as f:
        json.dump(witness, f, ensure_ascii=False, indent=2)

    print("Updated witness graph with GRETIL witnesses")

    # Print summary
    print(f"\n{'='*60}")
    print(f"{'Scripture':<30} {'Chapters':>8} {'Verses':>8}")
    print("-"*60)
    for scripture, data in sorted(canonical.items()):
        if 'total_chapters' in data and data['total_chapters'] > 0:
            print(f"{scripture:<30} {data['total_chapters']:>8} {data['total_verses']:>8}")
    print("="*60)


if __name__ == '__main__':
    main()
