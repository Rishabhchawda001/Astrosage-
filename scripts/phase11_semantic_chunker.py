"""
Phase 11: Semantic Chunking — AstroSage Knowledge System
Produces multi-level semantic chunks from frozen Knowledge v1.0.0.

Consumes ONLY: knowledge/releases/v1.0.0/
Produces: knowledge/releases/v1.0.0/chunks/ + chunk_manifest.json
"""
import json, os, hashlib, uuid, re
from datetime import datetime, timezone
from collections import defaultdict
from pathlib import Path

RELEASE_DIR = "knowledge/releases/v1.0.0"
GRAPH_DIR = os.path.join(RELEASE_DIR, "graph")
CHUNKS_DIR = os.path.join(RELEASE_DIR, "chunks")
CU_DIR = "knowledge/cuv/gretil_prose_clean"
GENERATED = datetime.now(timezone.utc).isoformat()
GIT_COMMIT = os.popen("git rev-parse HEAD").read().strip()

def sha256_bytes(data):
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def make_chunk_id(scripture, level, ref):
    """Deterministic chunk ID — stable across runs."""
    raw = f"astrosage.chunk.v1.{scripture}.{level}.{ref}"
    return hashlib.sha256(raw.encode()).hexdigest()[:24]

def load_frozen():
    entities = json.load(open(os.path.join(GRAPH_DIR, "nodes/entity_nodes.json")))
    scriptures = json.load(open(os.path.join(GRAPH_DIR, "nodes/scripture_nodes.json")))
    edges = json.load(open(os.path.join(GRAPH_DIR, "edges/relationship_edges.json")))
    schema = json.load(open(os.path.join(GRAPH_DIR, "schemas/graph_schema.json")))
    return entities, scriptures, edges, schema

def load_cu_files():
    """Load all GRETIL CU prose files."""
    cu_data = {}
    if not os.path.isdir(CU_DIR):
        return cu_data
    for fname in sorted(os.listdir(CU_DIR)):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(CU_DIR, fname)
        with open(fpath) as f:
            data = json.load(f)
        title = data.get("title", fname.replace(".json", ""))
        chapters = data.get("chapters", [])
        all_akus = []
        for ch in chapters:
            ch_num = ch.get("chapter_num", ch.get("chapter", "?"))
            for aku in ch.get("akus", []):
                aku["chapter"] = ch_num
                all_akus.append(aku)
        cu_data[fname] = {
            "title": title,
            "file": fname,
            "chapters": chapters,
            "akus": all_akus,
            "total_akus": len(all_akus),
        }
    return cu_data

def build_entity_index(entities):
    """Build lookup indices for entities."""
    by_guid = {e["GUID"]: e for e in entities}
    by_name = {}
    for e in entities:
        name = e["name"]
        if name not in by_name:
            by_name[name] = e
    return by_guid, by_name

def build_edge_index(edges):
    """Build edge indices."""
    by_entity = defaultdict(list)  # entity GUID -> list of edges
    by_scripture = defaultdict(list)  # scripture GUID -> list of edges
    by_type = defaultdict(list)  # edge type -> list of edges
    for e in edges:
        by_entity[e["source_GUID"]].append(e)
        by_scripture[e["target_GUID"]].append(e)
        by_type[e["type"]].append(e)
    return by_entity, by_scripture, by_type

def build_scripture_entity_map(edges, scripture_guids):
    """Map scripture GUID -> set of entity names mentioned."""
    mapping = defaultdict(set)
    entity_lookup = {}
    for e in edges:
        if e["type"] == "MENTIONED_IN" and e["target_GUID"] in scripture_guids:
            mapping[e["target_GUID"]].add(e["source_GUID"])
    return mapping

# ═══════════════════════════════════════════════════════
# CHUNK GENERATORS
# ═══════════════════════════════════════════════════════

def chunk_scripture_level(scripture, entity_names, cu_count):
    """One chunk per scripture — metadata + summary."""
    chunk = {
        "chunk_id": make_chunk_id(scripture["id"], "scripture", scripture["id"]),
        "level": "scripture",
        "scripture_id": scripture["id"],
        "scripture_name": scripture.get("canonical_name", scripture["id"]),
        "title": scripture["id"],
        "canonical_ref": scripture["id"],
        "chapter": None,
        "verse_range": None,
        "text": f"Scripture: {scripture['id']}. Canonical units: {cu_count}. Entities mentioned: {len(entity_names)}.",
        "entity_links": [{"guid": None, "name": n} for n in list(entity_names)[:50]],
        "relationship_links": [],
        "dialogue_links": [],
        "event_links": [],
        "concept_links": [],
        "provenance": {
            "source": f"knowledge/releases/v1.0.0/graph/nodes/scripture_nodes.json",
            "git_commit": GIT_COMMIT,
            "knowledge_version": "1.0.0",
        },
        "metadata": {
            "total_verses": scripture.get("total_verses", 0),
            "coverage": scripture.get("coverage", 0),
        },
    }
    chunk["hash"] = sha256_bytes(json.dumps(chunk, sort_keys=True, ensure_ascii=False))
    return chunk

