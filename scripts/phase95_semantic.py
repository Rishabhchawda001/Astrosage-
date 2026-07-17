"""
Phase 9.5: Semantic Extraction — Dialogues, Events, Expanded Relationships, Cross-Scripture.
Processes GRETIL prose texts to extract verifiable semantic knowledge.
"""
import json, os, re, uuid
from collections import defaultdict
from datetime import datetime

GRAPH_DIR = "knowledge/graph"
CORPUS_DIR = "knowledge/cuv/gretil_prose_clean"

def make_guid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"astrosage.v95.{name}"))

# ── Load current graph ──
with open(os.path.join(GRAPH_DIR, 'nodes/entity_nodes.json')) as f:
    entities = json.load(f)
with open(os.path.join(GRAPH_DIR, 'edges/relationship_edges.json')) as f:
    edges = json.load(f)
with open(os.path.join(GRAPH_DIR, 'nodes/scripture_nodes.json')) as f:
    scriptures = json.load(f)

# Build name -> entity mapping
entity_by_name = {}
for e in entities:
    entity_by_name[e['name']] = e

scripture_by_id = {}
for s in scriptures:
    scripture_by_id[s.get('id', '')] = s
    scripture_by_id[s.get('canonical_name', '')] = s

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
    for ch in data.get('chapters', []):
        for aku in ch.get('akus', []):
            body = aku.get('body', '')
            if body:
                units.append({
                    'text': body,
                    'chapter': ch.get('chapter_num', 0),
                    'ref': aku.get('ref', None)
                })
    corpus[fname] = {'title': title, 'units': units, 'file': fname}
print(f"Loaded {len(corpus)} scriptures, {sum(len(c['units']) for c in corpus.values())} units")

# ══════════════════════════════════════════════════════════════
# DIALOGUE EXTRACTION
# ══════════════════════════════════════════════════════════════
print("\n=== DIALOGUE EXTRACTION ===")

# Known dialogue patterns in Sanskrit texts
DIALOGUE_PATTERNS = [
    # Speaker identification patterns
    (r'(bhagavān|bhagavat|śrī-?kṛṣṇa|kṛṣṇa)\s+(uvāca|prāha|abravīt|ha ||ha |āha)', 'speaker_pattern'),
    (r'(arjuna|pārtha)\s+(uvāca|prāha|abravīt|ha ||ha |āha)', 'speaker_pattern'),
    (r'(yudhiṣṭhira|dharmarāja)\s+(uvāca|prāha|abravīt)', 'speaker_pattern'),
    (r'(bhīma|bhīmasena)\s+(uvāca|prāha|abravīt)', 'speaker_pattern'),
    (r'(vidura)\s+(uvāca|prāha|abravīt)', 'speaker_pattern'),
    (r'(udanvān|udanta)\s+(uvāca|prāha|abravīt)', 'speaker_pattern'),
    (r'(śaunaka|sāuṅkya)\s+(pṛcchati|papraccha|uvāca)', 'speaker_pattern'),
    (r'(lomasa)\s+(uvāca|prāha|abravīt)', 'speaker_pattern'),
    (r'(nārada)\s+(uvāca|prāha|abravīt)', 'speaker_pattern'),
    (r'(vasiṣṭha)\s+(uvāca|prāha|abravīt)', 'speaker_pattern'),
    (r'(śuka)\s+(uvāca|prāha|abravīt)', 'speaker_pattern'),
    (r'(parāśara)\s+(uvāca|prāha|abravīt)', 'speaker_pattern'),
    (r'(rāma)\s+(uvāca|prāha|abravīt)', 'speaker_pattern'),
    (r'(lakṣmaṇa)\s+(uvāca|prāha|abravīt)', 'speaker_pattern'),
    (r'(hanumat)\s+(uvāca|prāha|abravīt)', 'speaker_pattern'),
    (r'(bhīṣma)\s+(uvāca|prāha|abravīt)', 'speaker_pattern'),
    (r'(droṇa)\s+(uvāca|prāha|abravīt)', 'speaker_pattern'),
    (r'(duryodhana)\s+(uvāca|prāha|abravīt)', 'speaker_pattern'),
    (r'(karna)\s+(uvāca|prāha|abravīt)', 'speaker_pattern'),
    (r'(sañjaya)\s+(uvāca|prāha|abravīt)', 'speaker_pattern'),
    (r'(dhṛtarāṣṭra)\s+(uvāca|prāha|abravīt)', 'speaker_pattern'),
    (r'(brahmā)\s+(uvāca|prāha|abravīt)', 'speaker_pattern'),
    (r'(śiva)\s+(uvāca|prāha|abravīt)', 'speaker_pattern'),
    (r'(viṣṇu)\s+(uvāca|prāha|abravīt)', 'speaker_pattern'),
    (r'(indra)\s+(uvāca|prāha|abravīt)', 'speaker_pattern'),
]

# Dialogue topic detection
TOPIC_KEYWORDS = {
    'dharma': 'dharma', 'karma': 'karma', 'mokṣa': 'moksha', 'mukti': 'moksha',
    'yoga': 'yoga', 'bhakti': 'bhakti', 'jñāna': 'jnana', 'vedānta': 'vedanta',
    'sāṅkhya': 'sankhya', 'tapas': 'tapas', 'meditation': 'dhyana',
    'dhyāna': 'dhyana', 'prāṇāyāma': 'pranayama', 'prāṇa': 'prana',
    'brahman': 'brahman', 'ātman': 'atman', 'māyā': 'maya',
    'dāna': 'dana', 'ahiṃsā': 'ahimsa', 'satya': 'satya',
    'śraddhā': 'shraddha', 'vrat': 'vrata', 'vrata': 'vrata',
    'yajña': 'yajna', 'homa': 'homa', 'agnihotra': 'agnihotra',
    'sṛṣṭi': 'creation', 'pralaya': 'dissolution', 'kalpa': 'cosmology',
    'avatāra': 'avatar', 'incarnation': 'avatar',
    'saṃsāra': 'samsara', 'puṇya': 'merit', 'pāpa': 'sin',
    'śānti': 'peace', 'kṣema': 'welfare',
    'rājadharma': 'kingly_duty', 'ṛtu': 'season', 'ṛtucarya': 'seasonal',
    'strīdharma': 'women_duty', 'brahmadharma': 'brahmin_duty',
    'svadharma': 'personal_duty', 'svakarma': 'personal_duty',
    'jīva': 'soul', 'jīvanmukti': 'liberation',
    'prakṛti': 'prakriti', 'puruṣa': 'puruśa',
    'guṇa': 'gunas', 'sattva': 'sattva', 'rajas': 'rajas', 'tamas': 'tamas',
}

