# Semantic Chunking Skill

## Purpose
Create semantically coherent knowledge chunks from verified documents.

## Core Module
`core/chunking/engine.py`

## Rules
- NEVER use fixed token windows
- Follow document hierarchy
- Preserve semantic boundaries
- Preserve verse structure
- Preserve commentary separation
- Never split logical knowledge units

## Chunk Types
Book, Volume, Section, Chapter, Subchapter, Verse, Sloka,
Paragraph, Commentary, Footnote, Appendix, Glossary, Concept,
Definition, Biography, Timeline, Relationship, Knowledge Unit
