"""
Natural Language Answer Generator for AstroSage.

Converts structured evidence chains into human-readable answers with
proper citations and provenance tracing.
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Citation:
    """A single citation reference."""
    scripture: str
    chapter: str
    verse: str
    text_snippet: str
    confidence: float


@dataclass
class Answer:
    """Generated answer with citations."""
    question: str
    answer_text: str
    citations: list[Citation]
    confidence: float
    evidence_count: int
    entities_mentioned: list[str]
    provenance: dict


class AnswerGenerator:
    """
    Generates natural language answers from evidence chains.
    
    Features:
    - Template-based answer generation
    - Citation insertion
    - Confidence calibration
    - Provenance tracking
    """
    
    # Answer templates by question type
    TEMPLATES = {
        "who": [
            "{entity} is a {entity_type} mentioned in {scriptures}. {details}",
            "According to {scriptures}, {entity} is {description}.",
        ],
        "what": [
            "{concept} refers to {description} in Hindu philosophy.",
            "In the context of {context}, {concept} means {description}.",
        ],
        "where": [
            "{place} is located in {description}.",
            "According to {scriptures}, {place} is {description}.",
        ],
        "when": [
            "{event} occurred during {period}.",
            "The {event} is described in {scriptures} as happening {description}.",
        ],
        "why": [
            "{reason} because {explanation}.",
            "According to {scriptures}, {reason} due to {explanation}.",
        ],
        "how": [
            "{method} involves {description}.",
            "{process} is accomplished through {description}.",
        ],
        "default": [
            "{evidence_summary}",
            "Based on {scriptures}, {synthesis}.",
        ],
    }
    
    def __init__(self):
        self._entity_cache = {}
    
    def generate(
        self,
        question: str,
        evidence: list[dict],
        entities: list[dict],
        context: Optional[dict] = None,
    ) -> Answer:
        """
        Generate a natural language answer from evidence.
        
        Args:
            question: The original question
            evidence: List of evidence items from retrieval
            entities: List of relevant entities
            context: Optional additional context
            
        Returns:
            Answer with natural language text and citations
        """
        # Determine question type
        question_type = self._classify_question(question)
        
        # Extract key information
        scriptures = self._extract_scriptures(evidence)
        entity_names = [e.get("name", "") for e in entities]
        entity_types = [e.get("type", "") for e in entities]
        
        # Build answer components
        details = self._build_details(evidence, entities)
        citations = self._build_citations(evidence)
        
        # Select and fill template
        templates = self.TEMPLATES.get(question_type, self.TEMPLATES["default"])
        template = templates[0]
        
        # Fill template with available data
        fill_data = {
            "entity": entity_names[0] if entity_names else "this entity",
            "entity_type": entity_types[0] if entity_types else "concept",
            "scriptures": ", ".join(scriptures[:3]) if scriptures else "various scriptures",
            "details": details,
            "concept": entity_names[0] if entity_names else "this concept",
            "description": details,
            "context": scriptures[0] if scriptures else "Hindu philosophy",
            "place": entity_names[0] if entity_names else "this place",
            "event": entity_names[0] if entity_names else "this event",
            "period": "ancient times",
            "reason": entity_names[0] if entity_names else "this reason",
            "explanation": details,
            "method": entity_names[0] if entity_names else "this method",
            "process": entity_names[0] if entity_names else "this process",
            "evidence_summary": details,
            "synthesis": details,
        }
        
        answer_text = template.format(**fill_data)
        
        # Calculate confidence
        confidence = self._calculate_confidence(evidence, entities)
        
        # Build provenance
        provenance = {
            "generator": "AnswerGenerator v1.0",
            "question_type": question_type,
            "scriptures_cited": scriptures,
            "entities_used": entity_names,
            "evidence_count": len(evidence),
        }
        
        return Answer(
            question=question,
            answer_text=answer_text,
            citations=citations,
            confidence=confidence,
            evidence_count=len(evidence),
            entities_mentioned=entity_names,
            provenance=provenance,
        )
    
    def _classify_question(self, question: str) -> str:
        """Classify question type based on first word."""
        lower = question.lower().strip()
        for qtype in ["who", "what", "where", "when", "why", "how"]:
            if lower.startswith(qtype):
                return qtype
        return "default"
    
    def _extract_scriptures(self, evidence: list[dict]) -> list[str]:
        """Extract unique scripture names from evidence."""
        scriptures = set()
        for e in evidence:
            if "scripture" in e:
                scriptures.add(e["scripture"])
            if "source" in e:
                scriptures.add(e["source"])
        return sorted(scriptures)
    
    def _build_details(self, evidence: list[dict], entities: list[dict]) -> str:
        """Build detailed description from evidence."""
        parts = []
        
        # Add entity information
        for entity in entities[:3]:
            name = entity.get("name", "")
            etype = entity.get("type", "")
            if name:
                parts.append(f"{name} is a {etype}" if etype else name)
        
        # Add evidence details
        for e in evidence[:5]:
            text = e.get("text", e.get("snippet", ""))
            if text and len(text) > 10:
                parts.append(text[:200])
        
        return ". ".join(parts) if parts else "Information available in the knowledge base."
    
    def _build_citations(self, evidence: list[dict]) -> list[Citation]:
        """Build citation list from evidence."""
        citations = []
        for e in evidence[:5]:
            citations.append(Citation(
                scripture=e.get("scripture", e.get("source", "Unknown")),
                chapter=e.get("chapter", ""),
                verse=e.get("verse", ""),
                text_snippet=e.get("text", e.get("snippet", ""))[:100],
                confidence=e.get("confidence", 0.5),
            ))
        return citations
    
    def _calculate_confidence(
        self,
        evidence: list[dict],
        entities: list[dict],
    ) -> float:
        """Calculate answer confidence based on evidence quality."""
        if not evidence:
            return 0.0
        
        # Base confidence from evidence count
        evidence_confidence = min(len(evidence) / 10.0, 0.5)
        
        # Entity coverage bonus
        entity_coverage = min(len(entities) / 3.0, 0.3)
        
        # Source diversity bonus
        sources = set()
        for e in evidence:
            sources.add(e.get("scripture", e.get("source", "")))
        source_diversity = min(len(sources) / 3.0, 0.2)
        
        return min(evidence_confidence + entity_coverage + source_diversity, 1.0)
