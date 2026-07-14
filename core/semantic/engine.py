"""
Semantic Engine — Semantic analysis of chunks for knowledge boundary detection.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional

from core.chunking.engine import Chunk, ChunkType


@dataclass
class SemanticBoundary:
    """A detected semantic boundary."""
    boundary_id: str = ""
    boundary_type: str = ""  # section, verse, concept, commentary
    position: int = 0
    confidence: float = 0.0
    text_before: str = ""
    text_after: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SemanticSegment:
    """A semantically coherent segment of text."""
    text: str = ""
    segment_type: str = ""
    start_pos: int = 0
    end_pos: int = 0
    confidence: float = 0.0
    language: str = ""


class SemanticEngine:
    """
    Detects semantic boundaries in text for intelligent chunking.
    
    Identifies: section breaks, verse boundaries, concept transitions,
    commentary boundaries, paragraph breaks.
    """

    def __init__(self):
        self._boundary_patterns: dict[str, str] = {
            "verse_sanskrit": r"(?:॥|।)\s*",
            "verse_hindi": r"(?:।।|।)\s*",
            "section_english": r"\n\n+",
            "heading": r"^(#{1,6}\s+.{1,100})$",
            "numbered_section": r"^\d+[\.\)]\s+",
        }
        self._custom_patterns: dict[str, str] = {}

    def add_pattern(self, name: str, pattern: str) -> None:
        self._custom_patterns[name] = pattern

    def detect_boundaries(self, text: str, language: str = "") -> list[SemanticBoundary]:
        boundaries = []
        all_patterns = {**self._boundary_patterns, **self._custom_patterns}
        for name, pattern in all_patterns.items():
            for match in re.finditer(pattern, text, re.MULTILINE):
                boundaries.append(SemanticBoundary(
                    boundary_type=name,
                    position=match.start(),
                    text_before=text[max(0, match.start() - 50):match.start()],
                    text_after=text[match.end():match.end() + 50],
                    confidence=0.8,
                ))
        boundaries.sort(key=lambda b: b.position)
        return boundaries

    def segment_text(self, text: str, language: str = "", max_size: int = 5000) -> list[SemanticSegment]:
        boundaries = self.detect_boundaries(text, language)
        segments = []
        start = 0
        for boundary in boundaries:
            if boundary.position > start:
                segment_text = text[start:boundary.position].strip()
                if segment_text:
                    segments.append(SemanticSegment(
                        text=segment_text,
                        segment_type=boundary.boundary_type,
                        start_pos=start,
                        end_pos=boundary.position,
                        confidence=boundary.confidence,
                        language=language,
                    ))
            start = boundary.position
        # Last segment
        if start < len(text):
            segment_text = text[start:].strip()
            if segment_text:
                segments.append(SemanticSegment(
                    text=segment_text,
                    segment_type="remainder",
                    start_pos=start,
                    end_pos=len(text),
                    confidence=0.5,
                    language=language,
                ))
        return segments

    def detect_language_boundary(self, chunks: list[Chunk]) -> list[int]:
        """Find positions where language changes."""
        changes = []
        for i in range(1, len(chunks)):
            if chunks[i].language and chunks[i - 1].language:
                if chunks[i].language != chunks[i - 1].language:
                    changes.append(i)
        return changes

    def summary(self) -> dict:
        return {
            "pattern_count": len(self._boundary_patterns) + len(self._custom_patterns),
            "patterns": list(self._boundary_patterns.keys()) + list(self._custom_patterns.keys()),
        }
