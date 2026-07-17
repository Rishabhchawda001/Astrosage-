"""
Phase 9.6: Targeted Extraction for Low-Coverage Scriptures.
Loads corpus, extracts entities from zero/low-coverage scriptures,
builds edges, runs saturation check.
"""
import json, os, re, uuid
from collections import defaultdict, Counter
from datetime import datetime

GRAPH_DIR = "knowledge/graph"
CORPUS_DIR = "knowledge/cuv/gretil_prose_clean"

def make_guid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"astrosage.v96.{name}"))

# ── Load current graph ──
with open(os.path.join(GRAPH_DIR, 'nodes/entity_nodes.json')) as f:
    entities = json.load(f)
with open(os.path.join(GRAPH_DIR, 'edges/relationship_edges.json')) as f:
    edges = json.load(f)
with open(os.path.join(GRAPH_DIR, 'nodes/scripture_nodes.json')) as f:
    scriptures = json.load(f)

entity_by_name = {e['name']: e for e in entities}
scripture_by_id = {s.get('id',''): s for s in scriptures}

# ── Identify low-coverage scriptures ──
with open(os.path.join(GRAPH_DIR, 'coverage_report.json')) as f:
    cov = json.load(f)
zero_cov = [c['id'] for c in cov['scripture_coverage'] if c['entities_linked'] == 0]
low_cov = [c['id'] for c in cov['scripture_coverage'] if 0 < c['entities_linked'] < 30]
target_ids = set(zero_cov + low_cov)
print(f"Target scriptures: {len(target_ids)} (zero: {len(zero_cov)}, low: {len(low_cov)})")

# ── Load corpus ──
print("Loading corpus...")
corpus = {}
for fname in sorted(os.listdir(CORPUS_DIR)):
    if not fname.endswith('.json'):
        continue
    with open(os.path.join(CORPUS_DIR, fname)) as f:
        data = json.load(f)
    title = data.get('title', fname.replace('.json',''))
    units = []
    all_text = []
    for ch in data.get('chapters', []):
        for aku in ch.get('akus', []):
            body = aku.get('body', '')
            if body:
                units.append({'text': body, 'chapter': ch.get('chapter_num', 0), 'ref': aku.get('ref')})
                all_text.append(body.lower())
    corpus[fname] = {'title': title, 'units': units, 'text': ' '.join(all_text), 'file': fname, 'unit_count': len(units)}

# Map scripture IDs to corpus files
# The scripture IDs in the graph correspond to short codes
ID_TO_FILE = {
    'APASTAMBA_DS': 'apastamba_dharmasutra_gretil_prose.json',
    'BG': 'bhagavad_gita_4comm_gretil_prose_cert.json',  # fallback
    'BRAHMD': 'brahmand_puran_gretil_prose.json',
    'GAUTAMA_DS': 'gautama_dharmasutra_gretil_prose_cert.json',
    'ISHA': 'isha_upanishad_gretil_prose_cert.json',
    'KATH': None,  # not in gretil
    'KEN': None,
    'MAHAN': None,
    'MAITR': None,
    'MANU': 'manusmriti_gretil_prose_cert.json',
    'MUND': None,
    'NARADA_SM': 'narada_smriti_gretil_prose_cert.json',
    'PARASHARA': None,
    'SHVET': 'shvetashvatara_upanishad_gretil_prose_cert.json',
    'VISHNU_SM': 'vishnu_smriti_gretil_prose_cert.json',
    'VYU': None,
    'YAJNAV': None,
    'YOGA_SUTRA': 'yoga_sutra_bhasya_gretil_prose_cert.json',
    'NYAYA_SUTRA': None,
}

# Also try matching by title
TITLE_MAP = {}
for fname, info in corpus.items():
    TITLE_MAP[info['title']] = fname

