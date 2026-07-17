"""
Phase 9: Comprehensive Hindu Knowledge Graph Entity Extraction
Extracts all entity types from canonical corpus texts.
"""
import json, os, re, hashlib, uuid
from collections import defaultdict
from datetime import datetime

CORPUS_DIR = "knowledge/cuv/gretil_prose_clean"
GRAPH_DIR = "knowledge/graph"
COMPLETE_ENT_FILE = "knowledge/graph/complete_entity_extraction.json"

# ──────────────────────────────────────────────────────────────
# COMPREHENSIVE ENTITY DICTIONARIES
# Each entry: canonical_name -> (type, aliases_in_sanskrit_iast)
# ──────────────────────────────────────────────────────────────

DEITIES = {
    "Vishnu": ["viṣṇu", "nārāyaṇa", "hari", "vaikuṇṭha-pati", "keśava", "mādhava",
                "govinda", "madhusūdana", "trivikrama", "vāmana", "śrīdhara",
                "hṛṣīkeśa", "kṛṣṇa-vallabha", "yajñeśa", "vaikuntha-natha"],
    "Shiva": ["śiva", "maheśvara", "mahādeva", "pāśupati", "neelakantha", "hara",
              "śaṅkara", "ambikeshvara", "umāpati", "nīlakaṇṭha", "īśāna",
              "bhūteśa", "jagadīśa", "viśvanātha", "natarāja", "bhole-natha"],
    "Brahma": ["brahmā", "pitāmaha", "svayambhū", "hiraṇyagarbha", "prajāpati",
               "vedhas", "nābhya-vedapungava"],
    "Rama": ["rāma", "rāghava", "rāmaśaraṇa", "śrīrāma", "raghunandana",
             "dasarathi", "kākutstha", "sitāpati", "sītā-pati", "viśākhapatra"],
    "Krishna": ["kṛṣṇa", "kṛṣṇa-bhagavān", "mādhava", "keśava", "yādava",
                "muralīdhara", "govinda", "gopāla", "bauddha-kṛṣṇa", "vāsudeva",
                "devakī-nandana", "nanda-nandana", "rādhānātha"],
    "Ganesha": ["gaṇeśa", "gaṇapati", "vighneśvara", "vināyaka", "ekadanta",
                "gaṇanātha", "mahuṣkagaṇa-pati"],
    "Surya": ["sūrya", "savitā", "āditya", "bhāskara", "arka", "mitra",
              "divākara", "sūrya-narayana"],
    "Hanuman": ["hanumat", "anjaneya", "vaṭavānara", "vāyuputra", "mahānada",
                "saṅkarṣaṇa", "pavanaputra", "maruti"],
    "Lakshmi": ["lakṣmī", "śrī", "vaibhava", "kamalā", "padmā", "svadhā",
                "kīrti", "dhrsthi", "puṣṭi", "jaya", "ajitā"],
    "Saraswati": ["sarasvatī", "vāṇī", "bāṇī", "sarasvatyai"],
    "Parvati": ["pārvatī", "girijā", "umā", "śailajā", "himavatī", "devī",
                "durgā", "ambikā", "abhayā"],
    "Durga": ["durgā", "durgatināśinī", "surāri-nāśinī"],
    "Kali": ["kālī", "kālī-mātṛ", "mahākālī"],
    "Indra": ["indra", "śakra", "purandara", "mahendra", "devendra", "meghavāhana"],
    "Yama": ["yama", "dharmarāja", "mrtyu", "kāla", "antaka", "vaivasvata"],
    "Varuna": ["varuṇa", "udaka-pati", "meghanātha"],
    "Vayu": ["vāyu", "pavana", "marut", "anila", "mātariśvan"],
    "Agni": ["agni", "anala", "pāvaka", "jātavedas", "vahni", "hutāśana",
             "veda-mūrti", "śoṣaṇa"],
    "Ganga": ["gaṅgā", "bhāgīrathī", "jāhnavī", "gaṅgā-devī"],
    "Nandi": ["nandī", "nandikeśvara", "śaśigaṇa-pati"],
    "Kartikeya": ["kārttikeya", "skanda", "murugan", "śaktidhara", "guhana",
                  "kumāra", "senaṇya", "ārumuga"],
    "Lakshmana": ["lakṣmaṇa", "bharata", "śatrughna"],
    "Sita": ["sītā", "jānaki", "vaidehī", "mithilā-nandini", "maithilī"],
    "Sugriva": ["sugrīva", "rājāvaṇi"],
    "Vasistha": ["vasiṣṭha", "vasiṣṭha-maharṣi"],
    "Vishvamitra": ["viśvāmitra", "kaushika"],
    "Shukracharya": ["śukrācārya", "ukra"],
    "Brihaspati": ["bṛhaspati", "brahaspati", "guru-sura-guru"],
    "Chandra": ["chandra", "soma", "candra", "indu", "śaśīn"],
    "Narada": ["nārada"],
    "Shesha": ["śeṣa", "ananta", "adi-śeṣa", "ananta-śeṣa"],
    "Garuda": ["garuḍa", "suparṇa", "tārkṣya", "viṣṇuratha"],
    "Vasuki": ["vāsuki"],
    "Shesha": ["ananta", "śeṣa"],
    "Dattatreya": ["dattātreya", "atri-putra"],
    "Balarama": ["balabhadra", "balarāma", "saṅkarṣaṇa"],
    "Jambavan": ["jāmbavān", "jāmbavat"],
    "Ananta": ["ananta", "śeṣa", "anantā"],
}

