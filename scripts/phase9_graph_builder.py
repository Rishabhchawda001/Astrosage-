"""
Phase 9: Build Knowledge Graph — nodes, edges, relationships, sub-graphs, QA.
"""
import json, os, re, uuid, hashlib
from collections import defaultdict
from datetime import datetime

GRAPH_DIR = "knowledge/graph"
CUV_DIR = "knowledge/cuv/gretil_prose_clean"

def make_guid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"astrosage.v9.{name}"))

def load_extraction():
    with open(os.path.join(GRAPH_DIR, 'complete_entity_extraction_v9.json')) as f:
        return json.load(f)

def load_existing_graph():
    """Load existing Phase 8 graph for continuity."""
    with open(os.path.join(GRAPH_DIR, 'nodes/entity_nodes.json')) as f:
        old_entities = json.load(f)
    with open(os.path.join(GRAPH_DIR, 'nodes/scripture_nodes.json')) as f:
        old_scriptures = json.load(f)
    with open(os.path.join(GRAPH_DIR, 'edges/relationship_edges.json')) as f:
        old_edges = json.load(f)
    return old_entities, old_scriptures, old_edges

def load_scripture_nodes():
    with open(os.path.join(GRAPH_DIR, 'nodes/scripture_nodes.json')) as f:
        return json.load(f)

# ──────────────────────────────────────────────────────────────
# RELATIONSHIP DEFINITIONS (canonical, evidence-backed)
# ──────────────────────────────────────────────────────────────

