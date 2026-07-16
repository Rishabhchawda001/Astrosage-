#!/usr/bin/env python3
"""
Gap Analyzer - Identifies missing witnesses, editions, and evidence for each scripture
"""
import json
from pathlib import Path

SCRIPTURE_CANON_FILE = "/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage/knowledge/dtc/config/scripture_canon.json"
WITNESS_CLASSIFICATION_FILE = "/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage/knowledge/dtc/witness_classification.json"
OUTPUT_DIR = "/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage/knowledge/dtc/gaps"

def main():
    with open(SCRIPTURE_CANON_FILE) as f:
        canon = json.load(f)
    
    # Load witness classification if exists
    families_on_disk = {}
    if Path(WITNESS_CLASSIFICATION_FILE).exists():
        with open(WITNESS_CLASSIFICATION_FILE) as f:
            wc = json.load(f)
            families_on_disk = wc.get('by_scripture', {})
    
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    all_gaps = {}
    acquisition_queue = []
    
    for scripture in canon['scriptures']:
        sid = scripture['id']
        required = scripture.get('required_independent_families', 2)
        known_families = scripture.get('known_families_on_disk', [])
        missing_families = scripture.get('missing_families', [])
        
        on_disk = families_on_disk.get(sid, {})
        disk_families = list(on_disk.keys())
        
        # Count independent families on disk
        independent_on_disk = 0
        for fam in disk_families:
            if fam in known_families or 'INDEPENDENT' in fam or 'CRITICAL' in fam:
                independent_on_disk += 1
        
        gap = {
            "scripture_id": sid,
            "canonical_name": scripture['canonical_name'],
            "required_independent_families": required,
            "independent_families_on_disk": independent_on_disk,
            "total_families_on_disk": len(disk_families),
            "families_on_disk": disk_families,
            "missing_families": missing_families,
            "gap_severity": "CRITICAL" if independent_on_disk < required else ("HIGH" if independent_on_disk == required else "MEDIUM"),
            "can_be_verified": independent_on_disk >= required
        }
        
        all_gaps[sid] = gap
        
        # Generate acquisition items
        for missing in missing_families:
            acquisition_queue.append({
                "scripture_id": sid,
                "scripture_name": scripture['canonical_name'],
                "missing_family": missing,
                "priority": "CRITICAL" if independent_on_disk < required else "HIGH",
                "expected_evidence_gain": f"Adds independent family, moving from {independent_on_disk} to {independent_on_disk + 1}/{required}",
                "search_hints": {
                    "publishers": ["Gita Press", "Chowkhamba", "Motilal Banarsidass", "Anandashram", "Venkateshwar Press", "BORI"],
                    "editors": ["Aufrecht", "Max Müller", "Oldenberg", "Schmidt", "Lubotsky", "Geldner"],
                    "recensions": scripture.get('expected_structure', {}).get('recensions', []),
                    "formats": ["tei_xml", "native_unicode", "pdf", "djvu"]
                }
            })
    
    # Save gaps
    with open(Path(OUTPUT_DIR) / "gap_report.json", 'w') as f:
        json.dump(all_gaps, f, indent=2)
    
    # Save acquisition queue sorted by priority
    priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    acquisition_queue.sort(key=lambda x: priority_order.get(x['priority'], 99))
    
    with open(Path(OUTPUT_DIR) / "acquisition_queue.json", 'w') as f:
        json.dump(acquisition_queue, f, indent=2)
    
    print(f"Gap analysis complete. {len(all_gaps)} scriptures analyzed.")
    print(f"Acquisition queue: {len(acquisition_queue)} items")
    
    # Summary
    critical = sum(1 for g in all_gaps.values() if g['gap_severity'] == 'CRITICAL')
    high = sum(1 for g in all_gaps.values() if g['gap_severity'] == 'HIGH')
    medium = sum(1 for g in all_gaps.values() if g['gap_severity'] == 'MEDIUM')
    verified = sum(1 for g in all_gaps.values() if g['can_be_verified'])
    
    print(f"CRITICAL gaps: {critical}")
    print(f"HIGH gaps: {high}")
    print(f"MEDIUM gaps: {medium}")
    print(f"Can be verified: {verified}/{len(all_gaps)}")

if __name__ == '__main__':
    main()
