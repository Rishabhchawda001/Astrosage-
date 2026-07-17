"""Classify untyped entities and run saturation check."""
import json, os, uuid
from collections import Counter, defaultdict
from datetime import datetime

GRAPH_DIR = "knowledge/graph"

def make_guid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"astrosage.v95.{name}"))

with open(os.path.join(GRAPH_DIR, 'nodes/entity_nodes.json')) as f:
    entities = json.load(f)
with open(os.path.join(GRAPH_DIR, 'edges/relationship_edges.json')) as f:
    edges = json.load(f)
with open(os.path.join(GRAPH_DIR, 'nodes/scripture_nodes.json')) as f:
    scriptures = json.load(f)

# ── Reclassify untyped entities ──
PERSON_NAMES = {'Bhrigu', 'Shukracharya', 'Kashyapa', 'Saptarishis', 'Ancestors'}
# Everything else with underscores is a definition -> merge into parent concept

# Find definition nodes (names with underscores)
def is_definition(name):
    return '_' in name and not name.startswith('concept_')

# Build parent concept mapping for definitions
DEF_TO_CONCEPT = {}
for e in entities:
    if is_definition(e['name']):
        # This is a definition - it should be merged into its parent concept
        # Find which concept references it
        for edge in edges:
            if edge.get('target_GUID') == e['GUID'] and edge.get('type') in ('DEFINED_AS', 'INCLUDES'):
                src_guid = edge.get('source_GUID', '')
                for pe in entities:
                    if pe['GUID'] == src_guid:
                        DEF_TO_CONCEPT[e['GUID']] = pe['GUID']
                        break
                break

print(f"Definitions to merge: {len(DEF_TO_CONCEPT)}")

# Remove definition nodes and update edges
def_guids = set(DEF_TO_CONCEPT.keys())
new_entities = [e for e in entities if e['GUID'] not in def_guids]

# Reclassify remaining untyped
for e in new_entities:
    if e.get('entity_type','') == 'Entity':
        if e['name'] in PERSON_NAMES:
            e['type'] = 'Person'
            e['entity_type'] = 'Person'
        elif e.get('from_ref','').startswith('Concept:'):
            e['type'] = 'Concept'
            e['entity_type'] = 'Concept'
        elif e.get('from_ref','').startswith('Teaching:'):
            e['type'] = 'Concept'
            e['entity_type'] = 'Concept'
        elif e.get('from_ref','').startswith('Saptarishis'):
            e['type'] = 'Concept'
            e['entity_type'] = 'Concept'
        elif e.get('from_ref','').startswith('Dynasty:'):
            e['type'] = 'Dynasty'
            e['entity_type'] = 'Dynasty'

# Update edges that pointed to deleted definition nodes
for edge in edges:
    tg = edge.get('target_GUID', '')
    if tg in def_guids:
        new_target = DEF_TO_CONCEPT.get(tg, tg)
        edge['target_GUID'] = new_target

# Remove edges where source was deleted definition
edges = [e for e in edges if e.get('source_GUID','') not in def_guids]

print(f"After cleanup: {len(new_entities)} entities, {len(edges)} edges")

# ── Type breakdown ──
type_counts = Counter(n.get('entity_type', n.get('type','')) for n in new_entities)
print(f"\nEntity types:")
for t, c in type_counts.most_common():
    print(f"  {t}: {c}")

# ── Verify no orphans/broken ──
entity_guids = {e['GUID'] for e in new_entities}
scripture_guids = {s['GUID'] for s in scriptures}
all_guids = entity_guids | scripture_guids
connected = set()
for e in edges:
    if e.get('source_GUID') in entity_guids: connected.add(e['source_GUID'])
    if e.get('target_GUID') in entity_guids: connected.add(e['target_GUID'])
orphans = entity_guids - connected
broken = sum(1 for e in edges if e.get('source_GUID','') not in all_guids or e.get('target_GUID','') not in all_guids)
print(f"\nOrphans: {len(orphans)}, Broken: {broken}")

# ── Edge type distribution ──
edge_type_dist = dict(Counter(e.get('type','') for e in edges))
mentioned_in = [e for e in edges if e['type'] == 'MENTIONED_IN']
rel_edges = [e for e in edges if e['type'] != 'MENTIONED_IN']
print(f"\nEdge types: {len(edge_type_dist)}")
print(f"MENTIONED_IN: {len(mentioned_in)}, Relationships: {len(rel_edges)}")