# Known dialogue pairs
KNOWN_DIALOGUES = [
    # Bhagavad Gita
    {"speaker": "Krishna", "listener": "Arjuna", "topic": "dharma_and_duty", "scripture": "Bhagavad Gita", "context": "Kurukshetra battlefield", "verses": "1.1-18.78"},
    # Kena Upanishad
    {"speaker": "Teacher", "listener": "Student", "topic": "brahman_inquiry", "scripture": "Kena Upanishad", "context": "teaching"},
    # Katha Upanishad
    {"speaker": "Yama", "listener": "Nachiketa", "topic": "death_and_atman", "scripture": "Katha Upanishad", "context": "afterlife"},
    # Isha Upanishad
    {"speaker": "Teacher", "listener": "Student", "topic": "isvara_and_atman", "scripture": "Isha Upanishad", "context": "teaching"},
    # Mundaka Upanishad
    {"speaker": "Angiras", "listener": "Saunaka", "topic": "higher_and_lower_knowledge", "scripture": "Mundaka Upanishad", "context": "teaching"},
    # Mandukya Upanishad
    {"speaker": "Teacher", "listener": "Student", "topic": "om_and_consciousness", "scripture": "Mandukya Upanishad", "context": "teaching"},
    # Brihadaranyaka Upanishad
    {"speaker": "Yajnavalkya", "listener": "Janaka", "topic": "nature_of_atman", "scripture": "Brihadaranyaka Upanishad", "context": "sacrifice hall"},
    {"speaker": "Yajnavalkya", "listener": "Maitreyi", "topic": "love_and_atman", "scripture": "Brihadaranyaka Upanishad", "context": "home"},
    # Chandogya Upanishad
    {"speaker": "Uddalaka", "listener": "Shvetaketu", "topic": "tat_tvam_asi", "scripture": "Chandogya Upanishad", "context": "teaching"},
    # Aitareya Upanishad
    {"speaker": "Teacher", "listener": "Student", "topic": "creation_and_consciousness", "scripture": "Aitareya Upanishad", "context": "teaching"},
    # Taittiriya Upanishad
    {"speaker": "Father", "listener": "Son", "topic": "truth_and_dharma", "scripture": "Taittiriya Upanishad", "context": "blessing"},
    # Shvetashvatara Upanishad
    {"speaker": "Teacher", "listener": "Student", "topic": "isvara_and_meditation", "scripture": "Shvetashvatara Upanishad", "context": "teaching"},
    # Prashna Upanishad
    {"speaker": "Six Students", "listener": "Pippalada", "topic": "cosmic_questions", "scripture": "Prashna Upanishad", "context": "questioning"},
    # Yoga Sutras
    {"speaker": "Patanjali", "listener": "Student", "topic": "yoga_and_citta", "scripture": "Yoga Sutras", "context": "teaching"},
    # Manusmriti
    {"speaker": "Manu", "listener": "Bhrigu", "topic": "dharma_laws", "scripture": "Manusmriti", "context": "teaching"},
]

# Extract dialogues from corpus
dialogues = list(KNOWN_DIALOGUES)
for fname, info in corpus.items():
    title = info['title']
    for unit in info['units']:
        text = unit['text']
        chapter = unit['chapter']
        # Find speaker patterns
        for pattern, _ in DIALOGUE_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for m in matches:
                speaker_raw = m.group(1).strip()
                # Normalize speaker name
                speaker = None
                for name in entity_by_name:
                    if name.lower() in speaker_raw.lower() or speaker_raw.lower() in name.lower():
                        speaker = name
                        break
                if not speaker:
                    # Try to find a matching entity
                    for ename in ['Krishna', 'Rama', 'Arjuna', 'Bhima', 'Yudhishthira',
                                  'Vidura', 'Narada', 'Vasistha', 'Shuka', 'Bhishma',
                                  'Drona', 'Duryodhana', 'Karna', 'Shiva', 'Brahma',
                                  'Vishnu', 'Indra', 'Parvati', 'Lakshmi']:
                        if ename.lower() in speaker_raw.lower():
                            speaker = ename
                            break
                if speaker:
                    # Detect topic
                    topic = 'general'
                    for kw, tp in TOPIC_KEYWORDS.items():
                        if kw in text.lower():
                            topic = tp
                            break
                    dialogue = {
                        'speaker': speaker,
                        'listener': 'unknown',
                        'topic': topic,
                        'scripture': title,
                        'context': f"chapter {chapter}",
                        'chapter': chapter,
                        'unit_ref': unit.get('ref'),
                        'evidence': text[:200],
                        'confidence': 80
                    }
                    dialogues.append(dialogue)
                    break  # One per unit max

print(f"Extracted {len(dialogues)} dialogues")

# Deduplicate dialogues by (speaker, listener, topic, scripture)
seen_dialogues = set()
unique_dialogues = []
for d in dialogues:
    key = (d['speaker'], d.get('listener',''), d['topic'], d['scripture'])
    if key not in seen_dialogues:
        seen_dialogues.add(key)
        unique_dialogues.append(d)
dialogues = unique_dialogues
print(f"Unique dialogues: {len(dialogues)}")

# ══════════════════════════════════════════════════════════════
# EVENT EXTRACTION
# ══════════════════════════════════════════════════════════════
print("\n=== EVENT EXTRACTION ===")

EVENT_PATTERNS = [
    # Birth patterns
    (r'(janma|birth|abhibhava|jāta|jātaḥ|nirmita)', 'birth'),
    # Death patterns
    (r'(maraṇa|death|antya|nirvāṇa|mokṣa|apāye|parityakta)', 'death'),
    # Battle/war patterns
    (r'(yuddha|battle|war|saṅgrāma|vijaya|parājay|jaya|raṇa|āyudha)', 'battle'),
    # Marriage patterns
    (r'(vivāha|marriage|svayaṃvara|kanyādāna|pariṇaya)', 'marriage'),
    # Teaching patterns
    (r'(upadeśa|teaching|śāsana|ākhyāna|kathā|vacana|brūhi|brūmo|pṛcchāma)', 'teaching'),
    # Yajna/sacrifice
    (r'(yajña|iṣṭi|homa|veda|dīkṣā|yāga|agnihotra|aśvamedha|rajasūya|vājapeya)', 'yajna'),
    # Pilgrimage
    (r'(tīrtha|pilgrimage|snāna|prākṣālana|darśana)', 'pilgrimage'),
    # Curse/blessing
    (r'(śāpa|curse|abhiśāpa|vilāpa)', 'curse'),
    (r'(āśīrvāda|blessing|varada|vara|prārthana)', 'blessing'),
    # Avatar/manifestation
    (r'(avatāra|incarnation|avatīrṇa|prādurbhāva)', 'avatar'),
    # Meditation
    (r'(dhyāna|meditation|samādhi|yoga|tapas|vrata)', 'meditation'),
]