# Find which target scriptures have corpus files
available = {}
unavailable = []
for sid in target_ids:
    fname = ID_TO_FILE.get(sid)
    if fname and fname in corpus:
        available[sid] = fname
    else:
        # Try title matching
        sinfo = scripture_by_id.get(sid, {})
        sname = sinfo.get('canonical_name', sid)
        for title, fn in TITLE_MAP.items():
            if sname.lower() in title.lower() or title.lower() in sname.lower():
                available[sid] = fn
                break
        else:
            unavailable.append(sid)

print(f"Available in corpus: {len(available)}")
print(f"Unavailable: {len(unavailable)}: {unavailable}")

# ── Entity dictionaries for extraction ──
DEITIES = {
    'Vishnu': ['viṣṇu', 'nārāyaṇa', 'hari', 'vaikuṇṭha', 'keśava', 'mādhava', 'govinda'],
    'Shiva': ['śiva', 'maheśvara', 'mahādeva', 'pāśupati', 'śaṅkara', 'hara', 'nīlakaṇṭha'],
    'Brahma': ['brahmā', 'pitāmaha', 'svayambhū', 'hiraṇyagarbha', 'prajāpati'],
    'Rama': ['rāma', 'rāghava', 'śrīrāma'],
    'Krishna': ['kṛṣṇa', 'vāsudeva', 'govinda', 'gopāla', 'keśava'],
    'Ganesha': ['gaṇeśa', 'gaṇapati', 'vighneśvara', 'vināyaka'],
    'Surya': ['sūrya', 'savitā', 'āditya', 'bhāskara'],
    'Hanuman': ['hanumat', 'anjaneya', 'vāyuputra', 'pavanaputra'],
    'Lakshmi': ['lakṣmī', 'śrī', 'kamalā', 'padmā'],
    'Saraswati': ['sarasvatī', 'vāṇī'],
    'Parvati': ['pārvatī', 'girijā', 'umā', 'pārvatī'],
    'Durga': ['durgā', 'durgatināśinī'],
    'Indra': ['indra', 'śakra', 'purandara', 'mahendra'],
    'Yama': ['yama', 'dharmarāja', 'vaivasvata'],
    'Varuna': ['varuṇa'],
    'Vayu': ['vāyu', 'pavana', 'marut'],
    'Agni': ['agni', 'anala', 'pāvaka', 'jātavedas', 'vahni'],
    'Nandi': ['nandī', 'nandikeśvara'],
    'Kartikeya': ['kārttikeya', 'skanda', 'kumāra'],
    'Chandra': ['chandra', 'soma', 'candra'],
    'Narada': ['nārada'],
    'Garuda': ['garuḍa', 'suparṇa'],
    'Vasuki': ['vāsuki'],
    'Dattatreya': ['dattātreya'],
    'Balarama': ['balabhadra', 'balarāma'],
    'Lakshmana': ['lakṣmaṇa'],
    'Rudra': ['rudra'],
    'Surya': ['sūrya', 'āditya'],
}

