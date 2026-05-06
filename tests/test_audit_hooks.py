"""Integration tests for envdiff.audit_hooks."""

from __future__ import annotations

from pathlib import Path

import pytest

from envdiff.audit_hooks import audited_diff, audited_validate
from envdiff.auditor import load


@pytest.fixture()
def tmp_env(tmp_path: Path):
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


def test_audited_diff_records_entry(tmp_env: Path):
    base = _write(tmp_env / "base.env", "KEY_A=1\nKEY_B=2\n")
    other = _write(tmp_env / "other.env", "KEY_A=1\n")
    log = tmp_env / "audit.log"

    audited_diff(base, other, log_path=log)

    entries = load(log)
    assert len(entries) == 1
    assert entries[0].event == "diff"


def test_audited_diff_captures_missing_keys(tmp_env: Path):
    base = _write(tmp_env / "base.env", "KEY_A=1\nKEY_B=2\n")
    other = _write(tmp_env / "other.env", "KEY_A=1\n")
    log = tmp_env / "audit.log"

    audited_diff(base, other, log_path=log)

    entries = load(log)
    assert "KEY_B" in entries[0].details["missing"]


def test_audited_diff_returns_diff_result(tmp_env: Path):
    base = _write(tmp_env / "base.env", "KEY_A=1\n")
    other = _write(tmp_env / "other.env", "KEY_A=1\n")
    log = tmp_env / "audit.log"

    result = audited_diff(base, other, log_path=log)
    assert not result.missing_keys
    assert not result.extra_keys


def test_audited_validate_records_entry(tmp_env: Path):
    ref = _write(tmp_env / "ref.env", "KEY_A=1\nKEY_B=2\n")
    target = _write(tmp_env / "target.env", "KEY_A=hello\nKEY_B=world\n")
    log = tmp_env / "audit.log"

    audited_validate(ref, target, log_path=log)

    entries = load(log)
    assert len(entries) == 1
    assert entries[0].event == "validate"


def test_audited_validate_captures_missing(tmp_env: Path):
    ref = _write(tmp_env / "ref.env", "KEY_A=1\nKEY_B=2\n")
    target = _write(tmp_env / "target.env", "KEY_A=hello\n")
    log = tmp_env / "audit.log"

    audited_validate(ref, target, log_path=log)

    entries = load(log)
    assert "KEY_B" in entries[0].details["missing"]


def test_multiple_calls_append_entries(tmp_env: Path):
    base = _write(tmp_env / "base.env", "KEY_A=1\n")
    other = _write(tmp_env / "other.env", "KEY_A=1\n")
    log = tmp_env / "audit.log"

    audited_diff(base, other, log_path=log)
    audited_diff(base, other, log_path=log)

    entries = load(log)
    assert len(entries) == 2
