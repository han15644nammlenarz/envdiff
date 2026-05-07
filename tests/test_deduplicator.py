"""Tests for envdiff.deduplicator."""
from __future__ import annotations

import pytest
from pathlib import Path

from envdiff.deduplicator import deduplicate, DeduplicateResult


@pytest.fixture
def tmp_env(tmp_path: Path):
    return tmp_path / ".env"


def _write(p: Path, content: str) -> None:
    p.write_text(content, encoding="utf-8")


def test_returns_deduplicate_result(tmp_env):
    _write(tmp_env, "KEY=value\n")
    result = deduplicate(tmp_env)
    assert isinstance(result, DeduplicateResult)


def test_no_duplicates_clean_file(tmp_env):
    _write(tmp_env, "A=1\nB=2\nC=3\n")
    result = deduplicate(tmp_env)
    assert not result.has_duplicates
    assert result.duplicates == {}


def test_detects_single_duplicate(tmp_env):
    _write(tmp_env, "KEY=first\nOTHER=x\nKEY=second\n")
    result = deduplicate(tmp_env)
    assert result.has_duplicates
    assert "KEY" in result.duplicates
    assert result.duplicates["KEY"] == [1, 3]


def test_detects_multiple_duplicates(tmp_env):
    _write(tmp_env, "A=1\nB=2\nA=3\nB=4\n")
    result = deduplicate(tmp_env)
    assert len(result.duplicates) == 2
    assert "A" in result.duplicates
    assert "B" in result.duplicates


def test_kept_lines_removes_earlier_occurrences(tmp_env):
    _write(tmp_env, "KEY=first\nKEY=second\n")
    result = deduplicate(tmp_env)
    assert len(result.kept_lines) == 1
    assert "second" in result.kept_lines[0]


def test_comments_and_blanks_preserved(tmp_env):
    content = "# comment\nKEY=1\n\nKEY=2\n"
    _write(tmp_env, content)
    result = deduplicate(tmp_env)
    kept = "".join(result.kept_lines)
    assert "# comment" in kept
    assert "KEY=2" in kept
    assert "KEY=1" not in kept


def test_write_flag_rewrites_file(tmp_env):
    _write(tmp_env, "KEY=first\nKEY=second\n")
    deduplicate(tmp_env, write=True)
    content = tmp_env.read_text(encoding="utf-8")
    assert "KEY=second" in content
    assert "KEY=first" not in content


def test_write_flag_false_does_not_modify_file(tmp_env):
    original = "KEY=first\nKEY=second\n"
    _write(tmp_env, original)
    deduplicate(tmp_env, write=False)
    assert tmp_env.read_text(encoding="utf-8") == original


def test_summary_no_duplicates(tmp_env):
    _write(tmp_env, "A=1\n")
    result = deduplicate(tmp_env)
    assert "no duplicate" in result.summary()


def test_summary_with_duplicates(tmp_env):
    _write(tmp_env, "KEY=1\nKEY=2\n")
    result = deduplicate(tmp_env)
    assert "KEY" in result.summary()
    assert "1 duplicate" in result.summary()


def test_original_line_count(tmp_env):
    _write(tmp_env, "A=1\nB=2\nA=3\n")
    result = deduplicate(tmp_env)
    assert result.original_line_count == 3
