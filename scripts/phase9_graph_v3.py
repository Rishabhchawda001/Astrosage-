"""
Phase 9 Graph Builder v3: Correct node merging.
"""
import json, os, uuid, re
from collections import defaultdict
from datetime import datetime

GRAPH_DIR = "knowledge/graph"

def make_guid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"astrosage.v9.{name}"))

with open(os.path.join(GRAPH_DIR, 'complete_entity_extraction_v9.json')) as f:
    extraction = json.load(f)
with open(os.path.join(GRAPH_DIR, 'nodes/entity_nodes.json')) as f:
    old_entities = json.load(f)
with open(os.path.join(GRAPH_DIR, 'nodes/scripture_nodes.json')) as f:
    old_scriptures = json.load(f)

print(f"Loaded: {len(extraction['entities'])} v9, {len(old_entities)} old entities, {len(old_scriptures)} scriptures")

# ── Build nodes list properly ──
nodes = []
guid_map = {}

# 1. Scripture nodes
for s in old_scriptures:
    nodes.append(s)
    sid = s.get('id', s.get('canonical_name',''))
    guid_map[sid] = s['GUID']

# 2. Old entity nodes — add them
old_name_to_node = {}
for e in old_entities:
    nodes.append(e)
    name = e.get('name', '')
    guid_map[name] = e['GUID']
    old_name_to_node[name] = e

# 3. New v9 entities — merge with old or add new
v9_new_count = 0
for key, info in extraction.get('entities', {}).items():
    name = info.get('name', key.split(':')[-1])
    if name in old_name_to_node:
        # Update existing node with v9 data
        node = old_name_to_node[name]
        node['mentions_v9'] = info.get('mentions', 0)
        node['sources_v9'] = info.get('sources', [])
        node['source_count_v9'] = info.get('source_count', 0)
        guid_map[key] = node['GUID']
    else:
        # New entity node
        guid = make_guid(key)
        node = {
            'GUID': guid,
            'name': name,
            'type': info.get('type', 'Entity'),
            'entity_type': info.get('type', 'unknown'),
            'total_mentions': info.get('mentions', 0),
            'sources': info.get('sources', []),
            'source_count': info.get('source_count', 0),
            'provenance': {'phase': 'v9', 'method': 'pattern_match'}
        }
        nodes.append(node)
        guid_map[key] = guid
        guid_map[name] = guid
        v9_new_count += 1

entity_nodes = [n for n in nodes if n.get('type','') not in ('Scripture','') and n.get('node_type','') != 'Scripture']
scripture_nodes = [n for n in nodes if n.get('node_type','') == 'Scripture' or n.get('type','') == 'Scripture']
print(f"Nodes: {len(nodes)} total ({len(scripture_nodes)} scriptures, {len(entity_nodes)} entities, {v9_new_count} new v9)")

# ── MENTIONED_IN edges ──
mentioned_edges = []
for key, info in extraction.get('entities', {}).items():
    entity_guid = guid_map.get(key) or guid_map.get(info.get('name',''))
    if not entity_guid:
        continue
    for source_title in info.get('sources', []):
        matched_guid = None
        for s in old_scriptures:
            cn = s.get('canonical_name', '').lower()
            st = source_title.lower().strip()
            if cn in st or st in cn:
                matched_guid = s['GUID']
                break
            words = re.findall(r'[a-z]{5,}', st)
            if any(w in cn for w in words):
                matched_guid = s['GUID']
                break
        if matched_guid:
            mentioned_edges.append({
                'GUID': make_guid(f"m-{key}-{matched_guid[:8]}"),
                'type': 'MENTIONED_IN',
                'source_GUID': entity_guid,
                'target_GUID': matched_guid,
                'evidence': {'entity': info.get('name',''), 'scripture': source_title, 'mentions': info.get('mentions',0)},
                'confidence': 90, 'phase': 'v9'
            })

# Keep Phase 8 MENTIONED_IN edges
with open(os.path.join(GRAPH_DIR, 'edges/relationship_edges.json')) as f:
    old_edges = json.load(f)
