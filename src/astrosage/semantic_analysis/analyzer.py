"""
Semantic Corpus Analysis.

Extracts named entities, key terms, and relationships from the corpus.
Produces graph-ready data for future Knowledge Graph construction.

Uses rule-based extraction (no ML dependencies) for:
  - Named entities (people, places, scriptures)
  - Key concepts (philosophical schools, practices)
  - Frequently occurring terms
  - Cross-references between documents
"""
from __future__ import annotations

import json
import logging
import re
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── Entity Patterns ──

KNOWN_SCRIPTURES = [
    "Rigveda", "Yajurveda", "Samaveda", "Atharvaveda",
    "Bhagavad Gita", "Bhagavata Purana", "Vishnu Purana", "Shiva Purana",
    "Brahma Purana", "Markandeya Purana", "Garuda Purana", "Agni Purana",
    "Padma Purana", "Skanda Purana", "Matsya Purana", "Kurma Purana",
    "Linga Purana", "Vayu Purana", "Brahmanda Purana",
    "Upanishads", "Brahma Sutras", "Yoga Sutras",
    "Manusmriti", "Yajnavalkya Smriti",
    "Arthashastra", "Kamasutra",
    "Ramayana", "Mahabharata", "Harivamsha",
    "Ashtadhyayi", "Mahabhashya",
    "Charaka Samhita", "Sushruta Samhita", "Ashtanga Hridaya",
    "Bhakti Sutras", "Vivekachudamani",
    "Yoga Vashishtha", "Shiva Sutras",
    "Vimanika Shastra", "Surya Siddhanta",
    "Brihat Parashara Hora Shastra",
    "Tattwa Bodha", "Atma Bodha",
]

KNOWN_PEOPLE = [
    "Vyasa", "Valmiki", "Kalidasa", "Panini", "Patanjali",
    "Aryabhata", "Brahmagupta", "Bhaskara",
    "Shankaracharya", "Ramanuja", "Madhvacharya",
    "Vivekananda", "Ramakrishna", "Dayananda",
    "Chanakya", "Vidura", "Bhishma",
    "Rama", "Krishna", "Hanuman", "Shiva", "Vishnu", "Brahma",
    "Ganesha", "Durga", "Lakshmi", "Saraswati", "Parvati",
    "Kabir", "Tulsidas", "Surdas", "Mirabai",
    "Tukaram", "Eknath", "Namdev",
    "Swami Prabhupada", "Ramana Maharshi",
    "Bhrigu", "Narada", "Parashara",
]

KNOWN_CONCEPTS = [
    "Dharma", "Karma", "Moksha", "Samsara", "Brahman", "Atman",
    "Yoga", "Bhakti", "Jnana", "Karma Yoga", "Raja Yoga", "Hatha Yoga",
    "Tantra", "Mantra", "Yantra", "Mudra",
    "Ayurveda", "Jyotish", "Vastu", "Sthapatya",
    "Vedanta", "Samkhya", "Nyaya", "Vaisheshika", "Mimamsa",
    "Advaita", "Vishishtadvaita", "Dvaita",
    "Chakra", "Kundalini", "Prana", "Nadi",
    "Manas", "Buddhi", "Ahamkara", "Chitta",
    "Sattva", "Rajas", "Tamas",
    "Sanskrit", "Devanagari", "Vedic",
    "Puja", "Yajna", "Homa", "Dhyana",
    "Sadhana", "Tapas", "Brahmacharya",
]

# Sanskrit/Devanagari patterns
DEVANAGARI_NAME_PATTERN = re.compile(
    r"[\u0900-\u097F]{2,}(?:\s+[\u0900-\u097F]{2,})*"
)


@dataclass
class Entity:
    name: str
    entity_type: str  # person, scripture, concept, place, organization
    frequency: int = 0
    documents: list = field(default_factory=list)


@dataclass
class TermFrequency:
    term: str
    count: int
    documents: list = field(default_factory=list)


@dataclass
class SemanticProfile:
    """Complete semantic profile of the corpus."""
    # Entities
    scriptures: list = field(default_factory=list)
    people: list = field(default_factory=list)
    concepts: list = field(default_factory=list)
    places: list = field(default_factory=list)
    
    # Terms
    top_terms: list = field(default_factory=list)
    domain_terms: list = field(default_factory=list)
    
    # Cross-references
    cross_references: list = field(default_factory=list)
    
    # Stats
    total_entities_found: int = 0
    unique_terms: int = 0
    analysis_time_seconds: float = 0.0


