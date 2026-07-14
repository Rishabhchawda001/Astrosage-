"""Known command definitions — Scaffold for future implementation."""
KNOWN_COMMANDS = [
    {"name": "verify", "description": "Verify answer or citation against sources", "category": "verification"},
    {"name": "recover", "description": "Trigger knowledge recovery for a document", "category": "recovery"},
    {"name": "research", "description": "Search for information across sources", "category": "research"},
    {"name": "benchmark", "description": "Run a benchmark", "category": "benchmark"},
    {"name": "index", "description": "Index a document or re-index the corpus", "category": "index"},
    {"name": "ocr", "description": "OCR a document or page", "category": "ocr"},
    {"name": "chunk", "description": "Chunk a document", "category": "chunking"},
    {"name": "embed", "description": "Generate embeddings", "category": "embedding"},
    {"name": "graph", "description": "Query the knowledge graph", "category": "knowledge_graph"},
    {"name": "corpus", "description": "Corpus management operations", "category": "corpus"},
    {"name": "skills", "description": "Manage skills", "category": "skills"},
    {"name": "github", "description": "GitHub operations", "category": "github"},
    {"name": "search", "description": "Search the knowledge base", "category": "search"},
    {"name": "validate", "description": "Validate pipeline outputs", "category": "validation"},
]
