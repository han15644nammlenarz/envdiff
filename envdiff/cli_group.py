"""CLI sub-command: envdiff group — show key groups in a .env file."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from envdiff.grouper import group


def add_group_subcommand(subparsers: Any) -> None:  # noqa: ANN401
    p: argparse.ArgumentParser = subparsers.add_parser(
        "group",
        help="Group .env keys by prefix and display statistics.",
    )
    p.add_argument("file", help="Path to the .env file.")
    p.add_argument(
        "--separator",
        default="_",
        help="Separator character used to detect key prefixes (default: '_').",
    )
    p.add_argument(
        "--min-prefix",
        type=int,
        default=1,
        dest="min_prefix",
        help="Minimum prefix length to form a group (default: 1).",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text).",
    )
    p.set_defaults(func=run_group)


def run_group(args: argparse.Namespace) -> int:
    result = group(
        path=args.file,
        separator=args.separator,
        min_prefix_length=args.min_prefix,
    )

    if args.fmt == "json":
        data = {
            "path": result.path,
            "separator": result.separator,
            "groups": {
                name: {
                    "keys": keys,
                    "secret_count": len(result.secret_keys_in_group(name)),
                }
                for name, keys in result.groups.items()
            },
            "ungrouped": result.ungrouped,
        }
        print(json.dumps(data, indent=2))
    else:
        print(result.summary())

    return 0