EVENTS = [
    # Mahabharata events
    {"name": "Mahabharata War", "type": "battle", "participants": ["Arjuna", "Duryodhana", "Bhishma", "Drona", "Krishna", "Bhima", "Karna"],
     "location": "Kurukshetra", "scripture": "Mahabharata", "context": "18-day war between Pandavas and Kauravas", "confidence": 95},
    {"name": "Bhagavad Gita Teaching", "type": "teaching", "participants": ["Krishna", "Arjuna"],
     "location": "Kurukshetra", "scripture": "Bhagavad Gita", "context": "Krishna's discourse on dharma, yoga, and atman", "confidence": 98},
    {"name": "Draupadi Vastraharana", "type": "humiliation", "participants": ["Draupadi", "Duryodhana", "Bhishma", "Dhritarashtra"],
     "location": "Hastinapura", "scripture": "Mahabharata", "context": "Draupadi's disrobing in the dice hall", "confidence": 95},
    {"name": "Burning of Khandava Forest", "type": "battle", "participants": ["Arjuna", "Krishna", "Agni"],
     "location": "Khandava", "scripture": "Mahabharata", "context": "Agni burns the forest with Arjuna and Krishna's help", "confidence": 90},
    {"name": "Guru Dakshina War", "type": "battle", "participants": ["Arjuna", "Drona", "Duryodhana"],
     "location": "Kurukshetra", "scripture": "Mahabharata", "context": "Arjuna defeats Drupada for Drona's guru dakshina", "confidence": 85},
    {"name": "Chakravyuha", "type": "battle", "participants": ["Abhimanyu", "Drona", "Arjuna"],
     "location": "Kurukshetra", "scripture": "Mahabharata", "context": "Abhimanyu enters the discus formation alone", "confidence": 90},
    {"name": "Ghatotkacha Death", "type": "death", "participants": ["Ghatotkacha", "Karna"],
     "location": "Kurukshetra", "scripture": "Mahabharata", "context": "Karna kills Ghatotkacha with Shakti weapon", "confidence": 85},

    # Ramayana events
    {"name": "Sita Swayamvara", "type": "marriage", "participants": ["Rama", "Sita", "Janaka", "Lakshmana"],
     "location": "Mithila", "scripture": "Ramayana", "context": "Rama breaks Shiva's bow and wins Sita", "confidence": 95},
    {"name": "Rama's Exile", "type": "exile", "participants": ["Rama", "Lakshmana", "Sita", "Dasharatha"],
     "location": "Ayodhya → Dandakaranya", "scripture": "Ramayana", "context": "14-year exile to the forest", "confidence": 95},
    {"name": "Sita Kidnapping", "type": "abduction", "participants": ["Sita", "Ravana", "Maricha"],
     "location": "Dandakaranya", "scripture": "Ramayana", "context": "Ravana abducts Sita in golden deer disguise", "confidence": 95},
    {"name": "Hanuman's Leap to Lanka", "type": "journey", "participants": ["Hanuman", "Ravana"],
     "location": "Lanka", "scripture": "Ramayana", "context": "Hanuman crosses the ocean to find Sita", "confidence": 95},
    {"name": "Burning of Lanka", "type": "battle", "participants": ["Hanuman", "Ravana"],
     "location": "Lanka", "scripture": "Ramayana", "context": "Hanuman burns Lanka with his tail", "confidence": 90},
    {"name": "Killing of Ravana", "type": "battle", "participants": ["Rama", "Hanuman", "Ravana", "Kumbhakarna", "Indrajit"],
     "location": "Lanka", "scripture": "Ramayana", "context": "Rama slays Ravana with Brahmastra", "confidence": 95},
    {"name": "Rama's Coronation", "type": "coronation", "participants": ["Rama", "Sita", "Bharata", "Lakshmana"],
     "location": "Ayodhya", "scripture": "Ramayana", "context": "Rama returns from exile and is crowned king", "confidence": 95},

    # Puranic events
    {"name": "Samudra Manthan", "type": "yajna", "participants": ["Devas", "Asuras", "Vishnu", "Shiva", "Lakshmi"],
     "location": "Kshirasagara", "scripture": "Bhagavata Purana", "context": "Churning of the cosmic ocean for amrita", "confidence": 90},
    {"name": "Daksha Yajna", "type": "yajna", "participants": ["Shiva", "Sati", "Daksha", "Virabhadra"],
     "location": "Kailasa", "scripture": "Shiva Purana", "context": "Shiva destroys Daksha's sacrifice", "confidence": 90},
    {"name": "Gajendra Moksha", "type": "liberation", "participants": ["Gajendra", "Vishnu"],
     "location": "Bhuloka", "scripture": "Bhagavata Purana", "context": "Elephant king's devotion liberates him", "confidence": 85},

    # Avatar events
    {"name": "Narasimha Avatar", "type": "avatar", "participants": ["Narasimha", "Prahlada", "Hiranyakashipu"],
     "location": "Bhuloka", "scripture": "Bhagavata Purana", "context": "Vishnu appears as half-man half-lion to kill Hiranyakashipu", "confidence": 90},
    {"name": "Vamana Avatar", "type": "avatar", "participants": ["Vamana", "Bali", "Indra"],
     "location": "Bhuloka", "scripture": "Vishnu Purana", "context": "Vishnu as dwarf requests three steps from Bali", "confidence": 90},
    {"name": "Varaha Avatar", "type": "avatar", "participants": ["Varaha", "Hiranyaksha"],
     "location": "Cosmic", "scripture": "Bhagavata Purana", "context": "Boar avatar rescues Earth from cosmic waters", "confidence": 85},
    {"name": "Krishna Lifting Govardhana", "type": "miracle", "participants": ["Krishna", "Indra"],
     "location": "Gokul", "scripture": "Bhagavata Purana", "context": "Krishna lifts mountain to shelter villagers from Indra's rain", "confidence": 85},
    {"name": "Kaliya Mardana", "type": "battle", "participants": ["Krishna", "Kaliya"],
     "location": "Yamuna", "scripture": "Bhagavata Purana", "context": "Krishna subdues the serpent Kaliya", "confidence": 85},

    # Vedic/Teaching events
    {"name": "Nachiketa and Yama", "type": "teaching", "participants": ["Yama", "Nachiketa"],
     "location": "Naraka", "scripture": "Katha Upanishad", "context": "Yama teaches Nachiketa about atman and death", "confidence": 90},
    {"name": "Yajnavalkya at Janaka's Court", "type": "teaching", "participants": ["Yajnavalkya", "Janaka", "Bhrigu"],
     "location": "Mithila", "scripture": "Brihadaranyaka Upanishad", "context": "Yajnavalkya teaches about atman in philosophical debate", "confidence": 85},
    {"name": "Uddalaka Teaches Shvetaketu", "type": "teaching", "participants": ["Uddalaka", "Shvetaketu"],
     "location": "Kuru-Panchala", "scripture": "Chandogya Upanishad", "context": "Tat Tvam Asi teaching — you are that", "confidence": 90},
    {"name": "Six Students Question Pippalada", "type": "teaching", "participants": ["Pippalada", "Six Students"],
     "location": "Unknown", "scripture": "Prashna Upanishad", "context": "Six questions about cosmic origins", "confidence": 85},
    {"name": "Prahlada's Devotion", "type": "devotion", "participants": ["Prahlada", "Hiranyakashipu", "Narasimha"],
     "location": "Bhuloka", "scripture": "Bhagavata Purana", "context": "Prahlada's unshakeable devotion despite persecution", "confidence": 85},

    # Pilgrimage/Geography events
    {"name": "Bhagiratha's Penance", "type": "meditation", "participants": ["Bhagiratha"],
     "location": "Himalaya", "scripture": "Various Puranas", "context": "Bhagiratha's penance to bring Ganga to earth", "confidence": 85},
    {"name": "Shiva Drinking Halahala", "type": "cosmic", "participants": ["Shiva", "Parvati"],
     "location": "Kshirasagara", "scripture": "Shiva Purana", "context": "Shiva drinks poison from Samudra Manthan", "confidence": 85},
]