PERSONS = {
    "Veda Vyasa": ["vyāsa", "veda-vyāsa", "krishna-dvaipayana", "kr̥ṣṇadvāipayana",
                    "vasavyāsa", "bādarāyaṇa"],
    "Vasistha": ["vasiṣṭha", "vasiṣṭha-maharṣi"],
    "Vishvamitra": ["viśvāmitra", "kaushika"],
    "Vashistha": ["vasiṣṭha"],
    "Shuka": ["śuka", "śuka-deva"],
    "Parashara": ["parāśara"],
    "Gautama": ["gautama", "ahalyā-pati"],
    "Bharadvaja": ["bharadvāja", "bārhaspatya"],
    "Atri": ["atri"],
    "Bharata": ["bharata", "rājā-bharata"],
    "Arjuna": ["arjuna", "jishnu", "phālguna", "dhanañjaya", "kīrti",
               "savyasacin", "gāuḍḍaki", "pārtha", "vijaya", "kauṇḍinya",
               "kaunteya", "pāṇḍava"],
    "Bhima": ["bhīma", "bhīmasena", "vṛkodara", "pāṇḍava"],
    "Yudhishthira": ["yudhiṣṭhira", "dharma-putra", "pāṇḍava"],
    "Nakula": ["nakula", "pāṇḍava"],
    "Sahadeva": ["sahadeva", "pāṇḍava"],
    "Drona": ["droṇa", "droṇācārya", "droṇa-bhāradvāja"],
    "Duryodhana": ["duryodhana", "suyodhana", "dhṛtarāṣṭra-putra"],
    "Bhishma": ["bhīṣma", "devavrata", "gāṅgeya"],
    "Karna": ["karṇa", "rādhā-putra", "sūrya-putra", "aṅga-rāja"],
    "Kripacharya": ["kṛpācārya", "kṛpa"],
    "Ashvatthama": ["aśvatthāman", "droṇa-putra"],
    "Vidura": ["vidura", "vidura-nīti"],
    "Dhritarashtra": ["dhṛtarāṣṭra"],
    "Pandu": ["pāṇḍu"],
    "Kunti": ["kuntī", "pṛthā"],
    "Gandhari": ["gāndhārī"],
    "Draupadi": ["draupadī", "kr̥ṣṇā", "pāñcālī"],
    "Subhadra": ["subhadrā"],
    "Abhimanyu": ["abhimanyu"],
    "Ghatotkacha": ["ghaṭotkaca"],
    "Meghanada": ["meghanāda", "indrajit"],
    "Vibhishana": ["vibhīṣaṇa"],
    "Kumbhakarna": ["kumbhakarṇa"],
    "Ravana": ["rāvaṇa", "rākṣasa-rāja", "dāśagrīva", "daśānana", "lankā-pati"],
    "Maricha": ["mārīca"],
    "Surpanakha": ["surpaṇakhā"],
    "Ahiravana": ["ahirāvaṇa"],
    "Shabari": ["śabarī"],
    "Jatayu": ["jatāyu"],
    "Angada": ["aṅgada"],
    "Nala": ["nala", "nala-rāja"],
    "Damayanti": ["damayantī"],
    "Shakuntala": ["śakuntalā"],
    "Dushyanta": ["duṣyanta", "puru-vaṃśa-rāja"],
    "Bharata (king)": ["bharata"],
    "Harishchandra": ["harischandra", "harīścandra", "satya-rāja"],
    "Bhagiratha": ["bhagīratha"],
    "Rantideva": ["rantideva"],
    "Ikshvaku": ["ikṣvāku"],
    "Mandhata": ["mandhātā"],
    "Muchukunda": ["muchukunda"],
    "Trishanku": ["triśaṅku", "satyavrata"],
    "Vena": ["vena", "vena-rāja"],
    "Prithu": ["pṛthu", "pṛthu-rāja"],
    "Rishabhadeva": ["r̥ṣabha", "r̥ṣabhadeva", "adeva"],
    "Narayana Rishi": ["nārāyaṇa-ṛṣi"],
    "Brahmarishi": ["brahmar̥ṣi"],
    "Prajapati": ["prajāpati"],
    "Manu": ["manu", "svāyambhuva-manu", "vaivasvata-manu", "svārociṣa-manu",
             "uttama-manu", "raivata-manu", "cākṣuṣa-manu"],
    "Shravana": ["śravaṇa"],
    "Trishanku": ["triśaṅku"],
    "Ambarisha": ["ambarīṣa"],
    "Dilipa": ["dilīpa"],
    "Raghu": ["raghu"],
    "Shibi": ["śibi", "śibi-rāja"],
    "Trasadasyu": ["trasadasyu"],
    "Aja": ["aja"],
    "Dasharatha": ["daśaratha", "daśaratha-rāja"],
    "Bharadvaja": ["bharadvāja"],
    "Chyavana": ["cyavana"],
    "Ashtavakra": ["aṣṭāvakra", "aṣṭāvakra-guru"],
    "Uddalaka": ["uddālaka", "śvetaketu-pitā"],
    "Shvetaketu": ["śvetaketu"],
    "Yajnavalkya": ["yājñavalkya"],
    "Brihadaranyaka Upanishad sage": [],
    "Jaivali": ["jābāli", "jābāli"],
    "Angirasa": ["aṅgirasa"],
    "Bhrgu": ["bhṛgu", "bhr̥gu"],
    "Sanatkumara": ["sanatkumāra"],
    "Sananda": ["sananda"],
    "Sanat": ["sanat"],
    "Narada (son of Brahma)": ["nārada"],
    "Lomasa": ["lomasa"],
    "Astika": ["astika"],
    "Janamejaya": ["janamejaya"],
    "Parikshit": ["parīkṣit"],
    "Janaka": ["janaka", "janaka-rāja", "videha-rāja"],
    "Lava": ["lava"],
    "Kusha": ["kuśa"],
    "Kakustha": ["kākutstha"],
    "Nimi": ["nimi"],
    "Pushkara": ["puṣkara"],
    "Saunaka": ["śaunaka", "sāuṅkya"],
    "Shounaka": ["śaunaka"],
}