# ── Save ──
with open(os.path.join(GRAPH_DIR, 'nodes/entity_nodes.json'), 'w') as f:
    json.dump(new_entities, f, indent=2, ensure_ascii=False)
with open(os.path.join(GRAPH_DIR, 'edges/relationship_edges.json'), 'w') as f:
    json.dump(edges, f, indent=2, ensure_ascii=False)

# Update all outputs
all_nodes = scriptures + new_entities
with open(os.path.join(GRAPH_DIR, 'graph.json'), 'w') as f:
    json.dump({'version':'9.5','generated':datetime.now().isoformat(),'nodes':all_nodes,'edges':edges,
               'stats':{'total_nodes':len(all_nodes),'total_edges':len(edges)}}, f, indent=2, ensure_ascii=False)

connected_entities = connected & entity_guids
prov_count = sum(1 for n in new_entities if n.get('sources') or n.get('provenance'))

with open(os.path.join(GRAPH_DIR, 'graph_statistics.json'), 'w') as f:
    json.dump({
        'version':'9.5','generated':datetime.now().isoformat(),'phase':9.5,
        'nodes':{'total':len(all_nodes),'scriptures':len(scriptures),'entities':len(new_entities)},
        'edges':{'total':len(edges),'by_type':edge_type_dist},
        'entity_breakdown':dict(type_counts),
        'orphan_nodes':len(orphans),
        'evidence_coverage_pct':round(prov_count/max(1,len(new_entities))*100,1)
    }, f, indent=2, ensure_ascii=False)

with open(os.path.join(GRAPH_DIR, 'validation/graph_validation.json'), 'w') as f:
    json.dump({
        'generated':datetime.now().isoformat(),'phase':'9.5',
        'total_nodes':len(all_nodes),'total_edges':len(edges),
        'orphan_nodes':len(orphans),'broken_references':broken,
        'evidence_coverage_pct':round(prov_count/max(1,len(new_entities))*100,1),
        'edge_type_distribution':edge_type_dist,'node_type_distribution':dict(type_counts),
        'pass':broken==0
    }, f, indent=2, ensure_ascii=False)

with open(os.path.join(GRAPH_DIR, 'graph_completeness.json'), 'w') as f:
    json.dump({
        'generated':datetime.now().isoformat(),'phase':'9.5',
        'total_entities':len(new_entities),
        'entities_with_relationships':len(connected_entities),
        'relationship_coverage_pct':round(len(connected_entities)/max(1,len(new_entities))*100,1),
        'total_edges':len(edges)
    }, f, indent=2, ensure_ascii=False)

# Entity/CUID indexes
entity_index = {n.get('name',''):{'GUID':n['GUID'],'type':n.get('type',''),'mentions':n.get('total_mentions',n.get('mentions',0))} for n in new_entities}
with open(os.path.join(GRAPH_DIR, 'indexes/entity_index.json'), 'w') as f:
    json.dump(entity_index, f, indent=2, ensure_ascii=False)
cuid_index = {n.get('CUID',n.get('name','')):n['GUID'] for n in new_entities+scriptures if n.get('CUID') or n.get('name')}
with open(os.path.join(GRAPH_DIR, 'cuid_index.json'), 'w') as f:
    json.dump(cuid_index, f, indent=2, ensure_ascii=False)

# Manifest
manifest_files = {}
for fname in os.listdir(GRAPH_DIR):
    fp = os.path.join(GRAPH_DIR, fname)
    if os.path.isfile(fp): manifest_files[fname] = {'size': os.path.getsize(fp)}
for sd in ['nodes','edges','validation','indexes','schemas']:
    sp = os.path.join(GRAPH_DIR, sd)
    if os.path.isdir(sp):
        for fname in os.listdir(sp): manifest_files[f'{sd}/{fname}'] = {'size': os.path.getsize(os.path.join(sp, fname))}
with open(os.path.join(GRAPH_DIR, 'graph_manifest.json'), 'w') as f:
    json.dump({'version':'9.5','generated':datetime.now().isoformat(),'files':manifest_files}, f, indent=2)

print(f"\nFinal: {len(all_nodes)} nodes, {len(edges)} edges")