def chunk_verse_level(aku, scripture_id, chapter_num):
    """One chunk per verse / aku."""
    text = aku.get("body", aku.get("text", ""))
    if not text or len(text.strip()) < 5:
        return None
    ref = aku.get("aku_id", f"{scripture_id}_ch{chapter_num}_aku{aku.get('id','?')}")
    chunk = {
        "chunk_id": make_chunk_id(scripture_id, "verse", ref),
        "level": "verse",
        "scripture_id": scripture_id,
        "canonical_ref": ref,
        "chapter": chapter_num,
        "verse_range": ref,
        "text": text.strip(),
        "entity_links": [],
        "relationship_links": [],
        "dialogue_links": [],
        "event_links": [],
        "concept_links": [],
        "provenance": {
            "source": f"knowledge/cuv/gretil_prose_clean/{scripture_id}",
            "git_commit": GIT_COMMIT,
            "knowledge_version": "1.0.0",
        },
        "metadata": {},
    }
    chunk["hash"] = sha256_bytes(json.dumps(chunk, sort_keys=True, ensure_ascii=False))
    return chunk

def chunk_dialogue(dialogue, index):
    """One chunk per dialogue."""
    speaker = dialogue.get("speaker", "Unknown")
    listener = dialogue.get("listener", "Unknown")
    topic = dialogue.get("topic", "")
    scripture = dialogue.get("scripture", "")
    context = dialogue.get("context", "")
    verses = dialogue.get("verses", "")
    text = f"Dialogue: {speaker} speaks to {listener}. Topic: {topic}. Context: {context}. Verses: {verses}. Scripture: {scripture}."
    chunk = {
        "chunk_id": make_chunk_id(scripture or "unknown", "dialogue", f"d{index}"),
        "level": "dialogue",
        "scripture_id": scripture,
        "canonical_ref": verses,
        "chapter": None,
        "verse_range": verses,
        "text": text,
        "entity_links": [{"name": speaker}, {"name": listener}],
        "relationship_links": [],
        "dialogue_links": [{"speaker": speaker, "listener": listener, "topic": topic}],
        "event_links": [],
        "concept_links": [],
        "provenance": {
            "source": "knowledge/releases/v1.0.0/graph/dialogue_graph.json",
            "git_commit": GIT_COMMIT,
            "knowledge_version": "1.0.0",
        },
        "metadata": {
            "speaker": speaker,
            "listener": listener,
            "topic": topic,
            "context": context,
        },
    }
    chunk["hash"] = sha256_bytes(json.dumps(chunk, sort_keys=True, ensure_ascii=False))
    return chunk

def chunk_event(event, index):
    """One chunk per event."""
    name = event.get("name", event.get("event", f"Event {index}"))
    location = event.get("location", "")
    participants = event.get("participants", event.get("people", []))
    scripture = event.get("scripture", "")
    text = f"Event: {name}."
    if location:
        text += f" Location: {location}."
    if participants:
        text += f" Participants: {', '.join(participants) if isinstance(participants, list) else participants}."
    chunk = {
        "chunk_id": make_chunk_id(scripture or "unknown", "event", f"e{index}"),
        "level": "event",
        "scripture_id": scripture,
        "canonical_ref": event.get("verses", ""),
        "chapter": None,
        "verse_range": event.get("verses", ""),
        "text": text,
        "entity_links": [{"name": p} for p in (participants if isinstance(participants, list) else [])],
        "relationship_links": [],
        "dialogue_links": [],
        "event_links": [{"name": name, "location": location}],
        "concept_links": [],
        "provenance": {
            "source": "knowledge/releases/v1.0.0/graph/event_graph.json",
            "git_commit": GIT_COMMIT,
            "knowledge_version": "1.0.0",
        },
        "metadata": {
            "event_name": name,
            "location": location,
            "participants": participants,
        },
    }
    chunk["hash"] = sha256_bytes(json.dumps(chunk, sort_keys=True, ensure_ascii=False))
    return chunk