# Kings and royal dynasties
DYNASTIES = {
    "Solar Dynasty": ["sūrya-vaṃśa", "sūryavaṃśa", "ikṣvāku-vaṃśa"],
    "Lunar Dynasty": ["somavaṃśa", "chandra-vaṃśa", "lunar-dynasty"],
    "Pandava Dynasty": ["pāṇḍava-vaṃśa", "kuru-vaṃśa"],
    "Yadava Dynasty": ["yādava-vaṃśa", "vṛṣṇi-vaṃśa"],
    "Bharata Dynasty": ["bharata-vaṃśa"],
    "Kuru Dynasty": ["kuru-vaṃśa"],
    "Puru Dynasty": ["puru-vaṃśa", "puravaṃśa"],
}

PLACES = {
    "Ayodhya": ["ayodhyā", "ayodhyā-purī"],
    "Mathura": ["mathurā", "mathurā-purī", "madhupurī"],
    "Dvaraka": ["dvārakā", "dvārāvatī"],
    "Dwarka": ["dvārakā", "dvārāvatī"],
    "Vrindavan": ["vṛndāvana", "vrindāvana"],
    "Gokul": ["gokula"],
    "Hastinapura": ["hastināpura", "hastinā-pura"],
    "Indraprastha": ["indraprastha", "indra-prastha"],
    "Kurukshetra": ["kuru-kṣetra", "kuru-kshetra", "dharmakṣetra"],
    "Patala": ["pātāla", "pātālaloka"],
    "Svarga": ["svarga", "svarga-loka", "indra-loka", "devaloka"],
    "Brahmaloka": ["brahma-loka", "brahmaloka"],
    "Vaikuntha": ["vaikuṇṭha", "vaikuṇṭha-loka"],
    "Kailas": ["kailāsa", "kailāsa-parvata"],
    "Kailasa": ["kailāsa"],
    "Kashi": ["kāśī", "vārāṇasī", "benares"],
    "Pushkar": ["puṣkara"],
    "Prayaga": ["prayāga", "prāyaga"],
    "Ganga": ["gaṅgā", "gaṅgā-nadī"],
    "Yamuna": ["yamunā", "jamunā"],
    "Narmada": ["narmadā"],
    "Saraswati river": ["sarasvatī-nadī"],
    "Godavari": ["godāvarī"],
    "Meru": ["meru", "meru-parvata"],
    "Himalaya": ["himalaya", "himavat", "himālaya", "himālāya"],
    "Lanka": ["laṅkā"],
    "Puri": ["puri", "jagannātha-purī"],
    "Ujjain": ["ujjayinī", "ujjain"],
    "Madurai": ["madurai", "madurā"],
    "Haridwar": ["haridvāra", "haridvār"],
    "Tirupati": ["tirupati", "venkaṭādri"],
    "Kanchi": ["kāñcī", "kāñcipuram"],
    "Rameshwaram": ["rāmeśvara"],
    "Nashik": ["nāsikā", "nasik"],
    "Kamakhya": ["kāmākhya"],
    "Naimisharanya": ["naimiṣāraṇya"],
    "Nashik": ["nāsikā"],
    "Vindhyas": ["vindhya", "vindhyā"],
    "Vaitarna": ["vaitaṛṇī"],
    "Gandhamadana": ["gandhamādana"],
    "Mithila": ["mithilā"],
    "Videha": ["videha"],
    "Champa": ["campā"],
    "Magadha": ["magadha"],
    "Anga": ["aṅga"],
    "Kosala": ["kośala"],
    "Kuru": ["kuru"],
    "Panchala": ["pañcāla"],
    "Kamarupa": ["kāmarūpa"],
    "Jambudvipa": ["jambūdvīpa"],
    "Patalaloka": ["pātāla-loka"],
    "Svarloka": ["svarga-loka", "svarloka"],
    "Bhuvarloka": ["bhuvarloka", "bhuvar-loka"],
    "Maharloka": ["maharloka"],
    "Janaloka": ["janaloka", "jana-loka"],
    "Tapoloka": ["tapoloka", "tapa-loka"],
    "Satyaloka": ["satyaloka", "satya-loka"],
}

