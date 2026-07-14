"""
AstroSage Knowledge Engine — CLI entry point.

Commands:
  ingest     Run the ingestion pipeline
  search     Search the knowledge base
  status     Show pipeline status
  serve      Start the MCP server
  stats      Show index statistics
  audit      Run integrity audit
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

console = Console()


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option(
    "--source-dir",
    default="knowledge/source_library",
    help="Source document directory",
)
@click.pass_context
def main(ctx, verbose, source_dir):
    """AstroSage Knowledge Engine — Self-hosted Knowledge Operating System."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    ctx.ensure_object(dict)
    ctx.obj["source_dir"] = source_dir


@main.command()
@click.option("--force", is_flag=True, help="Force re-ingestion of all files")
@click.pass_context
def ingest(ctx, force):
    """Run the ingestion pipeline."""
    from .pipeline import IngestionPipeline

    console.print("[bold blue]Starting ingestion pipeline...[/]")

    pipeline = IngestionPipeline(source_dir=ctx.obj["source_dir"])
    status = pipeline.run(force=force)

    table = Table(title="Ingestion Results")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    table.add_row("Documents ingested", str(status.ingested))
    table.add_row("Chunks indexed", str(status.indexed))
    table.add_row("Failed", str(status.failed))
    table.add_row("Last run", status.last_run)

    console.print(table)

    if status.errors:
        console.print(f"\n[red]{len(status.errors)} errors:[/]")
        for err in status.errors[:10]:
            console.print(f"  - {err}")


@main.command()
@click.argument("query")
@click.option("--top-k", "-k", default=10, help="Number of results")
@click.pass_context
def search(ctx, query, top_k):
    """Search the knowledge base."""
    from .pipeline import IngestionPipeline

    console.print(f"[bold blue]Searching: {query}[/]")

    pipeline = IngestionPipeline(source_dir=ctx.obj["source_dir"])
    result = pipeline.search(query, top_k=top_k)

    console.print(f"\nFound {len(result.results)} results in {result.processing_time_ms:.1f}ms\n")

    for r in result.results:
        console.print(f"[bold]Rank {r.rank}[/] (score: {r.score:.4f}, {r.confidence.value})")
        console.print(f"  Source: {r.chunk.document_id}")
        if r.chunk.page_numbers:
            console.print(f"  Pages: {r.chunk.page_numbers}")
        console.print(f"  {r.chunk.text[:200]}...")
        console.print()


@main.command()
@click.pass_context
def status(ctx):
    """Show pipeline status."""
    import json

    report_file = Path("knowledge/reports/ingestion_status.json")
    if report_file.exists():
        with open(report_file) as f:
            report = json.load(f)
        console.print_json(json.dumps(report, indent=2))
    else:
        console.print("[yellow]No ingestion reports found. Run 'ingest' first.[/]")


@main.command()
def serve():
    """Start the MCP server."""
    from .mcp.server import main as mcp_main

    mcp_main()


@main.command()
def stats():
    """Show index statistics."""
    from .storage.vector_store import VectorStore

    vs = VectorStore(backend="chroma")
    try:
        vs.connect()
        info = vs.get_stats()
        console.print_json(json.dumps(info, indent=2))
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")


@main.command()
def audit():
    """Run integrity audit."""
    import json
    import hashlib

    console.print("[bold blue]Running integrity audit...[/]")

    inventory_file = Path("knowledge/inventory/inventory.json")
    hash_file = Path("knowledge/inventory/file_hashes.json")
    source_dir = Path(ctx.obj.get("source_dir", "knowledge/source_library"))

    report = {
        "inventory_exists": inventory_file.exists(),
        "hash_file_exists": hash_file.exists(),
        "source_dir_exists": source_dir.exists(),
    }

    if source_dir.exists():
        files = [f for f in source_dir.rglob("*") if f.is_file()]
        report["total_source_files"] = len(files)

    if inventory_file.exists():
        with open(inventory_file) as f:
            inv = json.load(f)
        report["inventory_count"] = len(inv)

    if hash_file.exists():
        with open(hash_file) as f:
            hashes = json.load(f)
        report["total_hashes"] = len(hashes)

    console.print_json(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
