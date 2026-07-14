"""
Semantic chunking pipeline.

Never chunk using fixed token windows alone.
Prefer semantic boundaries (chapter, section, paragraph, verse).
Preserve context, citations, and page references.
"""
from __future__ import annotations

import hashlib
import logging
import re
from pathlib import Path
from typing import Optional

from ..models import Chunk, Document, PageContent

logger = logging.getLogger(__name__)


# Maximum tokens per chunk (conservative for BGE-M3's 8192 limit)
MAX_TOKENS = 2048
OVERLAP_TOKENS = 100

# Approximate: 1 token ≈ 4 characters for English, varies for Devanagari
TOKEN_ESTIMATE_RATIO = 4.0


class SemanticChunker:
    """Chunks documents using semantic boundaries."""

    def __init__(
        self,
        max_tokens: int = MAX_TOKENS,
        overlap_tokens: int = OVERLAP_TOKENS,
    ):
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens

    def chunk_document(
        self, document: Document, min_chunk_length: int = 50
    ) -> list[Chunk]:
        """Chunk a complete document into semantic units."""
        all_chunks: list[Chunk] = []

        for page in document.pages:
            page_chunks = self._chunk_page(
                page, document.metadata.document_id, min_chunk_length
            )
            all_chunks.extend(page_chunks)

        # Post-processing: assign chunk IDs and hashes
        for i, chunk in enumerate(all_chunks):
            chunk.chunk_id = f"chunk_{document.metadata.document_id}_{i:06d}"
            chunk.compute_sha256()

        return all_chunks

    def _chunk_page(
        self,
        page: PageContent,
        document_id: str,
        min_chunk_length: int,
    ) -> list[Chunk]:
        """Chunk a single page into semantic units."""
        text = page.text
        if not text or len(text) < min_chunk_length:
            return []

        # Try to split by semantic boundaries first
        chunks = self._split_by_verses(text, page.page_number, document_id, min_chunk_length)
        if chunks:
            return chunks

        chunks = self._split_by_headers(text, page.page_number, document_id, min_chunk_length)
        if chunks:
            return chunks

        chunks = self._split_by_paragraphs(text, page.page_number, document_id, min_chunk_length)
        if chunks:
            return chunks

        # Fallback: semantic sentence grouping
        return self._split_by_sentences(text, page.page_number, document_id, min_chunk_length)

    def _split_by_verses(
        self,
        text: str,
        page_number: int,
        document_id: str,
        min_chunk_length: int,
    ) -> list[Chunk]:
        """Split text by verse boundaries (Sanskrit/Vedic texts)."""
        # Vedic verse patterns: verse numbers like verse 1.2.3 or || or ॥
        verse_patterns = [
            r"\|\|",  # || delimiter
            r"॥",  # Devanagari double danda
            r"।",  # Devanagari single danda
            r"\n\d+\.[\d.]+\s",  # Verse numbers like "1.2.3 "
            r"\n\d+\.\s",  # Verse numbers like "1. "
        ]

        import re

        # Try splitting by a composite pattern
        for pattern in verse_patterns:
            parts = re.split(pattern, text)
            if len(parts) > 1 and self._all_long_enough(parts, min_chunk_length):
                chunks = []
                for part in parts:
                    part = part.strip()
                    if len(part) >= min_chunk_length:
                        chunks.append(
                            Chunk(
                                document_id=document_id,
                                text=part,
                                page_numbers=[page_number],
                                token_count=self._token_count(part),
                            )
                        )
                if self._exceeds_max_tokens(chunks):
                    break  # Fall through to next method
                return chunks
        return []

    def _split_by_headers(
        self,
        text: str,
        page_number: int,
        document_id: str,
        min_chunk_length: int,
    ) -> list[Chunk]:
        """Split using markdown-style headers or numbered sections."""
        header_patterns = [
            r"\n#{1,6}\s+.*\n",  # Markdown headers
            r"\n[IVXLCDM]+\.\s+.*\n",  # Roman numeral headers
            r"\n\d+\.\d+\s+.*\n",  # Numbered section headers
            r"\nअध्याय\s+\d+",  # Hindi "Adhyay" (chapter)
            r"\nश्लोक\s+\d+",  # Hindi "Shlok" (verse)
        ]

        for pattern in header_patterns:
            parts = re.split(pattern, text)
            if len(parts) > 1 and self._all_long_enough(parts, min_chunk_length):
                chunks = []
                for part in parts:
                    part = part.strip()
                    if len(part) >= min_chunk_length:
                        chunks.append(
                            Chunk(
                                document_id=document_id,
                                text=part,
                                page_numbers=[page_number],
                                token_count=self._token_count(part),
                            )
                        )
                if self._exceeds_max_tokens(chunks):
                    break
                return chunks
        return []

    def _split_by_paragraphs(
        self,
        text: str,
        page_number: int,
        document_id: str,
        min_chunk_length: int,
    ) -> list[Chunk]:
        """Split by double newlines (paragraph boundaries)."""
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if len(paragraphs) <= 1:
            return []

        # Group paragraphs into chunks that fit within max_tokens
        chunks = []
        current_parts = []
        current_tokens = 0

        for para in paragraphs:
            para_tokens = self._token_count(para)

            if current_tokens + para_tokens > self.max_tokens and current_parts:
                # Create chunk from current accumulation
                chunk_text = "\n\n".join(current_parts)
                if len(chunk_text) >= min_chunk_length:
                    chunks.append(
                        Chunk(
                            document_id=document_id,
                            text=chunk_text,
                            page_numbers=[page_number],
                            token_count=current_tokens,
                        )
                    )
                # Overlap: keep the last paragraph
                current_parts = current_parts[-1:] if current_parts else []
                current_tokens = self._token_count(current_parts[0]) if current_parts else 0

            current_parts.append(para)
            current_tokens += para_tokens

        # Final chunk
        if current_parts:
            chunk_text = "\n\n".join(current_parts)
            if len(chunk_text) >= min_chunk_length:
                chunks.append(
                    Chunk(
                        document_id=document_id,
                        text=chunk_text,
                        page_numbers=[page_number],
                        token_count=current_tokens,
                    )
                )

        return chunks

    def _split_by_sentences(
        self,
        text: str,
        page_number: int,
        document_id: str,
        min_chunk_length: int,
    ) -> list[Chunk]:
        """Fallback: group sentences into token-bounded chunks."""
        # Sentence boundaries: . ? ! for Latin, । for Devanagari
        sentence_pattern = r"(?<=[.!?।])\s+"
        sentences = re.split(sentence_pattern, text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) <= 1:
            return []

        chunks = []
        current_parts = []
        current_tokens = 0

        for sentence in sentences:
            sent_tokens = self._token_count(sentence)

            if current_tokens + sent_tokens > self.max_tokens and current_parts:
                chunk_text = " ".join(current_parts)
                if len(chunk_text) >= min_chunk_length:
                    chunks.append(
                        Chunk(
                            document_id=document_id,
                            text=chunk_text,
                            page_numbers=[page_number],
                            token_count=current_tokens,
                        )
                    )
                current_parts = current_parts[-1:] if current_parts else []
                current_tokens = self._token_count(current_parts[0]) if current_parts else 0

            current_parts.append(sentence)
            current_tokens += sent_tokens

        if current_parts:
            chunk_text = " ".join(current_parts)
            if len(chunk_text) >= min_chunk_length:
                chunks.append(
                    Chunk(
                        document_id=document_id,
                        text=chunk_text,
                        page_numbers=[page_number],
                        token_count=current_tokens,
                    )
                )

        return chunks

    def _token_count(self, text: str) -> int:
        """Estimate token count."""
        return max(1, len(text) // int(TOKEN_ESTIMATE_RATIO))

    def _all_long_enough(
        self, parts: list[str], min_length: int
    ) -> bool:
        """Check if all parts meet minimum length."""
        long_parts = [p for p in parts if len(p.strip()) >= min_length]
        return len(long_parts) >= len(parts) // 2

    def _exceeds_max_tokens(self, chunks: list[Chunk]) -> bool:
        """Check if any chunk exceeds max tokens."""
        return any(c.token_count > self.max_tokens for c in chunks)