GENEALOGY_EDGES = [
    # Ramayana genealogy (Solar Dynasty)
    ("Person:Dasharatha", "FATHER_OF", "Deity:Rama"),
    ("Person:Dasharatha", "FATHER_OF", "Person:Bharata (king)"),
    ("Person:Dasharatha", "FATHER_OF", "Person:Lakshmana"),
    ("Person:Dasharatha", "FATHER_OF", "Person:Shatrughna"),
    ("Deity:Rama", "HUSBAND_OF", "Person:Sita"),
    ("Deity:Rama", "FATHER_OF", "Person:Lava"),
    ("Deity:Rama", "FATHER_OF", "Person:Kusha"),
    ("Person:Lakshmana", "BROTHER_OF", "Deity:Rama"),
    ("Person:Sita", "DAUGHTER_OF", "Person:Janaka"),
    # Mahabharata genealogy (Lunar Dynasty)
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
    # Krishna connections
    ("Deity:Krishna", "HUSBAND_OF", "Person:Subhadra"),
    ("Deity:Krishna", "FATHER_OF", "Person:Pradyumna"),
    ("Deity:Balarama", "BROTHER_OF", "Deity:Krishna"),
    ("Person:Subhadra", "SISTER_OF", "Deity:Krishna"),
    # Dasharatha / Rama
    ("Person:Vasistha", "TEACHER_OF", "Deity:Rama"),
    ("Person:Vishvamitra", "TEACHER_OF", "Deity:Rama"),
    ("Person:Drona", "TEACHER_OF", "Person:Arjuna"),
    ("Person:Drona", "TEACHER_OF", "Person:Duryodhana"),
    ("Person:Bhishma", "GUARDIAN_OF", "Person:Yudhishthira"),
    # Ravana connections
    ("Person:Vibhishana", "BROTHER_OF", "Person:Ravana"),
    ("Person:Kumbhakarna", "BROTHER_OF", "Person:Ravana"),
    ("Person:Surpanakha", "SISTER_OF", "Person:Ravana"),
    ("Person:Ravana", "RULER_OF", "Place:Lanka"),
    # Surya / Chandra dynasty
    ("Deity:Surya", "FATHER_OF", "Person:Karna"),
    ("Deity:Chandra", "ANCESTOR_OF", "Person:Yudhishthira"),
    # Brahma connections
    ("Deity:Brahma", "CREATOR_OF", "Deity:Saraswati"),
    ("Deity:Brahma", "CREATOR_OF", "Deity:Surya"),
    ("Deity:Brahma", "CREATOR_OF", "Deity:Chandra"),
    # Shiva connections
    ("Deity:Shiva", "HUSBAND_OF", "Deity:Parvati"),
    ("Deity:Shiva", "FATHER_OF", "Deity:Kartikeya"),
    ("Deity:Shiva", "FATHER_OF", "Deity:Ganesha"),
    ("Deity:Parvati", "MOTHER_OF", "Deity:Kartikeya"),
    ("Deity:Parvati", "MOTHER_OF", "Deity:Ganesha"),
    # Vishnu avatars
    ("Deity:Vishnu", "INCARNATION_OF", "Avatar:Matsya Avatar"),
    ("Deity:Vishnu", "INCARNATION_OF", "Avatar:Kurma Avatar"),
    ("Deity:Vishnu", "INCARNATION_OF", "Avatar:Varaha Avatar"),
    ("Deity:Vishnu", "INCARNATION_OF", "Avatar:Narasimha Avatar"),
    ("Deity:Vishnu", "INCARNATION_OF", "Avatar:Vamana Avatar"),
    ("Deity:Vishnu", "INCARNATION_OF", "Person:Rama"),
    ("Deity:Vishnu", "INCARNATION_OF", "Deity:Krishna"),
    ("Deity:Vishnu", "INCARNATION_OF", "Avatar:Parashurama"),
    # Vedic connections
    ("Person:Veda Vyasa", "COMPILER_OF", "Concept:Vedanta"),
    ("Person:Narada", "SON_OF", "Deity:Brahma"),
    ("Person:Narada", "STUDENT_OF", "Deity:Brahma"),
    # Sage teacher-student lineages
    ("Person:Vasistha", "TEACHER_OF", "Person:Vishvamitra"),
    ("Person:Atri", "TEACHER_OF", "Person:Dattatreya"),
    # Concept associations
    ("Concept:Bhakti", "PATH_TO", "Concept:Moksha"),
    ("Concept:Jnana", "PATH_TO", "Concept:Moksha"),
    ("Concept:Yoga", "PATH_TO", "Concept:Moksha"),
    ("Concept:Karma", "LEADS_TO", "Concept:Samsara"),
    ("Concept:Moksha", "LIBERATION_FROM", "Concept:Samsara"),
    ("Concept:Brahman", "IDENTICAL_TO", "Concept:Atman"),
    ("Concept:Dharma", "GUIDES", "Concept:Karma"),
    # Place relationships
    ("Place:Meru", "CENTER_OF", "Loka:Bhuloka"),
    ("Place:Vaikuntha", "ABODE_OF", "Deity:Vishnu"),
    ("Place:Kailas", "ABODE_OF", "Deity:Shiva"),
    ("Place:Hastinapura", "CAPITAL_OF", "Dynasty:Kuru Dynasty"),
    ("Place:Indraprastha", "CAPITAL_OF", "Dynasty:Pandava Dynasty"),
    ("Place:Kurukshetra", "BATTLEFIELD_OF", "Person:Arjuna"),
    ("Place:Lanka", "KINGDOM_OF", "Person:Ravana"),
    # Weapon associations
    ("Weapon:Gandiva", "WIELDED_BY", "Person:Arjuna"),
    ("Weapon:Chakra", "WIELDED_BY", "Deity:Vishnu"),
    ("Weapon:Trident", "WIELDED_BY", "Deity:Shiva"),
    ("Weapon:Vajra", "WIELDED_BY", "Deity:Indra"),
    ("Weapon:Brahmastra", "WIELDED_BY", "Person:Arjuna"),
    ("Weapon:Parashu", "WIELDED_BY", "Avatar:Parashurama"),
    ("Weapon:Sharnga", "WIELDED_BY", "Deity:Vishnu"),
    ("Weapon:Sudarshana", "WIELDED_BY", "Deity:Vishnu"),
    ("Weapon:Pinaka", "WIELDED_BY", "Deity:Shiva"),
    # Animal associations
    ("Animal:Garuda", "VEHICLE_OF", "Deity:Vishnu"),
    ("Animal:Nandi", "VEHICLE_OF", "Deity:Shiva"),
    ("Animal:Swan", "VEHICLE_OF", "Deity:Brahma"),
    ("Animal:Hamsa", "VEHICLE_OF", "Deity:Brahma"),
    ("Animal:Peacock", "VEHICLE_OF", "Deity:Kartikeya"),
    ("Animal:Mouse", "VEHICLE_OF", "Deity:Ganesha"),
    # Text/commentary relationships
    ("Commentary:Bhagavadgita-4comm", "COMMENTARY_ON", "Deity:Krishna"),
    ("Commentary:Bhagavadgita-Shankara", "COMMENTARY_ON", "Deity:Krishna"),
    # Cross-scripture links (text referencing another text)
    ("Concept:Upanishad", "REFERENCED_BY", "Concept:Brahman"),
    ("Concept:Yoga", "REFERENCED_BY", "Concept:Bhakti"),
]

