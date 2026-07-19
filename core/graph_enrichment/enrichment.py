"""
Knowledge Graph Enrichment Engine for AstroSage.

Analyzes MENTIONED_IN edges and proposes more specific relationship types
based on context clues, entity types, and corpus patterns.
"""
from __future__ import annotations
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from collections import defaultdict, Counter


@dataclass
class EnrichmentProposal:
    """Proposed enrichment for a single edge."""
    edge_guid: str
    current_type: str
    proposed_type: str
    confidence: float
    evidence: str
    source_entity: str
    target_entity: str


@dataclass
class EnrichmentReport:
    """Report of all enrichment proposals."""
    total_edges_analyzed: int = 0
    mentioned_in_edges: int = 0
    proposed_enrichments: list[EnrichmentProposal] = field(default_factory=list)
    type_distribution: dict[str, int] = field(default_factory=dict)
    confidence_stats: dict[str, float] = field(default_factory=dict)


class GraphEnrichmentEngine:
    """
    Analyzes the knowledge graph and proposes relationship enrichments.
    
    Heuristics:
    - Person + Scripture → TEACHES, COMPILER_OF, AUTHOR_OF, MENTIONS
    - Concept + Scripture → DEFINED_IN, TAUGHT_IN, EXPLORED_IN
    - Deity + Scripture → INVOKED_IN, WORSHIPPED_IN, DESCRIBED_IN
    - Person + Person → FATHER_OF, SON_OF, TEACHER_OF, STUDENT_OF, SPOUSE_OF
    - Deity + Deity → CONSORT_OF, ASPECT_OF, INCARNATION_OF
    - Deity + Weapon → WIELDS, POSSESSES
    - Place + Scripture → LOCATED_IN, DESCRIBED_IN, REFERENCED_IN
    """
    
    # Heuristic rules: (source_type, target_type) → [(proposed_type, confidence)]
    ENRICHMENT_RULES = {
        ("Person", "Scripture"): [
            ("TEACHES", 0.7),
            ("COMPILER_OF", 0.6),
            ("AUTHOR_OF", 0.5),
            ("MENTIONS", 0.4),
        ],
        ("Concept", "Scripture"): [
            ("DEFINED_IN", 0.8),
            ("TAUGHT_IN", 0.7),
            ("EXPLORED_IN", 0.6),
        ],
        ("Deity", "Scripture"): [
            ("INVOKED_IN", 0.8),
            ("WORSHIPPED_IN", 0.7),
            ("DESCRIBED_IN", 0.6),
        ],
        ("Person", "Person"): [
            ("FATHER_OF", 0.7),
            ("SON_OF", 0.7),
            ("TEACHER_OF", 0.6),
            ("STUDENT_OF", 0.6),
            ("SPOUSE_OF", 0.5),
        ],
        ("Deity", "Deity"): [
            ("CONSORT_OF", 0.7),
            ("ASPECT_OF", 0.6),
            ("INCARNATION_OF", 0.5),
        ],
        ("Deity", "Weapon"): [
            ("WIELDS", 0.8),
            ("POSSESSES", 0.7),
        ],
        ("Place", "Scripture"): [
            ("LOCATED_IN", 0.7),
            ("DESCRIBED_IN", 0.6),
            ("REFERENCED_IN", 0.5),
        ],
        ("Animal", "Deity"): [
            ("VEHICLE_OF", 0.8),
            ("ASSOCIATED_WITH", 0.6),
        ],
        ("Weapon", "Deity"): [
            ("WIELDED_BY", 0.8),
            ("POSSESSED_BY", 0.7),
        ],
        ("Dynasty", "Person"): [
            ("MEMBER_OF", 0.7),
            ("FOUNDER_OF", 0.6),
        ],
        ("Concept", "Concept"): [
            ("SUBCATEGORY_OF", 0.7),
            ("RELATED_TO", 0.5),
            ("CONTRASTS_WITH", 0.4),
        ],
    }
    
    # Entity name patterns for additional heuristics
    NAME_PATTERNS = {
        "son": "SON_OF",
        "father": "FATHER_OF",
        "mother": "MOTHER_OF",
        "teacher": "TEACHER_OF",
        "student": "STUDENT_OF",
        "wife": "SPOUSE_OF",
        "husband": "SPOUSE_OF",
        "brother": "BROTHER_OF",
        "sister": "SISTER_OF",
    }
    
    def __init__(self, graph_path: Optional[str] = None):
        self.graph_path = Path(graph_path or "knowledge/releases/v1.0.0/graph/graph.json")
        self._graph = None
        self._node_index = {}
        self._loaded = False
    
    def load(self):
        """Load the knowledge graph."""
        if self._loaded:
            return self
        
        with open(self.graph_path) as f:
            self._graph = json.load(f)
        
        for node in self._graph.get("nodes", []):
            self._node_index[node["GUID"]] = node
        
        self._loaded = True
        return self
    
    def analyze(self) -> EnrichmentReport:
        """
        Analyze the graph and propose enrichments.
        
        Returns:
            EnrichmentReport with all proposals
        """
        self.load()
        
        report = EnrichmentReport()
        report.total_edges_analyzed = len(self._graph.get("edges", []))
        
        # Count current edge types
        type_counter = Counter()
        for edge in self._graph.get("edges", []):
            type_counter[edge["type"]] += 1
        
        report.type_distribution = dict(type_counter.most_common())
        
        # Find MENTIONED_IN edges and propose enrichments
        mentioned_in_edges = [
            e for e in self._graph.get("edges", [])
            if e["type"] == "MENTIONED_IN"
        ]
        report.mentioned_in_edges = len(mentioned_in_edges)
        
        for edge in mentioned_in_edges:
            proposals = self._propose_enrichments(edge)
            report.proposed_enrichments.extend(proposals)
        
        # Calculate confidence statistics
        if report.proposed_enrichments:
            confidences = [p.confidence for p in report.proposed_enrichments]
            report.confidence_stats = {
                "mean": sum(confidences) / len(confidences),
                "min": min(confidences),
                "max": max(confidences),
                "count": len(confidences),
            }
        
        return report
    
    def _propose_enrichments(self, edge: dict) -> list[EnrichmentProposal]:
        """Propose enrichments for a single MENTIONED_IN edge."""
        proposals = []
        
        src_node = self._node_index.get(edge.get("source_GUID"), {})
        tgt_node = self._node_index.get(edge.get("target_GUID"), {})
        
        src_type = src_node.get("type", "Unknown")
        tgt_type = tgt_node.get("type", "Unknown")
        src_name = src_node.get("name", "")
        tgt_name = tgt_node.get("name", "")
        
        # Check enrichment rules
        rule_key = (src_type, tgt_type)
        if rule_key in self.ENRICHMENT_RULES:
            for proposed_type, confidence in self.ENRICHMENT_RULES[rule_key]:
                proposals.append(EnrichmentProposal(
                    edge_guid=edge.get("GUID", ""),
                    current_type="MENTIONED_IN",
                    proposed_type=proposed_type,
                    confidence=confidence,
                    evidence=f"{src_type} ({src_name}) mentioned in {tgt_type} ({tgt_name})",
                    source_entity=src_name,
                    target_entity=tgt_name,
                ))
        
        # Check name patterns for additional heuristics
        src_name_lower = src_name.lower()
        for pattern, rel_type in self.NAME_PATTERNS.items():
            if pattern in src_name_lower:
                proposals.append(EnrichmentProposal(
                    edge_guid=edge.get("GUID", ""),
                    current_type="MENTIONED_IN",
                    proposed_type=rel_type,
                    confidence=0.6,
                    evidence=f"Entity name '{src_name}' contains pattern '{pattern}'",
                    source_entity=src_name,
                    target_entity=tgt_name,
                ))
        
        # Return top proposal by confidence
        if proposals:
            proposals.sort(key=lambda p: p.confidence, reverse=True)
            return [proposals[0]]
        
        return []
    
    def apply_enrichments(
        self,
        report: EnrichmentReport,
        min_confidence: float = 0.7,
    ) -> dict:
        """
        Apply high-confidence enrichments to the graph.
        
        Args:
            report: EnrichmentReport from analyze()
            min_confidence: Minimum confidence to apply
            
        Returns:
            Statistics of applied enrichments
        """
        self.load()
        
        applied = 0
        skipped = 0
        
        for proposal in report.proposed_enrichments:
            if proposal.confidence < min_confidence:
                skipped += 1
                continue
            
            # Find and update the edge
            for edge in self._graph.get("edges", []):
                if edge.get("GUID") == proposal.edge_guid:
                    edge["type"] = proposal.proposed_type
                    edge["enrichment_confidence"] = proposal.confidence
                    edge["enrichment_evidence"] = proposal.evidence
                    applied += 1
                    break
        
        return {
            "applied": applied,
            "skipped": skipped,
            "total_proposals": len(report.proposed_enrichments),
        }
    
    def save_enriched_graph(self, output_path: str) -> None:
        """Save the enriched graph to a new file."""
        if self._graph is None:
            raise ValueError("Graph not loaded. Call load() first.")
        
        with open(output_path, "w") as f:
            json.dump(self._graph, f, indent=2)
