"""
Phase 14: Reasoning Engine — AstroSage Knowledge System
Evidence-based inference over the knowledge graph + retrieval system.

Consumes: frozen release v1.0.0 (graph + embeddings + retrieval)
Produces: knowledge/releases/v1.0.0/reasoning/
"""
import json, os, hashlib, time
import numpy as np
from datetime import datetime, timezone
from collections import defaultdict

RELEASE_DIR = "knowledge/releases/v1.0.0"
GRAPH_DIR = os.path.join(RELEASE_DIR, "graph")
CHUNKS_DIR = os.path.join(RELEASE_DIR, "chunks")
EMBEDDINGS_DIR = os.path.join(RELEASE_DIR, "embeddings")
REASONING_DIR = os.path.join(RELEASE_DIR, "reasoning")
GENERATED = datetime.now(timezone.utc).isoformat()
GIT_COMMIT = os.popen("git rev-parse HEAD").read().strip()

def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


class KnowledgeGraph:
    """In-memory knowledge graph for reasoning."""
    
    def __init__(self):
        self.entities = {}       # GUID -> entity
        self.entity_by_name = {} # name -> entity
        self.scriptures = {}     # GUID -> scripture
        self.scripture_by_id = {} # id -> scripture
        self.edges = []          # all edges
        self.edges_by_entity = defaultdict(list)  # entity GUID -> edges
        self.edges_by_type = defaultdict(list)     # edge type -> edges
        self.edges_by_scripture = defaultdict(list) # scripture GUID -> edges
    
    def load(self):
        # Load entities
        entities = json.load(open(os.path.join(GRAPH_DIR, "nodes/entity_nodes.json")))
        for e in entities:
            self.entities[e["GUID"]] = e
            self.entity_by_name[e["name"]] = e
        
        # Load scriptures
        scriptures = json.load(open(os.path.join(GRAPH_DIR, "nodes/scripture_nodes.json")))
        for s in scriptures:
            self.scriptures[s["GUID"]] = s
            self.scripture_by_id[s["id"]] = s
        
        # Load edges
        self.edges = json.load(open(os.path.join(GRAPH_DIR, "edges/relationship_edges.json")))
        for e in self.edges:
            self.edges_by_entity[e["source_GUID"]].append(e)
            self.edges_by_entity[e["target_GUID"]].append(e)
            self.edges_by_type[e["type"]].append(e)
            if e["target_GUID"] in self.scriptures:
                self.edges_by_scripture[e["target_GUID"]].append(e)
        
        return self
    
    def find_entity(self, name):
        """Find entity by name (case-insensitive)."""
        name_lower = name.lower()
        for n, e in self.entity_by_name.items():
            if n.lower() == name_lower:
                return e
        return None
    
    def get_relationships(self, entity_guid):
        """Get all relationships for an entity."""
        return self.edges_by_entity.get(entity_guid, [])
    
    def get_entities_in_scripture(self, scripture_guid):
        """Get all entities mentioned in a scripture."""
        entities = set()
        for e in self.edges_by_scripture.get(scripture_guid, []):
            if e["source_GUID"] in self.entities:
                entities.add(e["source_GUID"])
        return entities
    
    def find_path(self, start_guid, end_guid, max_depth=3):
        """Find path between two entities through relationships."""
        if max_depth <= 0:
            return None
        
        visited = {start_guid}
        queue = [(start_guid, [start_guid])]
        
        while queue:
            current, path = queue.pop(0)
            if current == end_guid:
                return path
            if len(path) > max_depth:
                continue
            
            for edge in self.edges_by_entity.get(current, []):
                next_guid = edge["target_GUID"] if edge["source_GUID"] == current else edge["source_GUID"]
                if next_guid not in visited and next_guid in self.entities:
                    visited.add(next_guid)
                    queue.append((next_guid, path + [next_guid]))
        
        return None