p8_mentioned = [e for e in old_edges if e['type'] == 'MENTIONED_IN']
all_mentioned = mentioned_edges + p8_mentioned

# ── Relationship edges ──
RELS = [
    ("Person:Dasharatha","FATHER_OF","Deity:Rama"),
    ("Person:Dasharatha","FATHER_OF","Person:Bharata (king)"),
    ("Person:Dasharatha","FATHER_OF","Person:Lakshmana"),
    ("Person:Dasharatha","FATHER_OF","Person:Shatrughna"),
    ("Deity:Rama","HUSBAND_OF","Person:Sita"),
    ("Deity:Rama","FATHER_OF","Person:Lava"),
    ("Deity:Rama","FATHER_OF","Person:Kusha"),
    ("Person:Lakshmana","BROTHER_OF","Deity:Rama"),
    ("Person:Sita","DAUGHTER_OF","Person:Janaka"),
    ("Person:Pandu","FATHER_OF","Person:Yudhishthira"),
    ("Person:Pandu","FATHER_OF","Person:Bhima"),
    ("Person:Pandu","FATHER_OF","Person:Arjuna"),
    ("Person:Pandu","FATHER_OF","Person:Nakula"),
    ("Person:Pandu","FATHER_OF","Person:Sahadeva"),
    ("Person:Dhritarashtra","FATHER_OF","Person:Duryodhana"),
    ("Person:Yudhishthira","HUSBAND_OF","Person:Draupadi"),
    ("Person:Bhima","HUSBAND_OF","Person:Draupadi"),
    ("Person:Arjuna","HUSBAND_OF","Person:Draupadi"),
    ("Person:Arjuna","HUSBAND_OF","Person:Subhadra"),
    ("Person:Arjuna","FATHER_OF","Person:Abhimanyu"),
    ("Person:Bhima","FATHER_OF","Person:Ghatotkacha"),
    ("Person:Kunti","MOTHER_OF","Person:Yudhishthira"),
    ("Person:Kunti","MOTHER_OF","Person:Bhima"),
    ("Person:Kunti","MOTHER_OF","Person:Arjuna"),
    ("Person:Karna","BROTHER_OF","Person:Yudhishthira"),
    ("Person:Karna","BROTHER_OF","Person:Bhima"),
    ("Person:Karna","BROTHER_OF","Person:Arjuna"),
    ("Deity:Krishna","HUSBAND_OF","Person:Subhadra"),
    ("Deity:Balarama","BROTHER_OF","Deity:Krishna"),
    ("Person:Subhadra","SISTER_OF","Deity:Krishna"),
    ("Person:Vasistha","TEACHER_OF","Deity:Rama"),
    ("Person:Vishvamitra","TEACHER_OF","Deity:Rama"),
    ("Person:Drona","TEACHER_OF","Person:Arjuna"),
    ("Person:Drona","TEACHER_OF","Person:Duryodhana"),
    ("Person:Bhishma","GUARDIAN_OF","Person:Yudhishthira"),
    ("Person:Vibhishana","BROTHER_OF","Person:Ravana"),
    ("Person:Kumbhakarna","BROTHER_OF","Person:Ravana"),
    ("Person:Surpanakha","SISTER_OF","Person:Ravana"),
    ("Person:Ravana","RULER_OF","Place:Lanka"),
    ("Deity:Surya","FATHER_OF","Person:Karna"),
    ("Deity:Chandra","ANCESTOR_OF","Person:Yudhishthira"),
    ("Deity:Brahma","CREATOR_OF","Deity:Saraswati"),
    ("Deity:Brahma","CREATOR_OF","Deity:Surya"),
    ("Deity:Brahma","CREATOR_OF","Deity:Chandra"),
    ("Deity:Shiva","HUSBAND_OF","Deity:Parvati"),
    ("Deity:Shiva","FATHER_OF","Deity:Kartikeya"),
    ("Deity:Shiva","FATHER_OF","Deity:Ganesha"),
    ("Deity:Parvati","MOTHER_OF","Deity:Kartikeya"),
    ("Deity:Parvati","MOTHER_OF","Deity:Ganesha"),
    ("Deity:Vishnu","INCARNATION_OF","Avatar:Matsya Avatar"),
    ("Deity:Vishnu","INCARNATION_OF","Avatar:Kurma Avatar"),
    ("Deity:Vishnu","INCARNATION_OF","Avatar:Varaha Avatar"),
    ("Deity:Vishnu","INCARNATION_OF","Avatar:Narasimha Avatar"),
    ("Deity:Vishnu","INCARNATION_OF","Avatar:Vamana Avatar"),
    ("Deity:Vishnu","INCARNATION_OF","Person:Rama"),
    ("Deity:Vishnu","INCARNATION_OF","Deity:Krishna"),
    ("Deity:Vishnu","INCARNATION_OF","Avatar:Parashurama"),
    ("Person:Veda Vyasa","COMPILER_OF","Concept:Vedanta"),
    ("Person:Narada","SON_OF","Deity:Brahma"),
    ("Person:Narada","STUDENT_OF","Deity:Brahma"),
    ("Person:Vasistha","TEACHER_OF","Person:Vishvamitra"),
    ("Concept:Bhakti","PATH_TO","Concept:Moksha"),
    ("Concept:Jnana","PATH_TO","Concept:Moksha"),
    ("Concept:Yoga","PATH_TO","Concept:Moksha"),
    ("Concept:Karma","LEADS_TO","Concept:Samsara"),
    ("Concept:Moksha","LIBERATION_FROM","Concept:Samsara"),
    ("Concept:Brahman","IDENTICAL_TO","Concept:Atman"),
    ("Concept:Dharma","GUIDES","Concept:Karma"),
    ("Place:Meru","CENTER_OF","Loka:Bhuloka"),
    ("Place:Vaikuntha","ABODE_OF","Deity:Vishnu"),
    ("Place:Kailas","ABODE_OF","Deity:Shiva"),
    ("Place:Hastinapura","CAPITAL_OF","Dynasty:Kuru Dynasty"),
    ("Place:Indraprastha","CAPITAL_OF","Dynasty:Pandava Dynasty"),
    ("Place:Kurukshetra","BATTLEFIELD_OF","Person:Arjuna"),
    ("Place:Lanka","KINGDOM_OF","Person:Ravana"),
    ("Weapon:Gandiva","WIELDED_BY","Person:Arjuna"),
    ("Weapon:Chakra","WIELDED_BY","Deity:Vishnu"),
    ("Weapon:Trident","WIELDED_BY","Deity:Shiva"),
    ("Weapon:Vajra","WIELDED_BY","Deity:Indra"),
    ("Weapon:Brahmastra","WIELDED_BY","Person:Arjuna"),
    ("Weapon:Parashu","WIELDED_BY","Avatar:Parashurama"),
    ("Weapon:Sharnga","WIELDED_BY","Deity:Vishnu"),
    ("Weapon:Sudarshana","WIELDED_BY","Deity:Vishnu"),
    ("Weapon:Pinaka","WIELDED_BY","Deity:Shiva"),
    ("Animal:Garuda","VEHICLE_OF","Deity:Vishnu"),
    ("Animal:Nandi","VEHICLE_OF","Deity:Shiva"),
    ("Animal:Swan","VEHICLE_OF","Deity:Brahma"),
    ("Animal:Hamsa","VEHICLE_OF","Deity:Brahma"),
    ("Animal:Peacock","VEHICLE_OF","Deity:Kartikeya"),
]

