#!/usr/bin/env python3
"""
Variant Classification Engine
Classifies differences using the hierarchy from quality_thresholds.json:
encoding > OCR > unicode > spacing > segmentation > punctuation > orthographic > 
editorial_normalization > commentarial_insertion > publisher_correction > formatting > 
authentic_textual_variant
"""
import re
import unicodedata
from typing import List, Dict, Tuple
from dataclasses import dataclass

# Classification hierarchy (first match wins)
CLASSIFICATION_RULES = [
    {
        "type": "encoding",
        "description": "Character encoding issues (replacement chars, mojibake)",
        "patterns": [
            r'\ufffd',  # Replacement character
            r'[\uE000-\uF8FF]',  # Private Use Area
            r'[\u200B-\u200F]',  # Zero-width chars
        ]
    },
    {
        "type": "ocr",
        "description": "OCR-specific errors",
        "patterns": [
            r'[|]{3,}',  # Multiple dandas
            r'[।]{3,}',  # Multiple devanagari dandas
            r'[०-९]{4,}',  # Long digit sequences (page numbers)
            r'^\s*\d+\s*$',  # Standalone page numbers
        ],
        "heuristics": [
            "repeated_single_char",
            "broken_conjuncts",
            "split_matra",
        ]
    },
    {
        "type": "unicode",
        "description": "Unicode normalization issues",
        "patterns": [
            r'[\u0300-\u036f]{2,}',  # Multiple combining marks
        ],
        "heuristics": ["nfc_nfd_mismatch", "decomposed_vs_composed"]
    },
    {
        "type": "spacing",
        "description": "Whitespace/spacing differences",
        "patterns": [
            r'\s+',
        ],
        "heuristics": ["extra_space", "missing_space", "danda_spacing"]
    },
    {
        "type": "segmentation",
        "description": "Word/pada segmentation differences",
        "heuristics": ["sandhi_vs_pada", "compound_split", "preverb_separation"]
    },
    {
        "type": "punctuation",
        "description": "Punctuation/danda differences",
        "patterns": [
            r'[।|]',  # Danda variations
            r'[॥]',   # Double danda
        ],
        "heuristics": ["danda_count", "danda_placement"]
    },
    {
        "type": "orthographic",
        "description": "Orthographic/spelling variations",
        "heuristics": [
            "anusvara_anunasika",  # ं vs ँ
            "visarga_alternation",  # ḥ vs h
            "vowel_length",  # a vs ā
            "retroflex_dental",  # ṭ vs t, ḍ vs d
            "sibilant_variation",  # ś vs ṣ vs s
        ]
    },
    {
        "type": "editorial_normalization",
        "description": "Editorial normalization choices",
        "heuristics": [
            "accent_placement",
            "sandhi_application",
            "compound_writing",
            "avagraha_usage",
        ]
    },
    {
        "type": "commentarial_insertion",
        "description": "Commentary text inserted into base text",
        "heuristics": ["bracketed_text", "commentary_markers", "explanatory_words"]
    },
    {
        "type": "publisher_correction",
        "description": "Publisher-specific corrections",
        "heuristics": ["modernized_spelling", "standardized_sandhi"]
    },
    {
        "type": "formatting",
        "description": "Formatting artifacts",
        "heuristics": ["line_breaks", "page_breaks", "headers_footers"]
    },
    {
        "type": "authentic_textual_variant",
        "description": "Genuine textual variant (recensional/manuscript)",
        "heuristics": []
    }
]

@dataclass
class VariantClassification:
    original_difference: str
    classification: str
    confidence: float
    reasoning: str
    eliminated: List[str]  # Simpler explanations that were ruled out

