"""Tests for envdiff.snapshotter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.snapshotter import Snapshot, capture, default_snapshot_path, load, save


@pytest.fixture()
def tmp_env(tmp_path: Path):
    def _write(content: str) -> str:
        p = tmp_path / ".env"
        p.write_text(content)
        return str(p)

    return _write


def test_capture_returns_snapshot(tmp_env):
    path = tmp_env("KEY=value\nSECRET=abc123\n")
    snap = capture(path)
    assert isinstance(snap, Snapshot)
    assert snap.values["KEY"] == "value"
    assert snap.values["SECRET"] == "abc123"
    assert snap.path == path


def test_capture_records_timestamp(tmp_env):
    path = tmp_env("A=1\n")
    snap = capture(path)
    assert "T" in snap.captured_at  # ISO-8601 contains 'T'


def test_save_and_load_roundtrip(tmp_env, tmp_path):
    path = tmp_env("FOO=bar\n")
    snap = capture(path)
    dest = str(tmp_path / "snaps" / "test.json")
    save(snap, dest)
    loaded = load(dest)
    assert loaded.values == snap.values
    assert loaded.captured_at == snap.captured_at
    assert loaded.path == snap.path


def test_save_creates_parent_dirs(tmp_env, tmp_path):
    path = tmp_env("X=1\n")
    snap = capture(path)
    dest = str(tmp_path / "deep" / "nested" / "snap.json")
    save(snap, dest)  # should not raise
    assert Path(dest).exists()


def test_to_dict_contains_required_keys(tmp_env):
    path = tmp_env("K=v\n")
    snap = capture(path)
    d = snap.to_dict()
    assert set(d.keys()) == {"path", "captured_at", "values"}


def test_from_dict_roundtrip():
    data = {"path": "/tmp/.env", "captured_at": "2024-01-01T00:00:00+00:00", "values": {"A": "1"}}
    snap = Snapshot.from_dict(data)
    assert snap.values == {"A": "1"}
    assert snap.path == "/tmp/.env"


def test_default_snapshot_path_uses_env_name():
    result = default_snapshot_path("/project/.env.production")
    assert "_env_production" in result
    assert result.endswith(".snapshot.json")


def test_default_snapshot_path_custom_dir():
    result = default_snapshot_path(".env", snapshot_dir="/custom/dir")
    assert result.startswith("/custom/dir")
