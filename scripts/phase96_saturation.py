"""
Phase 9.6: Saturation Loop — 3 passes measuring growth.
"""
import json, os, re, uuid
from collections import Counter
from datetime import datetime

GRAPH_DIR = "knowledge/graph"
CORPUS_DIR = "knowledge/cuv/gretil_prose_clean"
DL_DIR = "knowledge/downloads"

def make_guid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"astrosage.v96s.{name}"))

# Load current state
with open(os.path.join(GRAPH_DIR, 'nodes/entity_nodes.json')) as f:
    entities = json.load(f)
with open(os.path.join(GRAPH_DIR, 'edges/relationship_edges.json')) as f:
    edges = json.load(f)
with open(os.path.join(GRAPH_DIR, 'nodes/scripture_nodes.json')) as f:
    scriptures = json.load(f)

entity_by_name = {e['name']: e for e in entities}
scripture_by_id = {s.get('id',''): s for s in scriptures}

# Load ALL corpus texts (GRETIL prose + downloads)
print("Loading corpus...")
all_texts = {}

# GRETIL prose clean
for fname in sorted(os.listdir(CORPUS_DIR)):
    if not fname.endswith('.json'):
        continue
    with open(os.path.join(CORPUS_DIR, fname)) as f:
        data = json.load(f)
    title = data.get('title', fname)
    text = ' '.join(aku.get('body','') for ch in data.get('chapters',[]) for aku in ch.get('akus',[]) if aku.get('body'))
    all_texts[title] = text.lower()

# Downloads (only non-Devanagari files)
DL_FILES = {
    'BG': 'bhagavad_gita_4comm_gretil.xml',
    'ISHA': 'isha_upanishad_gretil.xml',
    'GAUTAMA_DS': 'gautama_dharmasutra_1_3_comm_gretil.xml',
    'VISHNU_SM': 'vishnu_smriti_gretil.xml',
}
for sid, fname in DL_FILES.items():
    fpath = os.path.join(DL_DIR, fname)
    if os.path.exists(fpath):
        with open(fpath, 'r', errors='ignore') as f:
            text = f.read()
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).lower()
        sinfo = scripture_by_id.get(sid, {})
        all_texts[sinfo.get('canonical_name', sid)] = text

print(f"Loaded {len(all_texts)} texts, {sum(len(t) for t in all_texts.values())} chars")

# Entity dictionaries (compact)
DEITIES = {
    'Vishnu': ['viṣṇu', 'nārāyaṇa', 'hari', 'vaikuṇṭha', 'keśava', 'mādhava', 'govinda', 'madhusūdana'],
    'Shiva': ['śiva', 'maheśvara', 'mahādeva', 'pāśupati', 'śaṅkara', 'hara', 'nīlakaṇṭha', 'rudra'],
    'Brahma': ['brahmā', 'pitāmaha', 'svayambhū', 'hiraṇyagarbha', 'prajāpati'],
    'Rama': ['rāma', 'rāghava'],
    'Krishna': ['kṛṣṇa', 'vāsudeva', 'govinda'],
    'Ganesha': ['gaṇeśa', 'gaṇapati', 'vighneśvara'],
    'Surya': ['sūrya', 'savitā', 'āditya', 'bhāskara'],
    'Hanuman': ['hanumat', 'anjaneya', 'vāyuputra'],
    'Lakshmi': ['lakṣmī', 'śrī'],
    'Saraswati': ['sarasvatī', 'vāṇī'],
    'Parvati': ['pārvatī', 'umā', 'ambikā'],
    'Indra': ['indra', 'śakra', 'purandara'],
    'Yama': ['yama', 'dharmarāja'],
    'Agni': ['agni', 'pāvaka', 'jātavedas'],
    'Chandra': ['chandra', 'soma'],
    'Narada': ['nārada'],
    'Garuda': ['garuḍa', 'suparṇa'],
    'Balarama': ['balabhadra', 'balarāma'],
    'Rudra': ['rudra'],
    'Durga': ['durgā'],
    'Varuna': ['varuṇa'],
    'Vayu': ['vāyu', 'pavana'],
    'Kartikeya': ['kārttikeya', 'skanda'],
    'Nandi': ['nandī'],
    'Dattatreya': ['dattātreya'],
    'Shesha': ['śeṣa', 'ananta'],
    'Kali': ['kālī'],
    'Bhairava': ['bhairava'],
}

