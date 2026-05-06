"""Diff a live .env file against a stored Snapshot."""

from __future__ import annotations

from envdiff.comparator import DiffResult, compare
from envdiff.parser import parse_env_file
from envdiff.snapshotter import Snapshot, load


def diff_against_snapshot(
    env_path: str,
    snapshot_path: str,
    ignore_values: bool = False,
) -> DiffResult:
    """Compare the current state of *env_path* against the saved snapshot.

    The snapshot is treated as the *reference* (base) and the live file as
    the *target*, so keys present in the snapshot but missing from the live
    file appear as ``missing`` and vice-versa as ``extra``.
    """
    snapshot: Snapshot = load(snapshot_path)
    current_values = parse_env_file(env_path)
    return compare(
        base=snapshot.values,
        target=current_values,
        ignore_values=ignore_values,
    )


def diff_snapshots(
    old_snapshot_path: str,
    new_snapshot_path: str,
    ignore_values: bool = False,
) -> DiffResult:
    """Compare two previously saved snapshots with each other."""
    old = load(old_snapshot_path)
    new = load(new_snapshot_path)
    return compare(
        base=old.values,
        target=new.values,
        ignore_values=ignore_values,
    )
