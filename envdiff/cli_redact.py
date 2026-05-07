"""CLI sub-command: redact — write a secret-free copy of a .env file."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.redactor import redact, write_redacted


def add_redact_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "redact",
        help="Produce a redacted copy of a .env file with secret values blanked.",
    )
    p.add_argument("source", help="Path to the source .env file.")
    p.add_argument(
        "-o",
        "--output",
        default=None,
        help="Destination path (default: <source>.redacted).",
    )
    p.add_argument(
        "--keywords",
        nargs="*",
        default=["password", "secret", "token", "key", "api"],
        help="Keywords that mark a key as secret.",
    )
    p.add_argument("--quiet", action="store_true", help="Suppress summary output.")
    p.set_defaults(func=run_redact)


def run_redact(args: argparse.Namespace) -> int:
    source = Path(args.source)
    if not source.exists():
        print(f"error: {source} does not exist.", file=sys.stderr)
        return 1

    dest = Path(args.output) if args.output else source.with_suffix(".redacted")
    keywords = tuple(args.keywords)

    result = redact(source, secret_keywords=keywords)
    write_redacted(result, dest)

    if not args.quiet:
        print(result.summary())
        print(f"Redacted file written to: {dest}")
    return 0