rel_edges = []
skipped = 0
for src, rel, tgt in RELS:
    src_guid = guid_map.get(src)
    tgt_guid = guid_map.get(tgt)
    if src_guid and tgt_guid:
        rel_edges.append({
            'GUID': make_guid(f"r-{src}-{rel}-{tgt}"),
            'type': rel, 'source_GUID': src_guid, 'target_GUID': tgt_guid,
            'source_ref': src, 'target_ref': tgt,
            'evidence': 'canonical_scripture', 'confidence': 95, 'phase': 'v9'
        })
    else:
        skipped += 1

old_rel = [e for e in old_edges if e['type'] not in ('MENTIONED_IN',)]
all_edges = all_mentioned + rel_edges + old_rel
print(f"Edges: {len(all_edges)} (MENTIONED_IN: {len(all_mentioned)}, relationships: {len(rel_edges)+len(old_rel)}, skipped: {skipped})")

# ── QA ──
node_guids = set(n['GUID'] for n in nodes)
connected = set()
for e in all_edges:
    sg = e.get('source_GUID','')
    tg = e.get('target_GUID','')
    if sg in node_guids: connected.add(sg)
    if tg in node_guids: connected.add(tg)
orphans = node_guids - connected
broken = sum(1 for e in all_edges if e.get('source_GUID') not in node_guids or e.get('target_GUID') not in node_guids)

