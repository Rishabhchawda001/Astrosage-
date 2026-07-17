"""
Phase 9 Graph Builder v2: Merge Phase 8 foundation + v9 relationships.
"""
import json, os, uuid, re
from collections import defaultdict
from datetime import datetime

GRAPH_DIR = "knowledge/graph"

def make_guid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"astrosage.v9.{name}"))

# ── Load all inputs ──
with open(os.path.join(GRAPH_DIR, 'complete_entity_extraction_v9.json')) as f:
    extraction = json.load(f)
with open(os.path.join(GRAPH_DIR, 'nodes/entity_nodes.json')) as f:
    old_entities = json.load(f)
with open(os.path.join(GRAPH_DIR, 'nodes/scripture_nodes.json')) as f:
    old_scriptures = json.load(f)
with open(os.path.join(GRAPH_DIR, 'edges/relationship_edges.json')) as f:
    old_edges = json.load(f)

print(f"Loaded: {len(extraction['entities'])} v9 entities, {len(old_entities)} old entities, {len(old_scriptures)} scriptures, {len(old_edges)} old edges")

# ── Build entity GUID map (merge old + new) ──
guid_map = {}
nodes = []

# Scripture nodes: keep old
for s in old_scriptures:
    guid_map[s['id']] = s['GUID']
    nodes.append(s)

# Entity nodes: merge — keep old ones with proper GUID, add new ones
old_name_map = {}
for e in old_entities:
    name = e.get('name', '')
    old_name_map[name] = e
    guid_map[name] = e['GUID']

# Add v9 entities that are new
for key, info in extraction.get('entities', {}).items():
    name = info.get('name', key.split(':')[-1])
    if name in old_name_map:
        # Update existing
        old_e = old_name_map[name]
        old_e['total_mentions'] = info.get('mentions', old_e.get('mentions', 0))
        old_e['source_count'] = info.get('source_count', old_e.get('source_count', 0))
        old_e['sources_v9'] = info.get('sources', [])
        guid_map[key] = old_e['GUID']
    else:
        # New entity
        guid = make_guid(key)
        node = {
            'GUID': guid,
            'name': name,
            'type': info.get('type', 'Entity'),
            'entity_type': info.get('type', 'unknown'),
            'mentions': info.get('mentions', 0),
            'total_mentions': info.get('mentions', 0),
            'sources': info.get('sources', []),
            'source_count': info.get('source_count', 0),
            'provenance': {'phase': 'v9', 'extraction': 'pattern_match'}
        }
        nodes.append(node)
        guid_map[key] = guid
        guid_map[name] = guid

entity_count = sum(1 for n in nodes if n.get('type', n.get('entity_type', '')) != 'Scripture')
print(f"Total nodes: {len(nodes)} ({entity_count} entities)")

# ── Build MENTIONED_IN edges using v9 source matching ──
# Build a mapping: scripture title -> scripture GUID
title_to_guid = {}
for s in old_scriptures:
    title = s.get('canonical_name', s.get('id', ''))
    title_to_guid[title] = s['GUID']
    title_to_guid[s.get('id','')] = s['GUID']

# Also map common abbreviations
abbr_map = {
    'AGNI': 'AGNI', 'AITAREYA': 'AITAREYA', 'APASTAMBA_DS': 'APASTAMBA_DS',
    'AV': 'AV', 'BAUDHAYANA_DS': 'BAUDHAYANA_DS', 'BHAG': 'BHAG',
    'BRAH': 'BRAH', 'BRAHMD': 'BRAHMD', 'BRIHAD': 'BRIHAD',
    'CHAND': 'CHAND', 'DEVI': 'DEVI', 'GARUDA': 'GARUDA',
    'HV': 'HV', 'KALI': 'KALI', 'KAUS': 'KAUS', 'KURM': 'KURM',
    'MALINI': 'MALINI', 'MANUSM': 'MANUSM', 'MARK': 'MARK',
    'NARAD': 'NARAD', 'NIRUKTA': 'NIRUKTA', 'PANCAV': 'PANCAV',
    'RGVEDA': 'RGVEDA', 'SAVEDA': 'SAVEDA', 'SHAT': 'SHAT',
    'SHIVAP': 'SHIVAP', 'SKANDAP': 'SKANDAP', 'TITIRI': 'TITIRI',
    'VAMANAP': 'VAMANAP', 'VASISTH_DS': 'VASISTH_DS',
    'VISHNU': 'VISHNU', 'VISHNU_SM': 'VISHNU_SM',
}

