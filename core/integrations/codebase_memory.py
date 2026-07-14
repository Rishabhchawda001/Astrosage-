"""
Codebase Memory MCP — Index and search the repository.

Indexes: Python, Markdown, JSON, YAML, configuration, architecture docs,
ADRs, memory docs, tests, plugins. Builds knowledge graph of the codebase.
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


@dataclass
class CodeIndex:
    file_path: str = ""
    file_type: str = ""
    size_bytes: int = 0
    line_count: int = 0
    checksum: str = ""
    symbols: list[str] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    classes: list[str] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
    indexed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class CodeRelation:
    source: str = ""
    target: str = ""
    relation_type: str = ""  # imports, calls, inherits, tests, documents
    confidence: float = 1.0


class CodebaseMemory:
    """
    Codebase Memory MCP. Indexes the repository and provides
    semantic search over code, docs, and architecture.
    """

    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self._index: dict[str, CodeIndex] = {}
        self._relations: list[CodeRelation] = []
        self._symbol_index: dict[str, list[str]] = {}

    def index_file(self, file_path: str) -> CodeIndex:
        full_path = self.root_dir / file_path
        if not full_path.exists():
            return CodeIndex(file_path=file_path)

        content = full_path.read_text(errors="replace")
        lines = content.split("\n")
        checksum = hashlib.sha256(content.encode()).hexdigest()[:16]

        symbols = []
        imports = []
        classes = []
        functions = []

        if file_path.endswith(".py"):
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("import ") or stripped.startswith("from "):
                    imports.append(stripped[:80])
                elif stripped.startswith("class "):
                    name = stripped.split("(")[0].split(":")[0].replace("class ", "").strip()
                    classes.append(name)
                    symbols.append(name)
                elif stripped.startswith("def "):
                    name = stripped.split("(")[0].replace("def ", "").strip()
                    functions.append(name)
                    symbols.append(name)

        idx = CodeIndex(file_path=file_path, file_type=full_path.suffix,
                        size_bytes=full_path.stat().st_size, line_count=len(lines),
                        checksum=checksum, symbols=symbols, imports=imports,
                        classes=classes, functions=functions)
        self._index[file_path] = idx

        for sym in symbols:
            self._symbol_index.setdefault(sym, []).append(file_path)
        return idx

    def index_directory(self, dir_path: str = ".", extensions: list[str] | None = None) -> int:
        extensions = extensions or [".py", ".md", ".json", ".yaml", ".yml"]
        count = 0
        for root, dirs, files in os.walk(self.root_dir / dir_path):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("__pycache__", "node_modules", ".git")]
            for f in files:
                if any(f.endswith(ext) for ext in extensions):
                    rel = os.path.relpath(os.path.join(root, f), self.root_dir)
                    self.index_file(rel)
                    count += 1
        return count

    def add_relation(self, source: str, target: str, relation_type: str, confidence: float = 1.0) -> None:
        self._relations.append(CodeRelation(source=source, target=target, relation_type=relation_type, confidence=confidence))

    def search_symbol(self, symbol: str) -> list[str]:
        return self._symbol_index.get(symbol, [])

    def get_file(self, file_path: str) -> Optional[CodeIndex]:
        return self._index.get(file_path)

    def get_relations(self, file_path: str) -> list[CodeRelation]:
        return [r for r in self._relations if r.source == file_path or r.target == file_path]

    def count(self) -> int: return len(self._index)

    def summary(self) -> dict:
        type_counts: dict[str, int] = {}
        for idx in self._index.values():
            type_counts[idx.file_type] = type_counts.get(idx.file_type, 0) + 1
        return {"total_files": self.count(), "total_symbols": len(self._symbol_index),
                "total_relations": len(self._relations), "by_type": type_counts}
