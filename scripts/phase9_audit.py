"""
Phase 9.5: Comprehensive Graph Audit
Recompute everything from source files.
"""
import json, os
from collections import defaultdict, Counter

GRAPH_DIR = "knowledge/graph"

def load_json(path):
    with open(os.path.join(GRAPH_DIR, path)) as f:
        return json.load(f)

# Load all graph data
entity_nodes = load_json('nodes/entity_nodes.json')
scripture_nodes = load_json('nodes/scripture_nodes.json')
edges = load_json('edges/relationship_edges.json')
graph_statistics = load_json('graph_statistics.json')
validation = load_json('validation/graph_validation.json')
completeness = load_json('graph_completeness.json')

# Load sub-graphs
subgraphs = {}
for fname in os.listdir(GRAPH_DIR):
    if fname.endswith('_graph.json') and fname != 'graph.json':
        with open(os.path.join(GRAPH_DIR, fname)) as f:
            subgraphs[fname] = json.load(f)

# ── Basic counts ──
all_nodes = scripture_nodes + entity_nodes
print(f"=== GRAPH AUDIT ===")
print(f"Scripture nodes: {len(scripture_nodes)}")
print(f"Entity nodes: {len(entity_nodes)}")
print(f"Total nodes: {len(all_nodes)}")
print(f"Total edges: {len(edges)}")

# ── Node type breakdown ──
type_counts = Counter()
for n in entity_nodes:
    t = n.get('entity_type', n.get('type', 'unknown'))
    type_counts[t] += 1
print(f"\nEntity type breakdown:")
for t, c in type_counts.most_common():
    print(f"  {t}: {c}")

# ── Edge type breakdown ──
edge_type_counts = Counter(e.get('type', 'unknown') for e in edges)
print(f"\nEdge type breakdown:")
for t, c in edge_type_counts.most_common():
    print(f"  {t}: {c}")

# ── Duplicate detection ──
node_guids = [n.get('GUID', '') for n in all_nodes]
edge_guids = [e.get('GUID', '') for e in edges]
dup_node_guids = len(node_guids) - len(set(node_guids))
dup_edge_guids = len(edge_guids) - len(set(edge_guids))

# Duplicate names
name_counts = Counter(n.get('name', '') for n in entity_nodes)
dup_names = {name: count for name, count in name_counts.items() if count > 1}
print(f"\nDuplicate node GUIDs: {dup_node_guids}")
print(f"Duplicate edge GUIDs: {dup_edge_guids}")
print(f"Duplicate entity names: {len(dup_names)}")
if dup_names:
    for name, count in list(dup_names.items())[:10]:
        print(f"  '{name}': {count} occurrences")

# ── Orphan detection ──
entity_guids = {n['GUID'] for n in entity_nodes}
scripture_guids = {n['GUID'] for n in scripture_nodes}
connected = set()
for e in edges:
    sg = e.get('source_GUID', '')
    tg = e.get('target_GUID', '')
    if sg in entity_guids: connected.add(sg)
    if tg in entity_guids: connected.add(tg)
orphan_entities = entity_guids - connected
print(f"\nOrphan entities: {len(orphan_entities)}")
if orphan_entities:
    for n in entity_nodes:
        if n['GUID'] in orphan_entities:
            print(f"  {n.get('type','?')}: {n.get('name','?')}")

# ── Broken references ──
all_guids = entity_guids | scripture_guids
broken = 0
broken_edges = []
for e in edges:
    sg = e.get('source_GUID', '')
    tg = e.get('target_GUID', '')
    if sg not in all_guids or tg not in all_guids:
        broken += 1
        broken_edges.append(e)
print(f"\nBroken references: {broken}")

# ── Coverage analysis ──
# MENTIONED_IN coverage
mentioned_in = [e for e in edges if e['type'] == 'MENTIONED_IN']
rel_edges = [e for e in edges if e['type'] != 'MENTIONED_IN']
print(f"\nMentioned_In edges: {len(mentioned_in)}")
print(f"Relationship edges: {len(rel_edges)}")

# Which scriptures have entity coverage?
scripture_entity_coverage = defaultdict(set)
for e in mentioned_in:
    tg = e.get('target_GUID', '')
    sg = e.get('source_GUID', '')
    if tg in scripture_guids and sg in entity_guids:
        # Find entity name
        for n in entity_nodes:
            if n['GUID'] == sg:
                scripture_entity_coverage[tg].add(n.get('name', ''))
                break

print(f"\nScripture entity coverage:")
for sg in scripture_nodes:
    sid = sg.get('id', sg.get('canonical_name', '?'))
    entities = scripture_entity_coverage.get(sg['GUID'], set())
    print(f"  {sid}: {len(entities)} entities")

# ── Dialogue coverage ──
# Check for dialogue-type edges
dialogue_edges = [e for e in edges if e['type'] in ('TEACHER_OF', 'STUDENT_OF')]
print(f"\nDialogue-type edges: {len(dialogue_edges)}")