# Title -> scripture ID matching
title_to_id = {}
for s in old_scriptures:
    title_to_id[s.get('canonical_name','')] = s.get('id','')
    # Try partial matching
    cn = s.get('canonical_name', '').lower()
    title_to_id[cn] = s.get('id','')

# Match v9 sources to scriptures
mentioned_edges = []
entity_keys = set(extraction.get('entities', {}).keys())

for key, info in extraction.get('entities', {}).items():
    entity_guid = guid_map.get(key)
    if not entity_guid:
        continue
    for source_title in info.get('sources', []):
        # Find matching scripture GUID
        matched_guid = None
        for s in old_scriptures:
            cn = s.get('canonical_name', '').lower()
            sid = s.get('id', '').lower()
            st = source_title.lower().strip()
            # Match if the source title contains the canonical name or vice versa
            if cn in st or st in cn or sid in st or st in sid:
                matched_guid = s['GUID']
                break
            # Fuzzy: check key words
            words = re.findall(r'[a-z]+', st)
            if any(w in cn for w in words if len(w) > 4):
                matched_guid = s['GUID']
                break
        if matched_guid:
            edge = {
                'GUID': make_guid(f"m-{key}-{matched_guid[:8]}"),
                'type': 'MENTIONED_IN',
                'source_GUID': entity_guid,
                'target_GUID': matched_guid,
                'evidence': {'entity': info.get('name',''), 'scripture': source_title, 'mentions': info.get('mentions',0)},
                'confidence': 90,
                'phase': 'v9'
            }
            mentioned_edges.append(edge)

# Keep Phase 8 MENTIONED_IN edges that don't conflict
p8_mentioned = [e for e in old_edges if e['type'] == 'MENTIONED_IN']
# Merge: add v9 edges, keep p8 edges that aren't duplicated
all_mentioned = mentioned_edges + p8_mentioned
print(f"MENTIONED_IN edges: {len(mentioned_edges)} (new) + {len(p8_mentioned)} (phase 8)")

