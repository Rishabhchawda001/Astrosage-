"""
Phase 12: Embeddings — AstroSage Knowledge System
Generates vector embeddings for all semantic chunks from frozen release v1.0.0.

Model: all-MiniLM-L6-v2 (80MB, 384-dim, fast, multilingual-capable)
Consumes ONLY: knowledge/releases/v1.0.0/chunks/
Produces: knowledge/releases/v1.0.0/embeddings/
"""
import json, os, hashlib, time
import numpy as np
from datetime import datetime, timezone
from pathlib import Path

RELEASE_DIR = "knowledge/releases/v1.0.0"
CHUNKS_DIR = os.path.join(RELEASE_DIR, "chunks")
EMBEDDINGS_DIR = os.path.join(RELEASE_DIR, "embeddings")
GENERATED = datetime.now(timezone.utc).isoformat()
GIT_COMMIT = os.popen("git rev-parse HEAD").read().strip()

# ── Model Config ──
MODEL_NAME = "all-MiniLM-L6-v2"
MODEL_DIM = 384
BATCH_SIZE = 256

def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()

def load_all_chunks():
    """Load all chunk files from the frozen release."""
    all_chunks = []
    
    # Load per-level files
    for fname in ["scripture_chunks.json", "dialogue_chunks.json", 
                   "entity_chunks.json", "event_chunks.json"]:
        fpath = os.path.join(CHUNKS_DIR, fname)
        if os.path.exists(fpath):
            with open(fpath) as f:
                chunks = json.load(f)
            all_chunks.extend(chunks)
            print(f"  Loaded {fname}: {len(chunks)} chunks")
    
    # Load per-scripture verse files
    verses_dir = os.path.join(CHUNKS_DIR, "verses")
    if os.path.isdir(verses_dir):
        for fname in sorted(os.listdir(verses_dir)):
            if fname.endswith(".json"):
                fpath = os.path.join(verses_dir, fname)
                with open(fpath) as f:
                    chunks = json.load(f)
                all_chunks.extend(chunks)
        print(f"  Loaded {len(os.listdir(verses_dir))} verse files")
    
    return all_chunks

def prepare_texts(chunks):
    """Prepare text inputs for embedding. Each chunk gets a text representation."""
    texts = []
    for c in chunks:
        # Combine level context + text for richer embedding
        level = c.get("level", "")
        text = c.get("text", "")
        scripture = c.get("scripture_id", "")
        
        # Prefix with level for disambiguation
        prefix = f"[{level}] "
        if scripture and level != "scripture":
            prefix += f"{scripture}: "
        
        full_text = prefix + text
        texts.append(full_text)
    return texts

