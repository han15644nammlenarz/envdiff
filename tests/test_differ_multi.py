"""Tests for envdiff.differ_multi."""
from __future__ import annotations

import pytest
from pathlib import Path

from envdiff.differ_multi import diff_multi, MultiDiffResult


@pytest.fixture()
def tmp_env(tmp_path: Path):
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


def test_returns_multi_diff_result(tmp_env):
    ref = _write(tmp_env / "ref.env", "A=1\nB=2\n")
    t1 = _write(tmp_env / "t1.env", "A=1\nB=2\n")
    result = diff_multi(ref, [t1])
    assert isinstance(result, MultiDiffResult)


def test_all_clean_when_identical(tmp_env):
    ref = _write(tmp_env / "ref.env", "A=1\nB=2\n")
    t1 = _write(tmp_env / "t1.env", "A=1\nB=2\n")
    result = diff_multi(ref, [t1])
    assert result.all_clean()


def test_detects_missing_key_in_target(tmp_env):
    ref = _write(tmp_env / "ref.env", "A=1\nB=2\n")
    t1 = _write(tmp_env / "t1.env", "A=1\n")
    result = diff_multi(ref, [t1])
    assert not result.all_clean()
    dr = result.results[str(t1)]
    assert "B" in dr.missing


def test_detects_extra_key_in_target(tmp_env):
    ref = _write(tmp_env / "ref.env", "A=1\n")
    t1 = _write(tmp_env / "t1.env", "A=1\nEXTRA=99\n")
    result = diff_multi(ref, [t1])
    dr = result.results[str(t1)]
    assert "EXTRA" in dr.extra


def test_multiple_targets_independent(tmp_env):
    ref = _write(tmp_env / "ref.env", "A=1\nB=2\n")
    t1 = _write(tmp_env / "t1.env", "A=1\nB=2\n")
    t2 = _write(tmp_env / "t2.env", "A=1\n")
    result = diff_multi(ref, [t1, t2])
    assert not result.all_clean()
    assert len(result.targets_with_differences()) == 1
    assert str(t2) in result.targets_with_differences()


def test_targets_with_differences_empty_when_clean(tmp_env):
    ref = _write(tmp_env / "ref.env", "A=1\n")
    t1 = _write(tmp_env / "t1.env", "A=1\n")
    result = diff_multi(ref, [t1])
    assert result.targets_with_differences() == []


def test_summary_contains_reference_path(tmp_env):
    ref = _write(tmp_env / "ref.env", "A=1\n")
    t1 = _write(tmp_env / "t1.env", "A=1\n")
    result = diff_multi(ref, [t1])
    assert "ref.env" in result.summary()


def test_summary_reports_all_clean(tmp_env):
    ref = _write(tmp_env / "ref.env", "A=1\n")
    t1 = _write(tmp_env / "t1.env", "A=1\n")
    result = diff_multi(ref, [t1])
    assert "All targets match" in result.summary()


def test_ignore_values_skips_mismatch(tmp_env):
    ref = _write(tmp_env / "ref.env", "A=1\n")
    t1 = _write(tmp_env / "t1.env", "A=different\n")
    result = diff_multi(ref, [t1], ignore_values=True)
    assert result.all_clean()