EDGES = []
for src, rel, tgt in GENEALOGY_EDGES:
    EDGES.append({
        'GUID': make_guid(f"{src}-{rel}-{tgt}"),
        'type': rel,
        'source_GUID': make_guid(src),
        'target_GUID': make_guid(tgt),
        'source_ref': src,
        'target_ref': tgt,
        'evidence': 'canonical_scripture',
        'confidence': 95,
        'phase': 'v9'
    })

# ──────────────────────────────────────────────────────────────
# BUILD GRAPH
# ──────────────────────────────────────────────────────────────

def build_nodes(extraction, scripture_nodes):
    """Build merged node list."""
    entities = extraction.get('entities', {})
    nodes = []
    guid_map = {}
    
    # Scripture nodes (from Phase 8, kept intact)
    for s in scripture_nodes:
        sid = s.get('id', s.get('canonical_name', ''))
        guid = s.get('GUID', make_guid(f"scripture:{sid}"))
        s['GUID'] = guid
        s['node_type'] = 'Scripture'
        guid_map[f"Scripture:{sid}"] = guid
        nodes.append(s)
    
    # Entity nodes (new v9 extraction)
    for key, info in entities.items():
        guid = make_guid(key)
        node = {
            'GUID': guid,
            'CUID': key,
            'node_type': info.get('type', 'Entity'),
            'name': info.get('name', key.split(':')[-1]),
            'entity_type': info.get('type', 'unknown'),
            'total_mentions': info.get('mentions', 0),
            'source_count': info.get('source_count', 0),
            'sources': info.get('sources', []),
            'provenance': {
                'phase': 'v9',
                'extraction_method': 'pattern_match',
                'corpus': 'GRETIL_prose_clean'
            },
            'confidence': min(95, 70 + info.get('source_count', 0))
        }
        guid_map[key] = guid
        nodes.append(node)
    
    return nodes, guid_map

def build_edges(extraction, guid_map):
    """Build all edges: MENTIONED_IN + relationship edges."""
    entities = extraction.get('entities', {})
    edges = []
    
    # ── MENTIONED_IN edges (entity appears in scripture) ──
    for key, info in entities.items():
        entity_guid = guid_map.get(key)
        if not entity_guid:
            continue
        for source_name in info.get('sources', []):
            # Find matching scripture node
            for skey, sguid in guid_map.items():
                if skey.startswith('Scripture:') and skey.split(':',1)[1] in source_name:
                    edge = {
                        'GUID': make_guid(f"{key}-MENTIONED_IN-{skey}"),
                        'type': 'MENTIONED_IN',
                        'source_GUID': entity_guid,
                        'target_GUID': sguid,
                        'evidence': {
                            'entity': info.get('name',''),
                            'scripture': source_name,
                            'mentions': info.get('mentions',0)
                        },
                        'confidence': 90,
                        'phase': 'v9'
                    }
                    edges.append(edge)
                    break
    
    # ── Relationship edges (canonical relationships) ──
    for edge_def in EDGES:
        src_guid = guid_map.get(edge_def['source_ref'])
        tgt_guid = guid_map.get(edge_def['target_ref'])
        if src_guid and tgt_guid:
            edge = {
                'GUID': edge_def['GUID'],
                'type': edge_def['type'],
                'source_GUID': src_guid,
                'target_GUID': tgt_guid,
                'source_ref': edge_def['source_ref'],
                'target_ref': edge_def['target_ref'],
                'evidence': edge_def['evidence'],
                'confidence': edge_def['confidence'],
                'phase': edge_def['phase']
            }
            edges.append(edge)
    
    return edges

