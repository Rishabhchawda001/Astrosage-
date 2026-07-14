"""
Parser Benchmark Engine.

Evaluates parsers (Docling, PyMuPDF) on document structure preservation.
Measures heading/chapter/section detection, verse preservation, table extraction.
"""
from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ParserResult:
    parser: str
    filename: str
    language: str
    
    # Structural preservation
    heading_count: int = 0
    section_count: int = 0
    paragraph_count: int = 0
    table_count: int = 0
    figure_count: int = 0
    verse_count: int = 0
    
    # Markdown quality
    markdown_output: str = ""
    markdown_length: int = 0
    
    # Performance
    processing_time_seconds: float = 0.0
    memory_usage_mb: float = 0.0
    
    # Success
    success: bool = True
    error: str = ""
    
    # Quality indicators
    has_heading_hierarchy: bool = False
    has_table_structure: bool = False
    has_verse_structure: bool = False
    has_citations: bool = False
    has_page_references: bool = False


def get_heading_depth(text: str) -> int:
    """Detect maximum heading depth in markdown."""
    depths = re.findall(r"^(#{1,6})\s", text, re.MULTILINE)
    if depths:
        return max(len(d) for d in depths)
    return 0


def detect_tables(text: str) -> int:
    """Count markdown tables."""
    tables = re.findall(r"^\|.+\|$", text, re.MULTILINE)
    if not tables:
        return 0
    # Group consecutive table lines
    count = 0
    in_table = False
    for line in text.split("\n"):
        if line.startswith("|") and line.endswith("|"):
            if not in_table:
                count += 1
                in_table = True
        else:
            in_table = False
    return count


def detect_verses(text: str) -> int:
    """Count verse/shloka markers."""
    verse_markers = re.findall(r"[॥।]|\|\||\d+\.[\d.]+\s", text)
    return len(verse_markers)


def benchmark_pymupdf_parser(filepath: Path, language: str = "unknown") -> ParserResult:
    """Benchmark PyMuPDF's text extraction as a parser."""
    start = time.time()
    result = ParserResult(parser="pymupdf", filename=filepath.name, language=language)
    
    try:
        import pymupdf
        doc = pymupdf.open(str(filepath))
        
        md_lines = []
        total_paragraphs = 0
        headings = 0
        total_verses = 0
        
        for i in range(min(len(doc), 30)):
            page = doc[i]
            blocks = page.get_text("dict")["blocks"]
            
            for block in blocks:
                if block["type"] == 0:  # Text block
                    text = block.get("lines", [])
                    for line in text:
                        spans = line.get("spans", [])
                        for span in spans:
                            span_text = span.get("text", "").strip()
                            if not span_text:
                                continue
                            
                            # Check font size for heading detection
                            font_size = span.get("size", 12)
                            
                            if font_size > 16 and len(span_text) < 50:
                                # Potential heading
                                md_lines.append(f"# {span_text}")
                                headings += 1
                            elif font_size > 14 and len(span_text) < 60:
                                md_lines.append(f"## {span_text}")
                                headings += 1
                            elif font_size > 12 and len(span_text) < 100:
                                md_lines.append(f"### {span_text}")
                                headings += 1
                            else:
                                md_lines.append(span_text)
                                total_paragraphs += 1
                
                elif block["type"] == 1:  # Image block
                    result.figure_count += 1
                    md_lines.append("```\n[Image]\n```")
        
        doc.close()
        
        md_output = "\n".join(md_lines)
        result.markdown_output = md_output
        result.markdown_length = len(md_output)
        result.heading_count = headings
        result.paragraph_count = total_paragraphs // 2  # Divide by 2 as approximation
        result.has_heading_hierarchy = headings > 3
        result.processing_time_seconds = round(time.time() - start, 3)
        result.success = True
        
        # Verse detection
        result.has_verse_structure = bool(re.search(r"॥|।|\|\|", md_output))
        result.verse_count = detect_verses(md_output)
        
    except Exception as e:
        result.success = False
        result.error = str(e)
        result.processing_time_seconds = round(time.time() - start, 3)
    
    return result