def main():
    print("=" * 70)
    print("Phase 12: Embeddings — AstroSage Knowledge System")
    print(f"Generated: {GENERATED}")
    print(f"Commit: {GIT_COMMIT}")
    print(f"Model: {MODEL_NAME} (dim={MODEL_DIM})")
    print("=" * 70)
    
    # ── Load chunks ──
    print("\n[1] Loading chunks from frozen release v1.0.0...")
    chunks = load_all_chunks()
    print(f"  Total chunks: {len(chunks)}")
    
    # ── Prepare texts ──
    print("\n[2] Preparing text inputs...")
    texts = prepare_texts(chunks)
    chunk_ids = [c["chunk_id"] for c in chunks]
    print(f"  Prepared {len(texts)} texts")
    print(f"  Avg text length: {sum(len(t) for t in texts) // len(texts)} chars")
    
    # ── Load model ──
    print(f"\n[3] Loading embedding model: {MODEL_NAME}...")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(MODEL_NAME)
    print(f"  Model loaded: {MODEL_DIM} dimensions")
    
    # ── Generate embeddings ──
    print(f"\n[4] Generating embeddings ({len(texts)} chunks, batch_size={BATCH_SIZE})...")
    start = time.time()
    embeddings = model.encode(
        texts,
        batch_size=BATCH_SIZE,
        show_progress_bar=True,
        normalize_embeddings=True,  # L2 normalize for cosine similarity
    )
    elapsed = time.time() - start
    print(f"  Generated {embeddings.shape} in {elapsed:.1f}s ({len(texts)/elapsed:.0f} chunks/sec)")
    
    # ── Save embeddings ──
    print("\n[5] Saving embeddings...")
    os.makedirs(EMBEDDINGS_DIR, exist_ok=True)
    
    # Save as numpy array (compact, fast to load)
    embeddings_file = os.path.join(EMBEDDINGS_DIR, "embeddings.npy")
    np.save(embeddings_file, embeddings)
    
    # Save chunk ID mapping
    mapping_file = os.path.join(EMBEDDINGS_DIR, "chunk_id_mapping.json")
    mapping = {
        "model": MODEL_NAME,
        "dimensions": MODEL_DIM,
        "total_chunks": len(chunk_ids),
        "normalized": True,
        "chunk_ids": chunk_ids,
    }
    with open(mapping_file, "w") as f:
        json.dump(mapping, f)
    
    # Save FAISS index for similarity search
    print("\n[6] Building FAISS index...")
    import faiss
    index = faiss.IndexFlatIP(MODEL_DIM)  # Inner product = cosine for normalized vectors
    index.add(embeddings.astype(np.float32))
    faiss_file = os.path.join(EMBEDDINGS_DIR, "faiss_index.bin")
    faiss.write_index(index, faiss_file)
    print(f"  FAISS index: {index.ntotal} vectors")
    
    # ── Build embedding manifest ──
    print("\n[7] Building embedding manifest...")
    manifest = {
        "version": "1.0.0",
        "knowledge_version": "1.0.0",
        "git_commit": GIT_COMMIT,
        "generated": GENERATED,
        "generator": "Phase 12 Embedding Pipeline",
        "model": {
            "name": MODEL_NAME,
            "dimensions": MODEL_DIM,
            "normalized": True,
            "max_sequence_length": 256,
            "parameters": "~22M",
            "source": "sentence-transformers/all-MiniLM-L6-v2",
        },
        "stats": {
            "total_chunks": len(chunk_ids),
            "embedding_shape": list(embeddings.shape),
            "generation_time_seconds": round(elapsed, 1),
            "chunks_per_second": round(len(texts) / elapsed, 0),
        },
        "artifacts": {},
    }
    
    # Hash all artifacts
    for fname in os.listdir(EMBEDDINGS_DIR):
        fpath = os.path.join(EMBEDDINGS_DIR, fname)
        if os.path.isfile(fpath):
            h = sha256_bytes(open(fpath, "rb").read())
            manifest["artifacts"][fname] = {
                "sha256": h,
                "size": os.path.getsize(fpath),
            }
    
    manifest_file = os.path.join(EMBEDDINGS_DIR, "embedding_manifest.json")
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)
    manifest["artifacts"]["embedding_manifest.json"] = {
        "sha256": sha256_bytes(open(manifest_file, "rb").read()),
        "size": os.path.getsize(manifest_file),
    }
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)
    
    # ── Validation: test search ──
    print("\n[8] Validating with sample search...")
    test_queries = [
        "Who is Vishnu?",
        "What is dharma?",
        "The Bhagavad Gita teaching",
        "Arjuna and Krishna dialogue",
    ]
    for q in test_queries:
        q_emb = model.encode([q], normalize_embeddings=True)
        D, I = index.search(q_emb.astype(np.float32), 3)
        print(f"  Query: '{q}'")
        for rank, (idx, score) in enumerate(zip(I[0], D[0])):
            if idx < len(chunks):
                c = chunks[idx]
                text_preview = c.get("text", "")[:80]
                print(f"    #{rank+1} (score={score:.3f}): [{c.get('level','')}] {text_preview}...")
    
    print(f"\n{'=' * 70}")
    print(f"Phase 12: Embeddings — COMPLETE")
    print(f"  Model: {MODEL_NAME}")
    print(f"  Vectors: {embeddings.shape[0]} x {embeddings.shape[1]}")
    print(f"  FAISS index: {index.ntotal} vectors")
    print(f"  Time: {elapsed:.1f}s")
    print(f"  Artifacts: {len(manifest['artifacts'])} files")
    print(f"{'=' * 70}")

if __name__ == "__main__":
    main()
