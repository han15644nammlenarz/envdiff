"""Tests for envdiff.aliaser."""
from __future__ import annotations

import pytest
from pathlib import Path

from envdiff.aliaser import alias, write_aliased, AliasResult


@pytest.fixture()
def tmp_env(tmp_path: Path):
    return tmp_path / ".env"


def _write(p: Path, text: str) -> None:
    p.write_text(text)


# ---------------------------------------------------------------------------
# alias()
# ---------------------------------------------------------------------------

def test_returns_alias_result(tmp_env):
    _write(tmp_env, "FOO=bar\n")
    result = alias(str(tmp_env), {"FOO": "BAZ"})
    assert isinstance(result, AliasResult)


def test_key_is_renamed(tmp_env):
    _write(tmp_env, "OLD_KEY=hello\n")
    result = alias(str(tmp_env), {"OLD_KEY": "NEW_KEY"})
    assert "OLD_KEY" in result.renamed
    assert result.renamed["OLD_KEY"] == "NEW_KEY"


def test_renamed_line_uses_new_key(tmp_env):
    _write(tmp_env, "OLD_KEY=hello\n")
    result = alias(str(tmp_env), {"OLD_KEY": "NEW_KEY"})
    assert any("NEW_KEY=hello" in line for line in result.lines)


def test_unreferenced_key_unchanged(tmp_env):
    _write(tmp_env, "KEEP=value\nOLD=x\n")
    result = alias(str(tmp_env), {"OLD": "NEW"})
    assert any("KEEP=value" in line for line in result.lines)


def test_comments_preserved(tmp_env):
    _write(tmp_env, "# comment\nFOO=bar\n")
    result = alias(str(tmp_env), {"FOO": "BAR"})
    assert any(line.strip().startswith("#") for line in result.lines)


def test_blank_lines_preserved(tmp_env):
    _write(tmp_env, "FOO=1\n\nBAR=2\n")
    result = alias(str(tmp_env), {})
    assert any(line.strip() == "" for line in result.lines)


def test_conflict_detected(tmp_env):
    _write(tmp_env, "A=1\nB=2\n")
    result = alias(str(tmp_env), {"A": "SAME", "B": "SAME"})
    assert "SAME" in result.conflicts


def test_conflict_key_not_renamed(tmp_env):
    _write(tmp_env, "A=1\nB=2\n")
    result = alias(str(tmp_env), {"A": "SAME", "B": "SAME"})
    # Neither A nor B should appear in renamed when there's a conflict
    assert "A" not in result.renamed
    assert "B" not in result.renamed


def test_summary_contains_source(tmp_env):
    _write(tmp_env, "X=1\n")
    result = alias(str(tmp_env), {"X": "Y"})
    assert str(tmp_env) in result.summary()


def test_summary_shows_renamed_count(tmp_env):
    _write(tmp_env, "X=1\nY=2\n")
    result = alias(str(tmp_env), {"X": "A", "Y": "B"})
    assert "renamed=2" in result.summary()


# ---------------------------------------------------------------------------
# write_aliased()
# ---------------------------------------------------------------------------

def test_write_aliased_creates_file(tmp_env, tmp_path):
    _write(tmp_env, "OLD=val\n")
    result = alias(str(tmp_env), {"OLD": "NEW"})
    dest = tmp_path / "out.env"
    write_aliased(result, str(dest))
    assert dest.exists()


def test_write_aliased_content_correct(tmp_env, tmp_path):
    _write(tmp_env, "OLD=val\n")
    result = alias(str(tmp_env), {"OLD": "NEW"})
    dest = tmp_path / "out.env"
    write_aliased(result, str(dest))
    content = dest.read_text()
    assert "NEW=val" in content
    assert "OLD=" not in content
