"""
Golden Evaluation Dataset Generator.

Creates representative questions from the corpus.
Each question includes:
  - Question text
  - Expected answer (from source)
  - Supporting document(s)
  - Supporting page(s)
  - Topic/subject
  - Difficulty
  - Language
  - Confidence
"""
from __future__ import annotations

import csv
import json
import logging
import re
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class EvalQuestion:
    question_id: str = ""
    question: str = ""
    expected_answer: str = ""
    supporting_documents: list = field(default_factory=list)
    supporting_pages: list = field(default_factory=list)
    topic: str = ""
    subject: str = ""
    difficulty: str = "medium"  # easy, medium, hard
    language: str = "english"
    confidence: float = 0.8
    source_file: str = ""
    source_page: int = 0
    generation_method: str = ""


def generate_eval_questions(
    text_dir: Path,
    manifest_path: Optional[Path] = None,
    max_questions: int = 1000,
) -> list[EvalQuestion]:
    """
    Generate evaluation questions from the corpus.
    
    Strategy:
    1. For each text file, extract key facts as questions
    2. Use sentence-level extraction for factual questions
    3. Use term-level extraction for definition questions
    """
    questions = []
    qid_counter = 0
    
    text_files = sorted(text_dir.rglob("*.txt"))
    logger.info(f"Generating eval questions from {len(text_files)} text files")
    
    for i, fp in enumerate(text_files):
        if len(questions) >= max_questions:
            break
        
        try:
            text = fp.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        
        if len(text) < 200:
            continue
        
        # Extract subject from path
        parts = fp.relative_to(text_dir).parts
        subject = parts[0] if len(parts) > 1 else "general"
        
        # Strategy 1: Sentence-level factual questions
        sentences = re.split(r"(?<=[.!?।])\s+", text)
        for sent in sentences:
            if len(questions) >= max_questions:
                break
            sent = sent.strip()
            if len(sent) < 30 or len(sent) > 500:
                continue
            
            # Check if it's a factual statement
            if _is_factual_statement(sent):
                qid_counter += 1
                question = _statement_to_question(sent)
                if question:
                    lang = "hindi" if any(0x0900 <= ord(c) <= 0x097F for c in sent) else "english"
                    questions.append(EvalQuestion(
                        question_id=f"GOLD-{qid_counter:04d}",
                        question=question,
                        expected_answer=sent,
                        supporting_documents=[fp.stem],
                        topic=subject,
                        subject=subject,
                        difficulty=_estimate_difficulty(sent),
                        language=lang,
                        source_file=str(fp),
                        generation_method="sentence_extraction",
                    ))
        
        # Strategy 2: Definition questions from terms
        term_pattern = re.compile(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:is|are|means|refers to|denotes)\s+(.+?)[.!]")
        for match in term_pattern.finditer(text):
            if len(questions) >= max_questions:
                break
            term = match.group(1).strip()
            definition = match.group(2).strip()
            if len(term) > 3 and len(definition) > 10:
                qid_counter += 1
                questions.append(EvalQuestion(
                    question_id=f"GOLD-{qid_counter:04d}",
                    question=f"What is {term}?",
                    expected_answer=f"{term} is {definition}.",
                    supporting_documents=[fp.stem],
                    topic=subject,
                    subject=subject,
                    difficulty="easy",
                    language="english",
                    source_file=str(fp),
                    generation_method="definition_extraction",
                ))
    
    logger.info(f"Generated {len(questions)} evaluation questions")
    return questions


def _is_factual_statement(sent: str) -> bool:
    """Check if a sentence is a factual statement suitable for a question."""
    # Skip very short or very long
    if len(sent.split()) < 5:
        return False
    
    # Good indicators of factual content
    indicators = [
        "was written", "is known", "was composed", "consists of",
        "contains", "describes", "teaches", "explains",
        "belongs to", "was born", "lived in", "authored",
        "translates to", "means", "refers to",
    ]
    sent_lower = sent.lower()
    return any(ind in sent_lower for ind in indicators)


def _statement_to_question(sent: str) -> Optional[str]:
    """Convert a factual statement into a question."""
    sent_lower = sent.lower()
    
    # "X was written by Y" → "Who wrote X?"
    match = re.match(r"(.+?)\s+was\s+written\s+by\s+(.+?)[.!]", sent)
    if match:
        return f"Who wrote {match.group(1).strip()}?"
    
    # "X was composed by Y" → "Who composed X?"
    match = re.match(r"(.+?)\s+was\s+composed\s+by\s+(.+?)[.!]", sent)
    if match:
        return f"Who composed {match.group(1).strip()}?"
    
    # "X consists of Y" → "What does X consist of?"
    match = re.match(r"(.+?)\s+consists\s+of\s+(.+?)[.!]", sent)
    if match:
        return f"What does {match.group(1).strip()} consist of?"
    
    # "X describes Y" → "What does X describe?"
    match = re.match(r"(.+?)\s+describes\s+(.+?)[.!]", sent)
    if match:
        return f"What does {match.group(1).strip()} describe?"
    
    # Generic: "X [verb] Y" → "What [verb] X?"
    match = re.match(r"(.+?)\s+(is known|is called|is considered|is called|is a)\s+(.+?)[.!]", sent)
    if match:
        return f"What is {match.group(1).strip()}?"
    
    return None


def _estimate_difficulty(sent: str) -> str:
    """Estimate question difficulty."""
    words = len(sent.split())
    if words < 15:
        return "easy"
    elif words < 30:
        return "medium"
    else:
        return "hard"


def save_eval_dataset(questions: list[EvalQuestion], output_dir: Path):
    """Save the evaluation dataset."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # CSV
    if questions:
        with open(output_dir / "golden_eval_dataset.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(asdict(questions[0]).keys()))
            writer.writeheader()
            for q in questions:
                row = asdict(q)
                row["supporting_documents"] = "|".join(row["supporting_documents"])
                row["supporting_pages"] = "|".join(str(p) for p in row["supporting_pages"])
                writer.writerow(row)
    
    # JSON
    with open(output_dir / "golden_eval_dataset.json", "w", encoding="utf-8") as f:
        json.dump([asdict(q) for q in questions], f, indent=2, ensure_ascii=False)
    
    # Summary
    summary = {
        "total_questions": len(questions),
        "by_difficulty": {},
        "by_language": {},
        "by_subject": {},
        "by_method": {},
    }
    for q in questions:
        summary["by_difficulty"][q.difficulty] = summary["by_difficulty"].get(q.difficulty, 0) + 1
        summary["by_language"][q.language] = summary["by_language"].get(q.language, 0) + 1
        summary["by_subject"][q.subject] = summary["by_subject"].get(q.subject, 0) + 1
        summary["by_method"][q.generation_method] = summary["by_method"].get(q.generation_method, 0) + 1
    
    with open(output_dir / "eval_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Eval dataset: {len(questions)} questions saved")