PERSONS = {
    'Veda Vyasa': ['vyāsa', 'bādarāyaṇa'],
    'Vasistha': ['vasiṣṭha'],
    'Vishvamitra': ['viśvāmitra'],
    'Shuka': ['śuka'],
    'Parashara': ['parāśara'],
    'Gautama': ['gautama'],
    'Atri': ['atri'],
    'Arjuna': ['arjuna', 'jishnu', 'phālguna', 'pārtha', 'kaunteya'],
    'Bhima': ['bhīma', 'bhīmasena'],
    'Yudhishthira': ['yudhiṣṭhira'],
    'Drona': ['droṇa', 'droṇācārya'],
    'Bhishma': ['bhīṣma', 'devavrata'],
    'Karna': ['karṇa'],
    'Duryodhana': ['duryodhana'],
    'Dhritarashtra': ['dhṛtarāṣṭra'],
    'Pandu': ['pāṇḍu'],
    'Kunti': ['kuntī', 'pṛthā'],
    'Draupadi': ['draupadī'],
    'Ravana': ['rāvaṇa', 'dāśagrīva'],
    'Manu': ['manu'],
    'Janaka': ['janaka'],
    'Bhrigu': ['bhṛgu'],
    'Kashyapa': ['kāśyapa'],
    'Yajnavalkya': ['yājñavalkya'],
    'Nachiketa': ['naciketas'],
    'Prahlada': ['prahlāda'],
    'Ashtavakra': ['aṣṭāvakra'],
    'Vidura': ['vidura'],
    'Sanjaya': ['sañjaya'],
    'Lakshmana': ['lakṣmaṇa'],
    'Vasudeva': ['vasudeva'],
    'Devaki': ['devakī'],
}

PLACES = {
    'Ayodhya': ['ayodhyā'],
    'Mathura': ['mathurā'],
    'Kurukshetra': ['kuru-kṣetra'],
    'Kailas': ['kailāsa'],
    'Lanka': ['laṅkā'],
    'Meru': ['meru'],
    'Himalaya': ['himālaya', 'himavat'],
    'Ganga': ['gaṅgā'],
    'Yamuna': ['yamunā'],
    'Vaikuntha': ['vaikuṇṭha'],
    'Patala': ['pātāla'],
}

CONCEPTS = {
    'Dharma': ['dharma'],
    'Karma': ['karma'],
    'Moksha': ['mokṣa', 'mukti'],
    'Bhakti': ['bhakti'],
    'Jnana': ['jñāna'],
    'Yoga': ['yoga'],
    'Brahman': ['brahman'],
    'Atman': ['ātman', 'ātmā'],
    'Maya': ['māyā'],
    'Prakriti': ['prakṛti'],
    'Purusha': ['puruṣa'],
    'Samsara': ['saṃsāra'],
    'Tapas': ['tapas'],
    'Mantra': ['mantra'],
    'Yajna': ['yajña'],
    'Ahimsa': ['ahiṃsā'],
    'Satya': ['satya'],
    'Gunas': ['guṇa'],
}

ALL_DICTS = [(DEITIES, 'Deity'), (PERSONS, 'Person'), (PLACES, 'Place'), (CONCEPTS, 'Concept')]