# ── Relationship edges ──
RELATIONSHIPS = [
    ("Person:Dasharatha", "FATHER_OF", "Deity:Rama"),
    ("Person:Dasharatha", "FATHER_OF", "Person:Bharata (king)"),
    ("Person:Dasharatha", "FATHER_OF", "Person:Lakshmana"),
    ("Person:Dasharatha", "FATHER_OF", "Person:Shatrughna"),
    ("Deity:Rama", "HUSBAND_OF", "Person:Sita"),
    ("Deity:Rama", "FATHER_OF", "Person:Lava"),
    ("Deity:Rama", "FATHER_OF", "Person:Kusha"),
    ("Person:Lakshmana", "BROTHER_OF", "Deity:Rama"),
    ("Person:Sita", "DAUGHTER_OF", "Person:Janaka"),
    ("Person:Pandu", "FATHER_OF", "Person:Yudhishthira"),
    ("Person:Pandu", "FATHER_OF", "Person:Bhima"),
    ("Person:Pandu", "FATHER_OF", "Person:Arjuna"),
    ("Person:Pandu", "FATHER_OF", "Person:Nakula"),
    ("Person:Pandu", "FATHER_OF", "Person:Sahadeva"),
    ("Person:Dhritarashtra", "FATHER_OF", "Person:Duryodhana"),
    ("Person:Yudhishthira", "HUSBAND_OF", "Person:Draupadi"),
    ("Person:Bhima", "HUSBAND_OF", "Person:Draupadi"),
    ("Person:Arjuna", "HUSBAND_OF", "Person:Draupadi"),
    ("Person:Arjuna", "HUSBAND_OF", "Person:Subhadra"),
    ("Person:Arjuna", "FATHER_OF", "Person:Abhimanyu"),
    ("Person:Bhima", "FATHER_OF", "Person:Ghatotkacha"),
    ("Person:Kunti", "MOTHER_OF", "Person:Yudhishthira"),
    ("Person:Kunti", "MOTHER_OF", "Person:Bhima"),
    ("Person:Kunti", "MOTHER_OF", "Person:Arjuna"),
    ("Person:Karna", "BROTHER_OF", "Person:Yudhishthira"),
    ("Person:Karna", "BROTHER_OF", "Person:Bhima"),
    ("Person:Karna", "BROTHER_OF", "Person:Arjuna"),
    ("Deity:Krishna", "HUSBAND_OF", "Person:Subhadra"),
    ("Deity:Balarama", "BROTHER_OF", "Deity:Krishna"),
    ("Person:Subhadra", "SISTER_OF", "Deity:Krishna"),
    ("Person:Vasistha", "TEACHER_OF", "Deity:Rama"),
    ("Person:Vishvamitra", "TEACHER_OF", "Deity:Rama"),
    ("Person:Drona", "TEACHER_OF", "Person:Arjuna"),
    ("Person:Drona", "TEACHER_OF", "Person:Duryodhana"),
    ("Person:Bhishma", "GUARDIAN_OF", "Person:Yudhishthira"),
    ("Person:Vibhishana", "BROTHER_OF", "Person:Ravana"),
    ("Person:Kumbhakarna", "BROTHER_OF", "Person:Ravana"),
    ("Person:Surpanakha", "SISTER_OF", "Person:Ravana"),
    ("Person:Ravana", "RULER_OF", "Place:Lanka"),
    ("Deity:Surya", "FATHER_OF", "Person:Karna"),
    ("Deity:Chandra", "ANCESTOR_OF", "Person:Yudhishthira"),
    ("Deity:Brahma", "CREATOR_OF", "Deity:Saraswati"),
    ("Deity:Brahma", "CREATOR_OF", "Deity:Surya"),
    ("Deity:Brahma", "CREATOR_OF", "Deity:Chandra"),
    ("Deity:Shiva", "HUSBAND_OF", "Deity:Parvati"),
    ("Deity:Shiva", "FATHER_OF", "Deity:Kartikeya"),
    ("Deity:Shiva", "FATHER_OF", "Deity:Ganesha"),
    ("Deity:Parvati", "MOTHER_OF", "Deity:Kartikeya"),
    ("Deity:Parvati", "MOTHER_OF", "Deity:Ganesha"),
    ("Deity:Vishnu", "INCARNATION_OF", "Avatar:Matsya Avatar"),
    ("Deity:Vishnu", "INCARNATION_OF", "Avatar:Kurma Avatar"),
    ("Deity:Vishnu", "INCARNATION_OF", "Avatar:Varaha Avatar"),
    ("Deity:Vishnu", "INCARNATION_OF", "Avatar:Narasimha Avatar"),
    ("Deity:Vishnu", "INCARNATION_OF", "Avatar:Vamana Avatar"),
    ("Deity:Vishnu", "INCARNATION_OF", "Person:Rama"),
    ("Deity:Vishnu", "INCARNATION_OF", "Deity:Krishna"),
    ("Deity:Vishnu", "INCARNATION_OF", "Avatar:Parashurama"),
    ("Person:Veda Vyasa", "COMPILER_OF", "Concept:Vedanta"),
    ("Person:Narada", "SON_OF", "Deity:Brahma"),
    ("Person:Narada", "STUDENT_OF", "Deity:Brahma"),
    ("Person:Vasistha", "TEACHER_OF", "Person:Vishvamitra"),
    ("Concept:Bhakti", "PATH_TO", "Concept:Moksha"),
    ("Concept:Jnana", "PATH_TO", "Concept:Moksha"),
    ("Concept:Yoga", "PATH_TO", "Concept:Moksha"),
    ("Concept:Karma", "LEADS_TO", "Concept:Samsara"),
    ("Concept:Moksha", "LIBERATION_FROM", "Concept:Samsara"),
    ("Concept:Brahman", "IDENTICAL_TO", "Concept:Atman"),
    ("Concept:Dharma", "GUIDES", "Concept:Karma"),
    ("Place:Meru", "CENTER_OF", "Loka:Bhuloka"),
    ("Place:Vaikuntha", "ABODE_OF", "Deity:Vishnu"),
    ("Place:Kailas", "ABODE_OF", "Deity:Shiva"),
    ("Place:Hastinapura", "CAPITAL_OF", "Dynasty:Kuru Dynasty"),
    ("Place:Indraprastha", "CAPITAL_OF", "Dynasty:Pandava Dynasty"),
    ("Place:Kurukshetra", "BATTLEFIELD_OF", "Person:Arjuna"),
    ("Place:Lanka", "KINGDOM_OF", "Person:Ravana"),
    ("Weapon:Gandiva", "WIELDED_BY", "Person:Arjuna"),
    ("Weapon:Chakra", "WIELDED_BY", "Deity:Vishnu"),
    ("Weapon:Trident", "WIELDED_BY", "Deity:Shiva"),
    ("Weapon:Vajra", "WIELDED_BY", "Deity:Indra"),
    ("Weapon:Brahmastra", "WIELDED_BY", "Person:Arjuna"),
    ("Weapon:Parashu", "WIELDED_BY", "Avatar:Parashurama"),
    ("Weapon:Sharnga", "WIELDED_BY", "Deity:Vishnu"),
    ("Weapon:Sudarshana", "WIELDED_BY", "Deity:Vishnu"),
    ("Weapon:Pinaka", "WIELDED_BY", "Deity:Shiva"),
    ("Animal:Garuda", "VEHICLE_OF", "Deity:Vishnu"),
    ("Animal:Nandi", "VEHICLE_OF", "Deity:Shiva"),
    ("Animal:Swan", "VEHICLE_OF", "Deity:Brahma"),
    ("Animal:Hamsa", "VEHICLE_OF", "Deity:Brahma"),
    ("Animal:Peacock", "VEHICLE_OF", "Deity:Kartikeya"),
]

