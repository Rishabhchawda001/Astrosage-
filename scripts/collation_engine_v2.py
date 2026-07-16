#!/usr/bin/env python3
"""
Multi-witness collation engine for canonical units
Compares only INDEPENDENT witness families at verse/pada/word/akshara level
"""
import json
import re
import unicodedata
from pathlib import Path
from typing import Dict, List, Tuple, Any
from collections import defaultdict
from dataclasses import dataclass, asdict

# Load witness family collapse rules
FAMILY_RULES_FILE = "/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage/knowledge/dtc/config/family_collapse_rules.json"

with open(FAMILY_RULES_FILE) as f:
    FAMILY_DATA = json.load(f)

# Build family map
FAMILY_MAP = {}
for family in FAMILY_DATA.get('families', []):
    fam_id = family['family_id']
    for rep in family.get('representatives', []):
        # Extract witness IDs
        if '(' in rep:
            wit = rep.split('(')[1].split(')')[0]
            FAMILY_MAP[wit] = fam_id

# Independent families for Rigveda
RV_INDEPENDENT_FAMILIES = ["F-AUFRECHT", "F-LUBOTSKY"]
RV_REFERENCE_FAMILIES = ["F-PADAPATHA"]

# Independent families for Bhagavad Gita
BG_INDEPENDENT_FAMILIES = ["F-GRETIL", "F-GITAPRESS"]

ACCENT_STRIP = dict.fromkeys(c for c in range(0x0300, 0x0370))
SANDHI_FINALS = set('mṃḥhṇnrrttsṭḍṣñṅ')

def strip_accents(s: str) -> str:
    """Remove Vedic accents"""
    return unicodedata.normalize('NFKD', s).translate(ACCENT_STRIP)

def normalize_for_comparison(s: str) -> str:
    """Normalize text for comparison: strip accents, normalize whitespace, visarga->h"""
    s = strip_accents(s.lower())
    s = re.sub(r'[\s\|\-]+', '', s)
    s = s.replace('ḥ', 'h')
    return s

def akshara_normalize(s: str) -> str:
    """Normalize to akshara level for comparison"""
    s = strip_accents(s.lower())
    s = re.sub(r'[\s\|\-]+', '', s)
    s = s.replace('ḥ', 'h')
    # Collapse sandhi finals
    for ch in SANDHI_FINALS:
        s = s.replace(ch, '#')
    s = re.sub(r'a#', '#', s)
    s = re.sub(r'#a', '#', s)
    return re.sub(r'[^a-zāīūṛḷṃḥṇñṅśṣṭḍ#]', '', s)

def extract_words(text: str) -> List[str]:
    """Extract words from text"""
    return [w for w in re.split(r'[\s\|\-]+', text) if w]

@dataclass
class CollationResult:
    cuid: str
    scripture: str
    position: Dict
    independent_families: List[str]
    readings: Dict[str, str]  # family -> reading
    agreements: List[Dict]
    disagreements: List[Dict]
    missing_families: List[str]
    variants: List[Dict]
    confidence: float