def chunk_entity(entity, mentions, relationships):
    """One chunk per entity — aggregating all mentions and relationships."""
    name = entity["name"]
    etype = entity.get("entity_type", entity.get("type", "?"))
    sources = entity.get("sources", [])
    desc = entity.get("description", "")
    text = f"Entity: {name} (type: {etype})."
    if desc:
        text += f" {desc}"
    text += f" Appears in: {', '.join(sources) if sources else 'unknown'}."
    text += f" Total mentions: {entity.get('total_mentions', 0)}."

    chunk = {
        "chunk_id": make_chunk_id("global", "entity", entity["GUID"]),
        "level": "entity",
        "scripture_id": "global",
        "canonical_ref": entity["GUID"],
        "chapter": None,
        "verse_range": None,
        "text": text,
        "entity_links": [{"guid": entity["GUID"], "name": name, "type": etype}],
        "relationship_links": [
            {
                "type": r["type"],
                "target": r.get("evidence", {}).get("entity", "") if isinstance(r.get("evidence"), dict) else r.get("target_ref", ""),
                "scripture": r.get("evidence", {}).get("scripture", "") if isinstance(r.get("evidence"), dict) else "",
            }
            for r in relationships[:50]
        ],
        "dialogue_links": [],
        "event_links": [],
        "concept_links": [],
        "provenance": {
            "source": "knowledge/releases/v1.0.0/graph/nodes/entity_nodes.json",
            "git_commit": GIT_COMMIT,
            "knowledge_version": "1.0.0",
        },
        "metadata": {
            "entity_type": etype,
            "total_mentions": entity.get("total_mentions", 0),
            "sources": sources,
        },
    }
    chunk["hash"] = sha256_bytes(json.dumps(chunk, sort_keys=True, ensure_ascii=False))
    return chunk