rel_edges = []
for src, rel, tgt in RELATIONSHIPS:
    src_guid = guid_map.get(src)
    tgt_guid = guid_map.get(tgt)
    if src_guid and tgt_guid:
        rel_edges.append({
            'GUID': make_guid(f"r-{src}-{rel}-{tgt}"),
            'type': rel,
            'source_GUID': src_guid,
            'target_GUID': tgt_guid,
            'source_ref': src,
            'target_ref': tgt,
            'evidence': 'canonical_scripture',
            'confidence': 95,
            'phase': 'v9'
        })
    else:
        print(f"  SKIP: {src} -> {tgt} (missing GUID: src={src_guid is not None}, tgt={tgt_guid is not None})")

print(f"Relationship edges: {len(rel_edges)}")
# Add non-MENTIONED_IN old edges
old_rel = [e for e in old_edges if e['type'] not in ('MENTIONED_IN',)]
all_edges = mentioned_edges + rel_edges + old_rel
print(f"Total edges: {len(all_edges)}")

# ── QA ──
node_guids = set(n['GUID'] for n in nodes)
connected = set()
for e in all_edges:
    connected.add(e.get('source_GUID',''))
    connected.add(e.get('target_GUID',''))
orphans = node_guids - connected
broken = sum(1 for e in all_edges if e.get('source_GUID') not in node_guids or e.get('target_GUID') not in node_guids)

