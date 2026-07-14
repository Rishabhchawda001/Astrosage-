"""Prompt schemas — Supporting CO-STAR, RISEN, RTF, ReAct, Few Shot, etc."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PromptTemplate:
    name: str = ""
    framework: str = ""  # CO-STAR, RISEN, RTF, ReAct, FewShot, Constitutional, XML, Citation, Verification, Recovery, Benchmark
    template: str = ""
    variables: list[str] = field(default_factory=list)
    description: str = ""
    category: str = ""  # recovery, verification, benchmark, citation, etc.


# Default prompt templates
DEFAULT_PROMPTS = [
    PromptTemplate(
        name="citation_verification",
        framework="Constitutional",
        template="Verify the following citation is accurate and supported by the source material:\n\nCitation: {citation}\nSource: {source_text}\n\nIs this citation supported? Answer with evidence.",
        variables=["citation", "source_text"],
        category="verification",
    ),
    PromptTemplate(
        name="recovery_candidate",
        framework="RTF",
        template="Given the original OCR text and evidence from multiple editions, propose a corrected version.\n\nOriginal: {original}\nEvidence: {evidence}\n\nProvide the recovered text with confidence score.",
        variables=["original", "evidence"],
        category="recovery",
    ),
    PromptTemplate(
        name="benchmark_eval",
        framework="ReAct",
        template="Evaluate the following retrieval result against the ground truth.\n\nQuery: {query}\nRetrieved: {retrieved}\nGround Truth: {ground_truth}\n\nProvide precision, recall, and relevance scores.",
        variables=["query", "retrieved", "ground_truth"],
        category="benchmark",
    ),
]