# ── Event coverage ──
event_sg = subgraphs.get('event_graph.json', {})
events = event_sg.get('events', [])
print(f"Canonical events: {len(events)}")

# ── Genealogy coverage ──
genealogy_edge_types = {'FATHER_OF', 'MOTHER_OF', 'SON_OF', 'DAUGHTER_OF', 'HUSBAND_OF', 'BROTHER_OF', 'SISTER_OF', 'ANCESTOR_OF', 'INCARNATION_OF', 'UNCLE_OF', 'NEPHEW_OF'}
genealogy_edges = [e for e in edges if e.get('type','') in genealogy_edge_types]
print(f"Genealogy edges: {len(genealogy_edges)}")

# ── Concept coverage ──
concept_edge_types = {'PATH_TO', 'LEADS_TO', 'GUIDES', 'IDENTICAL_TO', 'LIBERATION_FROM', 'CONTRASTS_WITH', 'SUBCATEGORY_OF'}
concept_edges = [e for e in edges if e.get('type','') in concept_edge_types]
concept_nodes = [n for n in entity_nodes if n.get('type','') == 'Concept']
print(f"Concept nodes: {len(concept_nodes)}")
print(f"Concept edges: {len(concept_edges)}")

# ── Ritual coverage ──
ritual_nodes = [n for n in entity_nodes if n.get('type','') == 'Ritual']
print(f"Ritual nodes: {len(ritual_nodes)}")

# ── Astronomy coverage ──
astro_nodes = [n for n in entity_nodes if n.get('type','') in ('Nakshatra', 'Graha', 'Astronomy')]
print(f"Astronomy nodes: {len(astro_nodes)}")

# ── Geography coverage ──
geo_nodes = [n for n in entity_nodes if n.get('type','') == 'Place']
geo_edge_types = {'LOCATED_IN', 'ABODE_OF', 'CAPITAL_OF', 'CENTER_OF', 'BATTLEFIELD_OF', 'KINGDOM_OF', 'RULER_OF'}
geo_edges = [e for e in edges if e.get('type','') in geo_edge_types]
print(f"Geography nodes: {len(geo_nodes)}")
print(f"Geography edges: {len(geo_edges)}")

# ── Cross-scripture coverage ──
cross_edge_types = {'REFERENCES', 'COMMENTARY_ON', 'SAME_TEACHING', 'SAME_EVENT', 'SAME_PERSON'}
cross_edges = [e for e in edges if e.get('type','') in cross_edge_types]
print(f"Cross-scripture edges: {len(cross_edges)}")

# ── Confidence analysis ──
confidences = [e.get('confidence', 0) for e in edges]
avg_confidence = sum(confidences) / len(confidences) if confidences else 0
min_confidence = min(confidences) if confidences else 0
max_confidence = max(confidences) if confidences else 0
print(f"\nConfidence: avg={avg_confidence:.1f}, min={min_confidence}, max={max_confidence}")

# ── Save audit ──
audit = {
    "generated": "2026-07-17",
    "phase": "9.5-audit",
    "totals": {
        "scripture_nodes": len(scripture_nodes),
        "entity_nodes": len(entity_nodes),
        "total_nodes": len(all_nodes),
        "total_edges": len(edges),
        "mentioned_in_edges": len(mentioned_in),
        "relationship_edges": len(rel_edges)
    },
    "entity_type_breakdown": dict(type_counts),
    "edge_type_breakdown": dict(edge_type_counts),
    "quality": {
        "duplicate_node_guids": dup_node_guids,
        "duplicate_edge_guids": dup_edge_guids,
        "duplicate_entity_names": len(dup_names),
        "duplicate_names_detail": dup_names,
        "orphan_entities": len(orphan_entities),
        "orphan_entity_names": [n.get('name','?') for n in entity_nodes if n['GUID'] in orphan_entities],
        "broken_references": broken,
        "avg_confidence": round(avg_confidence, 1),
        "min_confidence": min_confidence,
        "max_confidence": max_confidence
    },
    "coverage": {
        "dialogue_edges": len(dialogue_edges),
        "canonical_events": len(events),
        "genealogy_edges": len(genealogy_edges),
        "concept_nodes": len(concept_nodes),
        "concept_edges": len(concept_edges),
        "ritual_nodes": len(ritual_nodes),
        "astronomy_nodes": len(astro_nodes),
        "geography_nodes": len(geo_nodes),
        "geography_edges": len(geo_edges),
        "cross_scripture_edges": len(cross_edges)
    },
    "sub_graphs": {name: data.get('stats', {}) for name, data in subgraphs.items()}
}

with open(os.path.join(GRAPH_DIR, 'graph_audit.json'), 'w') as f:
    json.dump(audit, f, indent=2, ensure_ascii=False)

print(f"\n=== Audit saved to graph_audit.json ===")
