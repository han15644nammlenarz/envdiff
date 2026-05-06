"""CLI sub-commands for snapshot management."""

from __future__ import annotations

import argparse
import sys

from envdiff.reporter import format_json, format_text
from envdiff.snapshot_diff import diff_against_snapshot, diff_snapshots
from envdiff.snapshotter import capture, default_snapshot_path, save


def add_snapshot_subcommands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    # --- capture ---
    cap = subparsers.add_parser("snapshot", help="Capture a snapshot of an .env file")
    cap.add_argument("env_file", help="Path to the .env file to snapshot")
    cap.add_argument("--output", "-o", default=None, help="Destination path for the snapshot JSON")
    cap.set_defaults(func=run_capture)

    # --- snap-diff ---
    sd = subparsers.add_parser("snap-diff", help="Diff a live .env file against a snapshot")
    sd.add_argument("env_file", help="Path to the live .env file")
    sd.add_argument("snapshot", help="Path to the snapshot JSON")
    sd.add_argument("--format", choices=["text", "json"], default="text")
    sd.add_argument("--mask-secrets", action="store_true", default=False)
    sd.add_argument("--ignore-values", action="store_true", default=False)
    sd.set_defaults(func=run_snap_diff)


def run_capture(args: argparse.Namespace) -> int:
    snapshot = capture(args.env_file)
    dest = args.output or default_snapshot_path(args.env_file)
    save(snapshot, dest)
    print(f"Snapshot saved to {dest} (captured at {snapshot.captured_at})")
    return 0


def run_snap_diff(args: argparse.Namespace) -> int:
    result = diff_against_snapshot(
        env_path=args.env_file,
        snapshot_path=args.snapshot,
        ignore_values=args.ignore_values,
    )
    mask = getattr(args, "mask_secrets", False)
    if args.format == "json":
        print(format_json(result, mask_secrets=mask))
    else:
        print(format_text(result, mask_secrets=mask))
    return 1 if result.missing or result.extra or result.mismatched else 0
