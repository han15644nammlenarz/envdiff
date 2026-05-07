"""Tests for envdiff.formatter."""

from __future__ import annotations

import pytest
from pathlib import Path

from envdiff.formatter import (
    FormatResult,
    _format_line,
    format_env,
    summary,
    write_formatted,
)


@pytest.fixture
def tmp_env(tmp_path: Path):
    def _write(name: str, content: str) -> str:
        p = tmp_path / name
        p.write_text(content, encoding="utf-8")
        return str(p)
    return _write


# --- _format_line ---

def test_format_line_strips_spaces_around_equals():
    assert _format_line("KEY = value") == "KEY=value"


def test_format_line_strips_trailing_whitespace():
    assert _format_line("KEY=value   ") == "KEY=value"


def test_format_line_leaves_comment_intact():
    assert _format_line("# a comment") == "# a comment"


def test_format_line_leaves_blank_line_intact():
    assert _format_line("") == ""


def test_format_line_no_equals_returned_as_is():
    assert _format_line("EXPORT FOO") == "EXPORT FOO"


# --- format_env ---

def test_already_formatted_reports_zero_changes(tmp_env):
    path = tmp_env("a.env", "KEY=value\nOTHER=123\n")
    result = format_env(path)
    assert result.changes == 0
    assert not result.changed


def test_detects_spaces_around_equals(tmp_env):
    path = tmp_env("b.env", "KEY = value\n")
    result = format_env(path)
    assert result.changed
    assert result.changes >= 1
    assert result.formatted_lines[0] == "KEY=value"


def test_sort_keys_reorders_lines(tmp_env):
    path = tmp_env("c.env", "ZEBRA=1\nAPPLE=2\n")
    result = format_env(path, sort_keys=True)
    keys = [ln.split("=")[0] for ln in result.formatted_lines if "=" in ln]
    assert keys == sorted(keys)


def test_result_path_matches_input(tmp_env):
    path = tmp_env("d.env", "X=1\n")
    result = format_env(path)
    assert result.path == path


# --- summary ---

def test_summary_no_changes(tmp_env):
    path = tmp_env("e.env", "KEY=val\n")
    result = format_env(path)
    msg = summary(result)
    assert "no changes" in msg


def test_summary_with_changes(tmp_env):
    path = tmp_env("f.env", "KEY = val\n")
    result = format_env(path)
    msg = summary(result)
    assert "reformatted" in msg


# --- write_formatted ---

def test_write_formatted_persists_changes(tmp_env):
    path = tmp_env("g.env", "KEY = value\n")
    result = format_env(path)
    write_formatted(result)
    content = Path(path).read_text(encoding="utf-8")
    assert "KEY=value" in content
    assert "KEY = value" not in content