CONCEPTS = {
    "Dharma": ["dharma", "dharmam", "rta"],
    "Karma": ["karma", "karman"],
    "Moksha": ["mokṣa", "mukti", "kaivalya"],
    "Bhakti": ["bhakti", "bhakti-yoga"],
    "Jnana": ["jñāna", "jñāna-yoga", "vidyā"],
    "Yoga": ["yoga", "yogaśāstra"],
    "Brahman": ["brahman", "brahma", "para-brahman", "nirguṇa-brahman"],
    "Atman": ["ātman", "ātmā", "jīvātman"],
    "Maya": ["māyā"],
    "Prakriti": ["prakṛti"],
    "Purusha": ["puruṣa"],
    "Gunas": ["guṇa", "guṇas", "sattva", "rajas", "tamas"],
    "Samsara": ["saṃsāra", "saṃsāra-cakra"],
    "Ahimsa": ["ahiṃsā"],
    "Satya": ["satya"],
    "Tapas": ["tapas", "tapasyā"],
    "Dana": ["dāna"],
    "Dhyana": ["dhyāna", "dhyanam"],
    "Mantra": ["mantra"],
    "Yajna": ["yajña", "iṣṭi", "homa"],
    "Homa": ["homa", "havan"],
    "Shraddha": ["śraddhā"],
    "Diksha": ["dīkṣā"],
    "Pranayama": ["prāṇāyāma"],
    "Varna": ["varṇa"],
    "Ashrama": ["āśrama"],
    "Tattva": ["tattva"],
    "Vidya": ["vidyā"],
    "Upanishad": ["upaniṣad"],
    "Nyaya": ["nyāya"],
    "Vaisheshika": ["vaiśeṣika"],
    "Mimamsa": ["mīmāṃsā"],
    "Sankhya": ["sāṅkhya"],
    "Vedanta": ["vedānta"],
}