# ── Sub-graphs ──
dialogue_edges = [e for e in all_edges if e['type'] in ('TEACHER_OF','STUDENT_OF','REFERENCED_IN')]
genealogy_edges = [e for e in all_edges if e['type'] in ('FATHER_OF','MOTHER_OF','SON_OF','DAUGHTER_OF','HUSBAND_OF','BROTHER_OF','SISTER_OF','ANCESTOR_OF','INCARNATION_OF')]
concept_edges = [e for e in all_edges if e['type'] in ('PATH_TO','LEADS_TO','GUIDES','IDENTICAL_TO','LIBERATION_FROM')]
geo_edges = [e for e in all_edges if e['type'] in ('LOCATED_IN','ABODE_OF','CAPITAL_OF','CENTER_OF','BATTLEFIELD_OF','KINGDOM_OF','RULER_OF')]
assoc_edges = [e for e in all_edges if e['type'] in ('WIELDED_BY','VEHICLE_OF','CREATOR_OF')]

concept_nodes = [n for n in nodes if n.get('entity_type') == 'Concept']
ritual_nodes = [n for n in nodes if n.get('entity_type') == 'Ritual']
astro_nodes = [n for n in nodes if n.get('entity_type') in ('Nakshatra','Graha')]
geo_nodes = [n for n in nodes if n.get('entity_type') == 'Place']

subgraphs = {
    'dialogue_graph': {'type':'dialogue_graph','edges':dialogue_edges,'stats':{'total':len(dialogue_edges)}},
    'genealogy_graph': {'type':'genealogy_graph','edges':genealogy_edges,'stats':{'total':len(genealogy_edges)}},
    'concept_graph': {'type':'concept_graph','edges':concept_edges,
                       'nodes':[{'name':n.get('name',''),'GUID':n['GUID']} for n in concept_nodes],
                       'stats':{'edges':len(concept_edges),'nodes':len(concept_nodes)}},
    'geography_graph': {'type':'geography_graph','edges':geo_edges,
                         'nodes':[{'name':n.get('name',''),'GUID':n['GUID'],'mentions':n.get('total_mentions',0)} for n in geo_nodes],
                         'stats':{'edges':len(geo_edges),'nodes':len(geo_nodes)}},
    'ritual_graph': {'type':'ritual_graph',
                      'nodes':[{'name':n.get('name',''),'GUID':n['GUID'],'mentions':n.get('total_mentions',0)} for n in ritual_nodes],
                      'stats':{'nodes':len(ritual_nodes)}},
    'astronomy_graph': {'type':'astronomy_graph',
                         'nodes':[{'name':n.get('name',''),'GUID':n['GUID'],'type':n.get('entity_type',''),'mentions':n.get('total_mentions',0)} for n in astro_nodes],
                         'stats':{'nodes':len(astro_nodes)}},
    'association_graph': {'type':'association_graph','edges':assoc_edges,'stats':{'total':len(assoc_edges)}},
}

