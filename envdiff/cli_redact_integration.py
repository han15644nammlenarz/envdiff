"""Integration helper: wire redact into the main CLI parser.

Import and call ``attach(subparsers)`` from envdiff/cli.py to enable
the ``envdiff redact`` sub-command without modifying cli.py directly.
"""
from __future__ import annotations

import argparse

from envdiff.cli_redact import add_redact_subcommand


def attach(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the redact sub-command on an existing subparsers group."""
    add_redact_subcommand(subparsers)


if __name__ == "__main__":  # pragma: no cover
    import sys

    parser = argparse.ArgumentParser(
        prog="envdiff-redact",
        description="Standalone runner for the redact sub-command.",
    )
    sub = parser.add_subparsers(dest="command")
    add_redact_subcommand(sub)
    args = parser.parse_args()
    if hasattr(args, "func"):
        sys.exit(args.func(args))
    else:
        parser.print_help()
        sys.exit(0)