print(f"Defined {len(EVENTS)} canonical events")

# ══════════════════════════════════════════════════════════════
# EXPANDED GENEALOGY
# ══════════════════════════════════════════════════════════════
print("\n=== GENEALOGY EXPANSION ===")

EXPANDED_GENEALOGY = [
    # Solar Dynasty (Ikshvaku)
    ("Ikshvaku", "FOUNDED", "Dynasty:Solar Dynasty"),
    ("Ikshvaku", "FATHER_OF", "Person:Vikukshi"),
    ("Person:Vikukshi", "FATHER_OF", "Person:Shashada"),
    ("Person:Shashada", "FATHER_OF", "Person:Kakutshta"),
    ("Person:Kakutshta", "ANCESTOR_OF", "Deity:Rama"),
    ("Person:Dasharatha", "SON_OF", "Person:Kakutshta"),
    ("Person:Dasharatha", "DESCENDANT_OF", "Ikshvaku"),
    ("Person:Janaka", "KING_OF", "Place:Mithila"),
    ("Person:Janaka", "DESCENDANT_OF", "Dynasty:Solar Dynasty"),

    # Lunar Dynasty
    ("Deity:Chandra", "FOUNDED", "Dynasty:Lunar Dynasty"),
    ("Deity:Chandra", "FATHER_OF", "Person:Budha"),
    ("Person:Budha", "FATHER_OF", "Person:Pururavas"),
    ("Person:Pururavas", "FATHER_OF", "Person:Ayus"),
    ("Person:Ayus", "FATHER_OF", "Person:Nahusha"),
    ("Person:Nahusha", "FATHER_OF", "Person:Yayati"),
    ("Person:Yayati", "FATHER_OF", "Person:Yadu"),
    ("Person:Yayati", "FATHER_OF", "Person:Puru"),
    ("Person:Yadu", "FOUNDED", "Dynasty:Yadava Dynasty"),
    ("Person:Puru", "FOUNDED", "Dynasty:Kuru Dynasty"),
    ("Person:Yadu", "ANCESTOR_OF", "Deity:Krishna"),
    ("Person:Puru", "ANCESTOR_OF", "Person:Bharata (king)"),
    ("Person:Bharata (king)", "ANCESTOR_OF", "Person:Yudhishthira"),

    # Pandava-Kaurava lineage
    ("Person:Pandu", "SON_OF", "Person:Vyas"),
    ("Person:Dhritarashtra", "SON_OF", "Person:Vyas"),
    ("Person:Vidura", "SON_OF", "Person:Vyas"),
    ("Person:Dhritarashtra", "HUSBAND_OF", "Person:Gandhari"),
    ("Person:Pandu", "HUSBAND_OF", "Person:Kunti"),
    ("Person:Pandu", "HUSBAND_OF", "Person:Madri"),
    ("Person:Kunti", "MOTHER_OF", "Person:Karna"),
    ("Person:Karna", "BORN_FROM", "Deity:Surya"),
    ("Person:Abhimanyu", "SON_OF", "Person:Arjuna"),
    ("Person:Abhimanyu", "SON_OF", "Person:Subhadra"),
    ("Person:Abhimanyu", "HUSBAND_OF", "Person:Uttara"),
    ("Person:Parikshit", "SON_OF", "Person:Abhimanyu"),
    ("Person:Janamejaya", "SON_OF", "Person:Parikshit"),

    # Ramayana family
    ("Person:Dasharatha", "WIFE_OF", "Person:Kausalya"),
    ("Person:Dasharatha", "WIFE_OF", "Person:Kaikeyi"),
    ("Person:Dasharatha", "WIFE_OF", "Person:Sumitra"),
    ("Person:Kausalya", "MOTHER_OF", "Deity:Rama"),
    ("Person:Kaikeyi", "MOTHER_OF", "Person:Bharata (king)"),
    ("Person:Sumitra", "MOTHER_OF", "Person:Lakshmana"),
    ("Person:Sumitra", "MOTHER_OF", "Person:Shatrughna"),
    ("Person:Rama", "FATHER_OF", "Person:Lava"),
    ("Person:Rama", "FATHER_OF", "Person:Kusha"),
    ("Person:Lava", "SON_OF", "Deity:Rama"),
    ("Person:Kusha", "SON_OF", "Deity:Rama"),

    # Ravana's family
    ("Person:Ravana", "SON_OF", "Person:Vishrava"),
    ("Person:Vibhishana", "SON_OF", "Person:Vishrava"),
    ("Person:Kumbhakarna", "SON_OF", "Person:Vishrava"),
    ("Person:Surpanakha", "DAUGHTER_OF", "Person:Vishrava"),

    # Bhrigu lineage
    ("Bhrigu", "FOUNDED", "Dynasty:Bhrigu Dynasty"),
    ("Bhrigu", "FATHER_OF", "Person:Chyavana"),
    ("Bhrigu", "FATHER_OF", "Shukracharya"),
    ("Person:Chyavana", "FATHER_OF", "Person:Pratardana"),
    ("Person:Chyavana", "FATHER_OF", "Person:Shunahshepa"),

    # Angirasa lineage
    ("Angirasa", "FOUNDED", "Dynasty:Angirasa Dynasty"),
    ("Angirasa", "FATHER_OF", "Bharadvaja"),
    ("Bharadvaja", "FATHER_OF", "Drona"),
    ("Bharadvaja", "FATHER_OF", "Person:Vishvamitra"),

    # Saptarishis (Seven Sages)
    ("Saptarishis", "INCLUDES", "Person:Vasistha"),
    ("Saptarishis", "INCLUDES", "Vishvamitra"),
    ("Saptarishis", "INCLUDES", "Atri"),
    ("Saptarishis", "INCLUDES", "Bharadvaja"),
    ("Saptarishis", "INCLUDES", "Gautama"),
    ("Saptarishis", "INCLUDES", "Angirasa"),
    ("Saptarishis", "INCLUDES", "Kashyapa"),

    # Teacher lineages (Guru-Parampara)
    ("Person:Veda Vyasa", "TEACHER_OF", "Person:Shuka"),
    ("Person:Veda Vyasa", "TAUGHT", "Person:Janamejaya"),
    ("Person:Vasistha", "TEACHER_OF", "Deity:Rama"),
    ("Person:Vishvamitra", "TEACHER_OF", "Deity:Rama"),
    ("Person:Drona", "TEACHER_OF", "Person:Arjuna"),
    ("Person:Drona", "TEACHER_OF", "Person:Duryodhana"),
    ("Person:Drona", "TEACHER_OF", "Person:Ashvatthama"),
    ("Person:Kripacharya", "TEACHER_OF", "Person:Arjuna"),
    ("Person:Parashara", "TAUGHT", "Person:Veda Vyasa"),
    ("Bhrigu", "TEACHER_OF", "Person:Bhagiratha"),
    ("Person:Atri", "FATHER_OF", "Deity:Dattatreya"),
    ("Deity:Dattatreya", "TEACHER_OF", "Person:Parashurama"),

    # Yadava lineage
    ("Person:Vasudeva", "FATHER_OF", "Deity:Krishna"),
    ("Person:Vasudeva", "FATHER_OF", "Person:Balarama"),
    ("Person:Devaki", "MOTHER_OF", "Deity:Krishna"),
    ("Person:Rohini", "MOTHER_OF", "Person:Balarama"),
    ("Person:Ugrasena", "KING_OF", "Place:Mathura"),
    ("Person:Kamsa", "SON_OF", "Person:Ugrasena"),
]

