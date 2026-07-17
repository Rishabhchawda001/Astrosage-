"""
Phase 9.6: Extract entities from raw download files (XML/TXT).
"""
import json, os, re, uuid
from collections import defaultdict, Counter
from datetime import datetime

GRAPH_DIR = "knowledge/graph"
DL_DIR = "knowledge/downloads"

def make_guid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"astrosage.v96r.{name}"))

with open(os.path.join(GRAPH_DIR, 'nodes/entity_nodes.json')) as f:
    entities = json.load(f)
with open(os.path.join(GRAPH_DIR, 'edges/relationship_edges.json')) as f:
    edges = json.load(f)
with open(os.path.join(GRAPH_DIR, 'nodes/scripture_nodes.json')) as f:
    scriptures = json.load(f)

entity_by_name = {e['name']: e for e in entities}
scripture_by_id = {s.get('id',''): s for s in scriptures}

# Entity dictionaries
DEITIES = {
    'Vishnu': ['viṣṇu', 'nārāyaṇa', 'hari', 'vaikuṇṭha', 'keśava', 'mādhava', 'govinda', 'madhusūdana', 'vāmana', 'trivikrama'],
    'Shiva': ['śiva', 'maheśvara', 'mahādeva', 'pāśupati', 'śaṅkara', 'hara', 'nīlakaṇṭha', 'rudra'],
    'Brahma': ['brahmā', 'pitāmaha', 'svayambhū', 'hiraṇyagarbha', 'prajāpati'],
    'Rama': ['rāma', 'rāghava', 'śrīrāma', 'kākutstha'],
    'Krishna': ['kṛṣṇa', 'vāsudeva', 'govinda', 'gopāla', 'keśava', 'mādhava'],
    'Ganesha': ['gaṇeśa', 'gaṇapati', 'vighneśvara', 'vināyaka'],
    'Surya': ['sūrya', 'savitā', 'āditya', 'bhāskara', 'arka'],
    'Hanuman': ['hanumat', 'anjaneya', 'vāyuputra', 'pavanaputra'],
    'Lakshmi': ['lakṣmī', 'śrī', 'kamalā', 'padmā'],
    'Saraswati': ['sarasvatī', 'vāṇī'],
    'Parvati': ['pārvatī', 'girijā', 'umā', 'pārvatī', 'ambikā'],
    'Durga': ['durgā', 'durgatināśinī'],
    'Indra': ['indra', 'śakra', 'purandara', 'mahendra', 'meghavāhana'],
    'Yama': ['yama', 'dharmarāja', 'vaivasvata', 'mrtyu'],
    'Varuna': ['varuṇa'],
    'Vayu': ['vāyu', 'pavana', 'marut', 'anila'],
    'Agni': ['agni', 'anala', 'pāvaka', 'jātavedas', 'vahni', 'hutāśana'],
    'Nandi': ['nandī', 'nandikeśvara'],
    'Kartikeya': ['kārttikeya', 'skanda', 'kumāra'],
    'Chandra': ['chandra', 'soma', 'candra', 'śaśīn'],
    'Narada': ['nārada'],
    'Garuda': ['garuḍa', 'suparṇa', 'tārkṣya'],
    'Vasuki': ['vāsuki'],
    'Dattatreya': ['dattātreya'],
    'Balarama': ['balabhadra', 'balarāma', 'saṅkarṣaṇa'],
    'Shesha': ['śeṣa', 'ananta'],
    'Kali': ['kālī'],
    'Bhairava': ['bhairava'],
    'Skanda': ['skanda'],
    'Kartikeya': ['kārttikeya'],
}

