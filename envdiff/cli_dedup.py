"""CLI sub-command: deduplicate a .env file."""
from __future__ import annotations

import argparse
import sys

from envdiff.deduplicator import deduplicate


def add_dedup_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "dedup",
        help="Detect (and optionally remove) duplicate keys in a .env file.",
    )
    p.add_argument("file", help="Path to the .env file to inspect.")
    p.add_argument(
        "--fix",
        action="store_true",
        default=False,
        help="Rewrite the file keeping only the last occurrence of each duplicate key.",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="output_format",
        help="Output format (default: text).",
    )
    p.set_defaults(func=run_dedup)


def run_dedup(args: argparse.Namespace) -> int:
    try:
        result = deduplicate(args.file, write=args.fix)
    except FileNotFoundError:
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        return 1

    if args.output_format == "json":
        import json
        data = {
            "path": result.path,
            "has_duplicates": result.has_duplicates,
            "duplicates": result.duplicates,
            "original_line_count": result.original_line_count,
            "kept_line_count": len(result.kept_lines),
        }
        print(json.dumps(data, indent=2))
    else:
        print(result.summary())
        if result.has_duplicates and args.fix:
            print(f"  File rewritten: {result.path}")

    return 1 if result.has_duplicates else 0