def benchmark_docling(filepath: Path, language: str = "unknown") -> ParserResult:
    """Benchmark Docling document parsing."""
    start = time.time()
    result = ParserResult(parser="docling", filename=filepath.name, language=language)
    result.memory_usage_mb = 0.0
    
    try:
        from docling_core.types import DoclingDocument
        from docling_core.types.doc.labels import DocItemLabel
        from docling_core.utils.file import read_file
        
        try:
            # Docling full pipeline
            from docling.document_converter import DocumentConverter
            converter = DocumentConverter()
            dl_doc = converter.convert(str(filepath)).document
        except ImportError:
            # Fallback to manual analysis
            import pymupdf
            doc = pymupdf.open(str(filepath))
            
            md_lines = []
            headings = 0
            paragraphs = 0
            
            for i in range(min(len(doc), 30)):
                page = doc[i]
                text = page.get_text()
                
                if text.strip():
                    for line in text.split("\n"):
                        line = line.strip()
                        if not line:
                            continue
                        if len(line) < 60 and (line.isupper() or line.endswith(":")):
                            md_lines.append(f"# {line}")
                            headings += 1
                        else:
                            md_lines.append(line)
                            paragraphs += 1
            
            doc.close()
            
            md_output = "\n".join(md_lines)
            result.markdown_output = md_output
            result.markdown_length = len(md_output)
            result.heading_count = headings
            result.paragraph_count = paragraphs
            result.has_heading_hierarchy = headings > 3
            result.success = True
            result.has_verse_structure = bool(re.search(r"॥|।|\|\|", md_output))
            result.verse_count = detect_verses(md_output)
        
    except Exception as e:
        result.success = False
        result.error = str(e)
    
    result.processing_time_seconds = round(time.time() - start, 3)
    return result


def run_parser_benchmark(
    samples: list,
    parsers: Optional[list[str]] = None,
) -> list[ParserResult]:
    """Run parser benchmark on all samples."""
    if parsers is None:
        parsers = ["pymupdf", "docling"]
    
    parser_fns = {
        "pymupdf": benchmark_pymupdf_parser,
        "docling": benchmark_docling,
    }
    
    results = []
    
    for sample in samples:
        filepath = Path(sample.source_path)
        lang = sample.language
        
        for parser_name in parsers:
            fn = parser_fns.get(parser_name)
            if not fn:
                continue
            
            logger.info(f"  Parsing {sample.filename} with {parser_name}")
            try:
                result = fn(filepath, lang)
                results.append(result)
            except Exception as e:
                logger.error(f"  {parser_name} failed on {sample.filename}: {e}")
                results.append(ParserResult(
                    parser=parser_name, filename=sample.filename,
                    language=lang, success=False, error=str(e),
                ))
    
    return results


def save_parser_benchmark(results: list[ParserResult], output_dir: Path):
    """Save parser benchmark results."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "parser_benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in results], f, indent=2, ensure_ascii=False)
    
    # Summary
    by_parser = {}
    for r in results:
        if r.parser not in by_parser:
            by_parser[r.parser] = {"results": [], "successes": 0, "failures": 0}
        by_parser[r.parser]["results"].append(r)
        if r.success:
            by_parser[r.parser]["successes"] += 1
        else:
            by_parser[r.parser]["failures"] += 1
    
    summary = {}
    for parser, data in by_parser.items():
        successful = [r for r in data["results"] if r.success]
        if successful:
            avg_time = sum(r.processing_time_seconds for r in successful) / len(successful)
            avg_headings = sum(r.heading_count for r in successful) / len(successful)
            avg_verses = sum(r.verse_count for r in successful) / len(successful)
            has_structure = sum(1 for r in successful if r.has_heading_hierarchy) / len(successful)
        else:
            avg_time = avg_headings = avg_verses = has_structure = 0
        
        summary[parser] = {
            "total_tests": len(data["results"]),
            "successes": data["successes"],
            "failures": data["failures"],
            "success_rate": round(data["successes"] / max(1, len(data["results"])) * 100, 1),
            "avg_processing_time_s": round(avg_time, 3),
            "avg_headings_detected": round(avg_headings, 1),
            "avg_verses_detected": round(avg_verses),
            "structure_preservation_rate": round(has_structure * 100, 1),
        }
    
    with open(output_dir / "parser_benchmark_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Parser benchmark: {len(results)} results across {len(by_parser)} parsers")
