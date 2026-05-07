"""CLI sub-command: envdiff format — reformat .env files in place."""

from __future__ import annotations

import argparse
import sys
from typing import List

from envdiff.formatter import format_env, summary, write_formatted


def add_format_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "format",
        help="Reformat .env file(s) with consistent style",
    )
    p.add_argument("files", nargs="+", metavar="FILE", help=".env file(s) to format")
    p.add_argument(
        "--sort",
        action="store_true",
        default=False,
        help="Sort keys alphabetically",
    )
    p.add_argument(
        "--check",
        action="store_true",
        default=False,
        help="Exit with non-zero status if any file would be changed (dry-run)",
    )
    p.set_defaults(func=run_format)


def run_format(args: argparse.Namespace) -> int:
    any_changed = False
    for path in args.files:
        try:
            result = format_env(path, sort_keys=args.sort)
        except FileNotFoundError:
            print(f"error: file not found: {path}", file=sys.stderr)
            return 1

        print(summary(result))

        if result.changed:
            any_changed = True
            if not args.check:
                write_formatted(result)

    if args.check and any_changed:
        print("error: one or more files would be reformatted", file=sys.stderr)
        return 1
    return 0