PERSONS = {
    'Veda Vyasa': ['vyāsa', 'veda-vyāsa', 'bādarāyaṇa'],
    'Vasistha': ['vasiṣṭha'],
    'Vishvamitra': ['viśvāmitra', 'kaushika'],
    'Shuka': ['śuka'],
    'Parashara': ['parāśara'],
    'Gautama': ['gautama'],
    'Bharadvaja': ['bharadvāja'],
    'Atri': ['atri'],
    'Arjuna': ['arjuna', 'jishnu', 'phālguna', 'dhanañjaya', 'pārtha', 'kaunteya'],
    'Bhima': ['bhīma', 'bhīmasena', 'vṛkodara'],
    'Yudhishthira': ['yudhiṣṭhira', 'dharma-putra'],
    'Drona': ['droṇa', 'droṇācārya'],
    'Bhishma': ['bhīṣma', 'devavrata', 'gāṅgeya'],
    'Karna': ['karṇa', 'rādhā-putra', 'sūrya-putra'],
    'Duryodhana': ['duryodhana', 'suyodhana'],
    'Dhritarashtra': ['dhṛtarāṣṭra'],
    'Pandu': ['pāṇḍu'],
    'Kunti': ['kuntī', 'pṛthā'],
    'Draupadi': ['draupadī'],
    'Ravana': ['rāvaṇa', 'dāśagrīva', 'daśānana'],
    'Vibhishana': ['vibhīṣaṇa'],
    'Manu': ['manu', 'svāyambhuva-manu', 'vaivasvata-manu'],
    'Janaka': ['janaka', 'videha-rāja'],
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
    'Pippalada': ['pippalāda'],
    'Ashtavakra': ['aṣṭāvakra'],
    'Vasudeva': ['vasudeva'],
    'Devaki': ['devakī'],
    'Vidura': ['vidura'],
    'Sanjaya': ['sañjaya'],
    'Muchukunda': ['muchukunda'],
    'Ambarisha': ['ambarīṣa'],
    'Prithu': ['pṛthu'],
    'Ikshvaku': ['ikṣvāku'],
    'Bharata': ['bharata'],
    'Dasharatha': ['daśaratha'],
    'Lakshmana': ['lakṣmaṇa'],
    'Subhadra': ['subhadrā'],
    'Abhimanyu': ['abhimanyu'],
    'Gandhari': ['gāndhārī'],
    'Nala': ['nala'],
    'Shakuntala': ['śakuntalā'],
    'Bali': ['bali'],
    'Vasuki': ['vāsuki'],
    'Ananta': ['ananta'],
    'Shesha': ['śeṣa'],
    'Vasuki': ['vāsuki'],
}

PLACES = {
    'Ayodhya': ['ayodhyā'],
    'Mathura': ['mathurā'],
    'Dvaraka': ['dvārakā', 'dvārāvatī'],
    'Hastinapura': ['hastināpura'],
    'Kurukshetra': ['kuru-kṣetra', 'dharmakṣetra'],
    'Patala': ['pātāla'],
    'Kailas': ['kailāsa'],
    'Kashi': ['kāśī', 'vārāṇasī'],
    'Lanka': ['laṅkā'],
    'Meru': ['meru'],
    'Himalaya': ['himalaya', 'himavat', 'himālaya'],
    'Prayaga': ['prayāga'],
    'Pushkar': ['puṣkara'],
    'Gokul': ['gokula'],
    'Indraprastha': ['indraprastha'],
    'Vrindavan': ['vṛndāvana'],
    'Puri': ['puri', 'jagannātha'],
    'Mithila': ['mithilā'],
    'Ganga': ['gaṅgā', 'jāhnavī'],
    'Yamuna': ['yamunā'],
    'Narmada': ['narmadā'],
    'Saraswati river': ['sarasvatī-nadī'],
    'Patala': ['pātāla'],
    'Vaikuntha': ['vaikuṇṭha'],
    'Brahmaloka': ['brahma-loka'],
    'Satyaloka': ['satyaloka'],
    'Svarloka': ['svarga-loka'],
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
    'Yajna': ['yajña', 'iṣṭi'],
    'Dana': ['dāna'],
    'Varna': ['varṇa'],
    'Ahimsa': ['ahiṃsā'],
    'Satya': ['satya'],
    'Shraddha': ['śraddhā'],
    'Pranayama': ['prāṇāyāma'],
    'Vidya': ['vidyā'],
    'Upanishad': ['upaniṣad'],
    'Gunas': ['guṇa'],
    'Sattva': ['sattva'],
    'Rajas': ['rajas'],
    'Tamas': ['tamas'],
}

