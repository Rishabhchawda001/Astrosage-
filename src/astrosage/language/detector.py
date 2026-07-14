"""
Language Detection Engine.

Detects language, script, and multilingual content for every document.
Uses filename heuristics + character-level analysis.

Supported languages:
  - English
  - Hindi
  - Sanskrit
  - Devanagari-script languages
  - Bengali, Telugu, Tamil, Kannada, Malayalam, Gujarati, Odia, Punjabi
  - Mixed-language documents
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# ── Unicode ranges for Indian scripts ──
SCRIPT_RANGES = {
    "devanagari": (0x0900, 0x097F),
    "bengali": (0x0980, 0x09FF),
    "gurmukhi": (0x0A00, 0x0A7F),
    "gujarati": (0x0A80, 0x0AFF),
    "oriya": (0x0B00, 0x0B7F),
    "tamil": (0x0B80, 0x0BFF),
    "telugu": (0x0C00, 0x0C7F),
    "kannada": (0x0C80, 0x0CFF),
    "malayalam": (0x0D00, 0x0D7F),
    "sinhala": (0x0D80, 0x0DFF),
    "tibetan": (0x0F00, 0x0FFF),
}

LANGUAGE_KEYWORDS = {
    "hindi": ["hindi", "हिन्दी", "हिंदी"],
    "sanskrit": ["sanskrit", "संस्कृत"],
    "english": ["english"],
    "bengali": ["bengali", "bangla", "বাংলা"],
    "telugu": ["telugu", "తెలుగు"],
    "tamil": ["tamil", "தமிழ்"],
    "kannada": ["kannada", "ಕನ್ನಡ"],
    "malayalam": ["malayalam", "മലയാളം"],
    "gujarati": ["gujarati", "ગુજરાતી"],
    "odia": ["odia", "oriya", "ଓଡ଼ିଆ"],
    "punjabi": ["punjabi", "ਪੰਜਾਬੀ"],
}


@dataclass
class LanguageDetectionResult:
    """Result of language detection."""
    filename: str
    primary_language: str  # "english", "hindi", "sanskrit", etc.
    primary_script: str  # "latin", "devanagari", etc.
    confidence: float  # 0.0 - 1.0
    is_multilingual: bool
    detected_languages: list[str]  # All languages found
    detected_scripts: list[str]  # All scripts found
    script_ratios: dict[str, float]  # Script → ratio of text
    source: str  # "filename", "content", "combined"
    
    # Character counts
    total_chars: int = 0
    devanagari_chars: int = 0
    latin_chars: int = 0
    other_chars: int = 0


def _detect_script_from_chars(text: str) -> dict[str, float]:
    """Detect script distribution from character analysis."""
    script_counts: dict[str, int] = {}
    total_alpha = 0
    
    for char in text:
        if not char.isalpha() and not (0x0900 <= ord(char) <= 0x0DFF):
            continue
        
        total_alpha += 1
        assigned = False
        
        for script_name, (start, end) in SCRIPT_RANGES.items():
            if start <= ord(char) <= end:
                script_counts[script_name] = script_counts.get(script_name, 0) + 1
                assigned = True
                break
        
        if not assigned and char.isascii() and char.isalpha():
            script_counts["latin"] = script_counts.get("latin", 0) + 1
        elif not assigned:
            script_counts["other"] = script_counts.get("other", 0) + 1
    
    if total_alpha == 0:
        return {}
    
    return {s: c / total_alpha for s, c in script_counts.items()}


def _detect_language_from_filename(filename: str) -> Optional[str]:
    """Detect language from filename keywords."""
    filename_lower = filename.lower()
    
    # Check for language keywords
    for lang, keywords in LANGUAGE_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in filename_lower:
                return lang
    
    # Check for script indicators in filename
    devanagari_count = sum(1 for c in filename if 0x0900 <= ord(c) <= 0x097F)
    if devanagari_count > 0:
        return "hindi"  # Default Devanagari to Hindi
    
    return None


def _detect_language_from_path(filepath: str) -> Optional[str]:
    """Detect language from parent folder name."""
    parts = Path(filepath).parts
    for part in parts:
        result = _detect_language_from_filename(part)
        if result:
            return result
    return None


def detect_language(
    text: str,
    filename: str = "",
    filepath: str = "",
    sample_size: int = 50000,
) -> LanguageDetectionResult:
    """
    Detect language from text content and metadata.
    
    Strategy:
    1. Filename/path heuristics (fast, often accurate)
    2. Character-level script analysis (content-based)
    3. Combined scoring
    """
    # Sample text for efficiency
    sample = text[:sample_size] if len(text) > sample_size else text
    
    # Script analysis
    script_ratios = _detect_script_from_chars(sample)
    
    # Character counts
    total_chars = len(sample)
    devanagari_chars = sum(1 for c in sample if 0x0900 <= ord(c) <= 0x097F)
    latin_chars = sum(1 for c in sample if c.isascii() and c.isalpha())
    other_chars = total_chars - devanagari_chars - latin_chars
    
    # Determine primary script
    if script_ratios:
        primary_script = max(script_ratios, key=script_ratios.get)
    else:
        primary_script = "unknown"
    
    # Map script to language
    script_to_language = {
        "devanagari": "hindi",  # Default; could be Sanskrit
        "latin": "english",
        "bengali": "bengali",
        "telugu": "telugu",
        "tamil": "tamil",
        "kannada": "kannada",
        "malayalam": "malayalam",
        "gujarati": "gujarati",
        "oriya": "odia",
        "gurmukhi": "punjabi",
    }
    
    # Content-based language
    content_language = script_to_language.get(primary_script, "unknown")
    
    # Filename-based language
    filename_language = _detect_language_from_filename(filename)
    path_language = _detect_language_from_path(filepath)
    metadata_language = filename_language or path_language
    
    # Combined scoring
    if metadata_language and content_language == "unknown":
        primary_language = metadata_language
        confidence = 0.7
        source = "filename"
    elif metadata_language and content_language == metadata_language:
        primary_language = metadata_language
        confidence = 0.95
        source = "combined"
    elif script_ratios and max(script_ratios.values()) > 0.5:
        primary_language = content_language
        confidence = max(script_ratios.values())
        source = "content"
    elif metadata_language:
        primary_language = metadata_language
        confidence = 0.6
        source = "filename"
    else:
        primary_language = "unknown"
        confidence = 0.3
        source = "inference"
    
    # Detect if Sanskrit vs Hindi for Devanagari
    if primary_language == "hindi" and primary_script == "devanagari":
        # Sanskrit indicators in text
        sanskrit_indicators = ["॥", "ॐ", "श्री", "सूत्र", "श्लोक", "अध्याय", "वेद"]
        text_lower = sample.lower()
        sanskrit_score = sum(1 for ind in sanskrit_indicators if ind in text_lower)
        if sanskrit_score >= 2:
            primary_language = "sanskrit"
            confidence = min(confidence + 0.1, 1.0)
    
    # Multilingual detection
    significant_scripts = [s for s, r in script_ratios.items() if r > 0.1 and s != "other"]
    is_multilingual = len(significant_scripts) > 1
    
    detected_scripts = list(script_ratios.keys())
    detected_languages = []
    for s in detected_scripts:
        lang = script_to_language.get(s, s)
        if lang not in detected_languages:
            detected_languages.append(lang)
    
    if primary_language not in detected_languages:
        detected_languages.insert(0, primary_language)
    
    return LanguageDetectionResult(
        filename=filename,
        primary_language=primary_language,
        primary_script=primary_script,
        confidence=confidence,
        is_multilingual=is_multilingual,
        detected_languages=detected_languages,
        detected_scripts=detected_scripts,
        script_ratios=script_ratios,
        source=source,
        total_chars=total_chars,
        devanagari_chars=devanagari_chars,
        latin_chars=latin_chars,
        other_chars=other_chars,
    )


def detect_language_from_file(filepath: Path) -> LanguageDetectionResult:
    """Convenience: detect language directly from a file."""
    ext = filepath.suffix.lower()
    
    # For PDFs, extract a sample of text
    if ext == ".pdf":
        try:
            import pymupdf
            doc = pymupdf.open(str(filepath))
            sample_pages = min(5, len(doc))
            text = ""
            for i in range(sample_pages):
                text += doc[i].get_text()
            doc.close()
            
            if not text.strip():
                # No extractable text — rely on filename
                return detect_language("", filename=filepath.name, filepath=str(filepath))
            
            return detect_language(text, filename=filepath.name, filepath=str(filepath))
        except Exception:
            return detect_language("", filename=filepath.name, filepath=str(filepath))
    
    # For text-based files
    elif ext in (".txt", ".md", ".html", ".htm", ".csv", ".json"):
        try:
            text = filepath.read_text(encoding="utf-8", errors="replace")[:50000]
            return detect_language(text, filename=filepath.name, filepath=str(filepath))
        except Exception:
            return detect_language("", filename=filepath.name, filepath=str(filepath))
    
    # For DOCX
    elif ext == ".docx":
        try:
            from docx import Document as DocxDocument
            doc = DocxDocument(str(filepath))
            text = "\n".join(p.text for p in doc.paragraphs[:100])
            return detect_language(text, filename=filepath.name, filepath=str(filepath))
        except Exception:
            return detect_language("", filename=filepath.name, filepath=str(filepath))
    
    # For everything else, use filename
    else:
        return detect_language("", filename=filepath.name, filepath=str(filepath))
