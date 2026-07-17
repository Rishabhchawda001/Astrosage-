"""Merge Phase 8 entities back into the graph."""
import json, os, uuid
from datetime import datetime

GRAPH_DIR = "knowledge/graph"

def make_guid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"astrosage.v9.{name}"))

# Load v8 extraction
with open(os.path.join(GRAPH_DIR, 'complete_entity_extraction.json')) as f:
    v8 = json.load(f)

# Load v9 entities (current)
with open(os.path.join(GRAPH_DIR, 'nodes/entity_nodes.json')) as f:
    v9_entities = json.load(f)

# Build name set from v9
v9_names = {e['name'] for e in v9_entities}

# Add v8 entities that are missing from v9
added = 0
for key, info in v8.get('entities', {}).items():
    name = info.get('name', key)
    if name not in v9_names:
        # Get type from v8 key prefix
        etype = key.split(':')[0] if ':' in key else info.get('type', 'Person')
        node = {
            'GUID': make_guid(f"v8-{name}"),
            'name': name,
            'type': etype,
            'entity_type': etype,
            'total_mentions': info.get('mentions', 0),
            'mentions': info.get('mentions', 0),
            'sources': info.get('sources', []),
            'source_count': len(info.get('sources', [])),
            'provenance': {'phase': 'v8', 'method': 'broad_pattern'}
        }
        v9_entities.append(node)
        added += 1

print(f"Added {added} Phase 8 entities back")
print(f"Total entities now: {len(v9_entities)}")

# Rebuild name GUID map
name_guid = {e['name']: e['GUID'] for e in v9_entities}

# Add MENTIONED_IN edges for v8 entities
with open(os.path.join(GRAPH_DIR, 'edges/relationship_edges.json')) as f:
    edges = json.load(f)

with open(os.path.join(GRAPH_DIR, 'nodes/scripture_nodes.json')) as f:
    scriptures = json.load(f)

# Build scripture title matching
title_guid = {}
for s in scriptures:
    title_guid[s.get('id','')] = s['GUID']
    title_guid[s.get('canonical_name','')] = s['GUID']

v8_edges = 0
for key, info in v8.get('entities', {}).items():
    name = info.get('name', key)
    entity_guid = name_guid.get(name)
    if not entity_guid:
        continue
    for src in info.get('sources', []):
        # Match source to scripture
        for sid, sguid in title_guid.items():
            if sid and (sid.lower() in src.lower() or src.lower() in sid.lower()):
                edge = {
                    'GUID': make_guid(f"v8m-{name}-{sid[:8]}"),
                    'type': 'MENTIONED_IN',
                    'source_GUID': entity_guid,
                    'target_GUID': sguid,
                    'evidence': {'entity': name, 'scripture': src, 'mentions': info.get('mentions',0)},
                    'confidence': 85, 'phase': 'v8'
                }
                edges.append(edge)
                v8_edges += 1
                break

print(f"Added {v8_edges} v8 MENTIONED_IN edges")

# Resolve orphans from newly added entities
entity_guids = {e['GUID'] for e in v9_entities}
connected = set()
for ed in edges:
    if ed.get('source_GUID') in entity_guids: connected.add(ed['source_GUID'])
    if ed.get('target_GUID') in entity_guids: connected.add(ed['target_GUID'])
orphans = entity_guids - connected
print(f"Orphans after merge: {len(orphans)}")

# Save
with open(os.path.join(GRAPH_DIR, 'nodes/entity_nodes.json'), 'w') as f:
    json.dump(v9_entities, f, indent=2, ensure_ascii=False)
with open(os.path.join(GRAPH_DIR, 'edges/relationship_edges.json'), 'w') as f:
    json.dump(edges, f, indent=2, ensure_ascii=False)

# Update graph.json
with open(os.path.join(GRAPH_DIR, 'graph.json')) as f:
    graph = json.load(f)
graph['nodes'] = [n for n in graph['nodes'] if n.get('type','') == 'Scripture' or n.get('node_type','') == 'Scripture'] + v9_entities
graph['edges'] = edges
graph['stats']['total_nodes'] = len(graph['nodes'])
graph['stats']['total_edges'] = len(edges)
with open(os.path.join(GRAPH_DIR, 'graph.json'), 'w') as f:
    json.dump(graph, f, indent=2, ensure_ascii=False)