WEAPONS = {
    "Chakra": ["cakra", "sudarśana-cakra"],
    "Bow": ["dhanus", "chāpa", "kārmuka"],
    "Sword": ["khadga", "asi", "nandaka"],
    "Spear": ["śūla", "triśūla"],
    "Mace": ["gadā", "muṣṭi"],
    "Vajra": ["vajra"],
    "Trident": ["triśūla", "triśakti"],
    "Brahmastra": ["brahmāstra", "brahma-astra"],
    "Pashupatastra": ["pāśupata-astra", "pāśupatastram"],
    "Sudarshana": ["sudarśana"],
    "Parashu": ["paraśu", "kapaṭa"],
    "Pinaka": ["pināka"],
    "Kapala": ["kapāla"],
    "Khatvanga": ["khaṭvāṅga"],
    "Kunta": ["kunta"],
    "Nagastra": ["nāgāstra"],
    "Gandiva": ["gāṇḍīva"],
    "Vaishnavastra": ["vaiṣṇava-astra", "vaiṣṇavastra"],
    "Sharnga": ["śārṅga"],
    "Agneyastra": ["āgneyāstra"],
}

ANIMALS = {
    "Horse": ["aśva", "haya", "turaṅga", "āśva"],
    "Elephant": ["gaja", "nāga", "hastin", "kara"],
    "Cow": ["go", "gomata", "go-mātṛ"],
    "Garuda": ["garuḍa", "suparṇa"],
    "Swan": ["haṃsa"],
    "Peacock": ["mayūra"],
    "Tiger": ["vyāghra", "siṃha"],
    "Lion": ["siṃha", "simha"],
    "Snake": ["sarpa", "nāga", "ahi"],
    "Crow": ["kāka"],
    "Cuckoo": ["kokila", "krauñca"],
    "Fish": ["matsya"],
    "Rabbit": ["śaśa", "mīna"],
    "Monkey": ["markaṭa", "vānara"],
    "Boar": ["varāha", "vrsabha"],
    "Tortoise": ["kūrma", "kūrma-avatar"],
    "Camel": ["uṣṭra"],
    "Donkey": ["gardabha"],
}

AVATARS = {
    "Matsya Avatar": ["matsya", "matsya-avatāra", "matsya-rūpa"],
    "Kurma Avatar": ["kūrma", "kūrma-avatāra"],
    "Varaha Avatar": ["varāha", "varāha-avatāra", "yajña-varāha"],
    "Narasimha Avatar": ["narasiṃha", "narasiṃha-avatāra"],
    "Vamana Avatar": ["vāmana", "vāmana-avatāra", "upendra"],
    "Parashurama": ["paraśurāma", "bhārgava", "rāma-bhārgava"],
    "Rama": ["rāma"],
    "Krishna": ["kṛṣṇa"],
    "Balarama": ["balabhadra", "balarāma"],
    "Buddha": ["buddha", "gautama-buddha"],
    "Kalki": ["kalki", "kalki-avatāra"],
}