def build_subgraphs(nodes, edges, guid_map, extraction):
    """Build specialized sub-graphs."""
    
    # Dialogue graph
    dialogue_graph = {
        'type': 'dialogue_graph',
        'description': 'Teacher-student and dialogue relationships',
        'edges': [e for e in edges if e['type'] in ('TEACHER_OF', 'STUDENT_OF', 'REFERENCED_IN')],
        'stats': {}
    }
    dialogue_graph['stats']['total_dialogue_edges'] = len(dialogue_graph['edges'])
    
    # Event graph
    event_graph = {
        'type': 'event_graph',
        'description': 'Key events from Hindu scriptures',
        'events': [
            {'name': 'Mahabharata War', 'participants': ['Arjuna', 'Duryodhana', 'Bhishma', 'Drona'],
             'location': 'Kurukshetra', 'speaker': 'Krishna', 'scripture': 'Bhagavad Gita'},
            {'name': 'Sita Swayamvara', 'participants': ['Rama', 'Sita', 'Janaka'],
             'location': 'Mithila', 'scripture': 'Ramayana'},
            {'name': 'Samudra Manthan', 'participants': ['Devas', 'Asuras', 'Vishnu', 'Shiva'],
             'location': 'Kshirasagara', 'scripture': 'Puranas'},
            {'name': 'Daksha Yajna', 'participants': ['Shiva', 'Sati', 'Daksha'],
             'location': 'Kailasa', 'scripture': 'Shiva Purana'},
            {'name': 'Bhagavad Gita Teaching', 'participants': ['Krishna', 'Arjuna'],
             'location': 'Kurukshetra', 'scripture': 'Bhagavad Gita'},
            {'name': 'Churning of Milk Ocean', 'participants': ['Vishnu', 'Shesha', 'Devas', 'Asuras'],
             'location': 'Kshirasagara', 'scripture': 'Bhagavata Purana'},
            {'name': 'Rama\'s Exile', 'participants': ['Rama', 'Lakshmana', 'Sita', 'Dasharatha'],
             'location': 'Dandakaranya', 'scripture': 'Ramayana'},
            {'name': 'Burning of Khandava Forest', 'participants': ['Arjuna', 'Krishna', 'Agni'],
             'location': 'Khandava', 'scripture': 'Mahabharata'},
            {'name': 'Gajendra Moksha', 'participants': ['Gajendra', 'Vishnu'],
             'location': 'Bhuloka', 'scripture': 'Bhagavata Purana'},
            {'name': 'Draupadi Vastraharana', 'participants': ['Draupadi', 'Duryodhana', 'Bhishma'],
             'location': 'Hastinapura', 'scripture': 'Mahabharata'},
            {'name': 'Hanuman\'s Leap to Lanka', 'participants': ['Hanuman', 'Ravana'],
             'location': 'Lanka', 'scripture': 'Ramayana'},
            {'name': 'Killing of Ravana', 'participants': ['Rama', 'Hanuman', 'Ravana'],
             'location': 'Lanka', 'scripture': 'Ramayana'},
        ],
        'stats': {'total_events': 12}
    }
    
    # Genealogy graph
    genealogy_edges = [e for e in edges if e['type'] in ('FATHER_OF', 'MOTHER_OF', 'SON_OF', 'DAUGHTER_OF', 'HUSBAND_OF', 'WIFE_OF', 'BROTHER_OF', 'SISTER_OF', 'ANCESTOR_OF', 'INCARNATION_OF')]
    genealogy_graph = {
        'type': 'genealogy_graph',
        'description': 'Hindu genealogical relationships',
        'edges': genealogy_edges,
        'stats': {'total_genealogy_edges': len(genealogy_edges)}
    }
    
    # Concept graph
    concept_edges = [e for e in edges if e['type'] in ('PATH_TO', 'LEADS_TO', 'GUIDES', 'IDENTICAL_TO', 'LIBERATION_FROM')]
    concept_nodes = [n for n in nodes if n.get('entity_type') == 'Concept' or n.get('node_type') == 'Concept']
    concept_graph = {
        'type': 'concept_graph',
        'description': 'Philosophical and theological concept relationships',
        'edges': concept_edges,
        'nodes': [{'name': n.get('name',''), 'GUID': n.get('GUID','')} for n in concept_nodes],
        'stats': {'total_concept_edges': len(concept_edges), 'total_concept_nodes': len(concept_nodes)}
    }
    
    # Ritual graph
    ritual_nodes = [n for n in nodes if n.get('entity_type') == 'Ritual']
    ritual_graph = {
        'type': 'ritual_graph',
        'description': 'Vedic ritual entities and references',
        'nodes': [{'name': n.get('name',''), 'GUID': n.get('GUID',''), 'mentions': n.get('total_mentions',0)} for n in ritual_nodes],
        'stats': {'total_ritual_nodes': len(ritual_nodes)}
    }
    
    # Astronomy graph
    astronomy_nodes = [n for n in nodes if n.get('entity_type') in ('Nakshatra', 'Graha', 'Astronomy')]
    astronomy_graph = {
        'type': 'astronomy_graph',
        'description': 'Astronomical entities from Hindu scriptures',
        'nodes': [{'name': n.get('name',''), 'GUID': n.get('GUID',''), 'type': n.get('entity_type',''), 'mentions': n.get('total_mentions',0)} for n in astronomy_nodes],
        'stats': {'total_astronomy_nodes': len(astronomy_nodes)}
    }
    
    # Geography graph
    geo_edges = [e for e in edges if e['type'] in ('LOCATED_IN', 'ABODE_OF', 'CAPITAL_OF', 'CENTER_OF', 'BATTLEFIELD_OF', 'KINGDOM_OF')]
    geo_nodes = [n for n in nodes if n.get('entity_type') == 'Place' or n.get('node_type') == 'Place']
    geography_graph = {
        'type': 'geography_graph',
        'description': 'Geographic entities and spatial relationships',
        'edges': geo_edges,
        'nodes': [{'name': n.get('name',''), 'GUID': n.get('GUID',''), 'mentions': n.get('total_mentions',0)} for n in geo_nodes],
        'stats': {'total_geo_nodes': len(geo_nodes), 'total_geo_edges': len(geo_edges)}
    }
    
    # Weapon/Animal association graph
    assoc_edges = [e for e in edges if e['type'] in ('WIELDED_BY', 'VEHICLE_OF')]
    association_graph = {
        'type': 'association_graph',
        'description': 'Weapon/Animal divine associations',
        'edges': assoc_edges,
        'stats': {'total_association_edges': len(assoc_edges)}
    }
    
    return {
        'dialogue_graph': dialogue_graph,
        'event_graph': event_graph,
        'genealogy_graph': genealogy_graph,
        'concept_graph': concept_graph,
        'ritual_graph': ritual_graph,
        'astronomy_graph': astronomy_graph,
        'geography_graph': geography_graph,
        'association_graph': association_graph,
    }