def analyze_corpus_semantics(
    text_dir: Path,
    sample_size: int = 0,
) -> SemanticProfile:
    """
    Perform semantic analysis on extracted text files.
    Uses rule-based pattern matching (no ML dependencies).
    """
    start = time.time()
    profile = SemanticProfile()
    
    # Discover text files
    text_files = sorted(text_dir.rglob("*.txt"))
    if sample_size > 0:
        text_files = text_files[:sample_size]
    
    logger.info(f"Semantic analysis: {len(text_files)} text files")
    
    # Entity counters
    scripture_counts = Counter()
    people_counts = Counter()
    concept_counts = Counter()
    scripture_docs = defaultdict(set)
    people_docs = defaultdict(set)
    concept_docs = defaultdict(set)
    
    # Term frequency
    all_terms = Counter()
    term_docs = defaultdict(set)
    
    for i, fp in enumerate(text_files):
        if (i + 1) % 50 == 0:
            logger.info(f"  Analyzing: {i+1}/{len(text_files)}")
        
        try:
            text = fp.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        
        doc_name = fp.stem
        text_lower = text.lower()
        
        # Match scriptures
        for scripture in KNOWN_SCRIPTURES:
            if scripture.lower() in text_lower:
                scripture_counts[scripture] += 1
                scripture_docs[scripture].add(doc_name)
        
        # Match people
        for person in KNOWN_PEOPLE:
            if person.lower() in text_lower:
                people_counts[person] += 1
                people_docs[person].add(doc_name)
        
        # Match concepts
        for concept in KNOWN_CONCEPTS:
            if concept.lower() in text_lower:
                concept_counts[concept] += 1
                concept_docs[concept].add(doc_name)
        
        # Extract frequent terms (3+ character words, appear 3+ times)
        words = re.findall(r"\b[a-zA-Z]{3,}\b", text_lower)
        word_counts = Counter(words)
        for word, count in word_counts.items():
            if count >= 3 and word not in {"the", "and", "for", "that", "with", "this",
                                             "from", "are", "was", "were", "been", "have",
                                             "has", "had", "not", "but", "all", "can",
                                             "her", "his", "its", "our", "out", "who",
                                             "how", "may", "yet", "each", "make", "like",
                                             "long", "look", "many", "most", "over", "such",
                                             "take", "than", "them", "then", "what", "when",
                                             "will", "your", "also", "been", "into", "than",
                                             "some", "very", "just", "only"}:
                all_terms[word] += count
                term_docs[word].add(doc_name)
        
        # Extract Devanagari terms (3+ characters)
        deva_words = re.findall(r"[\u0900-\u097F]{3,}", text)
        deva_counts = Counter(deva_words)
        for word, count in deva_counts.items():
            if count >= 3:
                all_terms[word] += count
                term_docs[word].add(doc_name)
    
    # Build profile
    profile.scriptures = [
        Entity(name=s, entity_type="scripture", frequency=c, documents=sorted(scripture_docs[s]))
        for s, c in scripture_counts.most_common(50)
    ]
    profile.people = [
        Entity(name=p, entity_type="person", frequency=c, documents=sorted(people_docs[p]))
        for p, c in people_counts.most_common(50)
    ]
    profile.concepts = [
        Entity(name=c, entity_type="concept", frequency=freq, documents=sorted(concept_docs[c]))
        for c, freq in concept_counts.most_common(50)
    ]
    profile.top_terms = [
        TermFrequency(term=t, count=c, documents=sorted(term_docs[t])[:5])
        for t, c in all_terms.most_common(200)
    ]
    
    profile.total_entities_found = (
        len(profile.scriptures) + len(profile.people) + len(profile.concepts)
    )
    profile.unique_terms = len(all_terms)
    profile.analysis_time_seconds = round(time.time() - start, 1)
    
    logger.info(
        f"Semantic analysis: {profile.total_entities_found} entities, "
        f"{profile.unique_terms} unique terms in {profile.analysis_time_seconds}s"
    )
    
    return profile


def save_semantic_profile(profile: SemanticProfile, output_dir: Path):
    """Save semantic profile as JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    data = asdict(profile)
    with open(output_dir / "semantic_analysis.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Also save graph-ready entity list
    entities = []
    for e in profile.scriptures + profile.people + profile.concepts:
        entities.append({
            "id": f"entity_{e.name.lower().replace(' ', '_')}",
            "name": e.name,
            "type": e.entity_type,
            "frequency": e.frequency,
            "documents": e.documents,
        })
    
    with open(output_dir / "graph_entities.json", "w", encoding="utf-8") as f:
        json.dump(entities, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Semantic profile saved to {output_dir}")