events = [
    {'name':'Mahabharata War','participants':['Arjuna','Duryodhana','Bhishma','Drona','Krishna'],'location':'Kurukshetra','scriptures':['Mahabharata','Bhagavad Gita']},
    {'name':'Sita Swayamvara','participants':['Rama','Sita','Janaka'],'location':'Mithila','scriptures':['Ramayana']},
    {'name':'Samudra Manthan','participants':['Devas','Asuras','Vishnu','Shiva'],'location':'Kshirasagara','scriptures':['Puranas']},
    {'name':'Daksha Yajna','participants':['Shiva','Sati','Daksha'],'location':'Kailasa','scriptures':['Shiva Purana']},
    {'name':'Bhagavad Gita Teaching','participants':['Krishna','Arjuna'],'location':'Kurukshetra','scriptures':['Bhagavad Gita']},
    {'name':'Churning of Milk Ocean','participants':['Vishnu','Shesha','Devas','Asuras'],'location':'Kshirasagara','scriptures':['Bhagavata Purana']},
    {'name':'Rama Exile','participants':['Rama','Lakshmana','Sita','Dasharatha'],'location':'Dandakaranya','scriptures':['Ramayana']},
    {'name':'Burning of Khandava','participants':['Arjuna','Krishna','Agni'],'location':'Khandava','scriptures':['Mahabharata']},
    {'name':'Gajendra Moksha','participants':['Gajendra','Vishnu'],'location':'Bhuloka','scriptures':['Bhagavata Purana']},
    {'name':'Draupadi Vastraharana','participants':['Draupadi','Duryodhana','Bhishma'],'location':'Hastinapura','scriptures':['Mahabharata']},
    {'name':'Hanuman Leap to Lanka','participants':['Hanuman','Ravana'],'location':'Lanka','scriptures':['Ramayana']},
    {'name':'Killing of Ravana','participants':['Rama','Hanuman','Ravana','Kumbhakarna'],'location':'Lanka','scriptures':['Ramayana']},
    {'name':'Guru Dakshina War','participants':['Arjuna','Drona','Duryodhana'],'location':'Kurukshetra','scriptures':['Mahabharata']},
    {'name':'Narasimha Avatar','participants':['Narasimha','Prahlada','Hiranyakashipu'],'location':'Bhuloka','scriptures':['Bhagavata Purana']},
    {'name':'Vamana Avatar','participants':['Vamana','Bali','Indra'],'location':'Bhuloka','scriptures':['Vishnu Purana']},
]
subgraphs['event_graph'] = {'type':'event_graph','events':events,'stats':{'total':len(events)}}

# ── Statistics ──
type_counts = defaultdict(int)
edge_type_counts = defaultdict(int)
total_mentions = 0
for n in nodes:
    t = n.get('entity_type', n.get('type', n.get('node_type','')))
    type_counts[t] += 1
    total_mentions += n.get('total_mentions', n.get('mentions', 0))
for e in all_edges:
    edge_type_counts[e['type']] += 1

stats = {
    'version': '9.0',
    'generated': datetime.now().isoformat(),
    'phase': 9,
    'nodes': {'total': len(nodes), 'scriptures': type_counts.get('Scripture',0), 'entities': len(nodes) - type_counts.get('Scripture',0)},
    'edges': {'total': len(all_edges), 'by_type': dict(edge_type_counts)},
    'entity_breakdown': {k:v for k,v in sorted(type_counts.items(), key=lambda x:-x[1])},
    'total_mentions': total_mentions,
    'files_scanned': extraction.get('files_scanned', 0),
    'orphan_nodes': len(orphans),
    'evidence_coverage_pct': round(sum(1 for n in nodes if n.get('sources') or n.get('sources_v9') or n.get('provenance')) / len(nodes) * 100, 1) if nodes else 0
}

qa = {
    'generated': datetime.now().isoformat(),
    'total_nodes': len(nodes),
    'total_edges': len(all_edges),
    'orphan_nodes': len(orphans),
    'broken_references': broken,
    'duplicate_guids': len([n['GUID'] for n in nodes]) - len(set(n['GUID'] for n in nodes)),
    'evidence_coverage_pct': stats['evidence_coverage_pct'],
    'edge_type_distribution': dict(edge_type_counts),
    'node_type_distribution': dict(type_counts),
    'pass': broken == 0
}

comp = {
    'generated': datetime.now().isoformat(),
    'total_entities': len(nodes) - type_counts.get('Scripture',0),
    'entities_with_relationships': len(connected - set(s['GUID'] for s in old_scriptures)),
    'relationship_coverage_pct': round(len(connected - set(s['GUID'] for s in old_scriptures)) / max(1,len(nodes) - type_counts.get('Scripture',0)) * 100, 1),
    'total_edges': len(all_edges),
    'edge_types': dict(edge_type_counts)
}