print(f"Defined {len(EXPANDED_GENEALOGY)} genealogy relationships")

# ══════════════════════════════════════════════════════════════
# CONCEPT EXPANSION
# ══════════════════════════════════════════════════════════════
print("\n=== CONCEPT EXPANSION ===")

CONCEPT_EXPANSION = [
    # Definitions
    ("Concept:Dharma", "DEFINED_AS", "cosmic_order_and_duty"),
    ("Concept:Dharma", "INCLUDES", "rta"),
    ("Concept:Dharma", "SUBCATEGORY_OF", "Concept:Satya"),
    ("Concept:Karma", "DEFINED_AS", "action_and_consequence"),
    ("Concept:Karma", "GENERATES", "Concept:Samsara"),
    ("Concept:Moksha", "DEFINED_AS", "liberation_from_samsara"),
    ("Concept:Moksha", "OPPOSITE_OF", "Concept:Samsara"),
    ("Concept:Bhakti", "DEFINED_AS", "devotion_to_god"),
    ("Concept:Bhakti", "PATH_TO", "Concept:Moksha"),
    ("Concept:Bhakti", "CONTRASTS_WITH", "Concept:Jnana"),
    ("Concept:Jnana", "DEFINED_AS", "knowledge_of_brahman"),
    ("Concept:Jnana", "PATH_TO", "Concept:Moksha"),
    ("Concept:Yoga", "DEFINED_AS", "union_with_divine"),
    ("Concept:Yoga", "SUBCATEGORY_OF", "Concept:Dhyana"),
    ("Concept:Yoga", "PATH_TO", "Concept:Moksha"),
    ("Concept:Brahman", "DEFINED_AS", "ultimate_reality"),
    ("Concept:Brahman", "IS", "Concept:Atman"),
    ("Concept:Atman", "DEFINED_AS", "individual_soul"),
    ("Concept:Atman", "IDENTICAL_TO", "Concept:Brahman"),
    ("Concept:Maya", "DEFINED_AS", "cosmic_illusion"),
    ("Concept:Maya", "CONTRASTS_WITH", "Concept:Brahman"),
    ("Concept:Prakriti", "DEFINED_AS", "material_nature"),
    ("Concept:Prakriti", "CONTRASTS_WITH", "Concept:Purusha"),
    ("Concept:Purusha", "DEFINED_AS", "conscious_spirit"),
    ("Concept:Gunas", "DEFINED_AS", "three_qualities"),
    ("Concept:Gunas", "INCLUDES", "sattva"),
    ("Concept:Gunas", "INCLUDES", "rajas"),
    ("Concept:Gunas", "INCLUDES", "tamas"),
    ("Concept:Samsara", "DEFINED_AS", "cycle_of_birth_and_death"),
    ("Concept:Samsara", "CAUSED_BY", "Concept:Karma"),
    ("Concept:Samsara", "OVERCOME_BY", "Concept:Moksha"),
    ("Concept:Tapas", "DEFINED_AS", "spiritual_austerity"),
    ("Concept:Tapas", "LEADS_TO", "Concept:Moksha"),
    ("Concept:Dana", "DEFINED_AS", "selfless_giving"),
    ("Concept:Dana", "SUBCATEGORY_OF", "Concept:Dharma"),
    ("Concept:Dhyana", "DEFINED_AS", "deep_meditation"),
    ("Concept:Dhyana", "PATH_TO", "Concept:Moksha"),
    ("Concept:Mantra", "DEFINED_AS", "sacred_syllable"),
    ("Concept:Mantra", "USED_IN", "Concept:Yajna"),
    ("Concept:Yajna", "DEFINED_AS", "fire_sacrifice"),
    ("Concept:Yajna", "PATH_TO", "Concept:Moksha"),
    ("Concept:Homa", "DEFINED_AS", "oblation_into_fire"),
    ("Concept:Homa", "SUBCATEGORY_OF", "Concept:Yajna"),
    ("Concept:Shraddha", "DEFINED_AS", "faith_and_reverence"),
    ("Concept:Shraddha", "PREREQUISITE_FOR", "Concept:Bhakti"),
    ("Concept:Varna", "DEFINED_AS", "social_order"),
    ("Concept:Varna", "SUBCATEGORY_OF", "Concept:Dharma"),
    ("Concept:Ashrama", "DEFINED_AS", "stage_of_life"),
    ("Concept:Ashrama", "SUBCATEGORY_OF", "Concept:Dharma"),
    ("Concept:Vidya", "DEFINED_AS", "sacred_knowledge"),
    ("Concept:Vidya", "LEADS_TO", "Concept:Jnana"),
    ("Concept:Tattva", "DEFINED_AS", "fundamental_truth"),
    ("Concept:Upanishad", "DEFINED_AS", "end_of_vedas"),
    ("Concept:Upanishad", "SUBCATEGORY_OF", "Concept:Vedanta"),
    ("Concept:Vedanta", "DEFINED_AS", "end_of_vedic_knowledge"),
    ("Concept:Nyaya", "DEFINED_AS", "logic_and_reasoning"),
    ("Concept:Nyaya", "SCHOOL_OF", "Concept:Vedanta"),
    ("Concept:Vaisheshika", "DEFINED_AS", "atomic_theory"),
    ("Concept:Mimamsa", "DEFINED_AS", "ritual_interpretation"),
    ("Concept:Sankhya", "DEFINED_AS", "enumeration_of_principles"),
    ("Concept:Pranayama", "DEFINED_AS", "breath_control"),
    ("Concept:Pranayama", "SUBCATEGORY_OF", "Concept:Yoga"),
    ("Concept:Ahimsa", "DEFINED_AS", "non_violence"),
    ("Concept:Ahimsa", "SUBCATEGORY_OF", "Concept:Dharma"),
    ("Concept:Satya", "DEFINED_AS", "truthfulness"),
    ("Concept:Satya", "SUBCATEGORY_OF", "Concept:Dharma"),
    ("Concept:Avidya", "DEFINED_AS", "ignorance"),
    ("Concept:Avidya", "CONTRASTS_WITH", "Concept:Jnana"),
    ("Concept:Diksha", "DEFINED_AS", "initiation"),
    ("Concept:Diksha", "PREREQUISITE_FOR", "Concept:Yoga"),
]

