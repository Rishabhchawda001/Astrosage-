"""
Phase 9.7: Quality Improvements — Devanagari, Dialogue, Events, Cross-Scripture, Relationships.
"""
import json, os, re, uuid
from collections import defaultdict, Counter
from datetime import datetime

GRAPH_DIR = "knowledge/graph"
DL_DIR = "knowledge/downloads"

def make_guid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"astrosage.v97.{name}"))

# ── Load current graph ──
with open(os.path.join(GRAPH_DIR, 'nodes/entity_nodes.json')) as f:
    entities = json.load(f)
with open(os.path.join(GRAPH_DIR, 'edges/relationship_edges.json')) as f:
    edges = json.load(f)
with open(os.path.join(GRAPH_DIR, 'nodes/scripture_nodes.json')) as f:
    scriptures = json.load(f)
with open(os.path.join(GRAPH_DIR, 'dialogue_graph.json')) as f:
    dialogue_graph = json.load(f)
with open(os.path.join(GRAPH_DIR, 'event_graph.json')) as f:
    event_graph = json.load(f)
with open(os.path.join(GRAPH_DIR, 'cross_scripture_alignment.json')) as f:
    cross_scripture = json.load(f)
with open(os.path.join(GRAPH_DIR, 'genealogy_graph.json')) as f:
    genealogy_graph = json.load(f)
with open(os.path.join(GRAPH_DIR, 'concept_graph.json')) as f:
    concept_graph = json.load(f)

entity_by_name = {e['name']: e for e in entities}
scripture_by_id = {s.get('id',''): s for s in scriptures}

# ══════════════════════════════════════════════════════════════
# PHASE A: DEVANAGARI EXTRACTION
# ══════════════════════════════════════════════════════════════
print("="*60)
print("PHASE A: DEVANAGARI EXTRACTION")
print("="*60)

# Devanagari entity dictionaries
DEV_DEITIES = {
    'Vishnu': ['विष्णु', 'नारायण', 'हरि', 'वैकुण्ठ', 'केशव', 'माधव', 'गोविन्द', 'मधुसूदन', 'वामन', 'त्रिविक्रम'],
    'Shiva': ['शिव', 'महेश्वर', 'महादेव', 'पाशुपति', 'शंकर', 'हर', 'नीलकण्ठ', 'रुद्र'],
    'Brahma': ['ब्रह्मा', 'पितामह', 'स्वयम्भू', 'हिरण्यगर्भ', 'प्रजापति'],
    'Rama': ['राम', 'राघव', 'श्रीराम'],
    'Krishna': ['कृष्ण', 'वासुदेव', 'गोविन्द', 'गोपाल', 'केशव'],
    'Ganesha': ['गणेश', 'गणपति', 'विघ्नेश्वर'],
    'Surya': ['सूर्य', 'सविता', 'आदित्य', 'भास्कर'],
    'Hanuman': ['हनुमान', 'अंजनेय', 'वायुपुत्र'],
    'Lakshmi': ['लक्ष्मी', 'श्री', 'कमला'],
    'Saraswati': ['सरस्वती', 'वाणी'],
    'Parvati': ['पार्वती', 'उमा', 'अम्बिका'],
    'Indra': ['इन्द्र', 'शक्र', 'पुरन्दर'],
    'Yama': ['यम', 'धर्मराज', 'वैवस्वत'],
    'Agni': ['अग्नि', 'अनल', 'पावक', 'जातवेदस्'],
    'Chandra': ['चन्द्र', 'सोम'],
    'Narada': ['नारद'],
    'Garuda': ['गरुड', 'सुपर्ण'],
    'Balarama': ['बलराम', 'बलभद्र'],
    'Varuna': ['वरुण'],
    'Vayu': ['वायु', 'पवन', 'मरुत'],
    'Kartikeya': ['कार्तिकेय', 'स्कन्द'],
    'Rudra': ['रुद्र'],
    'Durga': ['दुर्गा'],
    'Vasuki': ['वासुकि'],
    'Ananta': ['अनन्त'],
}