# ═══════════════════════════════════════════════════════
# MAIN PIPELINE
# ═══════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("Phase 11: Semantic Chunking — AstroSage Knowledge System")
    print(f"Generated: {GENERATED}")
    print(f"Commit: {GIT_COMMIT}")
    print("=" * 70)

    # Load frozen knowledge
    print("\n[1] Loading frozen release v1.0.0...")
    entities, scriptures, edges, schema = load_frozen()
    by_guid, by_name = build_entity_index(entities)
    scripture_guids = {s["GUID"] for s in scriptures}
    scripture_id_map = {s["GUID"]: s["id"] for s in scriptures}

    print(f"    Entities: {len(entities)}")
    print(f"    Scriptures: {len(scriptures)}")
    print(f"    Edges: {len(edges)}")

    # Load CU files
    print("\n[2] Loading canonical unit files...")
    cu_data = load_cu_files()
    total_akus = sum(c["total_akus"] for c in cu_data.values())
    print(f"    CU files: {len(cu_data)}")
    print(f"    Total akus: {total_akus}")

    # Load sub-graphs
    print("\n[3] Loading sub-graphs...")
    dialogue_graph = json.load(open(os.path.join(GRAPH_DIR, "dialogue_graph.json")))
    event_graph = json.load(open(os.path.join(GRAPH_DIR, "event_graph.json")))

    dialogues = dialogue_graph.get("dialogues", []) if isinstance(dialogue_graph, dict) else dialogue_graph
    events = event_graph.get("events", []) if isinstance(event_graph, dict) else event_graph
    print(f"    Dialogues: {len(dialogues)}")
    print(f"    Events: {len(events)}")

    # Build edge indices
    print("\n[4] Building edge indices...")
    by_entity, by_scripture, by_type = build_edge_index(edges)
    scripture_entity_map = build_scripture_entity_map(edges, scripture_guids)

    # Create chunks directory
    os.makedirs(CHUNKS_DIR, exist_ok=True)

    all_chunks = []

    # ── Level 1: Scripture chunks ──
    print("\n[5] Generating scripture-level chunks...")
    for s in scriptures:
        sguid = s["GUID"]
        entity_names = set()
        for eguid in scripture_entity_map.get(sguid, set()):
            if eguid in by_guid:
                entity_names.add(by_guid[eguid]["name"])
        cu_count = sum(
            c["total_akus"]
            for fname, c in cu_data.items()
            if s["id"].lower().replace(" ", "_") in fname.lower()
            or s["id"].lower() in c["title"].lower()
        )
        chunk = chunk_scripture_level(s, entity_names, cu_count)
        all_chunks.append(chunk)
    print(f"    Generated: {len([c for c in all_chunks if c['level']=='scripture'])} scripture chunks")

    # ── Level 2: Verse chunks (from CU files) ──
    print("\n[6] Generating verse-level chunks from CU files...")
    verse_count = 0
    for fname, cu in cu_data.items():
        for aku in cu["akus"]:
            ch_num = aku.get("chapter", "?")
            chunk = chunk_verse_level(aku, cu["title"], ch_num)
            if chunk:
                all_chunks.append(chunk)
                verse_count += 1
    print(f"    Generated: {verse_count} verse chunks")

    # ── Level 3: Dialogue chunks ──
    print("\n[7] Generating dialogue chunks...")
    for i, d in enumerate(dialogues):
        chunk = chunk_dialogue(d, i)
        all_chunks.append(chunk)
    print(f"    Generated: {len(dialogues)} dialogue chunks")

    # ── Level 4: Event chunks ──
    print("\n[8] Generating event chunks...")
    for i, e in enumerate(events):
        chunk = chunk_event(e, i)
        all_chunks.append(chunk)
    print(f"    Generated: {len(events)} event chunks")

    # ── Level 5: Entity chunks ──
    print("\n[9] Generating entity chunks...")
    entity_count = 0
    for entity in entities:
        eguid = entity["GUID"]
        rels = by_entity.get(eguid, [])
        chunk = chunk_entity(entity, [], rels)
        all_chunks.append(chunk)
        entity_count += 1
    print(f"    Generated: {entity_count} entity chunks")

    # ── Write all chunks ──
    print(f"\n[10] Writing {len(all_chunks)} chunks...")
    chunk_file = os.path.join(CHUNKS_DIR, "semantic_chunks.json")
    with open(chunk_file, "w") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    # ── Build chunk manifest ──
    print("\n[11] Building chunk manifest...")
    level_counts = defaultdict(int)
    for c in all_chunks:
        level_counts[c["level"]] += 1

    total_text_len = sum(len(c.get("text", "")) for c in all_chunks)
    avg_text_len = total_text_len // max(len(all_chunks), 1)

    manifest = {
        "version": "1.0.0",
        "knowledge_version": "1.0.0",
        "git_commit": GIT_COMMIT,
        "generated": GENERATED,
        "generator": "Phase 11 Semantic Chunking Pipeline",
        "total_chunks": len(all_chunks),
        "levels": dict(level_counts),
        "total_text_characters": total_text_len,
        "average_text_characters": avg_text_len,
        "artifacts": {
            "semantic_chunks.json": {
                "sha256": sha256_file(chunk_file),
                "size": os.path.getsize(chunk_file),
            }
        },
        "schema": {
            "fields": [
                "chunk_id", "level", "scripture_id", "canonical_ref",
                "chapter", "verse_range", "text", "entity_links",
                "relationship_links", "dialogue_links", "event_links",
                "concept_links", "provenance", "metadata", "hash"
            ],
            "levels": ["scripture", "verse", "dialogue", "event", "entity"],
            "id_deterministic": True,
            "id_algorithm": "SHA256(astrosage.chunk.v1.{scripture}.{level}.{ref})[:24]",
        },
    }
    manifest_file = os.path.join(CHUNKS_DIR, "chunk_manifest.json")
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    manifest["artifacts"]["chunk_manifest.json"] = {
        "sha256": sha256_file(manifest_file),
        "size": os.path.getsize(manifest_file),
    }
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    # ── Validation ──
    print("\n[12] Validating chunks...")
    issues = []
    for i, c in enumerate(all_chunks):
        if not c.get("chunk_id"):
            issues.append(f"Chunk {i}: missing chunk_id")
        if not c.get("text"):
            issues.append(f"Chunk {i}: empty text")
        if not c.get("provenance"):
            issues.append(f"Chunk {i}: missing provenance")
        if not c.get("hash"):
            issues.append(f"Chunk {i}: missing hash")

    validation = {
        "generated": GENERATED,
        "version": "1.0.0",
        "total_chunks": len(all_chunks),
        "issues": issues,
        "issue_count": len(issues),
        "status": "PASS" if len(issues) == 0 else "FAIL",
    }
    validation_file = os.path.join(CHUNKS_DIR, "chunk_validation.json")
    with open(validation_file, "w") as f:
        json.dump(validation, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 70}")
    print(f"Phase 11: Semantic Chunking — COMPLETE")
    print(f"  Total chunks: {len(all_chunks)}")
    for level, count in sorted(level_counts.items()):
        print(f"    {level}: {count}")
    print(f"  Total text: {total_text_len:,} characters")
    print(f"  Average chunk: {avg_text_len:,} characters")
    print(f"  Validation: {validation['status']} ({len(issues)} issues)")
    print(f"{'=' * 70}")

    return all_chunks, manifest, validation


if __name__ == "__main__":
    main()
