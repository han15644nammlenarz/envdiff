"""CLI subcommand for sorting .env file keys."""
from __future__ import annotations

import argparse
import sys

from envdiff.sorter import sort_env, summary


def add_sort_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    parser = subparsers.add_parser(
        "sort",
        help="Sort keys in a .env file alphabetically.",
    )
    parser.add_argument("file", help="Path to the .env file to sort.")
    parser.add_argument(
        "--reverse",
        action="store_true",
        default=False,
        help="Sort keys in descending (Z→A) order.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        default=False,
        help="Write sorted output back to the file.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        default=False,
        help="Exit with code 1 if the file is not already sorted.",
    )
    parser.set_defaults(func=run_sort)


def run_sort(args: argparse.Namespace) -> int:
    """Execute the sort subcommand.

    Returns:
        0 on success / already sorted; 1 if --check fails.
    """
    try:
        result = sort_env(args.file, reverse=args.reverse, write=args.write)
    except FileNotFoundError:
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        return 1

    print(summary(result))

    if args.check and result.changed:
        print(
            f"  File is not sorted. Re-run without --check to fix.",
            file=sys.stderr,
        )
        return 1

    if args.write and result.changed:
        print(f"  Sorted file written to {args.file}.")

    if not args.write and result.changed:
        print("  (Use --write to apply changes.)")

    return 0