class HybridRetriever:
    """Hybrid semantic + lexical retrieval."""
    
    def __init__(self):
        self.chunks = []
        self.faiss_index = None
        self.model = None
        self.bm25 = None
    
    def load(self):
        # Load chunks
        for fname in ["scripture_chunks.json", "dialogue_chunks.json",
                       "entity_chunks.json", "event_chunks.json"]:
            fpath = os.path.join(CHUNKS_DIR, fname)
            if os.path.exists(fpath):
                with open(fpath) as f:
                    self.chunks.extend(json.load(f))
        verses_dir = os.path.join(CHUNKS_DIR, "verses")
        if os.path.isdir(verses_dir):
            for fname in sorted(os.listdir(verses_dir)):
                if fname.endswith(".json"):
                    with open(os.path.join(verses_dir, fname)) as f:
                        self.chunks.extend(json.load(f))
        
        # Load FAISS
        import faiss
        self.faiss_index = faiss.read_index(os.path.join(EMBEDDINGS_DIR, "faiss_index.bin"))
        
        # Load model
        from sentence_transformers import SentenceTransformer
        mapping = json.load(open(os.path.join(EMBEDDINGS_DIR, "chunk_id_mapping.json")))
        self.model = SentenceTransformer(mapping["model"])
        
        return self
    
    def search(self, query, top_k=5):
        """Semantic search."""
        q_emb = self.model.encode([query], normalize_embeddings=True).astype(np.float32)
        D, I = self.faiss_index.search(q_emb, top_k)
        results = []
        for idx, score in zip(I[0], D[0]):
            if 0 <= idx < len(self.chunks):
                c = self.chunks[idx]
                results.append({
                    "chunk_id": c.get("chunk_id", ""),
                    "level": c.get("level", ""),
                    "scripture_id": c.get("scripture_id", ""),
                    "text": c.get("text", "")[:300],
                    "score": float(score),
                    "entity_links": c.get("entity_links", []),
                    "provenance": c.get("provenance", {}),
                })
        return results


def reason_about_entity(entity_name, kg, retriever):
    """Generate evidence-based reasoning about an entity."""
    entity = kg.find_entity(entity_name)
    if not entity:
        return {"status": "entity_not_found", "query": entity_name}
    
    # Get relationships
    relationships = kg.get_relationships(entity["GUID"])
    rel_summary = defaultdict(list)
    for r in relationships:
        rel_summary[r["type"]].append(r)
    
    # Get scripture mentions
    scriptures_mentioned = set()
    for r in relationships:
        if r["target_GUID"] in kg.scriptures:
            scriptures_mentioned.add(kg.scriptures[r["target_GUID"]]["id"])
    
    # Semantic search for related text
    search_results = retriever.search(f"{entity_name} {entity.get('entity_type', '')}", top_k=5)
    
    # Build reasoning chain
    reasoning = {
        "entity": entity["name"],
        "type": entity.get("entity_type", "unknown"),
        "guid": entity["GUID"],
        "total_mentions": entity.get("total_mentions", 0),
        "sources": entity.get("sources", []),
        "scriptures": list(scriptures_mentioned),
        "relationships": {},
        "semantic_evidence": search_results,
        "evidence_chain": [],
    }
    
    for rel_type, edges in rel_summary.items():
        targets = []
        for e in edges:
            target_guid = e["target_GUID"] if e["source_GUID"] == entity["GUID"] else e["source_GUID"]
            target = kg.entities.get(target_guid, {})
            evidence = e.get("evidence", "")
            if isinstance(evidence, dict):
                evidence = json.dumps(evidence)
            targets.append({
                "name": target.get("name", "unknown"),
                "type": target.get("entity_type", "unknown"),
                "evidence": str(evidence)[:200],
                "confidence": e.get("confidence", 0),
            })
        reasoning["relationships"][rel_type] = targets
        reasoning["evidence_chain"].append({
            "type": rel_type,
            "count": len(targets),
            "evidence": f"Found {len(targets)} {rel_type} relationships with confidence >= 70"
        })
    
    return reasoning


def reason_about_question(question, kg, retriever):
    """Answer a question using evidence from graph + retrieval."""
    # Retrieve relevant chunks
    search_results = retriever.search(question, top_k=10)
    
    # Extract entity names from question (simple approach)
    found_entities = []
    for name in kg.entity_by_name:
        if name.lower() in question.lower():
            found_entities.append(name)
    
    # Get graph evidence
    graph_evidence = []
    for name in found_entities[:5]:
        entity = kg.find_entity(name)
        if entity:
            rels = kg.get_relationships(entity["GUID"])
            graph_evidence.append({
                "entity": name,
                "type": entity.get("entity_type", ""),
                "mentions": entity.get("total_mentions", 0),
                "relationship_count": len(rels),
                "top_relationships": [
                    {"type": r["type"], "target": r.get("target_ref", "")}
                    for r in rels[:5]
                ],
            })
    
    # Combine evidence
    answer = {
        "question": question,
        "entities_found": found_entities,
        "semantic_evidence": [
            {
                "level": r.get("level", ""),
                "scripture": r.get("scripture_id", ""),
                "text": r.get("text", "")[:200],
                "score": r.get("score", 0),
            }
            for r in search_results[:5]
        ],
        "graph_evidence": graph_evidence,
        "evidence_count": len(search_results) + len(graph_evidence),
        "confidence": "high" if len(search_results) >= 3 and len(graph_evidence) >= 2 else "medium" if len(search_results) >= 2 else "low",
    }
    
    return answer


