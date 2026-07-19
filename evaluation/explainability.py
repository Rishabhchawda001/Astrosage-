"""Explainability engine — produces human-readable reasoning traces."""
import json
from dataclasses import dataclass, field


@dataclass
class EvidenceChain:
    source_entity: str
    target_entity: str
    relationship: str
    confidence: str
    scripture: str
    canonical_ref: str = ""


@dataclass
class ReasoningTrace:
    question: str
    entities_identified: list[str] = field(default_factory=list)
    evidence_chains: list[EvidenceChain] = field(default_factory=list)
    confidence: str = "low"
    confidence_score: float = 0.0
    summary: str = ""
    supporting_scriptures: list[str] = field(default_factory=list)
    key_relationships: list[str] = field(default_factory=list)
    reasoning_steps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "question": self.question,
            "entities_identified": self.entities_identified,
            "evidence_chains": [
                {
                    "source": ec.source_entity,
                    "target": ec.target_entity,
                    "relationship": ec.relationship,
                    "confidence": ec.confidence,
                    "scripture": ec.scripture,
                    "canonical_ref": ec.canonical_ref,
                }
                for ec in self.evidence_chains
            ],
            "confidence": self.confidence,
            "confidence_score": self.confidence_score,
            "summary": self.summary,
            "supporting_scriptures": self.supporting_scriptures,
            "key_relationships": self.key_relationships,
            "reasoning_steps": self.reasoning_steps,
        }

    def to_narrative(self) -> str:
        """Produce a human-readable explanation of the reasoning."""
        lines = [f"Question: {self.question}", ""]

        if self.entities_identified:
            lines.append(
                f"Entities identified: {', '.join(self.entities_identified)}"
            )
            lines.append("")

        if self.reasoning_steps:
            lines.append("Reasoning chain:")
            for i, step in enumerate(self.reasoning_steps, 1):
                lines.append(f"  {i}. {step}")
            lines.append("")

        if self.evidence_chains:
            lines.append("Evidence sources:")
            for ec in self.evidence_chains:
                lines.append(
                    f"  - {ec.source_entity} --[{ec.relationship}]--> "
                    f"{ec.target_entity} (confidence: {ec.confidence}, "
                    f"source: {ec.scripture})"
                )
            lines.append("")

        lines.append(f"Overall confidence: {self.confidence}")
        if self.supporting_scriptures:
            lines.append(
                f"Supporting scriptures: {', '.join(self.supporting_scriptures)}"
            )

        return "\n".join(lines)


class ExplainabilityEngine:
    """Builds human-readable reasoning traces from answer results."""

    def build_trace(self, question: str, answer_result: dict) -> ReasoningTrace:
        trace = ReasoningTrace(question=question)

        # Extract entities
        entities = answer_result.get("entities", [])
        trace.entities_identified = [
            e.get("name", str(e)) if isinstance(e, dict) else str(e)
            for e in entities
        ]

        # Extract evidence chains
        evidence = answer_result.get("evidence", {})
        sources = evidence.get("sources", [])
        for src in sources:
            if isinstance(src, dict):
                trace.evidence_chains.append(
                    EvidenceChain(
                        source_entity=src.get("source_entity", "unknown"),
                        target_entity=src.get("target_entity", "unknown"),
                        relationship=src.get("relationship", "MENTIONED_IN"),
                        confidence=src.get("confidence", "medium"),
                        scripture=src.get("scripture", "unknown"),
                        canonical_ref=src.get("canonical_ref", ""),
                    )
                )

        # Confidence
        trace.confidence = answer_result.get("confidence", "low")
        trace.confidence_score = _confidence_to_num(trace.confidence)

        # Build reasoning steps
        trace.reasoning_steps = self._build_steps(answer_result, trace)

        # Supporting scriptures
        trace.supporting_scriptures = list(
            set(
                ec.scripture
                for ec in trace.evidence_chains
                if ec.scripture != "unknown"
            )
        )

        # Key relationships
        trace.key_relationships = list(
            set(ec.relationship for ec in trace.evidence_chains)
        )

        # Build summary
        trace.summary = self._build_summary(trace)

        return trace

    def _build_steps(
        self, answer_result: dict, trace: ReasoningTrace
    ) -> list[str]:
        steps = []
        if trace.entities_identified:
            steps.append(
                f"Identified {len(trace.entities_identified)} relevant entities: "
                f"{', '.join(trace.entities_identified[:5])}"
            )

        evidence = answer_result.get("evidence", {})
        sources = evidence.get("sources", [])
        if sources:
            steps.append(f"Found {len(sources)} evidence sources across scriptures")

        provenance = evidence.get("provenance_traced", False)
        if provenance:
            steps.append("All evidence traces to canonical sources with provenance")

        scripture_count = len(trace.supporting_scriptures)
        if scripture_count > 1:
            steps.append(
                f"Cross-referenced across {scripture_count} scriptures for consistency"
            )

        steps.append(
            f"Confidence assessment: {trace.confidence} "
            f"({trace.confidence_score:.0%})"
        )
        return steps

    def _build_summary(self, trace: ReasoningTrace) -> str:
        entity_str = ", ".join(trace.entities_identified[:3])
        scripture_str = ", ".join(trace.supporting_scriptures[:3])
        rel_count = len(trace.evidence_chains)

        return (
            f"Based on {rel_count} evidence relationships involving "
            f"{entity_str}, sourced from {scripture_str}. "
            f"Confidence: {trace.confidence}."
        )


def _confidence_to_num(confidence: str) -> float:
    return {"low": 0.25, "medium": 0.55, "high": 0.85}.get(confidence, 0.5)