ANIMALS = {
    'Horse': ['aśva', 'haya', 'turaṅga'],
    'Elephant': ['gaja', 'hastin'],
    'Cow': ['go', 'gomata'],
    'Swan': ['haṃsa'],
    'Snake': ['sarpa', 'nāga'],
    'Fish': ['matsya'],
    'Monkey': ['markaṭa', 'vānara'],
}

WEAPONS = {
    'Bow': ['dhanus', 'chāpa'],
    'Sword': ['khadga'],
    'Trident': ['triśūla'],
    'Mace': ['gadā'],
    'Vajra': ['vajra'],
    'Chakra': ['cakra'],
}

ALL_DICTS = [(DEITIES, 'Deity'), (PERSONS, 'Person'), (PLACES, 'Place'),
             (CONCEPTS, 'Concept'), (ANIMALS, 'Animal'), (WEAPONS, 'Weapon')]

# Target files and their scripture IDs
TARGET_FILES = {
    'bhagavad_gita_4comm_gretil.xml': 'BG',
    'brahmanda_puran_ia_ia.txt': 'BRAHMD',
    'gautama_dharmasutra_1_3_comm_gretil.xml': 'GAUTAMA_DS',
    'isha_upanishad_gretil.xml': 'ISHA',
    'kena_upanishad_ia.txt': 'KEN',
    'mundaka_upanishad_ia.txt': 'MUND',
    'shvetashvatara_upanishad_gp_ia_ia_djvu.txt': 'SHVET',
    'vishnu_smriti_gretil.xml': 'VISHNU_SM',
    'revakhanda_vayu_puran_gretil.xml': 'VYU',
    'narada_smriti_commentary_ia_ia_djvu.txt': 'NARADA_SM',
    'yajnavalkya_smriti_bombay_ia_ia_djvu.txt': 'YAJNAV',
    'nyaya_sutra_archive_A Bilingual Index of Nyaya Bindu - Satish Chandra Vidyabhushana 1917 (BIS)_djvu.txt': 'NYAYA_SUTRA',
    'mahan_archive_Mahanarayanopanishad_djvu.txt': 'MAHAN',
    'parashara_archive_SriParasharaSmrithiPdf_djvu.txt': 'PARASHARA',
}

def read_file(path):
    """Read file, strip XML tags if present."""
    with open(path, 'r', errors='ignore') as f:
        text = f.read()
    # Strip XML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # Strip extra whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.lower()

new_entities = []
new_edges = []
stats = {}

for fname, sid in TARGET_FILES.items():
    fpath = os.path.join(DL_DIR, fname)
    if not os.path.exists(fpath):
        print(f"  MISSING: {fname}")
        continue
    
    text = read_file(fpath)
    sinfo = scripture_by_id.get(sid, {})
    sname = sinfo.get('canonical_name', sid)
    
    found = defaultdict(lambda: {'count': 0, 'type': ''})
    for entity_dict, etype in ALL_DICTS:
        for canonical, aliases in entity_dict.items():
            count = 0
            for alias in aliases:
                pattern = r'\b' + re.escape(alias) + r'\b'
                count += len(re.findall(pattern, text))
            if count > 0:
                if canonical not in found or count > found[canonical]['count']:
                    found[canonical] = {'count': count, 'type': etype}
    
    scripture_added = 0
    scripture_guid = sinfo.get('GUID', make_guid(f"scripture-{sid}"))
    
    for canonical, data in found.items():
        if canonical in entity_by_name:
            entity_guid = entity_by_name[canonical]['GUID']
        else:
            guid = make_guid(f"{sid}-{canonical}")
            new_e = {
                'GUID': guid,
                'name': canonical,
                'type': data['type'],
                'entity_type': data['type'],
                'total_mentions': data['count'],
                'mentions': data['count'],
                'sources': [sname],
                'source_count': 1,
                'provenance': {'phase': 'v9.6', 'method': 'raw_extraction', 'scripture': sid}
            }
            new_entities.append(new_e)
            entity_by_name[canonical] = new_e
            entity_guid = guid
            scripture_added += 1
        
        new_edges.append({
            'GUID': make_guid(f"r-{sid}-{canonical}"),
            'type': 'MENTIONED_IN',
            'source_GUID': entity_guid,
            'target_GUID': scripture_guid,
            'evidence': {'entity': canonical, 'scripture': sname, 'mentions': data['count']},
            'confidence': 85,
            'phase': 'v9.6'
        })
    
    stats[sid] = {'title': sname, 'file': fname, 'entities': len(found), 'new': scripture_added, 'text_len': len(text)}
    print(f"  {sid:12} {sname[:30]:30} text={len(text):>8} entities={len(found):>3} new={scripture_added}")