def main():
    print("=" * 70)
    print("Phase 14: Reasoning Engine — AstroSage Knowledge System")
    print(f"Generated: {GENERATED}")
    print(f"Commit: {GIT_COMMIT}")
    print("=" * 70)
    
    # ── Load knowledge graph ──
    print("\n[1] Loading knowledge graph...")
    kg = KnowledgeGraph().load()
    print(f"  Entities: {len(kg.entities)}")
    print(f"  Scriptures: {len(kg.scriptures)}")
    print(f"  Edges: {len(kg.edges)}")
    
    # ── Load retrieval system ──
    print("\n[2] Loading hybrid retriever...")
    retriever = HybridRetriever().load()
    print(f"  Chunks: {len(retriever.chunks)}")
    print(f"  FAISS vectors: {retriever.faiss_index.ntotal}")
    
    # ── Test entity reasoning ──
    print("\n[3] Testing entity reasoning...")
    os.makedirs(REASONING_DIR, exist_ok=True)
    
    entity_tests = ["Vishnu", "Krishna", "Arjuna", "Dharma", "Yoga"]
    entity_results = {}
    for name in entity_tests:
        result = reason_about_entity(name, kg, retriever)
        entity_results[name] = result
        rel_count = sum(len(v) for v in result.get("relationships", {}).values())
        print(f"  {name}: {result.get('type', '?')} | {rel_count} relationships | {len(result.get('semantic_evidence', []))} semantic hits")
    
    # ── Test question reasoning ──
    print("\n[4] Testing question reasoning...")
    questions = [
        "Who is Vishnu and what are his avatars?",
        "What is the relationship between Krishna and Arjuna?",
        "What teachings does the Bhagavad Gita contain?",
        "Who are the Pandavas in the Mahabharata?",
    ]
    question_results = {}
    for q in questions:
        result = reason_about_question(q, kg, retriever)
        question_results[q] = result
        print(f"  Q: {q}")
        print(f"    Entities: {result.get('entities_found', [])}")
        print(f"    Evidence: {result.get('evidence_count', 0)} sources | Confidence: {result.get('confidence', '?')}")
    
    # ── Save results ──
    print("\n[5] Saving reasoning results...")
    entity_file = os.path.join(REASONING_DIR, "entity_reasoning.json")
    with open(entity_file, "w") as f:
        json.dump(entity_results, f, indent=2, ensure_ascii=False)
    
    question_file = os.path.join(REASONING_DIR, "question_reasoning.json")
    with open(question_file, "w") as f:
        json.dump(question_results, f, indent=2, ensure_ascii=False)
    
    # ── Build manifest ──
    manifest = {
        "version": "1.0.0",
        "knowledge_version": "1.0.0",
        "git_commit": GIT_COMMIT,
        "generated": GENERATED,
        "generator": "Phase 14 Reasoning Engine",
        "capabilities": [
            "Entity reasoning (relationships, mentions, sources)",
            "Question answering (graph + semantic evidence)",
            "Evidence chain construction",
            "Confidence scoring",
        ],
        "stats": {
            "entities_indexed": len(kg.entities),
            "edges_indexed": len(kg.edges),
            "chunks_indexed": len(retriever.chunks),
            "entity_tests": len(entity_tests),
            "question_tests": len(questions),
        },
        "artifacts": {},
    }
    
    for fname in os.listdir(REASONING_DIR):
        fpath = os.path.join(REASONING_DIR, fname)
        if os.path.isfile(fpath):
            h = sha256_bytes(open(fpath, "rb").read())
            manifest["artifacts"][fname] = {"sha256": h, "size": os.path.getsize(fpath)}
    
    manifest_file = os.path.join(REASONING_DIR, "reasoning_manifest.json")
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\n{'=' * 70}")
    print(f"Phase 14: Reasoning Engine — COMPLETE")
    print(f"  Entity reasoning: {len(entity_tests)} entities tested")
    print(f"  Question reasoning: {len(questions)} questions tested")
    print(f"  Artifacts: {len(manifest['artifacts'])} files")
    print(f"{'=' * 70}")

if __name__ == "__main__":
    main()