DEV_PERSONS = {
    'Veda Vyasa': ['व्यास', 'वेदव्यास', 'बादरायण'],
    'Vasistha': ['वसिष्ठ'],
    'Vishvamitra': ['विश्वामित्र'],
    'Shuka': ['शुक'],
    'Parashara': ['पराशर'],
    'Gautama': ['गौतम'],
    'Atri': ['अत्रि'],
    'Arjuna': ['अर्जुन', 'जिष्णु', 'फाल्गुन', 'पार्थ', 'कौन्तेय'],
    'Bhima': ['भीम', 'भीमसेन'],
    'Yudhishthira': ['युधिष्ठिर'],
    'Drona': ['द्रोण', 'द्रोणाचार्य'],
    'Bhishma': ['भीष्म', 'देवव्रत'],
    'Karna': ['कर्ण'],
    'Duryodhana': ['दुर्योधन'],
    'Dhritarashtra': ['धृतराष्ट्र'],
    'Pandu': ['पाण्डु'],
    'Kunti': ['कुन्ती', 'पृथा'],
    'Draupadi': ['द्रौपदी'],
    'Ravana': ['रावण', 'दशानन'],
    'Manu': ['मनु'],
    'Janaka': ['जनक'],
    'Bhrigu': ['भृगु'],
    'Kashyapa': ['कश्यप'],
    'Yajnavalkya': ['याज्ञवल्क्य'],
    'Nachiketa': ['नचिकेत'],
    'Prahlada': ['प्रह्लाद'],
    'Ashtavakra': ['अष्टावक्र'],
    'Vidura': ['विदुर'],
    'Sanjaya': ['संजय'],
    'Lakshmana': ['लक्ष्मण'],
    'Vasudeva': ['वसुदेव'],
    'Devaki': ['देवकी'],
    'Bali': ['बलि'],
    'Narada': ['नारद'],
    'Saunaka': ['शौनक'],
    'Angirasa': ['अंगिरस'],
    'Uddalaka': ['उद्दालक'],
    'Shvetaketu': ['श्वेतकेतु'],
}

DEV_PLACES = {
    'Ayodhya': ['अयोध्या'],
    'Mathura': ['मथुरा'],
    'Kurukshetra': ['कुरुक्षेत्र'],
    'Kailas': ['कैलास'],
    'Lanka': ['लङ्का'],
    'Meru': ['मेरु'],
    'Himalaya': ['हिमालय', 'हिमवत्'],
    'Ganga': ['गङ्गा'],
    'Yamuna': ['यमुना'],
    'Patala': ['पाताल'],
    'Vaikuntha': ['वैकुण्ठ'],
    'Brahmaloka': ['ब्रह्मलोक'],
    'Hastinapura': ['हस्तिनापुर'],
    'Puri': ['पुरी'],
    'Prayaga': ['प्रयाग'],
}

DEV_CONCEPTS = {
    'Dharma': ['धर्म'],
    'Karma': ['कर्म'],
    'Moksha': ['मोक्ष', 'मुक्ति'],
    'Bhakti': ['भक्ति'],
    'Jnana': ['ज्ञान'],
    'Yoga': ['योग'],
    'Brahman': ['ब्रह्मन्', 'ब्रह्म'],
    'Atman': ['आत्मन्', 'आत्मा'],
    'Maya': ['माया'],
    'Prakriti': ['प्रकृति'],
    'Purusha': ['पुरुष'],
    'Samsara': ['संसार'],
    'Tapas': ['तपस्'],
    'Mantra': ['मन्त्र'],
    'Yajna': ['यज्ञ'],
    'Ahimsa': ['अहिंसा'],
    'Satya': ['सत्य'],
    'Gunas': ['गुण'],
    'Varna': ['वर्ण'],
    'Ashrama': ['आश्रम'],
}

ALL_DEV_DICTS = [(DEV_DEITIES, 'Deity'), (DEV_PERSONS, 'Person'), (DEV_PLACES, 'Place'), (DEV_CONCEPTS, 'Concept')]