def graph_qa(nodes, edges, guid_map):
    """Run graph quality assurance checks."""
    issues = []
    warnings = []
    
    # Check for orphan nodes (no edges)
    node_guids = set(n['GUID'] for n in nodes)
    connected_guids = set()
    for e in edges:
        connected_guids.add(e.get('source_GUID',''))
        connected_guids.add(e.get('target_GUID',''))
    orphans = node_guids - connected_guids
    if orphans:
        warnings.append(f"{len(orphans)} orphan nodes (no edges)")
    
    # Check for broken references
    broken = 0
    for e in edges:
        if e.get('source_GUID') not in node_guids:
            broken += 1
        if e.get('target_GUID') not in node_guids:
            broken += 1
    if broken:
        issues.append(f"{broken} broken edge references")
    
    # Check for duplicate GUIDs
    all_guids = [n['GUID'] for n in nodes]
    dup_guids = len(all_guids) - len(set(all_guids))
    if dup_guids:
        issues.append(f"{dup_guids} duplicate node GUIDs")
    
    edge_guids = [e['GUID'] for e in edges]
    dup_edge = len(edge_guids) - len(set(edge_guids))
    if dup_edge:
        issues.append(f"{dup_edge} duplicate edge GUIDs")
    
    # Check for cyclic genealogies
    parent_edges = [e for e in edges if e['type'] in ('FATHER_OF', 'MOTHER_OF')]
    # Simple cycle detection
    parent_map = defaultdict(set)
    for e in parent_edges:
        parent_map[e['source_GUID']].add(e['target_GUID'])
    cycles = 0
    for src in parent_map:
        for child in parent_map[src]:
            if src in parent_map.get(child, set()):
                cycles += 1
    if cycles:
        issues.append(f"{cycles} potential cyclic genealogies")
    
    # Check evidence coverage
    entities_with_provenance = sum(1 for n in nodes if n.get('sources') or n.get('provenance'))
    evidence_pct = (entities_with_provenance / len(nodes) * 100) if nodes else 0
    
    # Entity type balance
    type_counts = defaultdict(int)
    for n in nodes:
        t = n.get('entity_type', n.get('node_type', 'unknown'))
        type_counts[t] += 1
    
    return {
        'generated': datetime.now().isoformat(),
        'total_nodes': len(nodes),
        'total_edges': len(edges),
        'orphan_nodes': len(orphans),
        'broken_references': broken,
        'duplicate_node_guids': dup_guids,
        'duplicate_edge_guids': dup_edge,
        'cyclic_genealogies': cycles,
        'entities_with_provenance': entities_with_provenance,
        'evidence_coverage_pct': round(evidence_pct, 1),
        'node_type_distribution': dict(type_counts),
        'issues': issues,
        'warnings': warnings,
        'pass': len(issues) == 0
    }

