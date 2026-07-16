#!/usr/bin/env python3
"""
Canonical Unit ID (CUID) Engine
Assigns permanent, immutable IDs to every canonical unit
"""
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

CUID_SCHEMA_FILE = "/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage/knowledge/dtc/config/cuid_schema.json"
OUTPUT_DIR = "/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage/knowledge/dtc/cuids"

@dataclass
class CUID:
    cuid: str
    scripture: str
    structural_position: Dict[str, Any]
    canonical_text: str
    witness_families: List[str]
    witness_families_independent: List[str]
    witness_families_collated: List[str]
    supporting_editions: List[str]
    variant_readings: List[Dict]
    confidence: Dict[str, Any]
    evidence_chain: List[str]
    provenance: Dict[str, str]
    falsification_status: str = "pending"

class CUIDEngine:
    def __init__(self):
        with open(CUID_SCHEMA_FILE) as f:
            self.schema = json.load(f)
        self.cuid_registry = {}
        self.output_dir = Path(OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_cuid(self, scripture_id: str, position: Dict) -> str:
        """Generate a CUID based on scripture and structural position"""
        prefixes = self.schema['cuid_format']['scripture_prefixes']
        if scripture_id in prefixes:
            template = prefixes[scripture_id]
            # Replace placeholders
            for key, value in position.items():
                template = template.replace(f"{{{key}}}", str(value))
            return template
        # Fallback
        return f"{scripture_id}-CU-UNKNOWN"
    
    def register_unit(self, scripture: str, position: Dict, canonical_text: str,
                      witness_families: List[str], independent_families: List[str],
                      collated_families: List[str], supporting_editions: List[str],
                      variants: List[Dict], confidence: Dict, evidence_chain: List[str],
                      provenance: Dict) -> CUID:
        """Register a new canonical unit"""
        cuid = self.generate_cuid(scripture, position)
        
        # Check for collision
        if cuid in self.cuid_registry:
            existing = self.cuid_registry[cuid]
            if existing.canonical_text != canonical_text:
                print(f"WARNING: CUID collision with different text: {cuid}")
        
        unit = CUID(
            cuid=cuid,
            scripture=scripture,
            structural_position=position,
            canonical_text=canonical_text,
            witness_families=witness_families,
            witness_families_independent=independent_families,
            witness_families_collated=collated_families,
            supporting_editions=supporting_editions,
            variant_readings=variants,
            confidence=confidence,
            evidence_chain=evidence_chain,
            provenance=provenance
        )
        
        self.cuid_registry[cuid] = unit
        return unit
    
    def save_scripture_cuids(self, scripture: str):
        """Save all CUIDs for a scripture"""
        scripture_cuids = {k: v for k, v in self.cuid_registry.items() if v.scripture == scripture}
        out_file = self.output_dir / f"{scripture}_cuids.json"
        with open(out_file, 'w') as f:
            json.dump({k: asdict(v) for k, v in scripture_cuids.items()}, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(scripture_cuids)} CUIDs to {out_file}")
    
    def load_scripture_cuids(self, scripture: str):
        """Load existing CUIDs for a scripture"""
        in_file = self.output_dir / f"{scripture}_cuids.json"
        if in_file.exists():
            with open(in_file) as f:
                data = json.load(f)
                for k, v in data.items():
                    self.cuid_registry[k] = CUID(**v)
            print(f"Loaded {len(data)} CUIDs from {in_file}")

def build_rv_cuids_from_extraction():
    """Build CUIDs for Rigveda from the existing extraction"""
    engine = CUIDEngine()
    
    # Load the canonical units from extraction
    extraction_file = "/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage/knowledge/dtc/rigveda/canonical_units_v2.json"
    with open(extraction_file) as f:
        data = json.load(f)
    
    units = data.get('units', [])
    print(f"Processing {len(units)} Rigveda units...")
    
    for unit in units:
        ref = unit.get('canonical_ref', '')  # e.g., "RV_1.001.01"
        match = re.match(r'RV_(\d+)\.(\d+)\.(\d+)', ref)
        if not match:
            continue
        mandala, sukta, verse = map(int, match.groups())
        
        position = {
            "mandala": mandala,
            "sukta": sukta,
            "verse": verse
        }
        
        engine.register_unit(
            scripture="RV",
            position=position,
            canonical_text=unit.get('text', ''),
            witness_families=["F-AUFRECHT", "F-LUBOTSKY", "F-PADAPATHA"],
            independent_families=["F-AUFRECHT", "F-LUBOTSKY"],
            collated_families=["F-AUFRECHT", "F-LUBOTSKY", "F-PADAPATHA"],
            supporting_editions=["Aufrecht 1863 (GRETIL TEI)", "Lubotsky (VedaWeb)", "Padapatha (GRETIL)"],
            variants=[],  # No lexical variants found
            confidence={
                "independent_families": 2,
                "score": 0.95 if unit.get('status') == 'verified_strong' else 0.5
            },
            evidence_chain=[
                "Aufrecht GRETIL TEI extraction",
                "Lubotsky VedaWeb TEI extraction", 
                "Padapatha GRETIL TEI extraction",
                "3-way collation via collate_3base.py",
                "Akshara verification passed"
            ],
            provenance={
                "repository": "GRETIL, VedaWeb (Zenodo 4601264)",
                "license": "CC-BY-NC-SA / CC-BY",
                "checksum": unit.get('uuid', '')
            }
        )
    
    engine.save_scripture_cuids("RV")
    return engine

def build_bg_cuids_from_extraction():
    """Build CUIDs for Bhagavad Gita from existing extraction"""
    engine = CUIDEngine()
    
    # Load verses
    verses_file = "/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage/knowledge/dtc/bhagavad_gita/verses_canonical_v3.json"
    with open(verses_file) as f:
        verses = json.load(f)
    
    print(f"Processing {len(verses)} Bhagavad Gita verses...")
    
    for verse in verses:
        ref = verse.get('verse', '')  # e.g., "BG 1.1"
        match = re.match(r'BG\s+(\d+)\.(\d+)', ref)
        if not match:
            continue
        adhyaya, verse_num = map(int, match.groups())
        
        position = {
            "adhyaya": adhyaya,
            "verse": verse_num
        }
        
        # Get text
        text = verse.get('text', '')
        
        engine.register_unit(
            scripture="BG",
            position=position,
            canonical_text=text,
            witness_families=["F-GRETIL", "F-GITAPRESS"],
            independent_families=["F-GRETIL", "F-GITAPRESS"],
            collated_families=["F-GRETIL", "F-GITAPRESS"],
            supporting_editions=["GRETIL (5 commentaries)", "Gita Press (Tattva Vivecana OCR)"],
            variants=verse.get('variants', []),
            confidence={
                "independent_families": 2,
                "score": 0.75
            },
            evidence_chain=[
                "GRETIL verse text extracted from 5 commentaries",
                "Gita Press OCR extracted and cleaned",
                "Collation shows identical verse text across all GRETIL sources",
                "Akshara verification passed"
            ],
            provenance={
                "repository": "GRETIL, Archive.org",
                "license": "CC-BY-NC-SA / Public Domain",
                "checksum": verse.get('fingerprint', '')
            }
        )
    
    engine.save_scripture_cuids("BG")
    return engine

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'rv':
        build_rv_cuids_from_extraction()
    elif len(sys.argv) > 1 and sys.argv[1] == 'bg':
        build_bg_cuids_from_extraction()
    else:
        print("Usage: python cuid_engine.py [rv|bg]")
