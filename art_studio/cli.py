#!/usr/bin/env python3
"""
AstroSage Art Studio CLI

Usage:
    python -m art_studio status
    python -m art_studio generate [--variant ID] [--seed N] [--count N]
    python -m art_studio evaluate <image_path> [--prompt-id ID]
    python -m art_studio accept <image_path> --prompt-id ID [--notes TEXT]
    python -m art_studio versions
    python -m art_studio prompts
    python -m art_studio providers
"""

import argparse
import json
import os
import sys

STUDIO_ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(STUDIO_ROOT)
FRONTEND_PUBLIC = os.path.join(PROJECT_ROOT, "frontend", "public")

sys.path.insert(0, PROJECT_ROOT)

from art_studio.integration.pipeline import ArtPipeline, PipelineConfig
from art_studio.prompts.library import load_library
from art_studio.providers import list_providers, get_provider


def get_pipeline(args=None) -> ArtPipeline:
    provider = getattr(args, "provider", "pollinations") if args else "pollinations"
    config = PipelineConfig(
        studio_root=STUDIO_ROOT,
        frontend_public=FRONTEND_PUBLIC,
        provider_name=provider,
    )
    return ArtPipeline(config)


def cmd_status(args):
    pipeline = get_pipeline(args)
    status = pipeline.status()
    print(json.dumps(status, indent=2))


def cmd_generate(args):
    pipeline = get_pipeline(args)
    count = getattr(args, "count", 1)
    pipeline.config.generate_variants = count
    variant = getattr(args, "variant", None)
    seed = getattr(args, "seed", None)
    results = pipeline.generate(variant_id=variant, seed_override=seed)
    print(f"\nGenerated {sum(1 for r in results if r['result'].success)} images")
    for r in results:
        s = "✓" if r["result"].success else "✗"
        print(f"  {s} {r['variant_id']} seed={r['seed']}")


def cmd_evaluate(args):
    pipeline = get_pipeline(args)
    prompt_id = getattr(args, "prompt_id", "unknown")
    report = pipeline.evaluate(args.image_path, prompt_id)
    print(f"\nScore: {report.overall_score:.2f}")
    print(f"Recommendation: {report.recommendation}")
    for d in report.dimensions:
        print(f"  {d.name}: {d.score:.2f} (weight={d.weight})")


def cmd_accept(args):
    pipeline = get_pipeline(args)
    result = pipeline.accept_version(
        image_path=args.image_path,
        prompt_id=args.prompt_id,
        notes=getattr(args, "notes", ""),
    )
    print(json.dumps(result, indent=2))


def cmd_versions(args):
    pipeline = get_pipeline(args)
    versions = pipeline.versions.get_all()
    active = pipeline.versions.get_active()
    print(f"Versions: {len(versions)}")
    if active:
        print(f"Active: {active.version} ({active.image_filename})")
    for v in versions:
        marker = " ← active" if v.is_active else ""
        print(f"  {v.version}: {v.image_filename} [{v.prompt_id}]{marker}")


def cmd_prompts(args):
    lib = load_library()
    print(f"Prompt variants: {len(lib.variants)}")
    print(f"Active: {lib.active_id}")
    for v in lib.variants:
        marker = " ← active" if v.id == lib.active_id else ""
        print(f"  {v.id}: {v.output_width}x{v.output_height} [{v.provider}]{marker}")
        print(f"    Scene: {v.scene[:80]}...")


def cmd_providers(args):
    names = list_providers()
    print(f"Available providers: {len(names)}")
    for name in names:
        p = get_provider(name)
        ok = "✓" if p.health_check() else "✗"
        print(f"  {ok} {name}: {p.description}")


def main():
    parser = argparse.ArgumentParser(description="AstroSage Art Studio CLI")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("status", help="Show pipeline status")

    gen = sub.add_parser("generate", help="Generate artwork")
    gen.add_argument("--variant", help="Prompt variant ID")
    gen.add_argument("--seed", type=int, help="Random seed")
    gen.add_argument("--count", type=int, default=1, help="Number of candidates")
    gen.add_argument("--provider", default="pollinations")

    ev = sub.add_parser("evaluate", help="Evaluate artwork quality")
    ev.add_argument("image_path", help="Path to image")
    ev.add_argument("--prompt-id", default="unknown")

    ac = sub.add_parser("accept", help="Accept and version artwork")
    ac.add_argument("image_path", help="Path to image")
    ac.add_argument("--prompt-id", required=True)
    ac.add_argument("--notes", default="")

    sub.add_parser("versions", help="List all versions")
    sub.add_parser("prompts", help="List prompt variants")
    sub.add_parser("providers", help="List and check providers")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    commands = {
        "status": cmd_status,
        "generate": cmd_generate,
        "evaluate": cmd_evaluate,
        "accept": cmd_accept,
        "versions": cmd_versions,
        "prompts": cmd_prompts,
        "providers": cmd_providers,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