PERSONS = {
    'Veda Vyasa': ['vyāsa', 'veda-vyāsa', 'kr̥ṣṇadvāipayana', 'bādarāyaṇa'],
    'Vasistha': ['vasiṣṭha'],
    'Vishvamitra': ['viśvāmitra', 'kaushika'],
    'Shuka': ['śuka', 'śuka-deva'],
    'Parashara': ['parāśara'],
    'Gautama': ['gautama'],
    'Bharadvaja': ['bharadvāja'],
    'Atri': ['atri'],
    'Arjuna': ['arjuna', 'jishnu', 'phālguna', 'dhanañjaya', 'pārtha'],
    'Bhima': ['bhīma', 'bhīmasena', 'vṛkodara'],
    'Yudhishthira': ['yudhiṣṭhira', 'dharma-putra'],
    'Drona': ['droṇa', 'droṇācārya'],
    'Bhishma': ['bhīṣma', 'devavrata'],
    'Karna': ['karṇa'],
    'Duryodhana': ['duryodhana', 'suyodhana'],
    'Dhritarashtra': ['dhṛtarāṣṭra'],
    'Pandu': ['pāṇḍu'],
    'Kunti': ['kuntī', 'pṛthā'],
    'Draupadi': ['draupadī'],
    'Ravana': ['rāvaṇa', 'dāśagrīva', 'daśānana'],
    'Vibhishana': ['vibhīṣaṇa'],
    'Manu': ['manu', 'svāyambhuva-manu', 'vaivasvata-manu'],
    'Janaka': ['janaka', 'videha-rāja'],
    'Nala': ['nala'],
    'Shakuntala': ['śakuntalā'],
    'Narada': ['nārada'],
    'Bhrigu': ['bhṛgu'],
    'Kashyapa': ['kāśyapa'],
    'Angirasa': ['aṅgirasa'],
    'Saunaka': ['śaunaka'],
    'Yajnavalkya': ['yājñavalkya'],
    'Uddalaka': ['uddālaka'],
    'Shvetaketu': ['śvetaketu'],
    'Nachiketa': ['naciketas'],
    'Prahlada': ['prahlāda'],
    'Bali': ['bali'],
    'Pippalada': ['pippalāda'],
    'Ashtavakra': ['aṣṭāvakra'],
    'Vasudeva': ['vasudeva'],
    'Devaki': ['devakī'],
    'Rohini': ['rohiṇī'],
    'Ugrasena': ['ugrasena'],
    'Kamsa': ['kaṃsa'],
    'Vidura': ['vidura'],
    'Sanjaya': ['sañjaya'],
    'Vasuki': ['vāsuki'],
    'Muchukunda': ['muchukunda'],
    'Ambarisha': ['ambarīṣa'],
    'Prithu': ['pṛthu'],
    'Ikshvaku': ['ikṣvāku'],
    'Bharata': ['bharata'],
    'Dilipa': ['dilīpa'],
    'Raghu': ['raghu'],
    'Dasharatha': ['daśaratha'],
    'Lava': ['lava'],
    'Kusha': ['kuśa'],
    'Shatrughna': ['śatrughna'],
    'Subhadra': ['subhadrā'],
    'Abhimanyu': ['abhimanyu'],
    'Gandhari': ['gāndhārī'],
    'Vasuki': ['vāsuki'],
}

PLACES = {
    'Ayodhya': ['ayodhyā'],
    'Mathura': ['mathurā'],
    'Dvaraka': ['dvārakā', 'dvārāvatī'],
    'Vrindavan': ['vṛndāvana'],
    'Hastinapura': ['hastināpura'],
    'Kurukshetra': ['kuru-kṣetra'],
    'Patala': ['pātāla'],
    'Kailas': ['kailāsa'],
    'Kashi': ['kāśī', 'vārāṇasī'],
    'Lanka': ['laṅkā'],
    'Meru': ['meru'],
    'Himalaya': ['himalaya', 'himavat'],
    'Puri': ['puri', 'jagannātha'],
    'Prayaga': ['prayāga'],
    'Pushkar': ['puṣkara'],
    'Kurukshetra': ['kuru-kṣetra', 'dharmakṣetra'],
    'Gokul': ['gokula'],
    'Indraprastha': ['indraprastha'],
    'Panchala': ['pañcāla'],
    'Magadha': ['magadha'],
    'Kosala': ['kośala'],
    'Mithila': ['mithilā'],
    'Videha': ['videha'],
    'Champa': ['campā'],
    'Kamarupa': ['kāmarūpa'],
}

CONCEPTS = {
    'Dharma': ['dharma'],
    'Karma': ['karma', 'karman'],
    'Moksha': ['mokṣa', 'mukti', 'kaivalya'],
    'Bhakti': ['bhakti'],
    'Jnana': ['jñāna', 'vidyā'],
    'Yoga': ['yoga'],
    'Brahman': ['brahman', 'brahma'],
    'Atman': ['ātman', 'ātmā'],
    'Maya': ['māyā'],
    'Prakriti': ['prakṛti'],
    'Purusha': ['puruṣa'],
    'Samsara': ['saṃsāra'],
    'Tapas': ['tapas', 'tapasyā'],
    'Dhyana': ['dhyāna'],
    'Mantra': ['mantra'],
    'Yajna': ['yajña', 'iṣṭi', 'homa'],
    'Dana': ['dāna'],
    'Varna': ['varṇa'],
    'Ashrama': ['āśrama'],
    'Ahimsa': ['ahiṃsā'],
    'Satya': ['satya'],
    'Shraddha': ['śraddhā'],
    'Pranayama': ['prāṇāyāma'],
    'Vidya': ['vidyā'],
    'Upanishad': ['upaniṣad'],
}

