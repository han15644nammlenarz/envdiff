"""CLI sub-command: envdiff rename — rename keys in .env files."""

from __future__ import annotations

import argparse
import sys
from typing import List

from envdiff.renamer import rename


def add_rename_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the *rename* sub-command onto *subparsers*."""
    p = subparsers.add_parser(
        "rename",
        help="Rename one or more keys in .env file(s)",
    )
    p.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help=".env file(s) to process",
    )
    p.add_argument(
        "--from",
        dest="old_key",
        required=True,
        metavar="OLD_KEY",
        help="Key name to rename from",
    )
    p.add_argument(
        "--to",
        dest="new_key",
        required=True,
        metavar="NEW_KEY",
        help="Key name to rename to",
    )
    p.add_argument(
        "--write",
        action="store_true",
        default=False,
        help="Write changes back to file(s) in place",
    )
    p.set_defaults(func=run_rename)


def run_rename(args: argparse.Namespace) -> int:
    """Execute the rename sub-command."""
    renames = {args.old_key: args.new_key}
    exit_code = 0

    for file_path in args.files:
        try:
            result = rename(file_path, renames, write=args.write)
        except FileNotFoundError:
            print(f"ERROR: File not found: {file_path}", file=sys.stderr)
            exit_code = 1
            continue

        print(result.summary())
        if result.skipped:
            exit_code = 1

    return exit_code
