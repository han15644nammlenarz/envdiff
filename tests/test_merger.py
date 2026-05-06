"""Tests for envdiff.merger."""
from __future__ import annotations

import os
import textwrap
from pathlib import Path

import pytest

from envdiff.merger import merge, MergeResult


@pytest.fixture()
def tmp_env(tmp_path: Path):
    """Return a helper that writes a named .env file and returns its path."""

    def _write(name: str, content: str) -> str:
        p = tmp_path / name
        p.write_text(textwrap.dedent(content))
        return str(p)

    return _write


def test_single_file_no_overrides(tmp_env):
    p = tmp_env("a.env", """
        FOO=bar
        BAZ=qux
    """)
    result = merge([p])
    assert result.merged == {"FOO": "bar", "BAZ": "qux"}
    assert result.overridden == []


def test_later_file_overrides_earlier(tmp_env):
    a = tmp_env("a.env", "FOO=original\nSHARED=a\n")
    b = tmp_env("b.env", "FOO=overridden\nEXTRA=yes\n")
    result = merge([a, b])
    assert result.merged["FOO"] == "overridden"
    assert result.merged["SHARED"] == "a"
    assert result.merged["EXTRA"] == "yes"
    assert "FOO" in result.overridden


def test_protected_key_not_overridden(tmp_env):
    a = tmp_env("a.env", "SECRET=original\n")
    b = tmp_env("b.env", "SECRET=hacked\n")
    result = merge([a, b], protected=["SECRET"])
    assert result.merged["SECRET"] == "original"
    assert "SECRET" not in result.overridden


def test_identical_values_not_marked_overridden(tmp_env):
    a = tmp_env("a.env", "FOO=same\n")
    b = tmp_env("b.env", "FOO=same\n")
    result = merge([a, b])
    assert result.overridden == []


def test_origins_track_all_sources(tmp_env):
    a = tmp_env("a.env", "KEY=v1\n")
    b = tmp_env("b.env", "KEY=v2\n")
    c = tmp_env("c.env", "KEY=v3\n")
    result = merge([a, b, c])
    assert len(result.origins["KEY"]) == 3
    values = [v for _, v in result.origins["KEY"]]
    assert values == ["v1", "v2", "v3"]


def test_empty_files_produce_empty_result(tmp_env):
    a = tmp_env("a.env", "")
    b = tmp_env("b.env", "")
    result = merge([a, b])
    assert result.merged == {}


def test_summary_contains_key_count(tmp_env):
    a = tmp_env("a.env", "A=1\nB=2\n")
    result = merge([a])
    assert "2" in result.summary()


def test_summary_lists_overridden_keys(tmp_env):
    a = tmp_env("a.env", "X=old\n")
    b = tmp_env("b.env", "X=new\n")
    result = merge([a, b])
    summary = result.summary()
    assert "X" in summary
    assert "old" in summary
    assert "new" in summary


def test_merge_result_is_dataclass():
    r = MergeResult()
    assert r.merged == {}
    assert r.overridden == []
    assert r.origins == {}