NAKSHATRAS = [
    "ashvini", "bharani", "krittika", "rohini", "mrigashira", "ardra",
    "punarvasu", "pushya", "ashlesha", "magha", "purvaphalguni",
    "uttaraphalguni", "hasta", "chitra", "swati", "vishakha", "anuradha",
    "jyeshtha", "mula", "purvashadha", "uttarashadha", "shravana",
    "dhanishta", "shatabhisha", "purvabhadra", "uttarabhadra", "revati",
    "kritika", "rohini", "mrigashirsha", "aridra", "ashwinee"
]

GRAHAS = [
    "surya", "chandra", "mangala", "budha", "brihaspati", "shukra",
    "shani", "rahu", "ketu", "ravi", "chandra", "mangal", "budh",
    "guru", "shukr", "shani", "rahu", "ketu"
]

LOKAS = [
    "bhuloka", "bhuvarloka", "svarloka", "maharloka", "janaloka",
    "tapoloka", "satyaloka", "atala", "vitala", "sutala", "rasatala",
    "talatala", "mahatala", "patala", "narakaloka", "vaikuntha",
    "kailasa", "brahmaloka", "indraloka", "yamaloka", "chandraloka",
    "suryaloka", "nagaloka", "gandharvaloka", "apsaraloka", "pitriloka"
]

RITUALS = [
    "yajna", "homa", "havan", "agnihotra", "soma-yajna", "ashvamedha",
    "rajasuya", "vajapeya", "agnicayana", "pravargya", "diksha",
    "upanayana", "samavartana", "vivaha", "antyeshti", "shraddha",
    "pitri-paksha", "tarpana", "pitri-yajna", "deva-yajna", "bhuta-yajna",
    "manushya-yajna", "brahma-yajna", "veda-parayana", "japa", "tapa",
    "vrata", "upavasa", "prajapater-vrata"
]

COMMENTARIES = [
    "shankarabhya", "shankara-bhashya", "ramanujabhya", "madhva-bhashya",
    "vallabh-bhashya", "manusmriti-bhashya", "yoga-bhashya", "nyaya-bhashya",
    "bhagavad-gita-bhashya", "brahma-sutra-bhashya", "upanishad-bhashya",
    "padma-purana-bhashya", "vedanta-sara", "vedanta-paribhasha",
    "vishishtadvaita", "advaita", "dvaita", "shuddhadvaita"
]

SCHOOLS = [
    "advaita", "vishishtadvaita", "dvaita", "shuddhadvaita", "achintya-bhedabheda",
    "yoga", "sankhya", "nyaya", "vaisheshika", "mimamsa", "vedanta",
    "pancharatra", "pancaratra", "vaikhanasas", "shaiva-siddhanta",
    "kashmir-shaivism", "tripura-rahasya", "nath-sampradaya", "gaudiya-vaishnavism"
]

AVATARS_SET = set()
for v in AVATARS.values():
    AVATARS_SET.update(v)

print(f"Entity dictionaries loaded:")
print(f"  Deities: {len(DEITIES)}")
print(f"  Persons: {len(PERSONS)}")
print(f"  Places: {len(PLACES)}")
print(f"  Concepts: {len(CONCEPTS)}")
print(f"  Weapons: {len(WEAPONS)}")
print(f"  Animals: {len(ANIMALS)}")
print(f"  Dynasties: {len(DYNASTIES)}")
print(f"  Avatars: {len(AVATARS)}")
print(f"  Nakshatras: {len(NAKSHATRAS)}")
print(f"  Lokas: {len(LOKAS)}")
print(f"  Rituals: {len(RITUALS)}")
print(f"  Commentaries: {len(COMMENTARIES)}")
print(f"  Schools: {len(SCHOOLS)}")

def make_guid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"astrosage.graph.{name}"))

def load_corpus():
    """Load all scripture texts from CUV prose files."""
    corpus = {}
    for fname in sorted(os.listdir(CORPUS_DIR)):
        if not fname.endswith('.json'):
            continue
        fpath = os.path.join(CORPUS_DIR, fname)
        with open(fpath) as f:
            data = json.load(f)
        title = data.get('title', fname.replace('.json',''))
        all_text = []
        for ch in data.get('chapters', []):
            for aku in ch.get('akus', []):
                body = aku.get('body', '')
                if body:
                    all_text.append(body.lower())
        corpus[fname] = {
            'title': title,
            'file': fname,
            'text': ' '.join(all_text),
            'total_units': data.get('total_akus', 0),
            'total_chapters': data.get('total_chapters', 0)
        }
        print(f"  Loaded {title}: {len(all_text)} units, {len(corpus[fname]['text'])} chars")
    return corpus