# Merge
entities.extend(new_entities)
edges.extend(new_edges)

# Dedup edges
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
edges = deduped

# Verify
entity_guids = {e['GUID'] for e in entities}
scripture_guids = {s['GUID'] for s in scriptures}
all_guids = entity_guids | scripture_guids
connected = set()
for e in edges:
    if e.get('source_GUID') in entity_guids: connected.add(e['source_GUID'])
    if e.get('target_GUID') in entity_guids: connected.add(e['target_GUID'])
orphans = entity_guids - connected
broken = sum(1 for e in edges if e.get('source_GUID','') not in all_guids or e.get('target_GUID','') not in all_guids)

print(f"\nNew entities: {len(new_entities)}")
print(f"Deduped edges: {dup_count}")
print(f"Orphans: {len(orphans)}, Broken: {broken}")
print(f"Final: {len(entities)} entities, {len(edges)} edges")

# Save
with open(os.path.join(GRAPH_DIR, 'nodes/entity_nodes.json'), 'w') as f:
    json.dump(entities, f, indent=2, ensure_ascii=False)
with open(os.path.join(GRAPH_DIR, 'edges/relationship_edges.json'), 'w') as f:
    json.dump(edges, f, indent=2, ensure_ascii=False)

all_nodes = scriptures + entities
with open(os.path.join(GRAPH_DIR, 'graph.json'), 'w') as f:
    json.dump({'version':'9.6','generated':datetime.now().isoformat(),'nodes':all_nodes,'edges':edges,
               'stats':{'total_nodes':len(all_nodes),'total_edges':len(edges)}}, f, indent=2, ensure_ascii=False)

# Stats
type_counts = dict(Counter(n.get('entity_type', n.get('type','')) for n in entities))
edge_type_dist = dict(Counter(e.get('type','') for e in edges))

with open(os.path.join(GRAPH_DIR, 'graph_statistics.json'), 'w') as f:
    json.dump({
        'version':'9.6','generated':datetime.now().isoformat(),'phase':9.6,
        'nodes':{'total':len(all_nodes),'scriptures':len(scriptures),'entities':len(entities)},
        'edges':{'total':len(edges),'by_type':edge_type_dist},
        'entity_breakdown':type_counts,
        'orphan_nodes':len(orphans),'broken_references':broken
    }, f, indent=2, ensure_ascii=False)

with open(os.path.join(GRAPH_DIR, 'validation/graph_validation.json'), 'w') as f:
    json.dump({
        'generated':datetime.now().isoformat(),'phase':'9.6',
        'total_nodes':len(all_nodes),'total_edges':len(edges),
        'orphan_nodes':len(orphans),'broken_references':broken,
        'edge_type_distribution':edge_type_dist,'node_type_distribution':type_counts,
        'pass':broken==0
    }, f, indent=2, ensure_ascii=False)

# Entity index
entity_index = {n.get('name',''):{'GUID':n['GUID'],'type':n.get('type',''),'mentions':n.get('total_mentions',n.get('mentions',0))} for n in entities}
with open(os.path.join(GRAPH_DIR, 'indexes/entity_index.json'), 'w') as f:
    json.dump(entity_index, f, indent=2, ensure_ascii=False)

# Save extraction stats
with open(os.path.join(GRAPH_DIR, 'extraction_stats_v96.json'), 'w') as f:
    json.dump(stats, f, indent=2, ensure_ascii=False)

print("\nDone")
