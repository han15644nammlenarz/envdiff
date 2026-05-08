"""CLI sub-command: classify — show key categories for a .env file."""

from __future__ import annotations

import argparse
import json
import sys

from envdiff.classifier import classify


def add_classify_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "classify",
        help="Classify keys in a .env file by type (secret, url, port, flag, path, general)",
    )
    p.add_argument("file", help="Path to the .env file")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--category",
        metavar="CAT",
        help="Only show keys belonging to this category",
    )
    p.set_defaults(func=run_classify)


def run_classify(args: argparse.Namespace) -> int:
    try:
        result = classify(args.file)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        data: dict = {
            "path": result.path,
            "categories": {
                cat: sorted(keys)
                for cat, keys in sorted(result.categories.items())
            },
        }
        if args.category:
            data = {
                "path": result.path,
                "category": args.category,
                "keys": sorted(result.keys_in(args.category)),
            }
        print(json.dumps(data, indent=2))
    else:
        if args.category:
            keys = result.keys_in(args.category)
            if not keys:
                print(f"No keys classified as '{args.category}'.")
            else:
                print(f"{args.category} ({len(keys)}):")
                for k in sorted(keys):
                    print(f"  {k}")
        else:
            print(result.summary())

    return 0
