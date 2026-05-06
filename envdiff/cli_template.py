"""CLI sub-command helpers for the 'template' command.

Integrates with envdiff.cli via build_parser's subparsers.
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from envdiff.templater import generate_template


def add_template_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the *template* sub-command onto *subparsers*."""
    parser = subparsers.add_parser(
        "template",
        help="Generate a .env.example template from a .env file.",
        description=(
            "Reads SOURCE and writes a sanitised template where secret keys "
            "have their values replaced with PLACEHOLDER."
        ),
    )
    parser.add_argument("source", help="Path to the source .env file.")
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output path (default: <source>.example).",
    )
    parser.add_argument(
        "--placeholder",
        default="",
        metavar="TEXT",
        help="Value to substitute for secrets (default: empty string).",
    )
    parser.add_argument(
        "--no-comments",
        dest="no_comments",
        action="store_true",
        help="Omit the auto-generated header comment.",
    )
    parser.add_argument(
        "--secret-keywords",
        nargs="+",
        default=None,
        metavar="KEYWORD",
        help="Extra keywords that mark a key as secret.",
    )
    parser.set_defaults(func=run_template)


def run_template(args: argparse.Namespace) -> int:
    """Execute the *template* sub-command; return an exit code."""
    try:
        result = generate_template(
            source=args.source,
            output=args.output,
            secret_keywords=args.secret_keywords,
            placeholder=args.placeholder,
            keep_comments=not args.no_comments,
        )
    except FileNotFoundError as exc:
        print(f"envdiff template: error: {exc}", file=sys.stderr)
        return 1

    print(result.summary())
    if result.keys_blanked:
        print(f"  Blanked : {', '.join(result.keys_blanked)}")
    if result.keys_written:
        print(f"  Retained: {', '.join(result.keys_written)}")
    return 0