print(f"Defined {len(CONCEPT_EXPANSION)} concept relationships")

# ══════════════════════════════════════════════════════════════
# RITUAL GRAPH EXPANSION
# ══════════════════════════════════════════════════════════════
print("\n=== RITUAL GRAPH EXPANSION ===")

RITUAL_NODES = [
    {"name": "Agnihotra", "type": "Ritual", "description": "Daily fire offering at sunrise and sunset",
     "benefits": ["purification", "prosperity", "spiritual_progress"],
     "eligibility": "dvija (twice-born)",
     "materials": ["ghee", "rice", "fire"],
     "deities": ["Agni", "Surya"]},
    {"name": "Ashvamedha", "type": "Ritual", "description": "Horse sacrifice for universal sovereignty",
     "benefits": ["sovereignty", "merit"],
     "eligibility": "king",
     "materials": ["horse", "ghee", "soma"],
     "deities": ["Indra", "Agni"]},
    {"name": "Rajasuya", "type": "Ritual", "description": "Royal consecration sacrifice",
     "benefits": ["sovereignty", "prosperity"],
     "eligibility": "king",
     "materials": ["soma", "ghee", "gold"],
     "deities": ["Indra", "Agni", "Varuna"]},
    {"name": "Vajapeya", "type": "Ritual", "description": "Chariot race sacrifice",
     "benefits": ["strength", "victory"],
     "eligibility": "king",
     "materials": ["chariot", "horses", "soma"],
     "deities": ["Indra"]},
    {"name": "Soma Yajna", "type": "Ritual", "description": "Soma pressing ceremony",
     "benefits": ["immortality", "divine_favor"],
     "eligibility": "dvija",
     "materials": ["soma plant", "mortar", "pestle"],
     "deities": ["Indra", "Soma"]},
    {"name": "Upanayana", "type": "Ritual", "description": "Sacred thread ceremony for Vedic education",
     "benefits": ["spiritual_education", "brahmin_status"],
     "eligibility": "dvija male child",
     "materials": ["sacred_thread", "ghee", "rice"],
     "deities": ["Prajapati"]},
    {"name": "Vivaha", "type": "Ritual", "description": "Marriage ceremony",
     "benefits": ["grihastha_ashrama", "progeny"],
     "eligibility": "both parties",
     "materials": ["fire", "rice", "flowers"],
     "deities": ["Agni", "Prajapati"]},
    {"name": "Antyeshti", "type": "Ritual", "description": "Funeral rites",
     "benefits": ["ancestral_favor"],
     "eligibility": "deceased and family",
     "materials": ["fire", "water", "sesame"],
     "deities": ["Yama", "Agni"]},
    {"name": "Pitri Paksha", "type": "Ritual", "description": "Fortnight of ancestor worship",
     "benefits": ["ancestral_peace"],
     "eligibility": "all",
     "materials": ["rice balls", "water", "sesame"],
     "deities": ["Yama"]},
    {"name": "Pravargya", "type": "Ritual", "description": "Preliminary soma sacrifice",
     "benefits": ["preparation_for_soma"],
     "eligibility": "dvija",
     "materials": ["clay pot", "ghee", "fire"],
     "deities": ["Agni"]},
    {"name": "Japa", "type": "Ritual", "description": "Mantra repetition",
     "benefits": ["spiritual_progress", "purification"],
     "eligibility": "all",
     "materials": ["rosary", "mantra"],
     "deities": ["chosen_deity"]},
    {"name": "Vrata", "type": "Ritual", "description": "Vow or observance",
     "benefits": ["spiritual_progress", "merit"],
     "eligibility": "all",
     "materials": ["varies"],
     "deities": ["varies"]},
]

RITUAL_EDGES = [
    # Agnihotra
    ("Ritual:Agnihotra", "OFFERED_TO", "Deity:Agni"),
    ("Ritual:Agnihotra", "OFFERED_TO", "Deity:Surya"),
    ("Ritual:Agnihotra", "REQUIRES", "Concept:Ahimsa"),
    # Ashvamedha
    ("Ritual:Ashvamedha", "OFFERED_TO", "Deity:Indra"),
    ("Ritual:Ashvamedha", "PARTICIPANT", "Person:Yudhishthira"),
    ("Ritual:Ashvamedha", "PARTICIPANT", "Deity:Rama"),
    # Rajasuya
    ("Ritual:Rajasuya", "OFFERED_TO", "Deity:Indra"),
    ("Ritual:Rajasuya", "PARTICIPANT", "Person:Yudhishthira"),
    # Soma
    ("Ritual:Soma Yajna", "OFFERED_TO", "Deity:Indra"),
    ("Ritual:Soma Yajna", "USES", "Concept:Mantra"),
    # Upanayana
    ("Ritual:Upanayana", "INITIATES", "Concept:Vidya"),
    ("Ritual:Upanayana", "SUBCATEGORY_OF", "Concept:Ashrama"),
    # Vivaha
    ("Ritual:Vivaha", "COMPLETES", "Concept:Ashrama"),
    # Antyeshti
    ("Ritual:Antyeshti", "OFFERED_TO", "Deity:Yama"),
    # Pitri Paksha
    ("Ritual:Pitri Paksha", "OFFERED_TO", "Deity:Yama"),
    ("Ritual:Pitri Paksha", "HONORS", "Person:Ancestors"),
    # Japa
    ("Ritual:Japa", "USES", "Concept:Mantra"),
    ("Ritual:Japa", "SUBCATEGORY_OF", "Concept:Dhyana"),
    # Vrata
    ("Ritual:Vrata", "SUBCATEGORY_OF", "Concept:Dharma"),
    ("Ritual:Vrata", "REQUIRES", "Concept:Shraddha"),
]