def graph_completeness(nodes, edges, extraction):
    """Compute completeness metrics."""
    entities = extraction.get('entities', {})
    
    # How many entities have evidence
    with_evidence = sum(1 for e in entities.values() if e.get('sources'))
    without_evidence = len(entities) - with_evidence
    
    # How many have relationships
    entity_keys = set(e for e in entities.keys())
    connected_entities = set()
    for edge in edges:
        for ref in [edge.get('source_ref',''), edge.get('target_ref','')]:
            if ref in entity_keys:
                connected_entities.add(ref)
    disconnected = entity_keys - connected_entities
    
    # Edge type coverage
    edge_types = defaultdict(int)
    for e in edges:
        edge_types[e['type']] += 1
    
    return {
        'generated': datetime.now().isoformat(),
        'total_entities': len(entities),
        'entities_with_evidence': with_evidence,
        'entities_without_evidence': without_evidence,
        'evidence_coverage_pct': round(with_evidence / len(entities) * 100, 1) if entities else 0,
        'entities_with_relationships': len(connected_entities),
        'entities_without_relationships': len(disconnected),
        'relationship_coverage_pct': round(len(connected_entities) / len(entities) * 100, 1) if entities else 0,
        'edge_type_distribution': dict(edge_types),
        'total_edges': len(edges)
    }

def review_queue(qa_result):
    """Generate review queue for issues."""
    items = []
    for issue in qa_result.get('issues', []):
        items.append({
            'type': 'issue',
            'description': issue,
            'severity': 'high',
            'status': 'needs_review'
        })
    for warning in qa_result.get('warnings', []):
        items.append({
            'type': 'warning',
            'description': warning,
            'severity': 'medium',
            'status': 'needs_review'
        })
    return items

