"""CLI sub-command: annotate — write inline diff annotations to a .env file."""
from __future__ import annotations

import argparse
import sys

from envdiff.differ import diff_files
from envdiff.annotator import annotate


def add_annotate_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "annotate",
        help="Annotate a .env file with inline diff comments vs a reference file.",
    )
    p.add_argument("reference", help="Reference .env file (e.g. .env.example)")
    p.add_argument("target", help="Target .env file to annotate")
    p.add_argument(
        "--mask-secrets",
        action="store_true",
        default=False,
        help="Mask secret values in mismatch annotations.",
    )
    p.add_argument(
        "--output",
        "-o",
        default="-",
        help="Output file path (default: stdout).",
    )
    p.set_defaults(func=run_annotate)


def run_annotate(args: argparse.Namespace) -> int:
    diff = diff_files(args.reference, args.target)
    result = annotate(args.target, diff, mask_secrets=args.mask_secrets)

    rendered = result.render()

    if args.output == "-":
        print(rendered)
    else:
        from pathlib import Path
        Path(args.output).write_text(rendered)
        print(result.summary(), file=sys.stderr)

    return 0