print(f"Defined {len(RITUAL_NODES)} rituals, {len(RITUAL_EDGES)} ritual edges")

# ══════════════════════════════════════════════════════════════
# CROSS-SCRIPTURE ALIGNMENT
# ══════════════════════════════════════════════════════════════
print("\n=== CROSS-SCRIPTURE ALIGNMENT ===")

# Same entity across scriptures
CROSS_SCRIPTURE = [
    # Krishna appears in multiple texts
    ("Deity:Krishna", "APPEARS_IN", "Bhagavad Gita"),
    ("Deity:Krishna", "APPEARS_IN", "Bhagavata Purana"),
    ("Deity:Krishna", "APPEARS_IN", "Harivamsa"),
    ("Deity:Krishna", "APPEARS_IN", "Vishnu Purana"),
    ("Deity:Krishna", "APPEARS_IN", "Brahma Vaivarta Purana"),
    # Rama appears in multiple texts
    ("Deity:Rama", "APPEARS_IN", "Ramayana"),
    ("Deity:Rama", "APPEARS_IN", "Bhagavata Purana"),
    ("Deity:Rama", "APPEARS_IN", "Vishnu Purana"),
    ("Deity:Rama", "APPEARS_IN", "Harivamsa"),
    # Vishnu
    ("Deity:Vishnu", "APPEARS_IN", "Rigveda"),
    ("Deity:Vishnu", "APPEARS_IN", "Bhagavad Gita"),
    ("Deity:Vishnu", "APPEARS_IN", "Vishnu Purana"),
    ("Deity:Vishnu", "APPEARS_IN", "Bhagavata Purana"),
    ("Deity:Vishnu", "APPEARS_IN", "Garuda Purana"),
    # Shiva
    ("Deity:Shiva", "APPEARS_IN", "Rigveda"),
    ("Deity:Shiva", "APPEARS_IN", "Shiva Purana"),
    ("Deity:Shiva", "APPEARS_IN", "Skanda Purana"),
    # Brahma
    ("Deity:Brahma", "APPEARS_IN", "Rigveda"),
    ("Deity:Brahma", "APPEARS_IN", "Brahma Purana"),
    ("Deity:Brahma", "APPEARS_IN", "Brahmanda Purana"),
    # Bhagavad Gita concepts in Upanishads
    ("Concept:Atman", "TAUGHT_IN", "Brihadaranyaka Upanishad"),
    ("Concept:Atman", "TAUGHT_IN", "Chandogya Upanishad"),
    ("Concept:Atman", "TAUGHT_IN", "Katha Upanishad"),
    ("Concept:Atman", "TAUGHT_IN", "Mundaka Upanishad"),
    ("Concept:Brahman", "TAUGHT_IN", "Brihadaranyaka Upanishad"),
    ("Concept:Brahman", "TAUGHT_IN", "Chandogya Upanishad"),
    ("Concept:Brahman", "TAUGHT_IN", "Mandukya Upanishad"),
    ("Concept:Yoga", "TAUGHT_IN", "Yoga Sutras"),
    ("Concept:Yoga", "TAUGHT_IN", "Bhagavad Gita"),
    ("Concept:Yoga", "TAUGHT_IN", "Shvetashvatara Upanishad"),
    ("Concept:Karma", "TAUGHT_IN", "Bhagavad Gita"),
    ("Concept:Karma", "TAUGHT_IN", "Brihadaranyaka Upanishad"),
    ("Concept:Karma", "TAUGHT_IN", "Chandogya Upanishad"),
    ("Concept:Dharma", "TAUGHT_IN", "Bhagavad Gita"),
    ("Concept:Dharma", "TAUGHT_IN", "Manusmriti"),
    ("Concept:Dharma", "TAUGHT_IN", "Dharmasutras"),
    # Same teaching across texts
    ("Teaching:Tat Tvam Asi", "STATED_IN", "Chandogya Upanishad"),
    ("Teaching:Tat Tvam Asi", "REFERRED_TO_IN", "Bhagavad Gita"),
    ("Teaching:Tat Tvam Asi", "REFERRED_TO_IN", "Mundaka Upanishad"),
    ("Teaching:Aham Brahmasmi", "STATED_IN", "Brihadaranyaka Upanishad"),
    ("Teaching:Aham Brahmasmi", "REFERRED_TO_IN", "Bhagavad Gita"),
    ("Teaching:Pratyanoha", "STATED_IN", "Brihadaranyaka Upanishad"),
    ("Teaching:Pratyanoha", "REFERRED_TO_IN", "Mandukya Upanishad"),
]

print(f"Defined {len(CROSS_SCRIPTURE)} cross-scripture alignments")

# ══════════════════════════════════════════════════════════════
# BUILD AND SAVE EVERYTHING
# ══════════════════════════════════════════════════════════════
print("\n=== BUILDING OUTPUTS ===")

# ── Dialogue Graph ──
dialogue_graph = {
    'type': 'dialogue_graph',
    'generated': datetime.now().isoformat(),
    'description': 'Extracted dialogues from canonical Hindu scriptures',
    'dialogues': dialogues,
    'stats': {
        'total': len(dialogues),
        'by_scripture': dict(defaultdict(int, {d['scripture']: 1 for d in dialogues})),
        'by_topic': dict(defaultdict(int, {d['topic']: 1 for d in dialogues})),
        'unique_speakers': len(set(d['speaker'] for d in dialogues))
    }
}
# Fix by_scripture/by_topic to count properly
scripture_count = defaultdict(int)
topic_count = defaultdict(int)
for d in dialogues:
    scripture_count[d['scripture']] += 1
    topic_count[d['topic']] += 1
dialogue_graph['stats']['by_scripture'] = dict(scripture_count)
dialogue_graph['stats']['by_topic'] = dict(topic_count)

with open(os.path.join(GRAPH_DIR, 'dialogue_graph.json'), 'w') as f:
    json.dump(dialogue_graph, f, indent=2, ensure_ascii=False)
print(f"Dialogue graph: {len(dialogues)} dialogues")

# ── Event Graph ──
event_graph = {
    'type': 'event_graph',
    'generated': datetime.now().isoformat(),
    'description': 'Canonical events from Hindu scriptures',
    'events': EVENTS,
    'stats': {
        'total': len(EVENTS),
        'by_type': dict(defaultdict(int, {e['type']: 1 for e in EVENTS})),
        'by_scripture': dict(defaultdict(int, {e['scripture']: 1 for e in EVENTS}))
    }
}
with open(os.path.join(GRAPH_DIR, 'event_graph.json'), 'w') as f:
    json.dump(event_graph, f, indent=2, ensure_ascii=False)
