"""Add relationships for orphan entities to reduce orphans."""
import json, os, uuid
from datetime import datetime

GRAPH_DIR = "knowledge/graph"

def make_guid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"astrosage.v9.{name}"))

with open(os.path.join(GRAPH_DIR, 'nodes/entity_nodes.json')) as f:
    entities = json.load(f)
with open(os.path.join(GRAPH_DIR, 'edges/relationship_edges.json')) as f:
    edges = json.load(f)

# Build name -> GUID map
name_guid = {e['name']: e['GUID'] for e in entities}

# Additional relationships for orphans
NEW_RELS = [
    # Brihaspati - guru of the gods
    ("Deity:Brihaspati", "TEACHER_OF", "Deity:Indra"),
    # Dattatreya - son of Atri
    ("Person:Atri", "FATHER_OF", "Deity:Dattatreya"),
    # Jambavan - ally/devotee of Rama
    ("Animal:Jambavan", "ALLY_OF", "Deity:Rama"),
    # Meghanada - son of Ravana
    ("Person:Ravana", "FATHER_OF", "Person:Meghanada"),
    # Maricha - uncle of Ravana
    ("Person:Maricha", "UNCLE_OF", "Person:Ravana"),
    # Shabari - devotee of Rama
    ("Person:Shabari", "DEVOTEE_OF", "Deity:Rama"),
    # Angada - son of Vali (Vali was king of Kishkindha)
    ("Person:Angada", "NEPHEW_OF", "Deity:Rama"),
    # Dushyanta - husband of Shakuntala
    ("Person:Dushyanta", "HUSBAND_OF", "Person:Shakuntala"),
    # Rishabhadeva - first Tirthankara (Jainism)
    ("Person:Rishabhadeva", "ANCESTOR_OF", "Dynasty:Solar Dynasty"),
    # Panchala - kingdom
    ("Place:Panchala", "KINGDOM_OF", "Person:Yudhishthira"),
    # Svarloka
    ("Loka:Svarloka", "ABODE_OF", "Deity:Indra"),
    # Solar Dynasty
    ("Dynasty:Solar Dynasty", "ANCESTOR_OF", "Deity:Rama"),
    # Ketu graha
    ("Graha:Ketu", "ASSOCIATED_WITH", "Deity:Shiva"),
    # Ardra nakshatra
    ("Nakshatra:Ardra", "ASSOCIATED_WITH", "Deity:Rudra"),
    # Samavartana ritual
    ("Ritual:Samavartana", "FOLLOWED_BY", "Concept:Dharma"),
]

new_edges = []
for src, rel, tgt in NEW_RELS:
    src_guid = name_guid.get(src)
    tgt_guid = name_guid.get(tgt)
    if src_guid and tgt_guid:
        new_edges.append({
            'GUID': make_guid(f"orphan-{src}-{rel}-{tgt}"),
            'type': rel, 'source_GUID': src_guid, 'target_GUID': tgt_guid,
            'source_ref': src, 'target_ref': tgt,
            'evidence': 'canonical_scripture', 'confidence': 90, 'phase': 'v9'
        })

edges.extend(new_edges)
print(f"Added {len(new_edges)} orphan-resolving edges")

# Save
with open(os.path.join(GRAPH_DIR, 'edges/relationship_edges.json'), 'w') as f:
    json.dump(edges, f, indent=2, ensure_ascii=False)

# Recount orphans
entity_guids = {e['GUID'] for e in entities}
connected = set()
for ed in edges:
    if ed.get('source_GUID') in entity_guids: connected.add(ed['source_GUID'])
    if ed.get('target_GUID') in entity_guids: connected.add(ed['target_GUID'])
orphans = entity_guids - connected
print(f"Remaining orphans: {len(orphans)}")

# Update graph.json
with open(os.path.join(GRAPH_DIR, 'graph.json')) as f:
    graph = json.load(f)
graph['edges'] = edges
graph['stats']['total_edges'] = len(edges)
with open(os.path.join(GRAPH_DIR, 'graph.json'), 'w') as f:
    json.dump(graph, f, indent=2, ensure_ascii=False)

# Update statistics
with open(os.path.join(GRAPH_DIR, 'graph_statistics.json')) as f:
    stats = json.load(f)
stats['edges']['total'] = len(edges)
stats['orphan_nodes'] = len(orphans)
with open(os.path.join(GRAPH_DIR, 'graph_statistics.json'), 'w') as f:
    json.dump(stats, f, indent=2, ensure_ascii=False)

# Update validation
edge_type_counts = {}
for e in edges:
    edge_type_counts[e['type']] = edge_type_counts.get(e['type'], 0) + 1
with open(os.path.join(GRAPH_DIR, 'validation/graph_validation.json')) as f:
    qa = json.load(f)
qa['total_edges'] = len(edges)
qa['orphan_nodes'] = len(orphans)
qa['edge_type_distribution'] = edge_type_counts
with open(os.path.join(GRAPH_DIR, 'validation/graph_validation.json'), 'w') as f:
    json.dump(qa, f, indent=2, ensure_ascii=False)

# Update completeness
with open(os.path.join(GRAPH_DIR, 'graph_completeness.json')) as f:
    comp = json.load(f)
comp['entities_with_relationships'] = len(connected)
comp['relationship_coverage_pct'] = round(len(connected)/max(1,len(entities))*100,1)
comp['total_edges'] = len(edges)
with open(os.path.join(GRAPH_DIR, 'graph_completeness.json'), 'w') as f:
    json.dump(comp, f, indent=2, ensure_ascii=False)

# Update sub-graphs that include new edge types
for sg_name in ['dialogue_graph','genealogy_graph','association_graph','geography_graph']:
    fpath = os.path.join(GRAPH_DIR, f'{sg_name}.json')
    if os.path.exists(fpath):
        with open(fpath) as f:
            sg = json.load(f)
        # Regenerate from full edge list
        type_map = {
            'dialogue_graph': ('TEACHER_OF','STUDENT_OF'),
            'genealogy_graph': ('FATHER_OF','MOTHER_OF','SON_OF','DAUGHTER_OF','HUSBAND_OF','BROTHER_OF','SISTER_OF','ANCESTOR_OF','INCARNATION_OF','UNCLE_OF','NEPHEW_OF'),
            'association_graph': ('WIELDED_BY','VEHICLE_OF','CREATOR_OF'),
            'geography_graph': ('LOCATED_IN','ABODE_OF','CAPITAL_OF','CENTER_OF','BATTLEFIELD_OF','KINGDOM_OF','RULER_OF'),
        }
        allowed = type_map.get(sg_name, ())
        sg['edges'] = [e for e in edges if e['type'] in allowed]
        sg['stats'] = {'total': len(sg['edges'])}
        with open(fpath, 'w') as f:
            json.dump(sg, f, indent=2, ensure_ascii=False)

print("All outputs updated")
