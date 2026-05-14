"""CLI subcommand: envdiff chain — compare a chain of .env files."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envdiff.comparator_chain import compare_chain


def add_chain_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "chain",
        help="Compare a sequence of .env files pairwise.",
    )
    p.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="Two or more .env files to compare in order.",
    )
    p.add_argument(
        "--ignore-values",
        action="store_true",
        default=False,
        help="Only check for key presence, ignore value differences.",
    )
    p.add_argument(
        "--ignore-extra",
        action="store_true",
        default=False,
        help="Do not report keys present in target but missing in base.",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="output_format",
    )
    p.set_defaults(func=run_chain)


def run_chain(args: argparse.Namespace) -> int:
    if len(args.files) < 2:
        print("chain requires at least two files.", file=sys.stderr)
        return 2

    chain = compare_chain(
        args.files,
        ignore_values=args.ignore_values,
        ignore_extra=args.ignore_extra,
    )

    if args.output_format == "json":
        out = {
            "summary": chain.summary(),
            "all_clean": chain.all_clean(),
            "links": [
                {
                    "base": lnk.base_path,
                    "target": lnk.target_path,
                    "missing": sorted(lnk.result.missing),
                    "extra": sorted(lnk.result.extra),
                    "mismatched": sorted(lnk.result.mismatched),
                    "has_differences": lnk.has_differences(),
                }
                for lnk in chain.links
            ],
        }
        print(json.dumps(out, indent=2))
    else:
        print(chain.summary())
        for lnk in chain.links_with_differences():
            print(f"\n  {lnk.base_path} → {lnk.target_path}")
            if lnk.result.missing:
                print(f"    Missing : {', '.join(sorted(lnk.result.missing))}")
            if lnk.result.extra:
                print(f"    Extra   : {', '.join(sorted(lnk.result.extra))}")
            if lnk.result.mismatched:
                print(f"    Mismatch: {', '.join(sorted(lnk.result.mismatched))}")

    return 0 if chain.all_clean() else 1
