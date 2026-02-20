#!/usr/bin/env python3
"""Upload YAML prompts to Langfuse for production management.

Loads all *.yaml prompt files from src/infrastructure/llm/prompts/
and uploads them to Langfuse with the specified label.

Usage:
  python scripts/upload_prompts_to_langfuse.py --production
  python scripts/upload_prompts_to_langfuse.py --staging
  python scripts/upload_prompts_to_langfuse.py --dry-run
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml


def load_prompts(prompts_dir: Path) -> list[dict]:
    """Load all YAML prompt files from directory."""
    prompts = []
    for yaml_file in sorted(prompts_dir.glob("*.yaml")):
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
            data["source_file"] = yaml_file.name
            prompts.append(data)
    return prompts


def upload_to_langfuse(prompts: list[dict], label: str = "production") -> None:
    """Upload prompts to Langfuse."""
    try:
        from langfuse import Langfuse
    except ImportError:
        print("ERROR: langfuse not installed. Run: pip install langfuse")
        sys.exit(1)

    try:
        client = Langfuse()
        for p in prompts:
            client.create_prompt(
                name=p["name"],
                prompt=p["prompt"],
                labels=[label],
                tags=["v5", "question-generation"],
            )
            print(f"  Uploaded: {p['name']} (label={label})")
    except Exception as e:
        print(f"ERROR: Upload failed: {e}")
        sys.exit(1)


def dry_run(prompts: list[dict]) -> None:
    """Print prompt summary without uploading."""
    for p in prompts:
        print(f"  [{p['source_file']}] {p['name']} v{p.get('version', 1)}")
        print(f"    Label: {p.get('label', 'production')}")
        print(f"    Length: {len(p.get('prompt', ''))} chars")


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload prompts to Langfuse")
    parser.add_argument(
        "--production", action="store_true", help="Upload with 'production' label"
    )
    parser.add_argument(
        "--staging", action="store_true", help="Upload with 'staging' label"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print summary without uploading"
    )
    args = parser.parse_args()

    prompts_dir = (
        Path(__file__).parent.parent
        / "src"
        / "infrastructure"
        / "llm"
        / "prompts"
    )
    if not prompts_dir.exists():
        print(f"ERROR: Prompts directory not found: {prompts_dir}")
        sys.exit(1)

    prompts = load_prompts(prompts_dir)
    print(f"Found {len(prompts)} prompts in {prompts_dir}")

    if args.dry_run:
        dry_run(prompts)
    elif args.production:
        upload_to_langfuse(prompts, label="production")
    elif args.staging:
        upload_to_langfuse(prompts, label="staging")
    else:
        print("Specify --production, --staging, or --dry-run")
        sys.exit(1)

    print("Done.")


if __name__ == "__main__":
    main()