ANIMALS = {
    'Horse': ['aśva', 'haya', 'turaṅga'],
    'Elephant': ['gaja', 'hastin'],
    'Cow': ['go', 'gomata'],
    'Swan': ['haṃsa'],
    'Snake': ['sarpa', 'nāga'],
    'Tiger': ['vyāghra'],
    'Lion': ['siṃha'],
    'Fish': ['matsya'],
    'Monkey': ['markaṭa', 'vānara'],
    'Tortoise': ['kūrma'],
}

WEAPONS = {
    'Bow': ['dhanus', 'chāpa'],
    'Sword': ['khadga', 'asi'],
    'Trident': ['triśūla'],
    'Mace': ['gadā'],
    'Vajra': ['vajra'],
    'Chakra': ['cakra'],
    'Kapala': ['kapāla'],
    'Khatvanga': ['khaṭvāṅga'],
}

def extract_entities_from_text(text, fname):
    """Extract entity mentions from scripture text."""
    found = defaultdict(lambda: {'count': 0, 'sources': set()})
    text_lower = text.lower()
    
    all_dicts = [
        (DEITIES, 'Deity'), (PERSONS, 'Person'), (PLACES, 'Place'),
        (CONCEPTS, 'Concept'), (ANIMALS, 'Animal'), (WEAPONS, 'Weapon')
    ]
    
    for entity_dict, etype in all_dicts:
        for canonical, aliases in entity_dict.items():
            count = 0
            for alias in aliases:
                pattern = r'\b' + re.escape(alias) + r'\b'
                count += len(re.findall(pattern, text_lower))
            if count > 0:
                found[canonical] = {'count': count, 'type': etype}
    
    return found

# ── Process target scriptures ──
print(f"\n=== TARGETED EXTRACTION ===")
new_entities = []
new_edges = []
total_new = 0

for sid, fname in available.items():
    info = corpus.get(fname, {})
    text = info.get('text', '')
    title = info.get('title', sid)
    unit_count = info.get('unit_count', 0)
    
    if not text:
        print(f"  {sid}: no text found in {fname}")
        continue
    
    found = extract_entities_from_text(text, sid)
    
    # Add new entities
    scripture_added = 0
    for canonical, data in found.items():
        if canonical in entity_by_name:
            # Already exists - just add edge
            entity_guid = entity_by_name[canonical]['GUID']
        else:
            # New entity
            etype = data['type']
            guid = make_guid(f"{sid}-{canonical}")
            new_e = {
                'GUID': guid,
                'name': canonical,
                'type': etype,
                'entity_type': etype,
                'total_mentions': data['count'],
                'mentions': data['count'],
                'sources': [title],
                'source_count': 1,
                'provenance': {'phase': 'v9.6', 'method': 'targeted_extraction', 'scripture': sid}
            }
            new_entities.append(new_e)
            entity_by_name[canonical] = new_e
            entity_guid = guid
            scripture_added += 1
            total_new += 1
        
        # Add MENTIONED_IN edge
        scripture_guid = scripture_by_id.get(sid, {}).get('GUID', make_guid(f"scripture-{sid}"))
        edge_key = (entity_guid, scripture_guid, 'MENTIONED_IN')
        new_edges.append({
            'GUID': make_guid(f"t-{sid}-{canonical}"),
            'type': 'MENTIONED_IN',
            'source_GUID': entity_guid,
            'target_GUID': scripture_guid,
            'evidence': {'entity': canonical, 'scripture': title, 'mentions': data['count']},
            'confidence': 88,
            'phase': 'v9.6'
        })
    
    print(f"  {sid:12} {title[:40]:40} units={unit_count:>5} entities={len(found):>3} new={scripture_added}")

