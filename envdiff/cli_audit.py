"""CLI sub-commands for the audit log (show, clear)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envdiff.auditor import load

_DEFAULT_LOG = ".envdiff_audit.log"


def add_audit_subcommands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    audit_p = subparsers.add_parser("audit", help="Manage the envdiff audit log")
    audit_sub = audit_p.add_subparsers(dest="audit_cmd", required=True)

    show_p = audit_sub.add_parser("show", help="Print audit log entries")
    show_p.add_argument("--log", default=_DEFAULT_LOG, help="Path to audit log file")
    show_p.add_argument("--format", choices=["text", "json"], default="text")
    show_p.add_argument("--event", default=None, help="Filter by event type")
    show_p.add_argument("--last", type=int, default=None, metavar="N", help="Show last N entries")

    clear_p = audit_sub.add_parser("clear", help="Delete all audit log entries")
    clear_p.add_argument("--log", default=_DEFAULT_LOG)


def run_audit(args: argparse.Namespace) -> int:
    if args.audit_cmd == "show":
        return _run_show(args)
    if args.audit_cmd == "clear":
        return _run_clear(args)
    return 1


def _run_show(args: argparse.Namespace) -> int:
    entries = load(args.log)
    if args.event:
        entries = [e for e in entries if e.event == args.event]
    if args.last is not None:
        entries = entries[-args.last:]

    if not entries:
        print("No audit entries found.")
        return 0

    if args.format == "json":
        print(json.dumps([e.to_dict() for e in entries], indent=2))
    else:
        for e in entries:
            print(f"[{e.timestamp}] {e.event.upper():10s} {', '.join(e.files)} — {e.summary}")
    return 0


def _run_clear(args: argparse.Namespace) -> int:
    path = Path(args.log)
    if path.exists():
        path.unlink()
        print(f"Audit log cleared: {path}")
    else:
        print("No audit log found.")
    return 0