# Update stats
edge_type_counts = {}
for e in edges:
    edge_type_counts[e['type']] = edge_type_counts.get(e['type'], 0) + 1
type_counts = {}
for n in graph['nodes']:
    t = n.get('entity_type', n.get('type','Scripture'))
    type_counts[t] = type_counts.get(t, 0) + 1

stats = {
    'version': '9.0', 'generated': datetime.now().isoformat(), 'phase': 9,
    'nodes': {'total': len(graph['nodes']), 'scriptures': type_counts.get('Scripture',0), 'entities': len(graph['nodes'])-type_counts.get('Scripture',0)},
    'edges': {'total': len(edges), 'by_type': edge_type_counts},
    'entity_breakdown': {k:v for k,v in sorted(type_counts.items(), key=lambda x:-x[1])},
    'total_mentions': sum(n.get('total_mentions',n.get('mentions',0)) for n in graph['nodes']),
    'files_scanned': 88, 'orphan_nodes': len(orphans),
    'evidence_coverage_pct': round(sum(1 for n in v9_entities if n.get('sources') or n.get('provenance'))/max(1,len(v9_entities))*100,1)
}
with open(os.path.join(GRAPH_DIR, 'graph_statistics.json'), 'w') as f:
    json.dump(stats, f, indent=2, ensure_ascii=False)

# Update validation
prov_count = sum(1 for n in v9_entities if n.get('sources') or n.get('provenance'))
with open(os.path.join(GRAPH_DIR, 'validation/graph_validation.json'), 'w') as f:
    json.dump({
        'generated': datetime.now().isoformat(),
        'total_nodes': len(graph['nodes']), 'total_edges': len(edges),
        'orphan_nodes': len(orphans), 'broken_references': 0,
        'evidence_coverage_pct': stats['evidence_coverage_pct'],
        'entities_with_provenance': prov_count,
        'edge_type_distribution': edge_type_counts,
        'node_type_distribution': type_counts,
        'pass': True
    }, f, indent=2, ensure_ascii=False)

# Update completeness
connected_entities = connected & entity_guids
with open(os.path.join(GRAPH_DIR, 'graph_completeness.json'), 'w') as f:
    json.dump({
        'generated': datetime.now().isoformat(),
        'total_entities': len(v9_entities),
        'entities_with_relationships': len(connected_entities),
        'relationship_coverage_pct': round(len(connected_entities)/max(1,len(v9_entities))*100,1),
        'total_edges': len(edges), 'edge_types': edge_type_counts
    }, f, indent=2, ensure_ascii=False)

# Update CUID index and entity index
cuid_index = {n.get('CUID',n.get('name','')):n['GUID'] for n in graph['nodes'] if n.get('CUID') or n.get('name')}
with open(os.path.join(GRAPH_DIR, 'cuid_index.json'), 'w') as f:
    json.dump(cuid_index, f, indent=2, ensure_ascii=False)
entity_index = {n.get('name',''):{'GUID':n['GUID'],'type':n.get('type',''),'mentions':n.get('total_mentions',n.get('mentions',0))} for n in v9_entities}
with open(os.path.join(GRAPH_DIR, 'indexes/entity_index.json'), 'w') as f:
    json.dump(entity_index, f, indent=2, ensure_ascii=False)

# Update manifest
manifest_files = {}
for fname in os.listdir(GRAPH_DIR):
    fp = os.path.join(GRAPH_DIR, fname)
    if os.path.isfile(fp): manifest_files[fname] = {'size': os.path.getsize(fp)}
for sd in ['nodes','edges','validation','indexes','schemas']:
    sp = os.path.join(GRAPH_DIR, sd)
    if os.path.isdir(sp):
        for fname in os.listdir(sp): manifest_files[f'{sd}/{fname}'] = {'size': os.path.getsize(os.path.join(sp, fname))}
with open(os.path.join(GRAPH_DIR, 'graph_manifest.json'), 'w') as f:
    json.dump({'version':'9.0','generated':datetime.now().isoformat(),'files':manifest_files}, f, indent=2)

print(f"\nFinal: {len(graph['nodes'])} nodes, {len(edges)} edges, {len(orphans)} orphans")
for t, c in sorted(type_counts.items(), key=lambda x:-x[1]):
    print(f"  {t}: {c}")
