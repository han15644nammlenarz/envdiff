"""Tests for envdiff.snapshot_diff."""

from __future__ import annotations

from pathlib import Path

import pytest

from envdiff.snapshotter import capture, save
from envdiff.snapshot_diff import diff_against_snapshot, diff_snapshots


@pytest.fixture()
def tmp_env(tmp_path: Path):
    counter = {"n": 0}

    def _write(content: str, name: str = ".env") -> str:
        p = tmp_path / name
        p.write_text(content)
        return str(p)

    return _write


def _snap(env_path: str, tmp_path: Path, name: str = "snap.json") -> str:
    snap = capture(env_path)
    dest = str(tmp_path / name)
    save(snap, dest)
    return dest


def test_no_diff_when_unchanged(tmp_env, tmp_path):
    path = tmp_env("A=1\nB=2\n")
    snap_path = _snap(path, tmp_path)
    result = diff_against_snapshot(path, snap_path)
    assert not result.missing
    assert not result.extra
    assert not result.mismatched


def test_detects_missing_key_in_live_file(tmp_env, tmp_path):
    path = tmp_env("A=1\nB=2\n")
    snap_path = _snap(path, tmp_path)
    # Remove B from live file
    Path(path).write_text("A=1\n")
    result = diff_against_snapshot(path, snap_path)
    assert "B" in result.missing


def test_detects_extra_key_in_live_file(tmp_env, tmp_path):
    path = tmp_env("A=1\n")
    snap_path = _snap(path, tmp_path)
    Path(path).write_text("A=1\nNEW_KEY=hello\n")
    result = diff_against_snapshot(path, snap_path)
    assert "NEW_KEY" in result.extra


def test_detects_mismatched_value(tmp_env, tmp_path):
    path = tmp_env("A=original\n")
    snap_path = _snap(path, tmp_path)
    Path(path).write_text("A=changed\n")
    result = diff_against_snapshot(path, snap_path)
    assert "A" in result.mismatched


def test_ignore_values_skips_mismatch(tmp_env, tmp_path):
    path = tmp_env("A=original\n")
    snap_path = _snap(path, tmp_path)
    Path(path).write_text("A=changed\n")
    result = diff_against_snapshot(path, snap_path, ignore_values=True)
    assert not result.mismatched


def test_diff_snapshots_detects_changes(tmp_env, tmp_path):
    path = tmp_env("A=1\nB=2\n")
    old_snap = _snap(path, tmp_path, "old.json")
    Path(path).write_text("A=1\nC=3\n")
    new_snap = _snap(path, tmp_path, "new.json")
    result = diff_snapshots(old_snap, new_snap)
    assert "B" in result.missing
    assert "C" in result.extra
