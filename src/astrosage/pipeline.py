"""
Main ingestion pipeline orchestrator.

Flow:
  1. Scan source_library for files
  2. Check SHA256 for deduplication
  3. Extract text (adaptive OCR)
  4. Generate metadata
  5. Chunk documents semantically
  6. Generate embeddings (BGE-M3)
  7. Store in vector database
  8. Build BM25 index
  9. Generate reports
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Optional

from .chunking.chunker import SemanticChunker
from .embedding.embedder import Embedder
from .ingestion.extractor import extract_document
from .models import Chunk, Document, IngestionStatus, now_utc
from .retrieval.search import BM25Index
from .storage.vector_store import VectorStore

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """Orchestrates the full ingestion pipeline."""

    def __init__(
        self,
        source_dir: str = "knowledge/source_library",
        inventory_dir: str = "knowledge/inventory",
        index_dir: str = "knowledge/indexes",
        reports_dir: str = "knowledge/reports",
        logs_dir: str = "knowledge/logs",
        vector_backend: str = "chroma",
    ):
        self.source_dir = Path(source_dir)
        self.inventory_dir = Path(inventory_dir)
        self.index_dir = Path(index_dir)
        self.reports_dir = Path(reports_dir)
        self.logs_dir = Path(logs_dir)

        for d in [self.inventory_dir, self.index_dir, self.reports_dir, self.logs_dir]:
            d.mkdir(parents=True, exist_ok=True)

        self.chunker = SemanticChunker()
        self.embedder = Embedder(device="cpu")
        self.vector_store = VectorStore(
            backend=vector_backend,
            persist_dir=str(self.index_dir),
        )
        self.bm25_index = BM25Index()
        self.status = IngestionStatus()

    def run(self, force: bool = False) -> IngestionStatus:
        """Execute the full pipeline."""
        start_time = time.time()
        logger.info("Starting ingestion pipeline")

        # Step 1: Scan and inventory
        files = self._scan_source()
        logger.info(f"Found {len(files)} files in source library")

        # Step 2: Load existing hashes for dedup
        existing_hashes = self._load_existing_hashes()

        # Step 3: Process each file
        all_documents: list[Document] = []
        all_chunks: list[Chunk] = []
        new_hashes: dict[str, str] = {}

        for i, filepath in enumerate(files):
            logger.info(f"[{i+1}/{len(files)}] Processing: {filepath.name}")

            try:
                # Compute SHA256
                sha256 = self._compute_sha256(filepath)

                # Skip if already processed
                if sha256 in existing_hashes and not force:
                    logger.info(f"  Skipping (already indexed): {sha256[:16]}")
                    self.status.ingested += 1
                    continue

                # Extract document
                doc = extract_document(filepath)
                doc.metadata.sha256 = sha256

                # Skip empty documents
                if not doc.pages or not doc.full_text.strip():
                    logger.warning(f"  Empty document, skipping: {filepath.name}")
                    self.status.failed += 1
                    continue

                # Chunk
                chunks = self.chunker.chunk_document(doc)
                logger.info(f"  Extracted {len(doc.pages)} pages, {len(chunks)} chunks")

                all_documents.append(doc)
                all_chunks.extend(chunks)
                new_hashes[sha256] = str(filepath)
                self.status.ingested += 1

            except Exception as e:
                logger.error(f"  Error processing {filepath.name}: {e}")
                self.status.failed += 1
                self.status.errors.append(f"{filepath.name}: {str(e)}")

        # Step 4: Generate embeddings
        if all_chunks:
            logger.info(f"Generating embeddings for {len(all_chunks)} chunks")
            texts = [c.text for c in all_chunks]
            embeddings = self.embedder.embed_documents(texts)
            dense = embeddings.get("dense")

            # Step 5: Store in vector DB
            if dense is not None:
                logger.info("Storing in vector database")
                self.vector_store.connect()
                self.vector_store.upsert_chunks(all_chunks, dense)

            # Step 6: Build BM25 index
            logger.info("Building BM25 index")
            self.bm25_index.build(all_chunks)

        # Step 7: Save hashes
        self._save_hashes(new_hashes)

        # Step 8: Save inventory
        self._save_inventory(all_documents)

        # Step 9: Generate reports
        elapsed = time.time() - start_time
        self.status.last_run = now_utc()
        self.status.indexed = len(all_chunks)

        self._save_reports(elapsed)

        logger.info(
            f"Pipeline complete in {elapsed:.1f}s: "
            f"{self.status.ingested} ingested, {self.status.indexed} chunks indexed, "
            f"{self.status.failed} failed"
        )

        return self.status

    def _scan_source(self) -> list[Path]:
        """Scan source directory for processable files."""
        processable_extensions = {
            ".pdf", ".docx", ".doc", ".txt", ".md",
            ".jpg", ".jpeg", ".png", ".gif", ".tiff",
            ".epub", ".zip",
        }

        files = []
        for ext in processable_extensions:
            files.extend(self.source_dir.rglob(f"*{ext}"))
            files.extend(self.source_dir.rglob(f"*{ext.upper()}"))

        # Deduplicate and sort
        unique = sorted(set(files))
        # Exclude the structured subdirectories we created
        structured = {"books", "scans", "epub", "docx", "txt", "images", "archives", "_quarantine"}
        return [
            f for f in unique
            if not any(part in structured for part in f.relative_to(self.source_dir).parts[:-1])
        ]

    def _compute_sha256(self, filepath: Path) -> str:
        sha = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha.update(chunk)
        return sha.hexdigest()

    def _load_existing_hashes(self) -> dict[str, str]:
        hash_file = self.inventory_dir / "file_hashes.json"
        if hash_file.exists():
            with open(hash_file) as f:
                return json.load(f)
        return {}

    def _save_hashes(self, new_hashes: dict[str, str]):
        hash_file = self.inventory_dir / "file_hashes.json"
        existing = self._load_existing_hashes()
        existing.update(new_hashes)
        with open(hash_file, "w") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)

    def _save_inventory(self, documents: list[Document]):
        inventory = []
        for doc in documents:
            inventory.append({
                "document_id": doc.metadata.document_id,
                "sha256": doc.metadata.sha256,
                "filename": doc.metadata.source_filename,
                "path": doc.metadata.source_path,
                "type": doc.metadata.document_type.value,
                "language": doc.metadata.language,
                "ocr_status": doc.metadata.ocr_status.value,
                "page_count": doc.metadata.page_count,
                "file_size": doc.metadata.file_size_bytes,
                "word_count": doc.word_count,
                "imported": doc.metadata.import_timestamp,
            })

        with open(self.inventory_dir / "inventory.json", "w", encoding="utf-8") as f:
            json.dump(inventory, f, indent=2, ensure_ascii=False)

    def _save_reports(self, elapsed: float):
        report = {
            "pipeline_version": "0.1.0",
            "run_timestamp": now_utc(),
            "elapsed_seconds": round(elapsed, 2),
            "status": {
                "total_documents": self.status.total_documents,
                "ingested": self.status.ingested,
                "indexed_chunks": self.status.indexed,
                "failed": self.status.failed,
                "errors": self.status.errors[:50],
            },
        }

        with open(self.reports_dir / "ingestion_status.json", "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

    def search(self, query: str, top_k: int = 10):
        """Run a search using the loaded index."""
        from .models import QueryRequest
        from .retrieval.search import HybridRetriever

        retriever = HybridRetriever(
            vector_store=self.vector_store,
            embedder=self.embedder,
            bm25_index=self.bm25_index,
        )

        request = QueryRequest(query=query, top_k=top_k)
        return retriever.search(request)
