"""Document processor adapter interfaces."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DocumentInput:
    file_path: str = ""
    file_bytes: bytes = b""
    mime_type: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class DocumentOutput:
    text: str = ""
    pages: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    confidence: float = 0.0
    errors: list[str] = field(default_factory=list)


class DocumentProcessorAdapter(ABC):
    @abstractmethod
    def name(self) -> str: ...
    @abstractmethod
    def process(self, input_data: DocumentInput) -> DocumentOutput: ...
    @abstractmethod
    def health(self) -> dict: ...


class PyMuPDFAdapter(DocumentProcessorAdapter):
    def name(self) -> str: return "pymupdf"
    def process(self, input_data: DocumentInput) -> DocumentOutput:
        return DocumentOutput(errors=["Not yet implemented"])
    def health(self) -> dict: return {"status": "scaffold"}


class TesseractAdapter(DocumentProcessorAdapter):
    def name(self) -> str: return "tesseract"
    def process(self, input_data: DocumentInput) -> DocumentOutput:
        return DocumentOutput(errors=["Not yet implemented"])
    def health(self) -> dict: return {"status": "scaffold"}


class PaddleOCRAdapter(DocumentProcessorAdapter):
    def name(self) -> str: return "paddleocr"
    def process(self, input_data: DocumentInput) -> DocumentOutput:
        return DocumentOutput(errors=["Not yet implemented"])
    def health(self) -> dict: return {"status": "scaffold"}


class OCRmyPDFAdapter(DocumentProcessorAdapter):
    def name(self) -> str: return "ocrmypdf"
    def process(self, input_data: DocumentInput) -> DocumentOutput:
        return DocumentOutput(errors=["Not yet implemented"])
    def health(self) -> dict: return {"status": "scaffold"}


class UnstructuredAdapter(DocumentProcessorAdapter):
    def name(self) -> str: return "unstructured"
    def process(self, input_data: DocumentInput) -> DocumentOutput:
        return DocumentOutput(errors=["Not yet implemented"])
    def health(self) -> dict: return {"status": "scaffold"}
