"""
Phase 13: Hybrid Retrieval — AstroSage Knowledge System
Lexical (BM25) + Semantic (FAISS) hybrid search over frozen chunks.

Consumes: knowledge/releases/v1.0.0/chunks/ + knowledge/releases/v1.0.0/embeddings/
Produces: knowledge/releases/v1.0.0/retrieval/
"""
import json, os, hashlib, time, re
import numpy as np
from datetime import datetime, timezone
from collections import defaultdict

RELEASE_DIR = "knowledge/releases/v1.0.0"
CHUNKS_DIR = os.path.join(RELEASE_DIR, "chunks")
EMBEDDINGS_DIR = os.path.join(RELEASE_DIR, "embeddings")
RETRIEVAL_DIR = os.path.join(RELEASE_DIR, "retrieval")
GENERATED = datetime.now(timezone.utc).isoformat()
GIT_COMMIT = os.popen("git rev-parse HEAD").read().strip()

def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()

def load_all_chunks():
    """Load all chunk files."""
    all_chunks = []
    for fname in ["scripture_chunks.json", "dialogue_chunks.json",
                   "entity_chunks.json", "event_chunks.json"]:
        fpath = os.path.join(CHUNKS_DIR, fname)
        if os.path.exists(fpath):
            with open(fpath) as f:
                all_chunks.extend(json.load(f))
    verses_dir = os.path.join(CHUNKS_DIR, "verses")
    if os.path.isdir(verses_dir):
        for fname in sorted(os.listdir(verses_dir)):
            if fname.endswith(".json"):
                with open(os.path.join(verses_dir, fname)) as f:
                    all_chunks.extend(json.load(f))
    return all_chunks

class BM25Index:
    """Simple BM25 index for lexical search."""
    
    def __init__(self, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
        self.doc_freqs = defaultdict(int)
        self.doc_lengths = []
        self.avg_dl = 0
        self.docs = []
        self.N = 0
    
    def tokenize(self, text):
        """Simple whitespace + lowercase tokenization."""
        return re.findall(r'\w+', text.lower())
    
    def build(self, texts):
        """Build index from list of texts."""
        self.N = len(texts)
        for text in texts:
            tokens = self.tokenize(text)
            self.doc_lengths.append(len(tokens))
            self.docs.append(tokens)
            seen = set()
            for t in tokens:
                if t not in seen:
                    self.doc_freqs[t] += 1
                    seen.add(t)
        self.avg_dl = sum(self.doc_lengths) / max(self.N, 1)
    
    def search(self, query, top_k=10):
        """Search and return (doc_index, score) pairs."""
        query_tokens = self.tokenize(query)
        scores = np.zeros(self.N)
        
        for qt in query_tokens:
            if qt not in self.doc_freqs:
                continue
            df = self.doc_freqs[qt]
            idf = np.log((self.N - df + 0.5) / (df + 0.5) + 1)
            
            for i, doc in enumerate(self.docs):
                tf = doc.count(qt)
                dl = self.doc_lengths[i]
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * dl / self.avg_dl)
                scores[i] += idf * numerator / denominator
        
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [(int(idx), float(scores[idx])) for idx in top_indices if scores[idx] > 0]


def hybrid_search(query, bm25, faiss_index, model, chunks, alpha=0.5, top_k=10):
    """Combine BM25 and semantic search scores."""
    # Lexical search
    bm25_results = bm25.search(query, top_k=top_k * 3)
    bm25_scores = {idx: score for idx, score in bm25_results}
    bm25_max = max(bm25_scores.values()) if bm25_scores else 1
    
    # Semantic search
    q_emb = model.encode([query], normalize_embeddings=True).astype(np.float32)
    D, I = faiss_index.search(q_emb, top_k * 3)
    sem_scores = {}
    for idx, score in zip(I[0], D[0]):
        if idx >= 0 and idx < len(chunks):
            sem_scores[int(idx)] = float(score)
    sem_max = max(sem_scores.values()) if sem_scores else 1
    
    # Combine scores
    combined = defaultdict(float)
    all_indices = set(bm25_scores.keys()) | set(sem_scores.keys())
    for idx in all_indices:
        bm25_norm = bm25_scores.get(idx, 0) / bm25_max if bm25_max else 0
        sem_norm = sem_scores.get(idx, 0) / sem_max if sem_max else 0
        combined[idx] = alpha * sem_norm + (1 - alpha) * bm25_norm
    
    # Sort and return top_k
    sorted_results = sorted(combined.items(), key=lambda x: -x[1])[:top_k]
    results = []
    for idx, score in sorted_results:
        chunk = chunks[idx]
        results.append({
            "chunk_id": chunk["chunk_id"],
            "level": chunk.get("level", ""),
            "scripture_id": chunk.get("scripture_id", ""),
            "text": chunk.get("text", "")[:200],
            "score": round(score, 4),
            "bm25_score": round(bm25_scores.get(idx, 0) / bm25_max, 4) if bm25_max else 0,
            "semantic_score": round(sem_scores.get(idx, 0) / sem_max, 4) if sem_max else 0,
        })
    return results