def main():
    print("=== Phase 9: Graph Builder ===")
    
    # Load data
    extraction = load_extraction()
    print(f"Loaded extraction: {extraction['unique_entities']} entities")
    
    old_entities, old_scriptures, old_edges = load_existing_graph()
    print(f"Loaded Phase 8 graph: {len(old_entities)} entities, {len(old_scriptures)} scriptures, {len(old_edges)} edges")
    
    # Build new graph
    nodes, guid_map = build_nodes(extraction, old_scriptures)
    print(f"Built {len(nodes)} nodes ({len(guid_map)} unique GUIDs)")
    
    edges = build_edges(extraction, guid_map)
    print(f"Built {len(edges)} edges")
    
    # Build sub-graphs
    subgraphs = build_subgraphs(nodes, edges, guid_map, extraction)
    for name, sg in subgraphs.items():
        stats = sg.get('stats', {})
        print(f"  {name}: {stats}")
    
    # Graph QA
    qa = graph_qa(nodes, edges, guid_map)
    print(f"\nGraph QA: {'PASS' if qa['pass'] else 'FAIL'}")
    print(f"  Nodes: {qa['total_nodes']}, Edges: {qa['total_edges']}")
    print(f"  Orphans: {qa['orphan_nodes']}, Broken refs: {qa['broken_references']}")
    print(f"  Evidence coverage: {qa['evidence_coverage_pct']}%")
    if qa['issues']:
        for i in qa['issues']:
            print(f"  ISSUE: {i}")
    if qa['warnings']:
        for w in qa['warnings']:
            print(f"  WARNING: {w}")
    
    # Completeness
    comp = graph_completeness(nodes, edges, extraction)
    print(f"\nCompleteness:")
    print(f"  Evidence: {comp['evidence_coverage_pct']}%")
    print(f"  Relationships: {comp['relationship_coverage_pct']}%")
    
    # Review queue
    rq = review_queue(qa)
    print(f"\nReview queue: {len(rq)} items")
    
    # ── Save all outputs ──
    os.makedirs(GRAPH_DIR, exist_ok=True)
    os.makedirs(os.path.join(GRAPH_DIR, 'nodes'), exist_ok=True)
    os.makedirs(os.path.join(GRAPH_DIR, 'edges'), exist_ok=True)
    os.makedirs(os.path.join(GRAPH_DIR, 'validation'), exist_ok=True)
    os.makedirs(os.path.join(GRAPH_DIR, 'indexes'), exist_ok=True)
    os.makedirs(os.path.join(GRAPH_DIR, 'schemas'), exist_ok=True)
    
    # Main outputs
    with open(os.path.join(GRAPH_DIR, 'nodes', 'entity_nodes.json'), 'w') as f:
        json.dump([n for n in nodes if n.get('node_type') != 'Scripture'], f, indent=2, ensure_ascii=False)
    
    with open(os.path.join(GRAPH_DIR, 'nodes', 'scripture_nodes.json'), 'w') as f:
        json.dump([n for n in nodes if n.get('node_type') == 'Scripture'], f, indent=2, ensure_ascii=False)
    
    with open(os.path.join(GRAPH_DIR, 'edges', 'relationship_edges.json'), 'w') as f:
        json.dump(edges, f, indent=2, ensure_ascii=False)
    
    # Merged graph
    graph = {
        'version': '9.0',
        'generated': datetime.now().isoformat(),
        'phase': 9,
        'nodes': nodes,
        'edges': edges,
        'stats': {
            'total_nodes': len(nodes),
            'total_edges': len(edges),
            'entity_types': qa['node_type_distribution']
        }
    }
    with open(os.path.join(GRAPH_DIR, 'graph.json'), 'w') as f:
        json.dump(graph, f, indent=2, ensure_ascii=False)
    
    # Sub-graphs
    for name, sg in subgraphs.items():
        with open(os.path.join(GRAPH_DIR, f'{name}.json'), 'w') as f:
            json.dump(sg, f, indent=2, ensure_ascii=False)
    
    # Statistics
    stats = {
        'version': '9.0',
        'generated': datetime.now().isoformat(),
        'nodes': {
            'total': len(nodes),
            'scriptures': sum(1 for n in nodes if n.get('node_type') == 'Scripture'),
            'entities': sum(1 for n in nodes if n.get('node_type') != 'Scripture')
        },
        'edges': {'total': len(edges)},
        'entity_breakdown': {},
        'edge_breakdown': defaultdict(int),
        'total_mentions': extraction.get('total_mentions', 0),
        'files_scanned': extraction.get('files_scanned', 0)
    }
    for n in nodes:
        t = n.get('entity_type', n.get('node_type', 'unknown'))
        stats['entity_breakdown'][t] = stats['entity_breakdown'].get(t, 0) + 1
    for e in edges:
        stats['edge_breakdown'][e['type']] += 1
    stats['edge_breakdown'] = dict(stats['edge_breakdown'])
    
    with open(os.path.join(GRAPH_DIR, 'graph_statistics.json'), 'w') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    # Validation
    with open(os.path.join(GRAPH_DIR, 'validation', 'graph_validation.json'), 'w') as f:
        json.dump(qa, f, indent=2, ensure_ascii=False)
    
    # Completeness
    with open(os.path.join(GRAPH_DIR, 'graph_completeness.json'), 'w') as f:
        json.dump(comp, f, indent=2, ensure_ascii=False)
    
    # Review queue
    with open(os.path.join(GRAPH_DIR, 'review_queue.json'), 'w') as f:
        json.dump(rq, f, indent=2, ensure_ascii=False)
    
    # CUID index
    cuid_index = {}
    for n in nodes:
        if n.get('CUID'):
            cuid_index[n['CUID']] = n['GUID']
    with open(os.path.join(GRAPH_DIR, 'cuid_index.json'), 'w') as f:
        json.dump(cuid_index, f, indent=2, ensure_ascii=False)
    
    # Entity index
    entity_index = {}
    for n in nodes:
        if n.get('node_type') != 'Scripture':
            entity_index[n.get('name','')] = {
                'GUID': n['GUID'],
                'type': n.get('entity_type',''),
                'mentions': n.get('total_mentions',0)
            }
    with open(os.path.join(GRAPH_DIR, 'indexes', 'entity_index.json'), 'w') as f:
        json.dump(entity_index, f, indent=2, ensure_ascii=False)
    
    # Manifest
    manifest_files = {
        'graph.json': {'size': os.path.getsize(os.path.join(GRAPH_DIR, 'graph.json'))},
        'graph_statistics.json': {'size': os.path.getsize(os.path.join(GRAPH_DIR, 'graph_statistics.json'))},
        'nodes/entity_nodes.json': {'size': os.path.getsize(os.path.join(GRAPH_DIR, 'nodes', 'entity_nodes.json'))},
        'nodes/scripture_nodes.json': {'size': os.path.getsize(os.path.join(GRAPH_DIR, 'nodes', 'scripture_nodes.json'))},
        'edges/relationship_edges.json': {'size': os.path.getsize(os.path.join(GRAPH_DIR, 'edges', 'relationship_edges.json'))},
        'validation/graph_validation.json': {'size': os.path.getsize(os.path.join(GRAPH_DIR, 'validation', 'graph_validation.json'))},
        'graph_completeness.json': {'size': os.path.getsize(os.path.join(GRAPH_DIR, 'graph_completeness.json'))},
        'review_queue.json': {'size': os.path.getsize(os.path.join(GRAPH_DIR, 'review_queue.json'))},
        'cuid_index.json': {'size': os.path.getsize(os.path.join(GRAPH_DIR, 'cuid_index.json'))},
        'indexes/entity_index.json': {'size': os.path.getsize(os.path.join(GRAPH_DIR, 'indexes', 'entity_index.json'))},
    }
    for name in subgraphs:
        fpath = os.path.join(GRAPH_DIR, f'{name}.json')
        if os.path.exists(fpath):
            manifest_files[f'{name}.json'] = {'size': os.path.getsize(fpath)}
    
    manifest = {
        'version': '9.0',
        'generated': datetime.now().isoformat(),
        'files': manifest_files
    }
    with open(os.path.join(GRAPH_DIR, 'graph_manifest.json'), 'w') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    print(f"\n=== All outputs saved to {GRAPH_DIR} ===")
    print(f"Files written:")
    for fname in sorted(os.listdir(GRAPH_DIR)):
        fpath = os.path.join(GRAPH_DIR, fname)
        if os.path.isfile(fpath):
            sz = os.path.getsize(fpath)
            print(f"  {fname}: {sz:,} bytes")
    
    return qa

if __name__ == '__main__':
    main()
