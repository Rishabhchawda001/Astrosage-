"""
Phase 9.5 Step 1: Deduplicate entity nodes and edges.
"""
import json, os
from collections import defaultdict
from datetime import datetime

GRAPH_DIR = "knowledge/graph"

with open(os.path.join(GRAPH_DIR, 'nodes/entity_nodes.json')) as f:
    entities = json.load(f)
with open(os.path.join(GRAPH_DIR, 'edges/relationship_edges.json')) as f:
    edges = json.load(f)
with open(os.path.join(GRAPH_DIR, 'nodes/scripture_nodes.json')) as f:
    scriptures = json.load(f)

print(f"Before dedup: {len(entities)} entities, {len(edges)} edges")

# ── 1. Merge duplicate entity names ──
# For duplicates, keep the one with higher mentions and merge sources
name_groups = defaultdict(list)
for e in entities:
    name_groups[e.get('name', '')].append(e)

merged_entities = []
merged_count = 0
for name, group in name_groups.items():
    if len(group) == 1:
        merged_entities.append(group[0])
    else:
        # Merge: keep highest-mentions, combine sources
        group.sort(key=lambda x: x.get('total_mentions', x.get('mentions', 0)), reverse=True)
        primary = group[0].copy()
        all_sources = set(primary.get('sources', []))
        total_mentions = primary.get('total_mentions', primary.get('mentions', 0))
        for other in group[1:]:
            all_sources.update(other.get('sources', []))
            total_mentions += other.get('total_mentions', other.get('mentions', 0))
        primary['sources'] = list(all_sources)
        primary['total_mentions'] = total_mentions
        primary['mentions'] = total_mentions
        primary['source_count'] = len(all_sources)
        primary['merged_from'] = [e.get('GUID', '') for e in group]
        merged_entities.append(primary)
        merged_count += 1
        print(f"  Merged {len(group)} '{name}' nodes -> {primary['GUID'][:8]}")

print(f"Merged {merged_count} duplicate entity groups")

# ── 2. Build GUID remap for merged entities ──
old_to_new = {}
for e in entities:
    name = e.get('name', '')
    for me in merged_entities:
        if me.get('name') == name:
            old_to_new[e['GUID']] = me['GUID']
            break

# ── 3. Deduplicate edges by (source, target, type) ──
edge_key_set = set()
deduped_edges = []
dup_edges = 0
for e in edges:
    sg = old_to_new.get(e.get('source_GUID', ''), e.get('source_GUID', ''))
    tg = old_to_new.get(e.get('target_GUID', ''), e.get('target_GUID', ''))
    key = (sg, tg, e.get('type', ''))
    if key not in edge_key_set:
        edge_key_set.add(key)
        e['source_GUID'] = sg
        e['target_GUID'] = tg
        deduped_edges.append(e)
    else:
        dup_edges += 1

print(f"Removed {dup_edges} duplicate edges")
print(f"After dedup: {len(merged_entities)} entities, {len(deduped_edges)} edges")

# ── 4. Update GUIDs in edges ──
for e in deduped_edges:
    e['source_GUID'] = old_to_new.get(e['source_GUID'], e['source_GUID'])
    e['target_GUID'] = old_to_new.get(e['target_GUID'], e['target_GUID'])

# ── 5. Verify no orphans after merge ──
entity_guids = {e['GUID'] for e in merged_entities}
scripture_guids = {s['GUID'] for s in scriptures}
connected = set()
for e in deduped_edges:
    if e.get('source_GUID') in entity_guids: connected.add(e['source_GUID'])
    if e.get('target_GUID') in entity_guids: connected.add(e['target_GUID'])
orphans = entity_guids - connected
print(f"Orphans after dedup: {len(orphans)}")

# ── 6. Save ──
with open(os.path.join(GRAPH_DIR, 'nodes/entity_nodes.json'), 'w') as f:
    json.dump(merged_entities, f, indent=2, ensure_ascii=False)
with open(os.path.join(GRAPH_DIR, 'edges/relationship_edges.json'), 'w') as f:
    json.dump(deduped_edges, f, indent=2, ensure_ascii=False)

# Update graph.json
all_nodes = scriptures + merged_entities
with open(os.path.join(GRAPH_DIR, 'graph.json'), 'w') as f:
    json.dump({
        'version': '9.5', 'generated': datetime.now().isoformat(),
        'nodes': all_nodes, 'edges': deduped_edges,
        'stats': {'total_nodes': len(all_nodes), 'total_edges': len(deduped_edges)}
    }, f, indent=2, ensure_ascii=False)

print("Deduplication complete")