class CollationEngine:
    def __init__(self, scripture: str):
        self.scripture = scripture
        if scripture == "RV":
            self.independent_families = RV_INDEPENDENT_FAMILIES
            self.reference_families = RV_REFERENCE_FAMILIES
        elif scripture == "BG":
            self.independent_families = BG_INDEPENDENT_FAMILIES
            self.reference_families = []
        else:
            self.independent_families = []
            self.reference_families = []
    
    def load_family_readings(self, family: str) -> Dict[str, str]:
        """Load readings for a witness family"""
        # This would load from the extracted witness files
        # For now, return empty - implement based on actual data structure
        return {}
    
    def compare_readings(self, readings: Dict[str, str]) -> Tuple[List[Dict], List[Dict]]:
        """Compare readings across families, return agreements and disagreements"""
        agreements = []
        disagreements = []
        
        families = list(readings.keys())
        if len(families) < 2:
            return agreements, disagreements
        
        # Compare pairwise
        for i, fam1 in enumerate(families):
            for fam2 in families[i+1:]:
                text1 = readings[fam1]
                text2 = readings[fam2]
                
                norm1 = normalize_for_comparison(text1)
                norm2 = normalize_for_comparison(text2)
                
                if norm1 == norm2:
                    agreements.append({
                        "families": [fam1, fam2],
                        "type": "identical_after_normalization",
                        "reading": text1[:100]
                    })
                else:
                    # Classify difference
                    ak1 = akshara_normalize(text1)
                    ak2 = akshara_normalize(text2)
                    
                    if ak1 == ak2:
                        diff_type = "sandhi_segmentation"
                    else:
                        # Check word level
                        words1 = set(extract_words(norm1))
                        words2 = set(extract_words(norm2))
                        if words1 == words2:
                            diff_type = "word_segmentation"
                        else:
                            diff_type = "lexical_variant"
                    
                    disagreements.append({
                        "families": [fam1, fam2],
                        "type": diff_type,
                        "family1_reading": text1[:200],
                        "family2_reading": text2[:200],
                        "normalized1": norm1[:200],
                        "normalized2": norm2[:200]
                    })
        
        return agreements, disagreements
    
    def classify_variants(self, disagreements: List[Dict]) -> List[Dict]:
        """Classify each disagreement using the classification hierarchy"""
        classified = []
        for d in disagreements:
            # Apply classification order from quality_thresholds.json
            # For now, use the type from comparison
            classified.append({
                **d,
                "classification": d["type"],
                "confidence": 0.9 if d["type"] != "lexical_variant" else 0.7
            })
        return classified
    
    def collate_cuid(self, cuid: str, position: Dict, family_readings: Dict[str, str]) -> CollationResult:
        """Collate a single canonical unit across families"""
        # Filter to independent families only
        independent_readings = {k: v for k, v in family_readings.items() if k in self.independent_families}
        
        agreements, disagreements = self.compare_readings(independent_readings)
        variants = self.classify_variants(disagreements)
        
        # Calculate confidence
        total_fams = len(self.independent_families)
        present_fams = len(independent_readings)
        if present_fams == total_fams:
            agreement_ratio = len(agreements) / max(1, len(agreements) + len(disagreements))
            confidence = 0.5 + 0.5 * agreement_ratio
        else:
            confidence = 0.3 * (present_fams / total_fams)
        
        missing = [f for f in self.independent_families if f not in family_readings]
        
        return CollationResult(
            cuid=cuid,
            scripture=self.scripture,
            position=position,
            independent_families=self.independent_families,
            readings=independent_readings,
            agreements=agreements,
            disagreements=disagreements,
            missing_families=missing,
            variants=variants,
            confidence=confidence
        )
    
    def collate_scripture(self, cuids_file: str) -> List[CollationResult]:
        """Collate all CUIDs for a scripture"""
        with open(cuids_file) as f:
            cuids = json.load(f)
        
        # Load witness readings for each family
        # This would need actual extraction from witness files
        # For now, return empty results as template
        results = []
        
        # Load actual readings if available
        if self.scripture == "RV":
            # Load from vedaweb_extract.json and canonical_units
            pass
        elif self.scripture == "BG":
            pass
        
        return results

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python collation_engine_v2.py [RV|BG]")
        return
    
    scripture = sys.argv[1].upper()
    engine = CollationEngine(scripture)
    
    if scripture == "RV":
        cuids_file = "/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage/knowledge/dtc/cuids/RV_cuids.json"
        # Also need to load witness readings
        print("Rigveda collation - implement witness reading loading")
    elif scripture == "BG":
        cuids_file = "/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage/knowledge/dtc/cuids/BG_cuids.json"
        print("Bhagavad Gita collation - implement witness reading loading")
    else:
        print(f"Unknown scripture: {scripture}")
        return

if __name__ == '__main__':
    main()