# ── Sub-graphs ──
dialogue_edges = [e for e in all_edges if e['type'] in ('TEACHER_OF','STUDENT_OF')]
genealogy_edges = [e for e in all_edges if e['type'] in ('FATHER_OF','MOTHER_OF','SON_OF','DAUGHTER_OF','HUSBAND_OF','BROTHER_OF','SISTER_OF','ANCESTOR_OF','INCARNATION_OF')]
concept_edges = [e for e in all_edges if e['type'] in ('PATH_TO','LEADS_TO','GUIDES','IDENTICAL_TO','LIBERATION_FROM')]
geo_edges = [e for e in all_edges if e['type'] in ('LOCATED_IN','ABODE_OF','CAPITAL_OF','CENTER_OF','BATTLEFIELD_OF','KINGDOM_OF','RULER_OF')]
assoc_edges = [e for e in all_edges if e['type'] in ('WIELDED_BY','VEHICLE_OF','CREATOR_OF')]

events = [
    {'name':'Mahabharata War','participants':['Arjuna','Duryodhana','Bhishma','Drona','Krishna'],'location':'Kurukshetra'},
    {'name':'Sita Swayamvara','participants':['Rama','Sita','Janaka'],'location':'Mithila'},
    {'name':'Samudra Manthan','participants':['Devas','Asuras','Vishnu','Shiva'],'location':'Kshirasagara'},
    {'name':'Daksha Yajna','participants':['Shiva','Sati','Daksha'],'location':'Kailasa'},
    {'name':'Bhagavad Gita Teaching','participants':['Krishna','Arjuna'],'location':'Kurukshetra'},
    {'name':'Churning of Milk Ocean','participants':['Vishnu','Shesha','Devas','Asuras'],'location':'Kshirasagara'},
    {'name':'Rama Exile','participants':['Rama','Lakshmana','Sita','Dasharatha'],'location':'Dandakaranya'},
    {'name':'Burning of Khandava','participants':['Arjuna','Krishna','Agni'],'location':'Khandava'},
    {'name':'Gajendra Moksha','participants':['Gajendra','Vishnu'],'location':'Bhuloka'},
    {'name':'Draupadi Vastraharana','participants':['Draupadi','Duryodhana','Bhishma'],'location':'Hastinapura'},
    {'name':'Hanuman Leap to Lanka','participants':['Hanuman','Ravana'],'location':'Lanka'},
    {'name':'Killing of Ravana','participants':['Rama','Hanuman','Ravana'],'location':'Lanka'},
    {'name':'Narasimha Avatar','participants':['Narasimha','Prahlada','Hiranyakashipu'],'location':'Bhuloka'},
    {'name':'Vamana Avatar','participants':['Vamana','Bali','Indra'],'location':'Bhuloka'},
    {'name':'Shakuntala Story','participants':['Shakuntala','Dushyanta'],'location':'Kanvashrama'},
]