print(f"\nTotal new entities: {total_new}")
print(f"Total new edges: {len(new_edges)}")

# ── Merge into main graph ──
entities.extend(new_entities)
edges.extend(new_edges)

# ── Dedup edges ──
edge_key_set = set()
deduped = []
dup_count = 0
for e in edges:
    key = (e.get('source_GUID',''), e.get('target_GUID',''), e.get('type',''))
    if key not in edge_key_set:
        edge_key_set.add(key)
        deduped.append(e)
    else:
        dup_count += 1

print(f"Deduped {dup_count} duplicate edges")
edges = deduped

# ── Verify ──
entity_guids = {e['GUID'] for e in entities}
scripture_guids = {s['GUID'] for s in scriptures}
all_guids = entity_guids | scripture_guids
connected = set()
for e in edges:
    if e.get('source_GUID') in entity_guids: connected.add(e['source_GUID'])
    if e.get('target_GUID') in entity_guids: connected.add(e['target_GUID'])
orphans = entity_guids - connected
broken = sum(1 for e in edges if e.get('source_GUID','') not in all_guids or e.get('target_GUID','') not in all_guids)

print(f"\nOrphans: {len(orphans)}, Broken: {broken}")
print(f"Final: {len(entities)} entities, {len(edges)} edges")

# ── Save ──
with open(os.path.join(GRAPH_DIR, 'nodes/entity_nodes.json'), 'w') as f:
    json.dump(entities, f, indent=2, ensure_ascii=False)
with open(os.path.join(GRAPH_DIR, 'edges/relationship_edges.json'), 'w') as f:
    json.dump(edges, f, indent=2, ensure_ascii=False)

all_nodes = scriptures + entities
with open(os.path.join(GRAPH_DIR, 'graph.json'), 'w') as f:
    json.dump({'version':'9.6','generated':datetime.now().isoformat(),'nodes':all_nodes,'edges':edges,
               'stats':{'total_nodes':len(all_nodes),'total_edges':len(edges)}}, f, indent=2, ensure_ascii=False)

# Update stats
type_counts = dict(Counter(n.get('entity_type', n.get('type','')) for n in entities))
edge_type_dist = dict(Counter(e.get('type','') for e in edges))
mentioned_in = len([e for e in edges if e['type'] == 'MENTIONED_IN'])

with open(os.path.join(GRAPH_DIR, 'graph_statistics.json'), 'w') as f:
    json.dump({
        'version':'9.6','generated':datetime.now().isoformat(),'phase':9.6,
        'nodes':{'total':len(all_nodes),'scriptures':len(scriptures),'entities':len(entities)},
        'edges':{'total':len(edges),'mentioned_in':mentioned_in,'relationships':len(edges)-mentioned_in,'by_type':edge_type_dist},
        'entity_breakdown':type_counts,
        'orphan_nodes':len(orphans),'broken_references':broken
    }, f, indent=2, ensure_ascii=False)

with open(os.path.join(GRAPH_DIR, 'validation/graph_validation.json'), 'w') as f:
    json.dump({
        'generated':datetime.now().isoformat(),'phase':'9.6',
        'total_nodes':len(all_nodes),'total_edges':len(edges),
        'orphan_nodes':len(orphans),'broken_references':broken,
        'pass':broken==0
    }, f, indent=2, ensure_ascii=False)

# Entity index
entity_index = {n.get('name',''):{'GUID':n['GUID'],'type':n.get('type',''),'mentions':n.get('total_mentions',n.get('mentions',0))} for n in entities}
with open(os.path.join(GRAPH_DIR, 'indexes/entity_index.json'), 'w') as f:
    json.dump(entity_index, f, indent=2, ensure_ascii=False)

print("\nDone")
