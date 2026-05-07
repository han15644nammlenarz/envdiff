"""Tests for envdiff.sorter."""
from __future__ import annotations

import pytest
from pathlib import Path

from envdiff.sorter import sort_env, summary, SortResult


@pytest.fixture
def tmp_env(tmp_path):
    return tmp_path / ".env"


def _write(p: Path, content: str) -> None:
    p.write_text(content)


def test_returns_sort_result(tmp_env):
    _write(tmp_env, "ZEBRA=1\nAPPLE=2\n")
    result = sort_env(str(tmp_env))
    assert isinstance(result, SortResult)


def test_already_sorted_no_change(tmp_env):
    _write(tmp_env, "ALPHA=1\nBETA=2\nZETA=3\n")
    result = sort_env(str(tmp_env))
    assert not result.changed


def test_unsorted_file_is_detected(tmp_env):
    _write(tmp_env, "ZEBRA=1\nAPPLE=2\n")
    result = sort_env(str(tmp_env))
    assert result.changed


def test_sorted_lines_are_alphabetical(tmp_env):
    _write(tmp_env, "ZEBRA=1\nAPPLE=2\nMIDDLE=3\n")
    result = sort_env(str(tmp_env))
    keys = [l.split("=")[0] for l in result.sorted_lines if "=" in l]
    assert keys == sorted(keys)


def test_reverse_sort(tmp_env):
    _write(tmp_env, "APPLE=1\nZEBRA=2\nMIDDLE=3\n")
    result = sort_env(str(tmp_env), reverse=True)
    keys = [l.split("=")[0] for l in result.sorted_lines if "=" in l]
    assert keys == sorted(keys, reverse=True)


def test_header_comments_preserved(tmp_env):
    _write(tmp_env, "# My env file\n\nZEBRA=1\nAPPLE=2\n")
    result = sort_env(str(tmp_env))
    assert result.sorted_lines[0].startswith("#")


def test_write_flag_updates_file(tmp_env):
    _write(tmp_env, "ZEBRA=1\nAPPLE=2\n")
    sort_env(str(tmp_env), write=True)
    content = tmp_env.read_text()
    lines = [l for l in content.splitlines() if "=" in l]
    keys = [l.split("=")[0] for l in lines]
    assert keys == sorted(keys)


def test_no_write_does_not_modify_file(tmp_env):
    original = "ZEBRA=1\nAPPLE=2\n"
    _write(tmp_env, original)
    sort_env(str(tmp_env), write=False)
    assert tmp_env.read_text() == original


def test_summary_changed(tmp_env):
    _write(tmp_env, "ZEBRA=1\nAPPLE=2\n")
    result = sort_env(str(tmp_env))
    msg = summary(result)
    assert "reordered" in msg


def test_summary_unchanged(tmp_env):
    _write(tmp_env, "ALPHA=1\nBETA=2\n")
    result = sort_env(str(tmp_env))
    msg = summary(result)
    assert "already sorted" in msg


def test_file_not_found_raises():
    with pytest.raises(FileNotFoundError):
        sort_env("/nonexistent/.env")