def extract_entity_mentions(corpus, entity_dict, entity_type):
    """Extract mentions of entities from the corpus."""
    results = {}
    for canonical_name, aliases in entity_dict.items():
        mentions = defaultdict(lambda: {'count': 0, 'contexts': []})
        total_mentions = 0
        sources = set()
        
        for fname, info in corpus.items():
            text = info['text']
            count = 0
            for alias in aliases:
                # Count occurrences using word boundaries
                pattern = r'\b' + re.escape(alias) + r'\b'
                found = re.findall(pattern, text)
                count += len(found)
            if count > 0:
                mentions[fname]['count'] = count
                mentions[fname]['title'] = info['title']
                total_mentions += count
                sources.add(info['title'])
        
        if total_mentions > 0:
            key = f"{entity_type}:{canonical_name}"
            results[key] = {
                'name': canonical_name,
                'type': entity_type,
                'total_mentions': total_mentions,
                'sources': list(sources),
                'by_file': {fname: {'count': m['count'], 'title': m.get('title','')}
                           for fname, m in mentions.items() if m['count'] > 0}
            }
    return results

def main():
    print("\n=== Phase 9: Knowledge Graph Saturation ===")
    print(f"Loading corpus from {CORPUS_DIR}...")
    corpus = load_corpus()
    print(f"\nLoaded {len(corpus)} scriptures")
    
    all_entities = {}
    extraction_stats = {}
    
    entity_sets = [
        (DEITIES, "Deity"), (PERSONS, "Person"), (PLACES, "Place"),
        (CONCEPTS, "Concept"), (WEAPONS, "Weapon"), (ANIMALS, "Animal"),
        (DYNASTIES, "Dynasty"), (AVATARS, "Avatar"),
    ]
    
    for entity_dict, entity_type in entity_sets:
        print(f"\nExtracting {entity_type}s...")
        extracted = extract_entity_mentions(corpus, entity_dict, entity_type)
        all_entities.update(extracted)
        extraction_stats[entity_type] = len(extracted)
        print(f"  Found {len(extracted)} {entity_type} entities with mentions")
    
    # Additional extraction: Nakshatras
    print(f"\nExtracting Nakshatras...")
    nakshatra_mentions = {}
    for nak in NAKSHATRAS:
        total = 0
        sources = set()
        by_file = {}
        for fname, info in corpus.items():
            count = len(re.findall(r'\b' + re.escape(nak) + r'\b', info['text']))
            if count > 0:
                total += count
                sources.add(info['title'])
                by_file[fname] = {'count': count, 'title': info['title']}
        if total > 0:
            key = f"Nakshatra:{nak.title()}"
            nakshatra_mentions[key] = {
                'name': nak.title(), 'type': 'Nakshatra',
                'total_mentions': total, 'sources': list(sources),
                'by_file': by_file
            }
    all_entities.update(nakshatra_mentions)
    extraction_stats['Nakshatra'] = len(nakshatra_mentions)
    print(f"  Found {len(nakshatra_mentions)} Nakshatras")
    
    # Lokas
    print(f"\nExtracting Lokas...")
    loka_mentions = {}
    for loka in LOKAS:
        total = 0
        sources = set()
        by_file = {}
        for fname, info in corpus.items():
            count = len(re.findall(r'\b' + re.escape(loka) + r'\b', info['text']))
            if count > 0:
                total += count
                sources.add(info['title'])
                by_file[fname] = {'count': count, 'title': info['title']}
        if total > 0:
            key = f"Loka:{loka.title()}"
            loka_mentions[key] = {
                'name': loka.title(), 'type': 'Loka',
                'total_mentions': total, 'sources': list(sources),
                'by_file': by_file
            }
    all_entities.update(loka_mentions)
    extraction_stats['Loka'] = len(loka_mentions)
    print(f"  Found {len(loka_mentions)} Lokas")
    
    # Rituals
    print(f"\nExtracting Rituals...")
    ritual_mentions = {}
    for rit in RITUALS:
        total = 0
        sources = set()
        by_file = {}
        for fname, info in corpus.items():
            count = len(re.findall(r'\b' + re.escape(rit) + r'\b', info['text']))
            if count > 0:
                total += count
                sources.add(info['title'])
                by_file[fname] = {'count': count, 'title': info['title']}
        if total > 0:
            key = f"Ritual:{rit.title()}"
            ritual_mentions[key] = {
                'name': rit.title(), 'type': 'Ritual',
                'total_mentions': total, 'sources': list(sources),
                'by_file': by_file
            }
    all_entities.update(ritual_mentions)
    extraction_stats['Ritual'] = len(ritual_mentions)
    print(f"  Found {len(ritual_mentions)} Rituals")
    
    # Schools
    print(f"\nExtracting Schools...")
    school_mentions = {}
    for sch in SCHOOLS:
        total = 0
        sources = set()
        by_file = {}
        for fname, info in corpus.items():
            count = len(re.findall(r'\b' + re.escape(sch) + r'\b', info['text']))
            if count > 0:
                total += count
                sources.add(info['title'])
                by_file[fname] = {'count': count, 'title': info['title']}
        if total > 0:
            key = f"School:{sch.title()}"
            school_mentions[key] = {
                'name': sch.title(), 'type': 'School',
                'total_mentions': total, 'sources': list(sources),
                'by_file': by_file
            }
    all_entities.update(school_mentions)
    extraction_stats['School'] = len(school_mentions)
    print(f"  Found {len(school_mentions)} Schools")
    
    # GRAHAS
    print(f"\nExtracting Grahas...")
    graha_mentions = {}
    for graha in GRAHAS:
        total = 0
        sources = set()
        by_file = {}
        for fname, info in corpus.items():
            count = len(re.findall(r'\b' + re.escape(graha) + r'\b', info['text']))
            if count > 0:
                total += count
                sources.add(info['title'])
                by_file[fname] = {'count': count, 'title': info['title']}
        if total > 0:
            key = f"Graha:{graha.title()}"
            graha_mentions[key] = {
                'name': graha.title(), 'type': 'Graha',
                'total_mentions': total, 'sources': list(sources),
                'by_file': by_file
            }
    all_entities.update(graha_mentions)
    extraction_stats['Graha'] = len(graha_mentions)
    print(f"  Found {len(graha_mentions)} Grahas")
    
    # ── Compute overall stats ──
    total_mentions = sum(e['total_mentions'] for e in all_entities.values())
    total_sources = set()
    for e in all_entities.values():
        total_sources.update(e['sources'])
    
    result = {
        'generated': datetime.now().isoformat(),
        'files_scanned': len(corpus),
        'total_mentions': total_mentions,
        'unique_entities': len(all_entities),
        'extraction_stats': extraction_stats,
        'type_breakdown': {},
        'entities': {}
    }
    
    type_counts = defaultdict(int)
    for key, info in all_entities.items():
        type_counts[info['type']] += 1
        # Flatten for output
        result['entities'][key] = {
            'name': info['name'],
            'type': info['type'],
            'mentions': info['total_mentions'],
            'sources': info['sources'],
            'source_count': len(info['sources'])
        }
    
    result['type_breakdown'] = dict(type_counts)
    
    # Save
    os.makedirs(GRAPH_DIR, exist_ok=True)
    out_path = os.path.join(GRAPH_DIR, 'complete_entity_extraction_v9.json')
    with open(out_path, 'w') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"Phase 9 Entity Extraction Complete")
    print(f"{'='*60}")
    print(f"Scriptures scanned: {len(corpus)}")
    print(f"Total mentions: {total_mentions:,}")
    print(f"Unique entities: {len(all_entities)}")
    print(f"Source scriptures: {len(total_sources)}")
    print(f"\nType breakdown:")
    for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {t}: {c}")
    print(f"\nSaved to: {out_path}")

if __name__ == '__main__':
    main()
