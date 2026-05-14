"""CLI sub-command: alias  — rename keys in a .env file.

Usage examples
--------------
  envdiff alias app.env --rename OLD_KEY=NEW_KEY --rename DB_PASS=DATABASE_PASSWORD
  envdiff alias app.env --rename FOO=BAR --output aliased.env
"""
from __future__ import annotations

import argparse
import sys

from envdiff.aliaser import alias, write_aliased


def add_alias_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "alias",
        help="Rename keys in a .env file using an alias mapping.",
    )
    p.add_argument("file", help="Path to the .env file.")
    p.add_argument(
        "--rename",
        metavar="OLD=NEW",
        action="append",
        default=[],
        help="Key rename rule (repeatable). Format: OLD_KEY=NEW_KEY.",
    )
    p.add_argument(
        "--output",
        metavar="PATH",
        default=None,
        help="Write aliased file to PATH (default: overwrite source).",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would change without writing any file.",
    )
    p.set_defaults(func=run_alias)


def run_alias(args: argparse.Namespace) -> int:
    if not args.rename:
        print("ERROR: supply at least one --rename OLD=NEW rule.", file=sys.stderr)
        return 1

    aliases: dict[str, str] = {}
    for rule in args.rename:
        if "=" not in rule:
            print(f"ERROR: invalid rename rule {rule!r} — expected OLD=NEW.", file=sys.stderr)
            return 1
        old, _, new = rule.partition("=")
        aliases[old.strip()] = new.strip()

    result = alias(args.file, aliases)

    if result.conflicts:
        print(
            "ERROR: conflicting aliases (multiple old keys map to the same new key): "
            + ", ".join(result.conflicts),
            file=sys.stderr,
        )
        return 1

    if args.dry_run:
        print(f"Would rename {len(result.renamed)} key(s): {result.renamed}")
        return 0

    dest = args.output or args.file
    write_aliased(result, dest)
    print(f"Aliased {len(result.renamed)} key(s) → {dest}")
    return 0
