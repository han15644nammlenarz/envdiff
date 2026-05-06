"""Tests for envdiff.auditor."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.auditor import (
    AuditEntry,
    record,
    load,
    make_diff_entry,
    make_validate_entry,
)


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    return tmp_path / "audit.log"


def test_record_creates_file(log_file: Path):
    entry = make_diff_entry(files=["a.env", "b.env"], summary="1 missing")
    record(log_file, entry)
    assert log_file.exists()


def test_record_appends_json_line(log_file: Path):
    e1 = make_diff_entry(["a.env"], "ok")
    e2 = make_validate_entry(["b.env"], "invalid")
    record(log_file, e1)
    record(log_file, e2)
    lines = [l for l in log_file.read_text().splitlines() if l.strip()]
    assert len(lines) == 2
    assert json.loads(lines[0])["event"] == "diff"
    assert json.loads(lines[1])["event"] == "validate"


def test_load_returns_empty_when_no_file(tmp_path: Path):
    result = load(tmp_path / "missing.log")
    assert result == []


def test_load_roundtrip(log_file: Path):
    entry = make_diff_entry(
        files=["x.env", "y.env"],
        summary="2 missing",
        details={"missing": ["KEY_A", "KEY_B"]},
    )
    record(log_file, entry)
    loaded = load(log_file)
    assert len(loaded) == 1
    assert loaded[0].event == "diff"
    assert loaded[0].summary == "2 missing"
    assert loaded[0].details["missing"] == ["KEY_A", "KEY_B"]


def test_make_diff_entry_has_timestamp():
    entry = make_diff_entry(["a.env"], "ok")
    assert entry.timestamp  # non-empty ISO string
    assert "T" in entry.timestamp


def test_make_validate_entry_event_name():
    entry = make_validate_entry(["ref.env", "target.env"], "valid")
    assert entry.event == "validate"


def test_to_dict_and_from_dict_roundtrip():
    original = make_diff_entry(["a.env"], "ok", details={"extra": ["FOO"]})
    restored = AuditEntry.from_dict(original.to_dict())
    assert restored.event == original.event
    assert restored.files == original.files
    assert restored.details == original.details


def test_record_creates_parent_dirs(tmp_path: Path):
    nested_log = tmp_path / "deep" / "nested" / "audit.log"
    record(nested_log, make_diff_entry(["a.env"], "ok"))
    assert nested_log.exists()
