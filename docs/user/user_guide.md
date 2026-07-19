# AstroSage User Guide

**Version**: 1.0.0
**Last Updated**: 2026-07-19

---

## 1. What Is AstroSage?

AstroSage is an Evidence-First Knowledge Operating System for Hindu scriptures.
It can search, retrieve, and reason over a knowledge graph containing 391 entities,
54 scriptures, and 5,044 relationships to produce provenance-traced answers.

Every answer includes evidence from the original canonical sources.

---

## 2. Supported Capabilities

### Search & Retrieval

Find information across 120,548 semantic chunks using hybrid search:

```python
# Example: Search for information about Vishnu
# The system returns the most relevant chunks ranked by combined score
```

### Entity Reasoning

Get detailed information about any entity in the knowledge graph:

- **Type** (Deity, Person, Place, Concept, etc.)
- **Mentions** across scriptures
- **Relationships** to other entities
- **Source scriptures** where the entity appears
- **Evidence chains** supporting each claim

### Question Answering

Ask questions about Hindu scriptures and receive answers with:

- **Confidence score** (high/medium/low)
- **Evidence sources** (average 11+ sources per answer)
- **Scripture references**
- **Canonical unit citations**

### Cross-Scripture Linking

Discover connections across different scriptures:

- Same person appearing in multiple texts
- Same event described in different traditions
- Same concept defined across schools

---

## 3. Example Searches

### "Who is Vishnu and what is his role?"

**Response includes**:
- Entity: Vishnu (Deity)
- Mentions: 610 across 32 scriptures
- Key relationships: INCARNATION_OF, WIELDED_BY, ABODE_OF, VEHICLE_OF
- Sources: Vedārthasaṃgraha, Bhagavadgītā, Brahmasūtra, Agnipurāṇa, and more

### "What is the relationship between Krishna and Arjuna?"

**Response includes**:
- Entity: Krishna (Deity) — 645 mentions, 31 scriptures
- Entity: Arjuna (Person) — 407 mentions, 18 scriptures
- Relationship: Teacher-student on Kurukshetra battlefield
- Evidence: Bhāgavatapurāṇa, Bhagavadgītābhāṣya, and commentaries

### "What are the main teachings of the Bhagavad Gita?"

**Response includes**:
- Text: Bhagavad Gita
- Key teachings: Dharma, Karma Yoga, Jnana Yoga, Bhakti Yoga
- Evidence from: Bhagavadgītā with Śaṃkara's commentary
- Verse references: Multiple canonical units

---

## 4. Evidence Tracing

Every claim includes:

```
Source: Bhagavadgītā with Śaṃkara's commentary (Adhyāyas 1-17)
Chapter: 2
Verse: 13
Canonical Unit: BG 2.13
Confidence: 0.95
Evidence: "dehīno 'smin yathā dehe..." (the soul transmigrates through bodies)
```

---

## 5. Confidence Levels

| Level | Description | When Used |
|-------|-------------|-----------|
| HIGH | Multiple corroborating sources, strong evidence | Well-established facts with clear textual support |
| MEDIUM | Some evidence, partial corroboration | Less commonly referenced or partially attested claims |

---

## 6. Known Limitations

- **4 scriptures** have no coverage (Kena, Mundaka, Mahanarayana, Parashara)
- **94.4% of relationships** are generic "mentioned in" type
- **No natural language generation** — answers are structured evidence
- **Rule-based reasoning only** — no neural reasoning augmentation
- **Limited cross-lingual support** — Devanagari texts may have reduced quality

---

## 7. Frequently Asked Questions

### Q: Is this a chatbot?

No. AstroSage is a knowledge operating system. It retrieves and synthesizes
evidence from canonical sources, not conversational AI.

### Q: Can I add new scriptures?

Yes, through the migration framework. See `docs/developer/developer_guide.md`.

### Q: Is the knowledge complete?

The knowledge layer covers 54 scriptures with 391 entities. Four scriptures
remain unrecoverable. The system is designed for continuous improvement through
versioned migrations.

### Q: How do I verify an answer?

Every answer includes scripture references, chapter numbers, verse ranges,
canonical unit IDs, and entity GUIDs. You can trace any claim back to the
original source.

### Q: What languages does it support?

The primary corpus is in IAST (International Alphabet of Sanskrit Transliteration).
Some Devanagari texts are included. Cross-lingual search is planned for future versions.
