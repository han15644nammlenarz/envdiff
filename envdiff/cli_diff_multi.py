"""CLI sub-command: multi-diff — compare a reference .env against N targets."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envdiff.differ_multi import diff_multi


def add_diff_multi_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "multi-diff",
        help="Compare a reference .env file against multiple target files.",
    )
    p.add_argument("reference", help="Reference .env file")
    p.add_argument("targets", nargs="+", help="Target .env files to compare")
    p.add_argument(
        "--ignore-values",
        action="store_true",
        default=False,
        help="Only check key presence, not values.",
    )
    p.add_argument(
        "--mask-secrets",
        action="store_true",
        default=False,
        help="Mask secret values in output.",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    p.set_defaults(func=run_diff_multi)


def run_diff_multi(args: argparse.Namespace) -> int:
    result = diff_multi(
        args.reference,
        args.targets,
        ignore_values=args.ignore_values,
        mask_secrets=args.mask_secrets,
    )

    if args.format == "json":
        payload: dict = {
            "reference": result.reference,
            "all_clean": result.all_clean(),
            "targets": {
                path: {
                    "missing": list(dr.missing),
                    "extra": list(dr.extra),
                    "mismatched": [
                        {"key": k, "ref": a, "target": b}
                        for k, (a, b) in dr.mismatched.items()
                    ],
                }
                for path, dr in result.results.items()
            },
        }
        print(json.dumps(payload, indent=2))
    else:
        print(result.summary())

    return 0 if result.all_clean() else 1