class VariantClassifier:
    def __init__(self):
        self.rules = CLASSIFICATION_RULES
    
    def classify_difference(self, text1: str, text2: str, 
                           family1: str, family2: str,
                           context: Dict = None) -> VariantClassification:
        """Classify a difference between two readings"""
        
        # Quick check: if identical after normalization
        norm1 = self.normalize_text(text1)
        norm2 = self.normalize_text(text2)
        
        if norm1 == norm2:
            return VariantClassification(
                original_difference=f"{text1[:50]}... vs {text2[:50]}...",
                classification="identical_after_normalization",
                confidence=1.0,
                reasoning="Texts identical after Unicode normalization, accent stripping, and whitespace normalization",
                eliminated=[]
            )
        
        # Check each classification level
        eliminated = []
        for rule in self.rules:
            result = self.check_rule(text1, text2, rule)
            if result:
                return VariantClassification(
                    original_difference=f"{text1[:50]}... vs {text2[:50]}...",
                    classification=rule["type"],
                    confidence=result["confidence"],
                    reasoning=result["reasoning"],
                    eliminated=eliminated
                )
            eliminated.append(rule["type"])
        
        # If nothing else matched, it's an authentic textual variant
        return VariantClassification(
            original_difference=f"{text1[:50]}... vs {text2[:50]}...",
            classification="authentic_textual_variant",
            confidence=0.8,
            reasoning="All simpler explanations eliminated; difference appears to be genuine textual variant",
            eliminated=eliminated
        )
    
    def check_rule(self, text1: str, text2: str, rule: Dict) -> Dict:
        """Check if a classification rule applies"""
        patterns = rule.get("patterns", [])
        heuristics = rule.get("heuristics", [])
        
        # Pattern-based checks
        for pattern in patterns:
            if re.search(pattern, text1) or re.search(pattern, text2):
                return {
                    "confidence": 0.9,
                    "reasoning": f"Matches {rule['type']} pattern: {pattern}"
                }
        
        # Heuristic checks
        for heuristic in heuristics:
            if self.check_heuristic(text1, text2, heuristic):
                return {
                    "confidence": 0.8,
                    "reasoning": f"Heuristic match: {heuristic}"
                }
        
        return None
    
    def check_heuristic(self, text1: str, text2: str, heuristic: str) -> bool:
        """Check a specific heuristic"""
        n1 = self.normalize_text(text1)
        n2 = self.normalize_text(text2)
        
        if heuristic == "repeated_single_char":
            return bool(re.search(r'(.)\1{3,}', text1) or re.search(r'(.)\1{3,}', text2))
        
        elif heuristic == "broken_conjuncts":
            # Check for broken Devanagari conjuncts
            return False  # Placeholder
        
        elif heuristic == "split_matra":
            # Check for separated matras
            return False  # Placeholder
        
        elif heuristic == "nfc_nfd_mismatch":
            nfc1 = unicodedata.normalize('NFC', text1)
            nfc2 = unicodedata.normalize('NFC', text2)
            nfd1 = unicodedata.normalize('NFD', text1)
            nfd2 = unicodedata.normalize('NFD', text2)
            return (nfc1 == nfc2 and nfd1 != nfd2) or (nfc1 != nfc2 and nfd1 == nfd2)
        
        elif heuristic == "decomposed_vs_composed":
            return False
        
        elif heuristic == "extra_space":
            return '  ' in text1 or '  ' in text2
        
        elif heuristic == "missing_space":
            # No space where expected (e.g., between words)
            return False
        
        elif heuristic == "danda_spacing":
            return bool(re.search(r'[।|]\s*[।|]', text1) or re.search(r'[।|]\s*[।|]', text2))
        
        elif heuristic == "sandhi_vs_pada":
            # Check if one has sandhi applied and other has pada form
            return False  # Placeholder - would need padapatha reference
        
        elif heuristic == "compound_split":
            return False
        
        elif heuristic == "preverb_separation":
            return False
        
        elif heuristic == "danda_count":
            d1 = text1.count('|') + text1.count('।')
            d2 = text2.count('|') + text2.count('।')
            return d1 != d2
        
        elif heuristic == "danda_placement":
            return False
        
        elif heuristic == "anusvara_anunasika":
            return ('ं' in text1 and 'ँ' in text2) or ('ँ' in text1 and 'ं' in text2)
        
        elif heuristic == "visarga_alternation":
            return ('ḥ' in text1 and 'h' in text2 and 'ḥ' not in text2) or \
                   ('ḥ' in text2 and 'h' in text1 and 'ḥ' not in text1)
        
        elif heuristic == "vowel_length":
            # Check for a/ā, i/ī, u/ū differences
            pairs = [('a', 'ā'), ('i', 'ī'), ('u', 'ū'), ('ṛ', 'ṝ'), ('ḷ', 'ḹ')]
            for short, long in pairs:
                if short in n1 and long in n2 and short not in n2:
                    return True
                if long in n1 and short in n2 and long not in n2:
                    return True
            return False
        
        elif heuristic == "retroflex_dental":
            pairs = [('ṭ', 't'), ('ṭh', 'th'), ('ḍ', 'd'), ('ḍh', 'dh'), ('ṇ', 'n')]
            for retro, dental in pairs:
                if retro in n1 and dental in n2 and retro not in n2:
                    return True
                if dental in n1 and retro in n2 and dental not in n2:
                    return True
            return False
        
        elif heuristic == "sibilant_variation":
            sibilants = ['ś', 'ṣ', 's']
            for s in sibilants:
                if s in n1 and any(other in n2 for other in sibilants if other != s):
                    return True
            return False
        
        elif heuristic == "accent_placement":
            # Check for accent mark differences
            acc1 = len(re.findall(r'[\u0300-\u036f]', text1))
            acc2 = len(re.findall(r'[\u0300-\u036f]', text2))
            return acc1 != acc2
        
        elif heuristic == "sandhi_application":
            return False  # Placeholder
        
        elif heuristic == "compound_writing":
            return False
        
        elif heuristic == "avagraha_usage":
            return ('ऽ' in text1) != ('ऽ' in text2)
        
        elif heuristic == "bracketed_text":
            return ('[' in text1 and ']' in text1) or ('[' in text2 and ']' in text2)
        
        elif heuristic == "commentary_markers":
            return bool(re.search(r'(iti|eva|ca|vā|iti)', text1)) != bool(re.search(r'(iti|eva|ca|vā|iti)', text2))
        
        elif heuristic == "explanatory_words":
            return False
        
        elif heuristic == "modernized_spelling":
            return False
        
        elif heuristic == "standardized_sandhi":
            return False
        
        elif heuristic == "line_breaks":
            return '\n' in text1 or '\n' in text2
        
        elif heuristic == "page_breaks":
            return bool(re.search(r'\f', text1)) or bool(re.search(r'\f', text2))
        
        elif heuristic == "headers_footers":
            return bool(re.search(r'(page|p\d+|अध्याय|अङ्क)', text1, re.I)) or \
                   bool(re.search(r'(page|p\d+|अध्याय|अङ्क)', text2, re.I))
        
        return False
    
    def normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        # Remove accents
        text = unicodedata.normalize('NFKD', text)
        text = ''.join(c for c in text if not unicodedata.combining(c))
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        # Normalize dandas
        text = text.replace('|', '।')
        text = re.sub(r'।+', '।', text)
        # Visarga to h
        text = text.replace('ḥ', 'h')
        return text.strip().lower()

