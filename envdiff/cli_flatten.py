"""CLI sub-command: envdiff flatten — display a nested tree view of a .env file."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict

from envdiff.flattener import flatten


def add_flatten_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "flatten",
        help="Display a .env file as a nested key tree.",
    )
    p.add_argument("file", help="Path to the .env file.")
    p.add_argument(
        "--separator",
        default="_",
        metavar="SEP",
        help="Key segment separator (default: '_').",
    )
    p.add_argument(
        "--max-depth",
        type=int,
        default=0,
        metavar="N",
        help="Maximum split depth (0 = unlimited).",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    p.set_defaults(func=run_flatten)


def _render_text(tree: Dict[str, Any], indent: int = 0) -> str:
    lines = []
    prefix = "  " * indent
    for key, value in sorted(tree.items()):
        if isinstance(value, dict):
            lines.append(f"{prefix}[{key}]")
            lines.append(_render_text(value, indent + 1))
        else:
            lines.append(f"{prefix}{key} = {value}")
    return "\n".join(lines)


def run_flatten(args: argparse.Namespace) -> int:
    try:
        result = flatten(args.file, separator=args.separator, max_depth=args.max_depth)
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps({"source": result.source, "tree": result.tree}, indent=2))
    else:
        print(result.summary())
        rendered = _render_text(result.tree)
        if rendered:
            print(rendered)

    return 0
