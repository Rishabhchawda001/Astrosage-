# AstroSage Architecture Diagrams

**Version**: 1.0.0

---

## 1. Overall Architecture

```mermaid
graph TB
    subgraph "Corpus Layer"
        A[Canonical Corpus<br/>54 scriptures] --> B[GRETIL Parser]
        B --> C[Entity Extraction]
        C --> D[Relationship Extraction]
    end
    
    subgraph "Knowledge Layer"
        D --> E[Knowledge Graph<br/>391 entities, 5,044 edges]
        E --> F[Knowledge Freeze v1.0.0<br/>Immutable Artifacts]
    end
    
    subgraph "Processing Layer"
        F --> G[Semantic Chunking<br/>120,548 chunks]
        F --> H[Embedding Generation<br/>MiniLM-L6-v2, 384d]
        F --> I[BM25 Indexing<br/>375K vocabulary]
    end
    
    subgraph "Retrieval Layer"
        H --> J[FAISS Index<br/>120,548 vectors]
        I --> K[Hybrid Retrieval<br/>BM25 + FAISS]
        J --> K
    end
    
    subgraph "Intelligence Layer"
        E --> L[Reasoning Engine<br/>Entity + Question]
        K --> L
        L --> M[Grounded Answer<br/>Provenance-traced]
    end
    
    style A fill:#e1f5fe
    style F fill:#fff3e0
    style K fill:#e8f5e9
    style M fill:#fce4ec
```

---

## 2. Data Flow

```mermaid
flowchart TD
    A[User Query] --> B[Query Embedding<br/>84ms CPU]
    B --> C[FAISS Search<br/>38ms avg]
    A --> D[BM25 Search<br/>lexical]
    C --> E[Fused Results<br/>α=0.6]
    D --> E
    E --> F[Entity Extraction]
    F --> G[Graph Traversal<br/><1ms per entity]
    G --> H[Evidence Chain<br/>11+ sources]
    H --> I[Confidence Scoring]
    I --> J[Answer Generation<br/>provenance-traced]
```

---

## 3. Knowledge Graph Structure

```mermaid
graph LR
    subgraph "Node Types"
        N1[Person<br/>124]
        N2[Deity<br/>46]
        N3[Place<br/>48]
        N4[Concept<br/>51]
        N5[Text<br/>19]
        N6[Weapon<br/>23]
        N7[Animal<br/>33]
    end
    
    subgraph "Edge Types"
        E1[MENTIONED_IN<br/>4763]
        E2[FATHER_OF<br/>32]
        E3[SON_OF<br/>14]
        E4[INCARNATION_OF<br/>7]
        E5[TEACHER_OF<br/>11]
        E6[OTHER<br/>65 types]
    end
    
    N1 -->|FATHER_OF| N1
    N1 -->|TEACHER_OF| N1
    N2 -->|INCARNATION_OF| N2
    N1 -->|MENTIONED_IN| N5
    N1 -->|RESIDES_IN| N3
```

---

## 4. Chunk Pipeline

```mermaid
flowchart LR
    A[Frozen Release<br/>v1.0.0] --> B[Level 1<br/>Scripture]
    A --> C[Level 2<br/>Verse]
    A --> D[Level 3<br/>Dialogue]
    A --> E[Level 4<br/>Event]
    A --> F[Level 5<br/>Entity]
    
    B --> G[120,548<br/>Deterministic Chunks]
    C --> G
    D --> G
    E --> G
    F --> G
    
    G --> H[SHA256 Chunk IDs]
    H --> I[Embedding<br/>Generation]
    I --> J[FAISS Index]
```

---

## 5. Retrieval Flow

```mermaid
flowchart TD
    A[Query] --> B{Lexical Match}
    A --> C{Semantic Match}
    
    B --> D[BM25 Scores<br/>375K vocabulary]
    C --> E[FAISS Scores<br/>cosine similarity]
    
    D --> F[Alpha Fusion<br/>α=0.6]
    E --> F
    
    F --> G[Top-K Results<br/>ranked by score]
    G --> H[Evidence Extraction]
    H --> I[Provenance Tracing]
```

---

## 6. Deployment Architecture

```mermaid
graph TB
    subgraph "Local Deployment"
        A[Python 3.10+] --> B[PyTorch<br/>CPU]
        A --> C[Sentence Transformers<br/>5.6.0]
        A --> D[FAISS<br/>CPU]
        
        B --> E[Frozen Release<br/>knowledge/releases/v1.0.0/]
        C --> E
        D --> E
    end
    
    subgraph "Storage"
        E --> F[Embeddings<br/>176.6MB]
        E --> G[FAISS Index<br/>176.6MB]
        E --> H[BM25 Index<br/>11.7MB]
        E --> I[Chunks<br/>112MB]
        E --> J[Graph<br/>2.5MB]
    end
```

---

## 7. Repository Structure

```mermaid
graph TB
    A[Astrosage-] --> B[knowledge/]
    A --> C[scripts/]
    A --> D[docs/]
    A --> E[.agent/]
    A --> F[.ai/]
    
    B --> B1[releases/v1.0.0/]
    B --> B2[migrations/]
    B --> B3[graph/]
    
    B1 --> B1A[graph/]
    B1 --> B1B[chunks/]
    B1 --> B1C[embeddings/]
    B1 --> B1D[retrieval/]
    B1 --> B1E[reasoning/]
    B1 --> B1F[answers/]
    
    C --> C1[phase10_knowledge_freeze.py]
    C --> C2[phase11_semantic_chunker.py]
    C --> C3[phase12_embeddings.py]
    C --> C4[phase13_hybrid_retrieval.py]
    C --> C5[phase14_reasoning_engine.py]
    C --> C6[phase15_answer_generation.py]
    
    D --> D1[architecture/]
    D --> D2[developer/]
    D --> D3[user/]
    D --> D4[operations/]
    D --> D5[api/]
```
