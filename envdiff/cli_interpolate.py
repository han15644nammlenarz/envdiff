"""CLI sub-command: envdiff interpolate — resolve variable references in a .env file."""
from __future__ import annotations

import argparse
import json
import sys

from envdiff.parser import parse_env_file
from envdiff.interpolator import interpolate


def add_interpolate_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "interpolate",
        help="Resolve variable interpolation references in a .env file",
    )
    p.add_argument("file", help="Path to the .env file")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--fail-on-unresolved",
        action="store_true",
        default=False,
        help="Exit with code 1 if any references are unresolved",
    )
    p.set_defaults(func=run_interpolate)


def run_interpolate(args: argparse.Namespace) -> int:
    try:
        env = parse_env_file(args.file)
    except FileNotFoundError:
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        return 2

    result = interpolate(env)

    if args.fmt == "json":
        payload = {
            "resolved": result.resolved,
            "unresolved": result.unresolved,
            "references": result.references,
        }
        print(json.dumps(payload, indent=2))
    else:
        print(result.summary())
        if result.references:
            print("\nReference map:")
            for key, refs in result.references.items():
                print(f"  {key} -> {refs}")

    if args.fail_on_unresolved and result.unresolved:
        return 1
    return 0