concept_nodes = [n for n in entity_nodes if n.get('type','') == 'Concept' or n.get('entity_type','') == 'Concept']
ritual_nodes = [n for n in entity_nodes if n.get('type','') == 'Ritual']
astro_nodes = [n for n in entity_nodes if n.get('type','') in ('Nakshatra','Graha')]
geo_nodes = [n for n in entity_nodes if n.get('type','') == 'Place']

subgraphs = {
    'dialogue_graph': {'type':'dialogue_graph','edges':dialogue_edges,'stats':{'total':len(dialogue_edges)}},
    'genealogy_graph': {'type':'genealogy_graph','edges':genealogy_edges,'stats':{'total':len(genealogy_edges)}},
    'concept_graph': {'type':'concept_graph','edges':concept_edges,
                       'nodes':[{'name':n.get('name',''),'GUID':n['GUID']} for n in concept_nodes],
                       'stats':{'edges':len(concept_edges),'nodes':len(concept_nodes)}},
    'geography_graph': {'type':'geography_graph','edges':geo_edges,
                         'nodes':[{'name':n.get('name',''),'GUID':n['GUID'],'mentions':n.get('total_mentions',n.get('mentions',0))} for n in geo_nodes],
                         'stats':{'edges':len(geo_edges),'nodes':len(geo_nodes)}},
    'ritual_graph': {'type':'ritual_graph',
                      'nodes':[{'name':n.get('name',''),'GUID':n['GUID'],'mentions':n.get('total_mentions',n.get('mentions',0))} for n in ritual_nodes],
                      'stats':{'nodes':len(ritual_nodes)}},
    'astronomy_graph': {'type':'astronomy_graph',
                         'nodes':[{'name':n.get('name',''),'GUID':n['GUID'],'type':n.get('type',''),'mentions':n.get('total_mentions',n.get('mentions',0))} for n in astro_nodes],
                         'stats':{'nodes':len(astro_nodes)}},
    'association_graph': {'type':'association_graph','edges':assoc_edges,'stats':{'total':len(assoc_edges)}},
    'event_graph': {'type':'event_graph','events':events,'stats':{'total':len(events)}},
}

# ── Stats ──
type_counts = defaultdict(int)
edge_type_counts = defaultdict(int)
total_mentions = 0
for n in nodes:
    t = n.get('entity_type', n.get('type','Scripture'))
    type_counts[t] += 1
    total_mentions += n.get('total_mentions', n.get('mentions', 0))
for e in all_edges:
    edge_type_counts[e['type']] += 1

prov_count = sum(1 for n in nodes if n.get('sources') or n.get('sources_v9') or n.get('provenance'))

stats = {
    'version': '9.0', 'generated': datetime.now().isoformat(), 'phase': 9,
    'nodes': {'total': len(nodes), 'scriptures': type_counts.get('Scripture',0), 'entities': len(nodes)-type_counts.get('Scripture',0)},
    'edges': {'total': len(all_edges), 'by_type': dict(edge_type_counts)},
    'entity_breakdown': {k:v for k,v in sorted(type_counts.items(), key=lambda x:-x[1])},
    'total_mentions': total_mentions, 'files_scanned': extraction.get('files_scanned',0),
    'orphan_nodes': len(orphans), 'evidence_coverage_pct': round(prov_count/len(nodes)*100,1)
}

entity_guids = set(n['GUID'] for n in entity_nodes)
connected_entities = connected & entity_guids

qa = {
    'generated': datetime.now().isoformat(),
    'total_nodes': len(nodes), 'total_edges': len(all_edges),
    'orphan_nodes': len(orphans), 'broken_references': broken,
    'duplicate_guids': len([n['GUID'] for n in nodes]) - len(set(n['GUID'] for n in nodes)),
    'evidence_coverage_pct': stats['evidence_coverage_pct'],
    'entities_with_provenance': prov_count,
    'edge_type_distribution': dict(edge_type_counts),
    'node_type_distribution': dict(type_counts),
    'pass': broken == 0
}

