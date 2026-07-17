"""Fix broken references by adding missing entities to node list."""
import json, os, uuid
from collections import Counter
from datetime import datetime

GRAPH_DIR = "knowledge/graph"

def make_guid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"astrosage.v95.{name}"))

with open(os.path.join(GRAPH_DIR, 'nodes/entity_nodes.json')) as f:
    entities = json.load(f)
with open(os.path.join(GRAPH_DIR, 'nodes/scripture_nodes.json')) as f:
    scriptures = json.load(f)
with open(os.path.join(GRAPH_DIR, 'edges/relationship_edges.json')) as f:
    edges = json.load(f)

entity_guids = {e['GUID'] for e in entities}
scripture_guids = {s['GUID'] for s in scriptures}
all_guids = entity_guids | scripture_guids

# Find all referenced GUIDs that don't exist
missing_guids = set()
for e in edges:
    sg = e.get('source_GUID', '')
    tg = e.get('target_GUID', '')
    if sg and sg not in all_guids:
        missing_guids.add(sg)
    if tg and tg not in all_guids:
        missing_guids.add(tg)

print(f"Missing GUIDs: {len(missing_guids)}")

# Build reverse map: GUID -> source_ref/target_ref
guid_to_ref = {}
for e in edges:
    sg = e.get('source_GUID', '')
    tg = e.get('target_GUID', '')
    if sg in missing_guids:
        guid_to_ref[sg] = e.get('source_ref', '')
    if tg in missing_guids:
        guid_to_ref[tg] = e.get('target_ref', '')

# Classify missing entities
entity_by_name = {e['name']: e for e in entities}
new_entities = []
for guid, ref in guid_to_ref.items():
    if ref in entity_by_name:
        # Already exists under different GUID - shouldn't happen after dedup
        continue
    
    # Determine type from ref prefix
    etype = 'Entity'
    name = ref
    if ':' in ref:
        prefix, name = ref.split(':', 1)
        type_map = {
            'Concept': 'Concept', 'Deity': 'Deity', 'Person': 'Person',
            'Place': 'Place', 'Avatar': 'Avatar', 'Weapon': 'Weapon',
            'Animal': 'Animal', 'Dynasty': 'Dynasty', 'Ritual': 'Ritual',
            'Nakshatra': 'Nakshatra', 'Graha': 'Graha', 'Loka': 'Loka',
            'School': 'School', 'Teaching': 'Concept', 'Saptarishis': 'Concept'
        }
        etype = type_map.get(prefix, 'Entity')
    
    new_entity = {
        'GUID': guid,
        'name': name,
        'type': etype,
        'entity_type': etype,
        'total_mentions': 0,
        'mentions': 0,
        'sources': [],
        'source_count': 0,
        'provenance': {'phase': 'v9.5', 'method': 'semantic_extraction'},
        'from_ref': ref
    }
    new_entities.append(new_entity)

print(f"New entities to add: {len(new_entities)}")
for ne in new_entities[:20]:
    print(f"  {ne['type']}: {ne['name']} ({ne['from_ref']})")

entities.extend(new_entities)
print(f"Total entities now: {len(entities)}")

# Verify no more broken refs
entity_guids = {e['GUID'] for e in entities}
all_guids = entity_guids | scripture_guids
broken = sum(1 for e in edges if e.get('source_GUID','') not in all_guids or e.get('target_GUID','') not in all_guids)
print(f"Broken references after fix: {broken}")

# Save
with open(os.path.join(GRAPH_DIR, 'nodes/entity_nodes.json'), 'w') as f:
    json.dump(entities, f, indent=2, ensure_ascii=False)

# Update graph.json
all_nodes = scriptures + entities
with open(os.path.join(GRAPH_DIR, 'graph.json'), 'w') as f:
    json.dump({
        'version': '9.5', 'generated': datetime.now().isoformat(),
        'nodes': all_nodes, 'edges': edges,
        'stats': {'total_nodes': len(all_nodes), 'total_edges': len(edges)}
    }, f, indent=2, ensure_ascii=False)

# Update stats
type_breakdown = dict(Counter(n.get('entity_type', n.get('type','')) for n in entities))
edge_type_dist = dict(Counter(e.get('type','') for e in edges))
mentioned_in = [e for e in edges if e['type'] == 'MENTIONED_IN']

entity_guids = {e['GUID'] for e in entities}
connected = set()
for e in edges:
    if e.get('source_GUID') in entity_guids: connected.add(e['source_GUID'])
    if e.get('target_GUID') in entity_guids: connected.add(e['target_GUID'])
orphans = entity_guids - connected

with open(os.path.join(GRAPH_DIR, 'graph_statistics.json'), 'w') as f:
    json.dump({
        'version': '9.5', 'generated': datetime.now().isoformat(), 'phase': 9.5,
        'nodes': {'total': len(all_nodes), 'scriptures': len(scriptures), 'entities': len(entities)},
        'edges': {'total': len(edges), 'by_type': edge_type_dist},
        'entity_breakdown': type_breakdown,
        'orphan_nodes': len(orphans),
        'evidence_coverage_pct': round(sum(1 for n in entities if n.get('sources') or n.get('provenance'))/max(1,len(entities))*100,1)
    }, f, indent=2, ensure_ascii=False)

with open(os.path.join(GRAPH_DIR, 'validation/graph_validation.json'), 'w') as f:
    json.dump({
        'generated': datetime.now().isoformat(), 'phase': '9.5',
        'total_nodes': len(all_nodes), 'total_edges': len(edges),
        'orphan_nodes': len(orphans), 'broken_references': broken,
        'evidence_coverage_pct': round(sum(1 for n in entities if n.get('sources') or n.get('provenance'))/max(1,len(entities))*100,1),
        'edge_type_distribution': edge_type_dist,
        'node_type_distribution': type_breakdown,
        'pass': broken == 0
    }, f, indent=2, ensure_ascii=False)

connected_entities = connected & entity_guids
with open(os.path.join(GRAPH_DIR, 'graph_completeness.json'), 'w') as f:
    json.dump({
        'generated': datetime.now().isoformat(), 'phase': '9.5',
        'total_entities': len(entities),
        'entities_with_relationships': len(connected_entities),
        'relationship_coverage_pct': round(len(connected_entities)/max(1,len(entities))*100,1),
        'total_edges': len(edges)
    }, f, indent=2, ensure_ascii=False)

# Update entity index
entity_index = {n.get('name',''):{'GUID':n['GUID'],'type':n.get('type',''),'mentions':n.get('total_mentions',n.get('mentions',0))} for n in entities}
with open(os.path.join(GRAPH_DIR, 'indexes/entity_index.json'), 'w') as f:
    json.dump(entity_index, f, indent=2, ensure_ascii=False)

# Update CUID index
cuid_index = {n.get('CUID',n.get('name','')):n['GUID'] for n in entities + scriptures if n.get('CUID') or n.get('name')}
with open(os.path.join(GRAPH_DIR, 'cuid_index.json'), 'w') as f:
    json.dump(cuid_index, f, indent=2, ensure_ascii=False)

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
    json.dump({'version':'9.5','generated':datetime.now().isoformat(),'files':manifest_files}, f, indent=2)

print(f"\nFinal: {len(all_nodes)} nodes, {len(edges)} edges, {len(orphans)} orphans, {broken} broken")