def main():
    import sys
    classifier = VariantClassifier()
    
    # Test cases
    test_cases = [
        ("agnim īḻe purohitam", "agnim īḷe purohitam", "F-AUFRECHT", "F-LUBOTSKY"),
        ("agnim īḷe purohitam", "agnim iḷe purohitam", "F-AUFRECHT", "F-LUBOTSKY"),
        ("agnim īḷe purohitam", "agnim iḍe purohitam", "F-AUFRECHT", "F-LUBOTSKY"),
        ("agnim īḍe purohitam", "agnim iḍe purohitam", "F-AUFRECHT", "F-LUBOTSKY"),
        ("agnim īḷe purohitam", "agnim iḷe purohitam |", "F-AUFRECHT", "F-LUBOTSKY"),
        ("agnim īḷe purohitam", "agnim īḷe puruhitam", "F-AUFRECHT", "F-LUBOTSKY"),
        ("agnim īḷe purohitam", "agnim iḍe purohitam", "F-AUFRECHT", "F-LUBOTSKY"),
    ]
    
    for t1, t2, f1, f2 in test_cases:
        result = classifier.classify_difference(t1, t2, f1, f2)
        print(f"\n{t1} vs {t2}")
        print(f"  Classification: {result.classification}")
        print(f"  Confidence: {result.confidence}")
        print(f"  Reasoning: {result.reasoning}")
        print(f"  Eliminated: {result.eliminated}")

if __name__ == '__main__':
    main()