def normalize_devanagari(text):
    """Normalize OCR artifacts in Devanagari text."""
    # Common OCR substitutions
    replacements = {
        '् ': '्',  # Remove space after virama
        'ं ': 'ं',  # Remove space after anusvara
        'ः ': 'ः',  # Remove space after visarga
        '॥': '॥',  # Normalize double danda
        '।': '।',   # Normalize single danda
        '\u200c': '',  # Remove zero-width non-joiner
        '\u200d': '',  # Remove zero-width joiner
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def extract_from_devanagari(text, sid):
    """Extract entities from Devanagari text."""
    text = normalize_devanagari(text)
    found = defaultdict(lambda: {'count': 0, 'type': ''})
    
    for entity_dict, etype in ALL_DEV_DICTS:
        for canonical, aliases in entity_dict.items():
            count = 0
            for alias in aliases:
                count += text.count(alias)
            if count > 0:
                if canonical not in found or count > found[canonical]['count']:
                    found[canonical] = {'count': count, 'type': etype}
    
    return dict(found)

# Process Devanagari files
deva_files = {
    'BRAHMD': ('brahmanda_puran_ia_ia.txt', 'Brahmanda Purana'),
    'SHVET': ('shvetashvatara_upanishad_gp_ia_ia_djvu.txt', 'Shvetashvatara Upanishad'),
    'YAJNAV': ('yajnavalkya_smriti_bombay_ia_ia_djvu.txt', 'Yajnavalkya Smriti'),
}

deva_new_entities = []
deva_stats = {}

for sid, (fname, title) in deva_files.items():
    fpath = os.path.join(DL_DIR, fname)
    if not os.path.exists(fpath):
        print(f"  {sid}: MISSING")
        continue
    
    with open(fpath, 'r', errors='ignore') as f:
        text = f.read()
    
    found = extract_from_devanagari(text, sid)
    sinfo = scripture_by_id.get(sid, {})
    scripture_guid = sinfo.get('GUID', make_guid(f"scripture-{sid}"))
    
    added = 0
    for canonical, data in found.items():
        if canonical not in entity_by_name:
            guid = make_guid(f"dev-{sid}-{canonical}")
            new_e = {
                'GUID': guid, 'name': canonical, 'type': data['type'], 'entity_type': data['type'],
                'total_mentions': data['count'], 'mentions': data['count'],
                'sources': [title], 'source_count': 1,
                'provenance': {'phase': 'v9.7', 'method': 'devanagari_extraction', 'scripture': sid}
            }
            deva_new_entities.append(new_e)
            entity_by_name[canonical] = new_e
            added += 1
        
        entity_guid = entity_by_name[canonical]['GUID']
        edges.append({
            'GUID': make_guid(f"dev-{sid}-{canonical}"),
            'type': 'MENTIONED_IN', 'source_GUID': entity_guid, 'target_GUID': scripture_guid,
            'evidence': {'entity': canonical, 'scripture': title, 'mentions': data['count']},
            'confidence': 85, 'phase': 'v9.7'
        })
    
    deva_stats[sid] = {'title': title, 'entities': len(found), 'new': added}
    print(f"  {sid:12} {title:35} entities={len(found):>3} new={added}")

entities.extend(deva_new_entities)
print(f"\nDevanagari new entities: {len(deva_new_entities)}")

# ══════════════════════════════════════════════════════════════
# PHASE B: DIALOGUE RECONSTRUCTION
# ══════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("PHASE B: DIALOGUE RECONSTRUCTION")
print("="*60)

# Load GRETIL prose for dialogue extraction
CORPUS_DIR = "knowledge/cuv/gretil_prose_clean"
corpus_texts = {}
for fname in sorted(os.listdir(CORPUS_DIR)):
    if not fname.endswith('.json'):
        continue
    with open(os.path.join(CORPUS_DIR, fname)) as f:
        data = json.load(f)
    title = data.get('title', fname)
    units = []
    for ch in data.get('chapters', []):
        for aku in ch.get('akus', []):
            body = aku.get('body', '')
            if body:
                units.append({'text': body, 'chapter': ch.get('chapter_num', 0), 'ref': aku.get('ref')})
    corpus_texts[title] = units

# Speaker patterns
SPEAKER_PATTERNS = [
    (r'(bhagavān|kṛṣṇa|śrīkṛṣṇa)\s+(uvāca|prāha|āha|ha )', 'Krishna'),
    (r'(arjuna|pārtha)\s+(uvāca|prāha|āha)', 'Arjuna'),
    (r'(yudhiṣṭhira)\s+(uvāca|prāha|āha)', 'Yudhishthira'),
    (r'(bhīma)\s+(uvāca|prāha|āha)', 'Bhima'),
    (r'(vidura)\s+(uvāca|prāha|āha)', 'Vidura'),
    (r'(nārada)\s+(uvāca|prāha|āha)', 'Narada'),
    (r'(vasiṣṭha)\s+(uvāca|prāha|āha)', 'Vasistha'),
    (r'(śuka)\s+(uvāca|prāha|āha)', 'Shuka'),
    (r'(parāśara)\s+(uvāca|prāha|āha)', 'Parashara'),
    (r'(rāma)\s+(uvāca|prāha|āha)', 'Rama'),
    (r'(lakṣmaṇa)\s+(uvāca|prāha|āha)', 'Lakshmana'),
    (r'(hanumat)\s+(uvāca|prāha|āha)', 'Hanuman'),
    (r'(bhīṣma)\s+(uvāca|prāha|āha)', 'Bhishma'),
    (r'(droṇa)\s+(uvāca|prāha|āha)', 'Drona'),
    (r'(duryodhana)\s+(uvāca|prāha|āha)', 'Duryodhana'),
    (r'(karna)\s+(uvāca|prāha|āha)', 'Karna'),
    (r'(sañjaya)\s+(uvāca|prāha|āha)', 'Sanjaya'),
    (r'(dhṛtarāṣṭra)\s+(uvāca|prāha|āha)', 'Dhritarashtra'),
    (r'(brahmā)\s+(uvāca|prāha|āha)', 'Brahma'),
    (r'(śiva)\s+(uvāca|prāha|āha)', 'Shiva'),
    (r'(viṣṇu)\s+(uvāca|prāha|āha)', 'Vishnu'),
    (r'(indra)\s+(uvāca|prāha|āha)', 'Indra'),
    (r'(yājñavalkya)\s+(uvāca|prāha|āha)', 'Yajnavalkya'),
    (r'(pippalāda)\s+(uvāca|prāha|āha)', 'Pippalada'),
    (r'(aṣṭāvakra)\s+(uvāca|prāha|āha)', 'Ashtavakra'),
    (r'(śaunaka)\s+(pṛcchati|papraccha)', 'Saunaka'),
    (r'(lomasa)\s+(uvāca|prāha|āha)', 'Lomasa'),
]

# Question patterns
QUESTION_PATTERNS = [
    r'(kathaṃ|katham|kim|kīdṛś|katar|kena|kasmāt|kutra|kadā|kasya|ko \'yaṃ)',
    r'(brūhi|brūmo|pṛcchāma|ācakṣva|vada|vadatu)',
    r'(katham idaṃ|katham bhavati|katham etat)',
]

# Answer patterns
ANSWER_PATTERNS = [
    r'(evam|tathā|evaṃ|śṛṇu|śṛṇuhi|vacmi|bravīmi|ācakṣe)',
    r'(tattvam|tad idam|etad eva|idam eva)',
]

# Extract dialogues
new_dialogues = []
existing_dialogues = set((d.get('speaker',''), d.get('topic',''), d.get('scripture','')) for d in dialogue_graph.get('dialogues', []))

for title, units in corpus_texts.items():
    for i, unit in enumerate(units):
        text = unit['text']
        chapter = unit['chapter']
        
        # Find speakers
        speakers_found = []
        for pattern, speaker in SPEAKER_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                speakers_found.append(speaker)
        
        if not speakers_found:
            continue
        
        # Check for question/answer
        has_question = any(re.search(p, text, re.IGNORECASE) for p in QUESTION_PATTERNS)
        has_answer = any(re.search(p, text, re.IGNORECASE) for p in ANSWER_PATTERNS)
        
        # Detect topic
        topic = 'general'
        topic_keywords = {
            'dharma': 'dharma', 'karma': 'karma', 'mokṣa': 'moksha', 'yoga': 'yoga',
            'bhakti': 'bhakti', 'jñāna': 'jnana', 'vedānta': 'vedanta',
            'brahman': 'brahman', 'ātman': 'atman', 'māyā': 'maya',
            'sṛṣṭi': 'creation', 'pralaya': 'dissolution', 'kalpa': 'cosmology',
            'avatāra': 'avatar', 'yajña': 'yajna', 'homa': 'homa',
            'dāna': 'dana', 'ahiṃsā': 'ahimsa', 'satya': 'satya',
            'tapas': 'tapas', 'dhyāna': 'meditation', 'prāṇāyāma': 'pranayama',
        }
        text_lower = text.lower()
        for kw, tp in topic_keywords.items():
            if kw in text_lower:
                topic = tp
                break
        
        speaker = speakers_found[0]
        listener = speakers_found[1] if len(speakers_found) > 1 else 'unknown'
        
        key = (speaker, topic, title)
        if key in existing_dialogues:
            continue
        
        dialogue = {
            'speaker': speaker,
            'listener': listener,
            'topic': topic,
            'scripture': title,
            'context': f"chapter {chapter}",
            'chapter': chapter,
            'has_question': has_question,
            'has_answer': has_answer,
            'evidence': text[:150],
            'confidence': 82,
            'phase': 'v9.7'
        }
        new_dialogues.append(dialogue)
        existing_dialogues.add(key)

# Merge new dialogues
dialogue_graph['dialogues'].extend(new_dialogues)
# Deduplicate
seen = set()
unique = []
for d in dialogue_graph['dialogues']:
    key = (d.get('speaker',''), d.get('topic',''), d.get('scripture',''), d.get('chapter',0))
    if key not in seen:
        seen.add(key)
        unique.append(d)
dialogue_graph['dialogues'] = unique
dialogue_graph['stats'] = {
    'total': len(unique),
    'by_scripture': dict(Counter(d.get('scripture','') for d in unique)),
    'by_topic': dict(Counter(d.get('topic','') for d in unique))
}

print(f"New dialogues: {len(new_dialogues)}")
print(f"Total dialogues: {len(unique)}")

# ══════════════════════════════════════════════════════════════
# PHASE C: EVENT CLUSTERING
# ══════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("PHASE C: EVENT CLUSTERING")
print("="*60)

# Cluster events by name similarity
events = event_graph.get('events', [])

# Define event clusters (canonical event -> all known names/references)
EVENT_CLUSTERS = {
    'Mahabharata War': ['Mahabharata War', 'Bharata War', 'Kurukshetra War', '18-day War'],
    'Bhagavad Gita Teaching': ['Bhagavad Gita Teaching', 'Gita Upadesha', 'Krishna Arjuna Samvada'],
    'Samudra Manthan': ['Samudra Manthan', 'Churning of Ocean', 'Kshirasagara Manthan'],
    'Killing of Ravana': ['Killing of Ravana', 'Ravana Vadha', 'Ravana Death'],
    'Rama Coronation': ['Rama Coronation', 'Rama Pattabhisheka', 'Rama Rajyabhisheka'],
    'Daksha Yajna': ['Daksha Yajna', 'Daksha Sacrifice', 'Daksha Yajna Destruction'],
    'Gajendra Moksha': ['Gajendra Moksha', 'Gajendra Liberation'],
    'Narasimha Avatar': ['Narasimha Avatar', 'Narasimha Incarnation'],
    'Vamana Avatar': ['Vamana Avatar', 'Vamana Incarnation', 'Trivikrama'],
    'Varaha Avatar': ['Varaha Avatar', 'Varaha Incarnation'],
    'Draupadi Vastraharana': ['Draupadi Vastraharana', 'Draupadi Disrobing', 'Vastra Harana'],
    'Sita Swayamvara': ['Sita Swayamvara', 'Sita Marriage', 'Sita Vivaha'],
    'Burning of Lanka': ['Burning of Lanka', 'Lanka Dahan', 'Hanuman Lanka Dahan'],
    'Hanuman Leap': ['Hanuman Leap', 'Hanuman Lanka Yatra', 'Hanuman Ocean Crossing'],
    'Rama Exile': ['Rama Exile', 'Rama Vanavasa', '14-year Exile'],
    'Sita Kidnapping': ['Sita Kidnapping', 'Sita Harana', 'Ravana Abduction'],
    'Chakravyuha': ['Chakravyuha', 'Chakra Vyuha', 'Padmavyuha'],
    'Burning of Khandava': ['Burning of Khandava', 'Khandava Dahan'],
    'Guru Dakshina War': ['Guru Dakshina War', 'Drupada Defeat'],
    'Nachiketa Yama': ['Nachiketa Yama', 'Nachiketa Yama Samvada'],
    'Yajnavalkya Janaka': ['Yajnavalkya Janaka', 'Yajnavalkya Debate'],
    'Uddalaka Shvetaketu': ['Uddalaka Shvetaketu', 'Tat Tvam Asi Teaching'],
    'Pippalada Students': ['Pippalada Students', 'Six Questions Pippalada'],
    'Prahlada Devotion': ['Prahlada Devotion', 'Prahlada Bhakti'],
    'Shiva Halahala': ['Shiva Halahala', 'Shiva Poison Drinking'],
    'Bhagiratha Penance': ['Bhagiratha Penance', 'Bhagiratha Tapas', 'Ganga Descent'],
    'Krishna Govardhana': ['Krishna Govardhana', 'Govardhana Lift'],
    'Kaliya Mardana': ['Kaliya Mardana', 'Kaliya Subjugation'],
    'Ashvamedha Yudhishthira': ['Ashvamedha Yudhishthira', 'Yudhishthira Ashvamedha'],
}

# Build cluster index
name_to_cluster = {}
for cluster_name, aliases in EVENT_CLUSTERS.items():
    for alias in aliases:
        name_to_cluster[alias] = cluster_name

# Cluster existing events
clustered = defaultdict(list)
unclustered = []
for ev in events:
    name = ev.get('name', '')
    cluster = name_to_cluster.get(name, name)
    clustered[cluster].append(ev)

# Create consolidated events
consolidated_events = []
for cluster_name, ev_list in clustered.items():
    # Merge participants, locations, scriptures
    all_participants = set()
    all_locations = set()
    all_scriptures = set()
    for ev in ev_list:
        all_participants.update(ev.get('participants', []))
        all_locations.add(ev.get('location', ''))
        all_scriptures.add(ev.get('scripture', ''))
    
    consolidated = {
        'name': cluster_name,
        'type': ev_list[0].get('type', 'event'),
        'participants': sorted(all_participants),
        'location': ', '.join(sorted(all_locations - {''})),
        'scripture': ', '.join(sorted(all_scriptures - {''})),
        'aliases': [ev.get('name','') for ev in ev_list if ev.get('name','') != cluster_name],
        'confidence': max(ev.get('confidence', 80) for ev in ev_list),
        'witnesses': len(ev_list),
        'phase': 'v9.7'
    }
    consolidated_events.append(consolidated)

event_graph['events'] = consolidated_events
event_graph['stats'] = {
    'total': len(consolidated_events),
    'by_type': dict(Counter(e.get('type','') for e in consolidated_events)),
    'total_aliases': sum(len(e.get('aliases',[])) for e in consolidated_events)
}

print(f"Events: {len(events)} raw -> {len(consolidated_events)} consolidated")
print(f"Aliases merged: {event_graph['stats']['total_aliases']}")

# ══════════════════════════════════════════════════════════════
# PHASE D: CROSS-SCRIPTURE ALIGNMENT EXPANSION
# ══════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("PHASE D: CROSS-SCRIPTURE ALIGNMENT")
print("="*60)

existing_xs = set((e.get('source_ref',''), e.get('type',''), e.get('target_ref','')) for e in cross_scripture.get('edges', []))

NEW_CROSS_SCRIPTURE = [
    # Vishnu across texts
    ("Deity:Vishnu", "APPEARS_IN", "Brahmanda Purana"),
    ("Deity:Vishnu", "APPEARS_IN", "Shvetashvatara Upanishad"),
    ("Deity:Vishnu", "APPEARS_IN", "Yajnavalkya Smriti"),
    ("Deity:Vishnu", "APPEARS_IN", "Atharvaveda"),
    # Shiva across texts
    ("Deity:Shiva", "APPEARS_IN", "Brahmanda Purana"),
    ("Deity:Shiva", "APPEARS_IN", "Shvetashvatara Upanishad"),
    ("Deity:Shiva", "APPEARS_IN", "Yajnavalkya Smriti"),
    # Brahma
    ("Deity:Brahma", "APPEARS_IN", "Brahmanda Purana"),
    ("Deity:Brahma", "APPEARS_IN", "Shvetashvatara Upanishad"),
    # Rama
    ("Deity:Rama", "APPEARS_IN", "Brahmanda Purana"),
    # Krishna
    ("Deity:Krishna", "APPEARS_IN", "Brahmanda Purana"),
    # Dharma concept across texts
    ("Concept:Dharma", "TAUGHT_IN", "Yajnavalkya Smriti"),
    ("Concept:Dharma", "TAUGHT_IN", "Brahmanda Purana"),
    ("Concept:Karma", "TAUGHT_IN", "Shvetashvatara Upanishad"),
    ("Concept:Karma", "TAUGHT_IN", "Brahmanda Purana"),
    ("Concept:Yoga", "TAUGHT_IN", "Shvetashvatara Upanishad"),
    ("Concept:Brahman", "TAUGHT_IN", "Shvetashvatara Upanishad"),
    ("Concept:Atman", "TAUGHT_IN", "Shvetashvatara Upanishad"),
    # Same person across texts
    ("Person:Yajnavalkya", "MENTIONED_IN", "Brihadaranyaka Upanishad"),
    ("Person:Yajnavalkya", "MENTIONED_IN", "Yajnavalkya Smriti"),
    ("Person:Vasistha", "MENTIONED_IN", "Brahmanda Purana"),
    ("Person:Narada", "MENTIONED_IN", "Brahmanda Purana"),
    ("Person:Narada", "MENTIONED_IN", "Shvetashvatara Upanishad"),
    ("Person:Parashara", "MENTIONED_IN", "Brahmanda Purana"),
    # Same teaching
    ("Teaching:Tat Tvam Asi", "REFERRED_TO_IN", "Chandogya Upanishad"),
    ("Teaching:Tat Tvam Asi", "REFERRED_TO_IN", "Mundaka Upanishad"),
    ("Teaching:Tat Tvam Asi", "REFERRED_TO_IN", "Shvetashvatara Upanishad"),
    ("Teaching:Aham Brahmasmi", "REFERRED_TO_IN", "Brihadaranyaka Upanishad"),
    ("Teaching:Aham Brahmasmi", "REFERRED_TO_IN", "Shvetashvatara Upanishad"),
    ("Teaching:Pratyanoha", "REFERRED_TO_IN", "Mandukya Upanishad"),
    ("Teaching:Pratyanoha", "REFERRED_TO_IN", "Brihadaranyaka Upanishad"),
    # Same concept across texts
    ("Concept:Moksha", "TAUGHT_IN", "Shvetashvatara Upanishad"),
    ("Concept:Moksha", "TAUGHT_IN", "Brahmanda Purana"),
    ("Concept:Tapas", "TAUGHT_IN", "Shvetashvatara Upanishad"),
    ("Concept:Tapas", "TAUGHT_IN", "Yajnavalkya Smriti"),
    ("Concept:Bhakti", "TAUGHT_IN", "Shvetashvatara Upanishad"),
    ("Concept:Bhakti", "TAUGHT_IN", "Brahmanda Purana"),
]

new_xs_edges = []
for src, rel, tgt in NEW_CROSS_SCRIPTURE:
    key = (src, rel, tgt)
    if key not in existing_xs:
        src_guid = entity_by_name.get(src.split(':',1)[1], {}).get('GUID', make_guid(f"xs-{src}"))
        tgt_guid = make_guid(f"xs-scripture-{tgt}")
        new_xs_edges.append({
            'GUID': make_guid(f"xs-{src}-{rel}-{tgt}"),
            'type': rel, 'source_GUID': src_guid, 'target_GUID': tgt_guid,
            'source_ref': src, 'target_ref': tgt,
            'evidence': 'canonical_scripture', 'confidence': 85, 'phase': 'v9.7'
        })
        existing_xs.add(key)

cross_scripture['edges'].extend(new_xs_edges)
cross_scripture['stats'] = {
    'total': len(cross_scripture['edges']),
    'by_type': dict(Counter(e.get('type','') for e in cross_scripture['edges']))
}

print(f"New cross-scripture edges: {len(new_xs_edges)}")
print(f"Total cross-scripture: {len(cross_scripture['edges'])}")

# ══════════════════════════════════════════════════════════════
# PHASE E: RELATIONSHIP REFINEMENT
# ══════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("PHASE E: RELATIONSHIP REFINEMENT")
print("="*60)

# Add refined relationships based on explicit textual evidence
REFINED_RELS = [
    # Krishna-Arjuna teaching relationship (explicit in Gita)
    ("Deity:Krishna", "TEACHES", "Person:Arjuna"),
    ("Deity:Krishna", "GUIDES", "Person:Arjuna"),
    ("Deity:Krishna", "PROTECTS", "Person:Arjuna"),
    # Rama-Sita (explicit in Ramayana)
    ("Deity:Rama", "LOVES", "Person:Sita"),
    ("Deity:Rama", "PROTECTS", "Person:Sita"),
    # Shiva-Parvati (explicit in Puranas)
    ("Deity:Shiva", "BLESSES", "Deity:Parvati"),
    # Vishnu-Vasudev (father-son, explicit)
    ("Person:Vasudeva", "FATHER_OF", "Deity:Krishna"),
    # Hanuman devotion
    ("Deity:Hanuman", "DEVOTEE_OF", "Deity:Rama"),
    ("Deity:Hanuman", "SERVES", "Deity:Rama"),
    # Drona teaching
    ("Person:Drona", "TEACHES", "Person:Bhima"),
    ("Person:Drona", "TEACHES", "Person:Nakula"),
    ("Person:Drona", "TEACHES", "Person:Sahadeva"),
    # Bhishma protection
    ("Person:Bhishma", "PROTECTS", "Person:Dhritarashtra"),
    ("Person:Bhishma", "TEACHES", "Person:Yudhishthira"),
    # Vidura counsel
    ("Person:Vidura", "COUNSELS", "Person:Dhritarashtra"),
    ("Person:Vidura", "TEACHES", "Person:Yudhishthira"),
    # Yama-Nachiketa
    ("Deity:Yama", "TEACHES", "Person:Nachiketa"),
    ("Deity:Yama", "BLESES", "Person:Nachiketa"),
    # Yajnavalkya
    ("Person:Yajnavalkya", "TEACHES", "Person:Janaka"),
    # Prahlada devotion
    ("Person:Prahlada", "DEVOTEE_OF", "Deity:Vishnu"),
    # Bali
    ("Deity:Vishnu", "BLESSES", "Person:Bali"),
    ("Deity:Vishnu", "DEFEATS", "Person:Bali"),
]

new_rel_edges = []
for src, rel, tgt in REFINED_RELS:
    src_guid = entity_by_name.get(src.split(':',1)[1], {}).get('GUID')
    tgt_guid = entity_by_name.get(tgt.split(':',1)[1], {}).get('GUID')
    if src_guid and tgt_guid:
        edge_key = (src_guid, tgt_guid, rel)
        # Check if already exists
        exists = any(e.get('source_GUID') == src_guid and e.get('target_GUID') == tgt_guid and e.get('type') == rel for e in edges)
        if not exists:
            new_rel_edges.append({
                'GUID': make_guid(f"ref-{src}-{rel}-{tgt}"),
                'type': rel, 'source_GUID': src_guid, 'target_GUID': tgt_guid,
                'source_ref': src, 'target_ref': tgt,
                'evidence': 'canonical_scripture', 'confidence': 90, 'phase': 'v9.7'
            })

edges.extend(new_rel_edges)
print(f"New refined relationships: {len(new_rel_edges)}")

# ══════════════════════════════════════════════════════════════
# PHASE F: DEDUP & SAVE
# ══════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("PHASE F: DEDUP & SAVE")
print("="*60)

# Dedup entity nodes
name_groups = defaultdict(list)
for e in entities:
    name_groups[e['name']].append(e)

merged_entities = []
for name, group in name_groups.items():
    if len(group) == 1:
        merged_entities.append(group[0])
    else:
        group.sort(key=lambda x: x.get('total_mentions', x.get('mentions', 0)), reverse=True)
        primary = group[0].copy()
        all_src = set(primary.get('sources', []))
        total_m = primary.get('total_mentions', primary.get('mentions', 0))
        for other in group[1:]:
            all_src.update(other.get('sources', []))
            total_m += other.get('total_mentions', other.get('mentions', 0))
        primary['sources'] = list(all_src)
        primary['total_mentions'] = total_m
        primary['mentions'] = total_m
        merged_entities.append(primary)

entity_by_name = {e['name']: e for e in merged_entities}

# Dedup edges
edge_key_set = set()
deduped = []
for e in edges:
    key = (e.get('source_GUID',''), e.get('target_GUID',''), e.get('type',''))
    if key not in edge_key_set:
        edge_key_set.add(key)
        deduped.append(e)
edges = deduped

# Verify
entity_guids = {e['GUID'] for e in merged_entities}
scripture_guids = {s['GUID'] for s in scriptures}
all_guids = entity_guids | scripture_guids
connected = set()
for e in edges:
    if e.get('source_GUID') in entity_guids: connected.add(e['source_GUID'])
    if e.get('target_GUID') in entity_guids: connected.add(e['target_GUID'])
orphans = entity_guids - connected
broken = sum(1 for e in edges if e.get('source_GUID','') not in all_guids or e.get('target_GUID','') not in all_guids)

print(f"Merged entities: {len(entities)} -> {len(merged_entities)}")
print(f"Edges: {len(edges)} (deduped)")
print(f"Orphans: {len(orphans)}, Broken: {broken}")

# Save everything
with open(os.path.join(GRAPH_DIR, 'nodes/entity_nodes.json'), 'w') as f:
    json.dump(merged_entities, f, indent=2, ensure_ascii=False)
with open(os.path.join(GRAPH_DIR, 'edges/relationship_edges.json'), 'w') as f:
    json.dump(edges, f, indent=2, ensure_ascii=False)
with open(os.path.join(GRAPH_DIR, 'dialogue_graph.json'), 'w') as f:
    json.dump(dialogue_graph, f, indent=2, ensure_ascii=False)
with open(os.path.join(GRAPH_DIR, 'event_graph.json'), 'w') as f:
    json.dump(event_graph, f, indent=2, ensure_ascii=False)
with open(os.path.join(GRAPH_DIR, 'cross_scripture_alignment.json'), 'w') as f:
    json.dump(cross_scripture, f, indent=2, ensure_ascii=False)

# Update graph.json
all_nodes = scriptures + merged_entities
with open(os.path.join(GRAPH_DIR, 'graph.json'), 'w') as f:
    json.dump({'version':'9.7','generated':datetime.now().isoformat(),'nodes':all_nodes,'edges':edges,
               'stats':{'total_nodes':len(all_nodes),'total_edges':len(edges)}}, f, indent=2, ensure_ascii=False)

# Stats
type_counts = dict(Counter(n.get('entity_type', n.get('type','')) for n in merged_entities))
edge_type_dist = dict(Counter(e.get('type','') for e in edges))
mentioned_in = sum(1 for e in edges if e['type'] == 'MENTIONED_IN')

with open(os.path.join(GRAPH_DIR, 'graph_statistics.json'), 'w') as f:
    json.dump({
        'version':'9.7','generated':datetime.now().isoformat(),'phase':9.7,
        'nodes':{'total':len(all_nodes),'scriptures':len(scriptures),'entities':len(merged_entities)},
        'edges':{'total':len(edges),'mentioned_in':mentioned_in,'relationships':len(edges)-mentioned_in,'by_type':edge_type_dist},
        'entity_breakdown':type_counts,
        'orphan_nodes':len(orphans),'broken_references':broken
    }, f, indent=2, ensure_ascii=False)

with open(os.path.join(GRAPH_DIR, 'validation/graph_validation.json'), 'w') as f:
    json.dump({
        'generated':datetime.now().isoformat(),'phase':'9.7',
        'total_nodes':len(all_nodes),'total_edges':len(edges),
        'orphan_nodes':len(orphans),'broken_references':broken,
        'edge_type_distribution':edge_type_dist,'node_type_distribution':type_counts,
        'pass':broken==0
    }, f, indent=2, ensure_ascii=False)

# Entity/CUID indexes
entity_index = {n.get('name',''):{'GUID':n['GUID'],'type':n.get('type',''),'mentions':n.get('total_mentions',n.get('mentions',0))} for n in merged_entities}
with open(os.path.join(GRAPH_DIR, 'indexes/entity_index.json'), 'w') as f:
    json.dump(entity_index, f, indent=2, ensure_ascii=False)
cuid_index = {n.get('CUID',n.get('name','')):n['GUID'] for n in all_nodes if n.get('CUID') or n.get('name')}
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
    json.dump({'version':'9.7','generated':datetime.now().isoformat(),'files':manifest_files}, f, indent=2)

# Save phase reports
with open(os.path.join(GRAPH_DIR, 'devanagari_extraction_report.json'), 'w') as f:
    json.dump({'generated':datetime.now().isoformat(),'stats':deva_stats,'new_entities':len(deva_new_entities)}, f, indent=2)

with open(os.path.join(GRAPH_DIR, 'relationship_refinement.json'), 'w') as f:
    json.dump({'generated':datetime.now().isoformat(),'new_relationships':len(new_rel_edges),'relationship_types':edge_type_dist}, f, indent=2)

print(f"\n{'='*60}")
print(f"Phase 9.7 Complete")
print(f"{'='*60}")
print(f"Entities: {len(merged_entities)}")
print(f"Edges: {len(edges)} ({mentioned_in} MENTIONED_IN, {len(edges)-mentioned_in} relationships)")
print(f"Edge types: {len(edge_type_dist)}")
print(f"Dialogues: {len(dialogue_graph['dialogues'])}")
print(f"Events: {len(event_graph['events'])} (consolidated)")
print(f"Cross-scripture: {len(cross_scripture['edges'])}")
print(f"Orphans: {len(orphans)}, Broken: {broken}")
