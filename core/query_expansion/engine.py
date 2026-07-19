"""
Query Expansion Engine for AstroSage.

Provides multi-lingual query expansion for Sanskrit, Hindi, and English terms.
Uses knowledge graph synonyms, transliteration mappings, and corpus-derived expansions.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from collections import defaultdict


@dataclass
class ExpandedQuery:
    """Expanded query with original and expanded terms."""
    original_query: str
    expanded_terms: list[str]
    synonyms: dict[str, list[str]]
    transliterations: dict[str, list[str]]
    semantic_variants: list[str]
    expansion_confidence: float


class QueryExpansionEngine:
    """
    Expands queries using:
    1. Knowledge graph entity synonyms
    2. Sanskrit-Hindi-English transliteration mappings
    3. Corpus-derived term co-occurrence
    4. Scriptural reference expansion
    """
    
    def __init__(self, graph_path: Optional[str] = None):
        self.graph_path = Path(graph_path or "knowledge/releases/v1.0.0/graph/graph.json")
        self._entity_index = {}
        self._synonym_index = defaultdict(list)
        self._transliteration_map = {}
        self._scripture_aliases = {}
        self._loaded = False
        
        # Sanskrit-English common mappings
        self.sanskrit_english = {
            "dharma": ["righteousness", "duty", "law", "justice", "virtue", "morality"],
            "karma": ["action", "deed", "work", "cause and effect", "action-reaction"],
            "moksha": ["liberation", "salvation", "enlightenment", "release", "freedom"],
            "bhakti": ["devotion", "love", "worship", "faith", "dedication"],
            "jnana": ["knowledge", "wisdom", "understanding", "insight", "gnosis"],
            "yoga": ["union", "discipline", "practice", "path", "way"],
            "atman": ["self", "soul", "spirit", "essence", "true self"],
            "brahman": ["absolute", "ultimate reality", "cosmic consciousness", "godhead"],
            "veda": ["knowledge", "sacred text", "revelation", "scripture"],
            "upanishad": ["philosophical text", "knowledge appendix", "teaching"],
            "purana": ["ancient lore", "mythology", "traditional narrative"],
            "smriti": ["remembered tradition", "law book", "manual"],
            "sutra": ["aphorism", "rule", "formula", "maxim"],
            "mantra": ["sacred formula", "chant", "prayer", "incantation"],
            "puja": ["worship", "ritual", "offering", "ceremony"],
            "yajna": ["fire ritual", "sacrifice", "oblation", "fire ceremony"],
            "guru": ["teacher", "master", "guide", "spiritual leader"],
            "ashram": ["hermitage", "monastery", "retreat", "spiritual community"],
            "samsara": ["cycle of birth", "worldly existence", "transmigration"],
            "ahimsa": ["non-violence", "non-harm", "non-injury"],
            "satya": ["truth", "truthfulness", "honesty"],
            "asteya": ["non-stealing", "honesty"],
            "brahmacharya": ["celibacy", "self-control", "chaste conduct"],
            "aparigraha": ["non-possessiveness", "non-attachment"],
            "agni": ["fire", "sacred fire", "fire god"],
            "vayu": ["wind", "air", "wind god"],
            "surya": ["sun", "sun god", "solar deity"],
            "chandra": ["moon", "moon god", "lunar deity"],
            "indra": ["king of gods", "lord of heaven", "thunderbolt wielder"],
            "varuna": ["water god", "cosmic order", "god of ocean"],
            "kubera": ["god of wealth", "treasurer of gods", "lord of riches"],
            "ganesh": ["elephant god", "remover of obstacles", "lord of beginnings"],
            "hanuman": ["monkey god", "wind god's son", "devotee of Rama"],
            "garuda": ["divine eagle", "Vishnu's mount", "king of birds"],
            "nandi": ["sacred bull", "Shiva's mount", "doorkeeper"],
            "shesha": ["cosmic serpent", "Ananta", "Vishnu's couch"],
        }
        
        # Hindi-English mappings
        self.hindi_english = {
            "bhagwan": ["god", "lord", "divine"],
            "paramatma": ["supreme soul", "supreme self", "god"],
            "ishwar": ["god", "lord", "ruler"],
            "prakriti": ["nature", "matter", "feminine principle"],
            "purusha": ["spirit", "consciousness", "masculine principle"],
            "maya": ["illusion", "magic", "cosmic power"],
            "tapas": ["austerity", "penance", "discipline"],
            "sankalp": ["resolve", "determination", "intention"],
            "dhyana": ["meditation", "contemplation", "focus"],
            "pranayama": ["breath control", "breathing exercise", "life force regulation"],
            "asana": ["posture", "seat", "yoga pose"],
        }
        
    def load(self):
        """Load knowledge graph and build indices."""
        if self._loaded:
            return self
            
        if self.graph_path.exists():
            with open(self.graph_path) as f:
                graph = json.load(f)
            
            # Build entity index
            for node in graph.get("nodes", []):
                name = node.get("name", "")
                if name:
                    self._entity_index[name.lower()] = node
                    # Add common aliases
                    self._synonym_index[name.lower()].append(name)
            
            # Build scripture aliases
            for node in graph.get("nodes", []):
                if node.get("type") == "Scripture":
                    sid = node.get("id", "")
                    name = node.get("name", sid)
                    self._scripture_aliases[sid.lower()] = name
                    self._scripture_aliases[name.lower()] = sid
            
            # Build transliteration mappings from edges
            for edge in graph.get("edges", []):
                src_name = ""
                tgt_name = ""
                for node in graph.get("nodes", []):
                    if node["GUID"] == edge.get("source_GUID"):
                        src_name = node.get("name", "")
                    if node["GUID"] == edge.get("target_GUID"):
                        tgt_name = node.get("name", "")
                if src_name and tgt_name and edge.get("type") == "ALIAS_FOR":
                    self._transliteration_map[src_name.lower()] = tgt_name
                    self._transliteration_map[tgt_name.lower()] = src_name
        
        self._loaded = True
        return self
    
    def expand(self, query: str) -> ExpandedQuery:
        """
        Expand a query with synonyms, transliterations, and semantic variants.
        
        Args:
            query: The original search query
            
        Returns:
            ExpandedQuery with all expansion information
        """
        self.load()
        
        words = query.lower().split()
        expanded_terms = list(words)
        synonyms = {}
        transliterations = {}
        semantic_variants = []
        
        for word in words:
            # Check Sanskrit-English mappings
            if word in self.sanskrit_english:
                syns = self.sanskrit_english[word]
                synonyms[word] = syns
                expanded_terms.extend(syns[:3])  # Top 3 synonyms
            
            # Check Hindi-English mappings
            if word in self.hindi_english:
                syns = self.hindi_english[word]
                synonyms[word] = syns
                expanded_terms.extend(syns[:3])
            
            # Check entity index for exact matches
            if word in self._entity_index:
                entity = self._entity_index[word]
                # Add entity type as context
                entity_type = entity.get("type", "")
                if entity_type:
                    expanded_terms.append(f"{word} {entity_type.lower()}")
            
            # Check transliterations
            if word in self._transliteration_map:
                transliterations[word] = self._transliteration_map[word]
                expanded_terms.append(self._transliteration_map[word])
            
            # Check scripture aliases
            if word in self._scripture_aliases:
                alias = self._scripture_aliases[word]
                expanded_terms.append(alias)
        
        # Generate semantic variants
        if "who" in words or "what" in words:
            # Entity-focused query
            entity_words = [w for w in words if w not in {"who", "what", "is", "are", "the", "of", "in", "and"}]
            if entity_words:
                semantic_variants.append(f"{' '.join(entity_words)} deity person concept")
                semantic_variants.append(f"{' '.join(entity_words)} scripture text")
        
        # Calculate expansion confidence
        expansion_count = len(expanded_terms) - len(words)
        confidence = min(0.3 + (expansion_count * 0.1), 1.0)
        
        return ExpandedQuery(
            original_query=query,
            expanded_terms=list(set(expanded_terms)),
            synonyms=synonyms,
            transliterations=transliterations,
            semantic_variants=semantic_variants,
            expansion_confidence=confidence,
        )
    
    def expand_for_search(self, query: str, max_terms: int = 15) -> str:
        """Expand query and return optimized search string."""
        expanded = self.expand(query)
        
        # Prioritize original terms, then synonyms, then variants
        search_terms = expanded.original_query.split()
        search_terms.extend(list(expanded.synonyms.keys())[:5])
        for syns in list(expanded.synonyms.values())[:3]:
            search_terms.extend(syns[:2])
        search_terms.extend(expanded.semantic_variants[:2])
        
        # Deduplicate while preserving order
        seen = set()
        unique_terms = []
        for term in search_terms:
            if term.lower() not in seen:
                seen.add(term.lower())
                unique_terms.append(term)
        
        return " ".join(unique_terms[:max_terms])