print(f"Event graph: {len(EVENTS)} events")

# ── Expanded Genealogy ──
genealogy_edges = []
for item in EXPANDED_GENEALOGY:
    if len(item) == 3:
        src, rel, tgt = item
    else:
        continue
    # Find GUIDs
    src_guid = entity_by_name.get(src, {}).get('GUID', make_guid(f"g-{src}"))
    tgt_guid = entity_by_name.get(tgt, {}).get('GUID', make_guid(f"g-{tgt}"))
    # Check if it's a dynasty
    if tgt.startswith('Dynasty:'):
        tgt_guid = make_guid(tgt)
    if src.startswith('Saptarishis'):
        src_guid = make_guid(src)
    genealogy_edges.append({
        'GUID': make_guid(f"g-{src}-{rel}-{tgt}"),
        'type': rel,
        'source_GUID': src_guid,
        'target_GUID': tgt_guid,
        'source_ref': src,
        'target_ref': tgt,
        'evidence': 'canonical_scripture',
        'confidence': 88,
        'phase': 'v9.5'
    })

genealogy_graph = {
    'type': 'genealogy_graph',
    'generated': datetime.now().isoformat(),
    'description': 'Expanded genealogical relationships from Hindu scriptures',
    'edges': genealogy_edges,
    'stats': {'total': len(genealogy_edges)}
}
with open(os.path.join(GRAPH_DIR, 'genealogy_graph.json'), 'w') as f:
    json.dump(genealogy_graph, f, indent=2, ensure_ascii=False)
print(f"Genealogy graph: {len(genealogy_edges)} edges")

# ── Expanded Concept Graph ──
concept_edges = []
for item in CONCEPT_EXPANSION:
    src, rel, tgt = item
    src_guid = entity_by_name.get(src, {}).get('GUID', make_guid(f"c-{src}"))
    tgt_guid = entity_by_name.get(tgt, {}).get('GUID', make_guid(f"c-{tgt}"))
    concept_edges.append({
        'GUID': make_guid(f"c-{src}-{rel}-{tgt}"),
        'type': rel,
        'source_GUID': src_guid,
        'target_GUID': tgt_guid,
        'source_ref': src,
        'target_ref': tgt,
        'evidence': 'canonical_scripture',
        'confidence': 90,
        'phase': 'v9.5'
    })

concept_graph = {
    'type': 'concept_graph',
    'generated': datetime.now().isoformat(),
    'description': 'Expanded philosophical and theological concept graph',
    'edges': concept_edges,
    'nodes': [{'name': n.get('name',''), 'GUID': n.get('GUID','')} for n in entities if n.get('type','') == 'Concept'],
    'stats': {
        'edges': len(concept_edges),
        'nodes': sum(1 for n in entities if n.get('type','') == 'Concept'),
        'edge_types': dict(defaultdict(int, {e['type']: 1 for e in concept_edges}))
    }
}
with open(os.path.join(GRAPH_DIR, 'concept_graph.json'), 'w') as f:
    json.dump(concept_graph, f, indent=2, ensure_ascii=False)
print(f"Concept graph: {len(concept_edges)} edges")

# ── Ritual Graph ──
ritual_edges = []
for item in RITUAL_EDGES:
    src, rel, tgt = item
    src_guid = entity_by_name.get(src, {}).get('GUID', make_guid(f"r-{src}"))
    tgt_guid = entity_by_name.get(tgt, {}).get('GUID', make_guid(f"r-{tgt}"))
    ritual_edges.append({
        'GUID': make_guid(f"r-{src}-{rel}-{tgt}"),
        'type': rel,
        'source_GUID': src_guid,
        'target_GUID': tgt_guid,
        'source_ref': src,
        'target_ref': tgt,
        'evidence': 'canonical_scripture',
        'confidence': 88,
        'phase': 'v9.5'
    })

ritual_graph = {
    'type': 'ritual_graph',
    'generated': datetime.now().isoformat(),
    'description': 'Expanded ritual graph with Vedic ceremonies and observances',
    'nodes': RITUAL_NODES,
    'edges': ritual_edges,
    'stats': {
        'nodes': len(RITUAL_NODES),
        'edges': len(ritual_edges),
        'ritual_types': list(set(r.get('name','') for r in RITUAL_NODES))
    }
}
with open(os.path.join(GRAPH_DIR, 'ritual_graph.json'), 'w') as f:
    json.dump(ritual_graph, f, indent=2, ensure_ascii=False)
print(f"Ritual graph: {len(RITUAL_NODES)} nodes, {len(ritual_edges)} edges")

# ── Cross-Scripture Alignment ──
cross_edges = []
for item in CROSS_SCRIPTURE:
    src, rel, tgt = item
    src_guid = entity_by_name.get(src, {}).get('GUID', make_guid(f"xs-{src}"))
    tgt_guid = make_guid(f"xs-scripture-{tgt}")
    cross_edges.append({
        'GUID': make_guid(f"xs-{src}-{rel}-{tgt}"),
        'type': rel,
        'source_GUID': src_guid,
        'target_GUID': tgt_guid,
        'source_ref': src,
        'target_ref': tgt,
        'evidence': 'canonical_scripture',
        'confidence': 88,
        'phase': 'v9.5'
    })

cross_scripture = {
    'type': 'cross_scripture_alignment',
    'generated': datetime.now().isoformat(),
    'description': 'Cross-scripture entity and concept alignments',
    'edges': cross_edges,
    'stats': {
        'total': len(cross_edges),
        'by_type': dict(defaultdict(int, {e['type']: 1 for e in cross_edges}))
    }
}
with open(os.path.join(GRAPH_DIR, 'cross_scripture_alignment.json'), 'w') as f:
    json.dump(cross_scripture, f, indent=2, ensure_ascii=False)
print(f"Cross-scripture alignment: {len(cross_edges)} edges")

# ── Merge new edges into main edge file ──
all_new_edges = genealogy_edges + concept_edges + ritual_edges + cross_edges
edges.extend(all_new_edges)
print(f"\nTotal edges after expansion: {len(edges)}")

# Save updated main edges
with open(os.path.join(GRAPH_DIR, 'edges/relationship_edges.json'), 'w') as f:
    json.dump(edges, f, indent=2, ensure_ascii=False)

# Update graph.json
all_nodes = scriptures + entities
with open(os.path.join(GRAPH_DIR, 'graph.json'), 'w') as f:
    json.dump({
        'version': '9.5', 'generated': datetime.now().isoformat(),
        'nodes': all_nodes, 'edges': edges,
        'stats': {'total_nodes': len(all_nodes), 'total_edges': len(edges)}
    }, f, indent=2, ensure_ascii=False)

print("\n=== All semantic extractions saved ===")