comp = {
    'generated': datetime.now().isoformat(),
    'total_entities': len(entity_nodes),
    'entities_with_relationships': len(connected_entities),
    'relationship_coverage_pct': round(len(connected_entities)/max(1,len(entity_nodes))*100,1),
    'total_edges': len(all_edges), 'edge_types': dict(edge_type_counts)
}

# ── Save ──
with open(os.path.join(GRAPH_DIR, 'nodes/entity_nodes.json'), 'w') as f:
    json.dump(entity_nodes, f, indent=2, ensure_ascii=False)
with open(os.path.join(GRAPH_DIR, 'nodes/scripture_nodes.json'), 'w') as f:
    json.dump(scripture_nodes, f, indent=2, ensure_ascii=False)
with open(os.path.join(GRAPH_DIR, 'edges/relationship_edges.json'), 'w') as f:
    json.dump(all_edges, f, indent=2, ensure_ascii=False)
with open(os.path.join(GRAPH_DIR, 'graph.json'), 'w') as f:
    json.dump({'version':'9.0','generated':datetime.now().isoformat(),'nodes':nodes,'edges':all_edges,'stats':{'total_nodes':len(nodes),'total_edges':len(all_edges)}}, f, indent=2, ensure_ascii=False)
with open(os.path.join(GRAPH_DIR, 'graph_statistics.json'), 'w') as f:
    json.dump(stats, f, indent=2, ensure_ascii=False)
with open(os.path.join(GRAPH_DIR, 'validation/graph_validation.json'), 'w') as f:
    json.dump(qa, f, indent=2, ensure_ascii=False)
with open(os.path.join(GRAPH_DIR, 'graph_completeness.json'), 'w') as f:
    json.dump(comp, f, indent=2, ensure_ascii=False)
with open(os.path.join(GRAPH_DIR, 'review_queue.json'), 'w') as f:
    rq = []
    if orphans: rq.append({'type':'warning','description':f'{len(orphans)} orphan nodes','severity':'medium'})
    json.dump(rq, f, indent=2)
for name, sg in subgraphs.items():
    with open(os.path.join(GRAPH_DIR, f'{name}.json'), 'w') as f:
        json.dump(sg, f, indent=2, ensure_ascii=False)
cuid_index = {n.get('CUID',n.get('name','')):n['GUID'] for n in nodes if n.get('CUID') or n.get('name')}
with open(os.path.join(GRAPH_DIR, 'cuid_index.json'), 'w') as f:
    json.dump(cuid_index, f, indent=2, ensure_ascii=False)
entity_index = {n.get('name',''):{'GUID':n['GUID'],'type':n.get('type',''),'mentions':n.get('total_mentions',n.get('mentions',0))} for n in entity_nodes}
with open(os.path.join(GRAPH_DIR, 'indexes/entity_index.json'), 'w') as f:
    json.dump(entity_index, f, indent=2, ensure_ascii=False)
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

print(f"\n{'='*60}")
print(f"Phase 9 Knowledge Graph v9.0")
print(f"{'='*60}")
print(f"Nodes: {len(nodes)} ({type_counts.get('Scripture',0)} scriptures, {len(entity_nodes)} entities)")
print(f"Edges: {len(all_edges)} (MENTIONED_IN: {edge_type_counts.get('MENTIONED_IN',0)}, relationships: {sum(v for k,v in edge_type_counts.items() if k!='MENTIONED_IN')})")
print(f"Orphan nodes: {len(orphans)}")
print(f"Broken refs: {broken}")
print(f"Evidence: {stats['evidence_coverage_pct']}%")
print(f"Relationship coverage: {comp['relationship_coverage_pct']}%")
print(f"\nEntity breakdown:")
for t, c in sorted(type_counts.items(), key=lambda x:-x[1]):
    print(f"  {t}: {c}")
print(f"\nEdge breakdown:")
for t, c in sorted(edge_type_counts.items(), key=lambda x:-x[1]):
    print(f"  {t}: {c}")