# ── Saturation passes ──
results = []
for pass_num in range(1, 4):
    print(f"\n=== PASS {pass_num} ===")
    prev_count = len(entities)
    prev_edge_count = len(edges)
    
    new_found = 0
    new_edges = 0
    
    for title, text in all_texts.items():
        for entity_dict, etype in ALL_DICTS:
            for canonical, aliases in entity_dict.items():
                # Check if this entity is already well-connected to this text
                already_connected = False
                for e in edges:
                    if e['type'] == 'MENTIONED_IN':
                        if entity_by_name.get(canonical, {}).get('GUID') == e.get('source_GUID'):
                            # Check if target scripture matches
                            for s in scriptures:
                                if s['GUID'] == e.get('target_GUID') and title.lower() in s.get('canonical_name','').lower():
                                    already_connected = True
                                    break
                        if already_connected:
                            break
                
                if already_connected:
                    continue
                
                # Count mentions
                count = 0
                for alias in aliases:
                    pattern = r'\b' + re.escape(alias) + r'\b'
                    count += len(re.findall(pattern, text))
                
                if count >= 3:  # Threshold: at least 3 mentions
                    if canonical in entity_by_name:
                        entity_guid = entity_by_name[canonical]['GUID']
                    else:
                        guid = make_guid(f"s{pass_num}-{canonical}")
                        new_e = {
                            'GUID': guid, 'name': canonical, 'type': etype, 'entity_type': etype,
                            'total_mentions': count, 'mentions': count,
                            'sources': [title], 'source_count': 1,
                            'provenance': {'phase': 'v9.6', 'method': 'saturation', 'pass': pass_num}
                        }
                        entities.append(new_e)
                        entity_by_name[canonical] = new_e
                        entity_guid = guid
                        new_found += 1
                    
                    # Find matching scripture
                    for s in scriptures:
                        if title.lower() in s.get('canonical_name','').lower():
                            edges.append({
                                'GUID': make_guid(f"s{pass_num}-{canonical}-{s.get('id','')}"),
                                'type': 'MENTIONED_IN',
                                'source_GUID': entity_guid,
                                'target_GUID': s['GUID'],
                                'evidence': {'entity': canonical, 'scripture': title, 'mentions': count},
                                'confidence': 85, 'phase': 'v9.6'
                            })
                            new_edges += 1
                            break
    
    entity_growth = (len(entities) - prev_count) / max(1, prev_count) * 100
    edge_growth = (len(edges) - prev_edge_count) / max(1, prev_edge_count) * 100
    
    results.append({
        'pass': pass_num,
        'entities_before': prev_count,
        'entities_after': len(entities),
        'new_entities': new_found,
        'entity_growth_pct': round(entity_growth, 2),
        'edges_before': prev_edge_count,
        'edges_after': len(edges),
        'new_edges': new_edges,
        'edge_growth_pct': round(edge_growth, 2)
    })
    
    print(f"  Entities: {prev_count} -> {len(entities)} (+{new_found}, {entity_growth:.2f}%)")
    print(f"  Edges: {prev_edge_count} -> {len(edges)} (+{new_edges}, {edge_growth:.2f}%)")

# Dedup edges
edge_key_set = set()
deduped = []
for e in edges:
    key = (e.get('source_GUID',''), e.get('target_GUID',''), e.get('type',''))
    if key not in edge_key_set:
        edge_key_set.add(key)
        deduped.append(e)
edges = deduped

# Convergence check
converged = all(r['entity_growth_pct'] < 0.1 and r['edge_growth_pct'] < 0.1 for r in results)
print(f"\nConvergence: {'YES' if converged else 'NO'}")
print(f"Pass results: {json.dumps(results, indent=2)}")

# Save
with open(os.path.join(GRAPH_DIR, 'nodes/entity_nodes.json'), 'w') as f:
    json.dump(entities, f, indent=2, ensure_ascii=False)
with open(os.path.join(GRAPH_DIR, 'edges/relationship_edges.json'), 'w') as f:
    json.dump(edges, f, indent=2, ensure_ascii=False)

# Save saturation report
with open(os.path.join(GRAPH_DIR, 'saturation_loop_results.json'), 'w') as f:
    json.dump({'passes': results, 'converged': converged, 'generated': datetime.now().isoformat()}, f, indent=2)

print("\nSaturation loop complete")
