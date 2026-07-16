#!/usr/bin/env python3
"""
Coverage Calculator - Computes evidence coverage metrics for each scripture
"""
import json
from pathlib import Path

SCRIPTURE_CANON_FILE = "/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage/knowledge/dtc/config/scripture_canon.json"
WITNESS_CLASSIFICATION_FILE = "/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage/knowledge/dtc/witness_classification.json"
DOWNLOADS_MANIFEST = "/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage/knowledge/dtc/downloads_manifest.json"
OUTPUT_DIR = "/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage/knowledge/dtc/coverage"

# Independent witness family patterns (these are genuinely independent editorial bases)
INDEPENDENT_FAMILY_PATTERNS = [
    "F-AUFRECHT", "F-LUBOTSKY", "F-MAXMULLER", "F-OLDENBERG",
    "F-VSM-SONTAKKE", "F-GRETIL", "F-GITAPRESS", "F-BORI",
    "F-PADAPATHA", "F-KHILA", "F-KAUTHUMA", "F-RANAYANIYA",
    "F-JAIMINIYA", "F-TAITTIRIYA", "F-MAITRAYANIYA", "F-KATHA",
    "F-SHAUNAKA", "F-PAIPPALADA", "F-BLOOMFIELD",
]

def load_json(path):
    with open(path) as f:
        return json.load(f)

def is_independent_family(family_id, scripture):
    """Determine if a family is an independent editorial base"""
    known = scripture.get('known_families_on_disk', [])
    # Direct match against known families
    if family_id in known:
        return True
    # Match against independent patterns
    for pattern in INDEPENDENT_FAMILY_PATTERNS:
        if family_id == pattern:
            return True
    # Families not in UNCLASSIFIED and not derived patterns
    if family_id == "F-UNCLASSIFIED":
        return False
    # Derived families (check relationship_to_parent in family rules)
    derived_patterns = ["F-CHOWKHAMBA", "F-RAMTEK-KKSU", "F-SAYANA",
                       "F-VEDAWEB-ZURICH", "F-GITAPRESS-OCR"]
    for dp in derived_patterns:
        if family_id == dp:
            return False
    # If it's a known scripture-specific family and not explicitly derived
    return False

def main():
    canon = load_json(SCRIPTURE_CANON_FILE)
    wc = load_json(WITNESS_CLASSIFICATION_FILE) if Path(WITNESS_CLASSIFICATION_FILE).exists() else {}
    manifest = load_json(DOWNLOADS_MANIFEST)
    
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    # Count files per scripture from manifest
    scripture_files = {}
    for f in manifest.get('files', []):
        sid = f.get('scripture_id', 'UNKNOWN')
        if sid not in scripture_files:
            scripture_files[sid] = []
        scripture_files[sid].append(f)
    
    coverage_report = {}
    
    for scripture in canon['scriptures']:
        sid = scripture['id']
        files = scripture_files.get(sid, [])
        
        # Count by type
        by_type = {}
        total_bytes = 0
        for f in files:
            t = f.get('file_type', 'unknown')
            by_type[t] = by_type.get(t, 0) + 1
            total_bytes += f.get('size_bytes', 0)
        
        # Witness families from classification
        families = wc.get('by_scripture', {}).get(sid, {})
        all_family_ids = list(families.keys())
        
        # Determine independent families
        independent_families = [f for f in all_family_ids if is_independent_family(f, scripture)]
        
        # Expected structure
        expected = scripture.get('expected_structure', {})
        expected_verses = expected.get('verses_approx', expected.get('verses', 0))
        
        # Actual extracted units
        actual_units = 0
        cuid_file = Path(f"/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage/knowledge/dtc/cuids/{sid}_cuids.json")
        if cuid_file.exists():
            with open(cuid_file) as f:
                cuids = json.load(f)
                actual_units = len(cuids)
        
        req = scripture.get('required_independent_families', 2)
        coverage = {
            "scripture_id": sid,
            "canonical_name": scripture['canonical_name'],
            "category": scripture['category'],
            "files_on_disk": len(files),
            "total_bytes": total_bytes,
            "by_file_type": by_type,
            "witness_families_on_disk": all_family_ids,
            "independent_families": independent_families,
            "independent_family_count": len(independent_families),
            "required_independent_families": req,
            "expected_verses": expected_verses,
            "extracted_units": actual_units,
            "extraction_coverage": actual_units / max(1, expected_verses) if expected_verses > 0 else 0,
            "verification_status": "VERIFIED" if len(independent_families) >= req and actual_units >= expected_verses * 0.9 else "EVIDENCE_INCOMPLETE",
            "quality_gate_passed": len(independent_families) >= req and actual_units >= expected_verses * 0.9
        }
        
        coverage_report[sid] = coverage
    
    # Save report
    with open(Path(OUTPUT_DIR) / "coverage_report.json", 'w') as f:
        json.dump(coverage_report, f, indent=2)
    
    # Summary
    total_scriptures = len(coverage_report)
    verified = sum(1 for c in coverage_report.values() if c['verification_status'] == 'VERIFIED')
    incomplete = sum(1 for c in coverage_report.values() if c['verification_status'] == 'EVIDENCE_INCOMPLETE')
    
    print(f"Coverage Report Generated: {OUTPUT_DIR}/coverage_report.json")
    print(f"Total scriptures: {total_scriptures}")
    print(f"VERIFIED: {verified}")
    print(f"EVIDENCE_INCOMPLETE: {incomplete}")
    
    for sid, cov in sorted(coverage_report.items(), key=lambda x: x[1]['scripture_id']):
        status = cov['verification_status']
        fam_count = cov['independent_family_count']
        req_fam = cov['required_independent_families']
        ext_cov = cov['extraction_coverage']
        families_str = ', '.join(cov['independent_families']) if cov['independent_families'] else 'none'
        print(f"  {sid}: {status} | families: {fam_count}/{req_fam} ({families_str}) | extraction: {ext_cov:.1%}")

if __name__ == '__main__':
    main()
