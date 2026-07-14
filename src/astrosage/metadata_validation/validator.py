"""Metadata Validation Engine — audits every document for metadata issues."""
from __future__ import annotations

import csv
import json
import logging
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ValidationIssue:
    filename: str
    field: str
    severity: str  # "error", "warning", "info"
    message: str
    current_value: str = ""


@dataclass
class ValidationReport:
    total_documents: int = 0
    documents_with_issues: int = 0
    issues_by_type: dict = field(default_factory=dict)
    issues_by_severity: dict = field(default_factory=dict)
    issues: list = field(default_factory=list)
    completeness: dict = field(default_factory=dict)


def validate_manifest(manifest_path: Path) -> ValidationReport:
    """Validate every row in the manifest CSV."""
    report = ValidationReport()
    
    with open(manifest_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    
    report.total_documents = len(rows)
    
    required_fields = ["uuid", "sha256", "original_filename", "language", "extension"]
    optional_fields = ["title", "author", "publisher", "edition", "subject", "page_count"]
    
    for row in rows:
        doc_issues = []
        filename = row.get("original_filename", "unknown")
        
        # Required fields
        for field_name in required_fields:
            val = row.get(field_name, "").strip()
            if not val:
                doc_issues.append(ValidationIssue(
                    filename=filename, field=field_name, severity="error",
                    message=f"Required field '{field_name}' is empty",
                ))
        
        # Title validation
        title = row.get("title", "").strip()
        if not title or title == filename:
            doc_issues.append(ValidationIssue(
                filename=filename, field="title", severity="warning",
                message="Title is empty or same as filename",
                current_value=title,
            ))
        
        # Author validation
        author = row.get("author", "").strip()
        if not author:
            doc_issues.append(ValidationIssue(
                filename=filename, field="author", severity="warning",
                message="Author not extracted",
            ))
        
        # Publisher validation
        publisher = row.get("publisher", "").strip()
        if not publisher:
            doc_issues.append(ValidationIssue(
                filename=filename, field="publisher", severity="info",
                message="Publisher not extracted",
            ))
        
        # Language validation
        language = row.get("language", "").strip()
        valid_languages = {"english", "hindi", "sanskrit", "bengali", "telugu", "tamil",
                          "kannada", "malayalam", "gujarati", "odia", "punjabi", "unknown"}
        if language and language.lower() not in valid_languages:
            doc_issues.append(ValidationIssue(
                filename=filename, field="language", severity="warning",
                message=f"Unusual language value: '{language}'",
                current_value=language,
            ))
        
        # Page count validation
        page_count = row.get("page_count", "0")
        try:
            pc = int(page_count)
            if pc == 0 and row.get("extension", "") == ".pdf":
                doc_issues.append(ValidationIssue(
                    filename=filename, field="page_count", severity="warning",
                    message="PDF has 0 pages (possibly encrypted or corrupted)",
                ))
            elif pc > 10000:
                doc_issues.append(ValidationIssue(
                    filename=filename, field="page_count", severity="warning",
                    message=f"Unusually high page count: {pc}",
                ))
        except ValueError:
            doc_issues.append(ValidationIssue(
                filename=filename, field="page_count", severity="error",
                message=f"Invalid page count: '{page_count}'",
                current_value=page_count,
            ))
        
        # UUID validation
        uuid = row.get("uuid", "")
        if uuid and not re.match(r"^BOOK-[a-f0-9]{8}$", uuid):
            doc_issues.append(ValidationIssue(
                filename=filename, field="uuid", severity="warning",
                message=f"UUID format unexpected: {uuid}",
                current_value=uuid,
            ))
        
        # SHA256 validation
        sha256 = row.get("sha256", "")
        if sha256 and len(sha256) != 64:
            doc_issues.append(ValidationIssue(
                filename=filename, field="sha256", severity="error",
                message=f"Invalid SHA256 length: {len(sha256)}",
            ))
        
        # File size sanity
        try:
            size = int(row.get("file_size_bytes", "0"))
            if size == 0:
                doc_issues.append(ValidationIssue(
                    filename=filename, field="file_size_bytes", severity="warning",
                    message="File size is 0 bytes",
                ))
        except ValueError:
            pass
        
        if doc_issues:
            report.documents_with_issues += 1
            report.issues.extend(doc_issues)
    
    # Summarize
    type_counts = defaultdict(int)
    severity_counts = defaultdict(int)
    field_counts = defaultdict(int)
    for issue in report.issues:
        type_counts[issue.field] += 1
        severity_counts[issue.severity] += 1
        field_counts[issue.field] += 1
    
    report.issues_by_type = dict(type_counts)
    report.issues_by_severity = dict(severity_counts)
    
    # Completeness
    for field_name in required_fields + optional_fields:
        present = sum(1 for r in rows if r.get(field_name, "").strip())
        report.completeness[field_name] = round(present / max(1, len(rows)) * 100, 1)
    
    return report


def save_validation_report(report: ValidationReport, output_dir: Path):
    """Save the validation report."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # JSON summary
    summary = {
        "total_documents": report.total_documents,
        "documents_with_issues": report.documents_with_issues,
        "total_issues": len(report.issues),
        "issues_by_severity": report.issues_by_severity,
        "issues_by_field": report.issues_by_type,
        "completeness": report.completeness,
    }
    with open(output_dir / "metadata_validation.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    # Detailed issues CSV
    if report.issues:
        with open(output_dir / "metadata_issues.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["filename", "field", "severity", "message", "current_value"])
            writer.writeheader()
            for issue in report.issues:
                writer.writerow(asdict(issue))
    
    logger.info(f"Validation: {report.documents_with_issues}/{report.total_documents} docs with issues")