# ── Save all ──
with open(os.path.join(GRAPH_DIR, 'nodes/entity_nodes.json'), 'w') as f:
    json.dump([n for n in nodes if n.get('type', n.get('entity_type','')) != 'Scripture' and n.get('node_type','') != 'Scripture'], f, indent=2, ensure_ascii=False)
with open(os.path.join(GRAPH_DIR, 'nodes/scripture_nodes.json'), 'w') as f:
    json.dump([n for n in nodes if n.get('node_type','') == 'Scripture' or n.get('type','') == 'Scripture'], f, indent=2, ensure_ascii=False)
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
    json.dump([{'type':'warning','description':f'{len(orphans)} orphan nodes','severity':'medium','status':'needs_review'}], f, indent=2)
for name, sg in subgraphs.items():
    with open(os.path.join(GRAPH_DIR, f'{name}.json'), 'w') as f:
        json.dump(sg, f, indent=2, ensure_ascii=False)

# CUID index
cuid_index = {}
for n in nodes:
    cn = n.get('CUID', n.get('name',''))
    if cn:
        cuid_index[cn] = n['GUID']
with open(os.path.join(GRAPH_DIR, 'cuid_index.json'), 'w') as f:
    json.dump(cuid_index, f, indent=2, ensure_ascii=False)

# Entity index
entity_index = {}
for n in nodes:
    if n.get('type','') != 'Scripture' and n.get('node_type','') != 'Scripture':
        entity_index[n.get('name','')] = {'GUID':n['GUID'],'type':n.get('entity_type',n.get('type','')),'mentions':n.get('total_mentions',n.get('mentions',0))}
with open(os.path.join(GRAPH_DIR, 'indexes/entity_index.json'), 'w') as f:
    json.dump(entity_index, f, indent=2, ensure_ascii=False)

# Manifest
manifest_files = {}
for fname in os.listdir(GRAPH_DIR):
    fpath = os.path.join(GRAPH_DIR, fname)
    if os.path.isfile(fpath):
        manifest_files[fname] = {'size': os.path.getsize(fpath)}
for subd in ['nodes','edges','validation','indexes','schemas']:
    sub_path = os.path.join(GRAPH_DIR, subd)
    if os.path.isdir(sub_path):
        for fname in os.listdir(sub_path):
            manifest_files[f'{subd}/{fname}'] = {'size': os.path.getsize(os.path.join(sub_path, fname))}
with open(os.path.join(GRAPH_DIR, 'graph_manifest.json'), 'w') as f:
    json.dump({'version':'9.0','generated':datetime.now().isoformat(),'files':manifest_files}, f, indent=2)

print(f"\n{'='*60}")
print(f"Phase 9 Knowledge Graph v9.0 — Complete")
print(f"{'='*60}")
print(f"Nodes: {len(nodes)} (scriptures: {type_counts.get('Scripture',0)}, entities: {len(nodes)-type_counts.get('Scripture',0)})")
print(f"Edges: {len(all_edges)} (MENTIONED_IN: {edge_type_counts.get('MENTIONED_IN',0)}, relationships: {sum(v for k,v in edge_type_counts.items() if k!='MENTIONED_IN')})")
print(f"Orphan nodes: {len(orphans)}")
print(f"Broken references: {broken}")
print(f"Evidence coverage: {stats['evidence_coverage_pct']}%")
print(f"Relationship coverage: {comp['relationship_coverage_pct']}%")
print(f"\nEntity breakdown:")
for t, c in sorted(type_counts.items(), key=lambda x:-x[1]):
    print(f"  {t}: {c}")
print(f"\nEdge breakdown:")
for t, c in sorted(edge_type_counts.items(), key=lambda x:-x[1]):
    print(f"  {t}: {c}")
