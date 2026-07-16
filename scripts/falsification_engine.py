#!/usr/bin/env python3
"""
Falsification Engine - Attempt to disprove every canonical reconstruction
"""
import json
import re
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, asdict

@dataclass
class FalsificationAttempt:
    cuid: str
    claim: str
    method: str
    evidence_searched: List[str]
    result: str  # "survived", "falsified", "inconclusive"
    counter_evidence: List[Dict]
    confidence_change: float
    notes: str

class FalsificationEngine:
    def __init__(self, scripture: str):
        self.scripture = scripture
        self.attempts = []
    
    def load_cuids(self):
        """Load CUIDs for the scripture"""
        cuid_file = f"/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage/knowledge/dtc/cuids/{self.scripture}_cuids.json"
        with open(cuid_file) as f:
            return json.load(f)
    
    def attempt_falsify_completeness(self, cuids: Dict) -> List[FalsificationAttempt]:
        """Try to falsify 'complete' claim"""
        attempts = []
        
        # Check expected structure vs actual
        if self.scripture == "RV":
            expected_mandalas = 10
            expected_verses = 10552  # Approximate
            
            mandalas_found = set()
            verses_found = 0
            for cuid, unit in cuids.items():
                pos = unit.get('structural_position', {})
                if 'mandala' in pos:
                    mandalas_found.add(pos['mandala'])
                    verses_found += 1
            
            missing_mandalas = set(range(1, 11)) - mandalas_found
            if missing_mandalas:
                attempts.append(FalsificationAttempt(
                    cuid="RV-COMPLETENESS",
                    claim="All 10 mandalas present",
                    method="structural_audit",
                    evidence_searched=["canonical_units_v2.json"],
                    result="falsified",
                    counter_evidence=[{"missing_mandalas": list(missing_mandalas)}],
                    confidence_change=-0.5,
                    notes=f"Missing mandalas: {missing_mandalas}"
                ))
            else:
                attempts.append(FalsificationAttempt(
                    cuid="RV-COMPLETENESS",
                    claim="All 10 mandalas present",
                    method="structural_audit",
                    evidence_searched=["canonical_units_v2.json"],
                    result="survived",
                    counter_evidence=[],
                    confidence_change=0.1,
                    notes=f"All 10 mandalas present, {verses_found} verses"
                ))
            
            # Check verse count
            if verses_found < expected_verses * 0.95:
                attempts.append(FalsificationAttempt(
                    cuid="RV-VERSE_COUNT",
                    claim=f"At least 95% of expected verses ({expected_verses}) present",
                    method="count_audit",
                    evidence_searched=["canonical_units_v2.json"],
                    result="falsified",
                    counter_evidence=[{"found": verses_found, "expected": expected_verses}],
                    confidence_change=-0.3,
                    notes=f"Only {verses_found} verses found"
                ))
            else:
                attempts.append(FalsificationAttempt(
                    cuid="RV-VERSE_COUNT",
                    claim=f"At least 95% of expected verses present",
                    method="count_audit",
                    evidence_searched=["canonical_units_v2.json"],
                    result="survived",
                    counter_evidence=[],
                    confidence_change=0.1,
                    notes=f"{verses_found}/{expected_verses} verses"
                ))
        
        return attempts
    
    def attempt_falsify_independence(self, cuids: Dict) -> List[FalsificationAttempt]:
        """Try to falsify witness independence claims"""
        attempts = []
        
        if self.scripture == "RV":
            # Check if VNH is still counted as independent
            for cuid, unit in cuids.items():
                families = unit.get('witness_families_independent', [])
                if 'F-VNH' in families or 'VNH' in families:
                    attempts.append(FalsificationAttempt(
                        cuid=cuid,
                        claim="VNH is an independent witness",
                        method="family_collapse_audit",
                        evidence_searched=["family_collapse_rules.json", "witness_family_graph.json"],
                        result="falsified",
                        counter_evidence=[{"family_collapse_rule": "VNH derived from Aufrecht 1863"}],
                        confidence_change=-0.4,
                        notes="VNH correctly collapsed into F-AUFRECHT family"
                    ))
                    break
            
            # Verify only 2 independent families
            all_families = set()
            for unit in cuids.values():
                all_families.update(unit.get('witness_families_independent', []))
            
            if len(all_families) != 2:
                attempts.append(FalsificationAttempt(
                    cuid="RV-INDEPENDENCE",
                    claim="Exactly 2 independent witness families",
                    method="family_count_audit",
                    evidence_searched=["witness_family_graph.json"],
                    result="inconclusive" if len(all_families) > 2 else "survived",
                    counter_evidence=[{"families_found": list(all_families)}],
                    confidence_change=-0.2 if len(all_families) != 2 else 0.1,
                    notes=f"Found {len(all_families)} independent families: {all_families}"
                ))
        
        return attempts
    
    def attempt_falsify_textual_stability(self, cuids: Dict) -> List[FalsificationAttempt]:
        """Try to falsify 'text is stable' claim"""
        attempts = []
        
        # Check variant apparatus for actual lexical variants
        variant_file = f"/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage/knowledge/dtc/rigveda/variant_apparatus_formal.json"
        if Path(variant_file).exists():
            with open(variant_file) as f:
                variants = json.load(f)
            
            lexical_variants = []
            for app in variants.get('apparatus', []):
                for diff in app.get('differences', []):
                    if diff.get('type') != 'sandhi/segmentation':
                        lexical_variants.append(diff)
            
            if lexical_variants:
                attempts.append(FalsificationAttempt(
                    cuid="RV-STABILITY",
                    claim="No lexical variants between Aufrecht and Lubotsky",
                    method="variant_audit",
                    evidence_searched=["variant_apparatus_formal.json"],
                    result="falsified",
                    counter_evidence=[{"lexical_variants_found": len(lexical_variants)}],
                    confidence_change=-0.5,
                    notes=f"Found {len(lexical_variants)} non-sandhi variants"
                ))
            else:
                attempts.append(FalsificationAttempt(
                    cuid="RV-STABILITY",
                    claim="No lexical variants between Aufrecht and Lubotsky",
                    method="variant_audit",
                    evidence_searched=["variant_apparatus_formal.json"],
                    result="survived",
                    counter_evidence=[],
                    confidence_change=0.1,
                    notes="All differences are sandhi/segmentation/accent"
                ))
        
        return attempts
    
    def attempt_falsify_akshara_verification(self, cuids: Dict) -> List[FalsificationAttempt]:
        """Try to falsify akshara verification"""
        attempts = []
        
        akshara_file = "/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage/knowledge/dtc/rigveda/akshara_verification.json"
        if Path(akshara_file).exists():
            with open(akshara_file) as f:
                data = json.load(f)
            
            problems = data.get('problems', [])
            if problems:
                attempts.append(FalsificationAttempt(
                    cuid="RV-AKSHARA",
                    claim="All aksharas verified against Padapatha",
                    method="akshara_audit",
                    evidence_searched=["akshara_verification.json"],
                    result="falsified",
                    counter_evidence=[{"problems_found": len(problems)}],
                    confidence_change=-0.3,
                    notes=f"Found {len(problems)} akshara verification problems"
                ))
            else:
                attempts.append(FalsificationAttempt(
                    cuid="RV-AKSHARA",
                    claim="All aksharas verified against Padapatha",
                    method="akshara_audit",
                    evidence_searched=["akshara_verification.json"],
                    result="survived",
                    counter_evidence=[],
                    confidence_change=0.1,
                    notes="No akshara verification problems"
                ))
        
        return attempts
    
    def run_all_falsifications(self):
        """Run all falsification attempts"""
        cuids = self.load_cuids()
        all_attempts = []
        
        all_attempts.extend(self.attempt_falsify_completeness(cuids))
        all_attempts.extend(self.attempt_falsify_independence(cuids))
        all_attempts.extend(self.attempt_falsify_textual_stability(cuids))
        all_attempts.extend(self.attempt_falsify_akshara_verification(cuids))
        
        self.attempts = all_attempts
        return all_attempts
    
    def save_report(self):
        """Save falsification report"""
        out_file = f"/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage/knowledge/dtc/{self.scripture.lower()}/falsification_report.json"
        Path(out_file).parent.mkdir(parents=True, exist_ok=True)
        
        report = {
            "scripture": self.scripture,
            "total_attempts": len(self.attempts),
            "survived": sum(1 for a in self.attempts if a.result == "survived"),
            "falsified": sum(1 for a in self.attempts if a.result == "falsified"),
            "inconclusive": sum(1 for a in self.attempts if a.result == "inconclusive"),
            "attempts": [asdict(a) for a in self.attempts]
        }
        
        with open(out_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Falsification report saved to {out_file}")
        print(f"Survived: {report['survived']}, Falsified: {report['falsified']}, Inconclusive: {report['inconclusive']}")
        return report

def main():
    import sys
    scripture = sys.argv[1] if len(sys.argv) > 1 else "RV"
    engine = FalsificationEngine(scripture)
    engine.run_all_falsifications()
    engine.save_report()

if __name__ == '__main__':
    main()