def main():
    print("=" * 70)
    print("Phase 13: Hybrid Retrieval — AstroSage Knowledge System")
    print(f"Generated: {GENERATED}")
    print(f"Commit: {GIT_COMMIT}")
    print("=" * 70)
    
    # ── Load chunks ──
    print("\n[1] Loading chunks...")
    chunks = load_all_chunks()
    texts = []
    for c in chunks:
        level = c.get("level", "")
        text = c.get("text", "")
        scripture = c.get("scripture_id", "")
        prefix = f"[{level}] "
        if scripture and level != "scripture":
            prefix += f"{scripture}: "
        texts.append(prefix + text)
    print(f"  Loaded {len(chunks)} chunks")
    
    # ── Build BM25 index ──
    print("\n[2] Building BM25 lexical index...")
    start = time.time()
    bm25 = BM25Index()
    bm25.build(texts)
    print(f"  Built in {time.time()-start:.1f}s")
    print(f"  Vocabulary size: {len(bm25.doc_freqs)}")
    
    # ── Load FAISS index and embeddings ──
    print("\n[3] Loading FAISS index...")
    import faiss
    from sentence_transformers import SentenceTransformer
    
    mapping_file = os.path.join(EMBEDDINGS_DIR, "chunk_id_mapping.json")
    mapping = json.load(open(mapping_file))
    model_name = mapping["model"]
    
    model = SentenceTransformer(model_name)
    faiss_file = os.path.join(EMBEDDINGS_DIR, "faiss_index.bin")
    faiss_index = faiss.read_index(faiss_file)
    print(f"  FAISS index: {faiss_index.ntotal} vectors")
    print(f"  Model: {model_name}")
    
    # ── Save BM25 index ──
    print("\n[4] Saving BM25 index...")
    os.makedirs(RETRIEVAL_DIR, exist_ok=True)
    bm25_data = {
        "doc_freqs": dict(bm25.doc_freqs),
        "doc_lengths": bm25.doc_lengths,
        "avg_dl": bm25.avg_dl,
        "N": bm25.N,
        "k1": bm25.k1,
        "b": bm25.b,
    }
    bm25_file = os.path.join(RETRIEVAL_DIR, "bm25_index.json")
    with open(bm25_file, "w") as f:
        json.dump(bm25_data, f)
    
    # ── Test hybrid search ──
    print("\n[5] Testing hybrid search...")
    test_queries = [
        "Who is Vishnu and what is his role?",
        "What is the teaching about dharma in the Bhagavad Gita?",
        "Tell me about the dialogue between Krishna and Arjuna",
        "What are the yoga practices described in the Yoga Sutras?",
        "Who are the Pandavas in the Mahabharata?",
    ]
    
    search_results = {}
    for q in test_queries:
        start = time.time()
        results = hybrid_search(q, bm25, faiss_index, model, chunks, alpha=0.6, top_k=5)
        elapsed = time.time() - start
        search_results[q] = {"results": results, "time_ms": round(elapsed * 1000)}
        print(f"\n  Query: '{q}' ({elapsed*1000:.0f}ms)")
        for r in results[:3]:
            print(f"    [{r['level']}] score={r['score']:.3f} | {r['text'][:100]}...")
    
    # ── Build retrieval manifest ──
    print("\n[6] Building retrieval manifest...")
    manifest = {
        "version": "1.0.0",
        "knowledge_version": "1.0.0",
        "git_commit": GIT_COMMIT,
        "generated": GENERATED,
        "generator": "Phase 13 Hybrid Retrieval Pipeline",
        "search_engine": {
            "lexical": "BM25 (k1=1.5, b=0.75)",
            "semantic": f"FAISS ({model_name}, {mapping['dimensions']}d)",
            "fusion": "alpha-weighted linear combination",
            "default_alpha": 0.6,
        },
        "stats": {
            "total_chunks_indexed": len(chunks),
            "vocabulary_size": len(bm25.doc_freqs),
            "faiss_vectors": faiss_index.ntotal,
        },
        "artifacts": {},
    }
    
    for fname in os.listdir(RETRIEVAL_DIR):
        fpath = os.path.join(RETRIEVAL_DIR, fname)
        if os.path.isfile(fpath):
            h = sha256_bytes(open(fpath, "rb").read())
            manifest["artifacts"][fname] = {"sha256": h, "size": os.path.getsize(fpath)}
    
    manifest_file = os.path.join(RETRIEVAL_DIR, "retrieval_manifest.json")
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)
    manifest["artifacts"]["retrieval_manifest.json"] = {
        "sha256": sha256_bytes(open(manifest_file, "rb").read()),
        "size": os.path.getsize(manifest_file),
    }
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)
    
    # Save test results
    test_file = os.path.join(RETRIEVAL_DIR, "search_validation.json")
    with open(test_file, "w") as f:
        json.dump(search_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'=' * 70}")
    print(f"Phase 13: Hybrid Retrieval — COMPLETE")
    print(f"  BM25 vocabulary: {len(bm25.doc_freqs)} tokens")
    print(f"  FAISS vectors: {faiss_index.ntotal}")
    print(f"  Test queries: {len(test_queries)}")
    print(f"  Artifacts: {len(manifest['artifacts'])} files")
    print(f"{'=' * 70}")

if __name__ == "__main__":
    main()
