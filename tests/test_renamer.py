"""Tests for envdiff.renamer."""

import pytest
from pathlib import Path

from envdiff.renamer import rename, RenameResult


@pytest.fixture
def tmp_env(tmp_path: Path):
    """Return a helper that writes a .env file and returns its path."""

    def _write(content: str) -> str:
        p = tmp_path / ".env"
        p.write_text(content)
        return str(p)

    return _write


def test_returns_rename_result(tmp_env):
    path = tmp_env("FOO=bar\n")
    result = rename(path, {"FOO": "BAZ"})
    assert isinstance(result, RenameResult)


def test_key_is_renamed(tmp_env):
    path = tmp_env("FOO=bar\nKEEP=yes\n")
    result = rename(path, {"FOO": "NEW_FOO"})
    assert "FOO" in result.applied
    assert result.applied["FOO"] == "NEW_FOO"
    assert any("NEW_FOO=" in line for line in result.lines)


def test_original_key_removed_from_lines(tmp_env):
    path = tmp_env("OLD_KEY=value\n")
    result = rename(path, {"OLD_KEY": "NEW_KEY"})
    assert not any(line.startswith("OLD_KEY=") for line in result.lines)


def test_missing_key_is_skipped(tmp_env):
    path = tmp_env("FOO=bar\n")
    result = rename(path, {"MISSING": "SOMETHING"})
    assert "MISSING" in result.skipped
    assert result.applied == {}


def test_multiple_renames(tmp_env):
    path = tmp_env("A=1\nB=2\nC=3\n")
    result = rename(path, {"A": "ALPHA", "B": "BETA"})
    assert result.applied == {"A": "ALPHA", "B": "BETA"}
    assert result.skipped == []


def test_write_flag_updates_file(tmp_env):
    path = tmp_env("SECRET_KEY=abc\n")
    rename(path, {"SECRET_KEY": "APP_SECRET"}, write=True)
    updated = Path(path).read_text()
    assert "APP_SECRET=abc" in updated
    assert "SECRET_KEY" not in updated


def test_no_write_does_not_change_file(tmp_env):
    original = "FOO=bar\n"
    path = tmp_env(original)
    rename(path, {"FOO": "BAZ"}, write=False)
    assert Path(path).read_text() == original


def test_summary_contains_path(tmp_env):
    path = tmp_env("X=1\n")
    result = rename(path, {"X": "Y"})
    assert path in result.summary()


def test_summary_shows_rename(tmp_env):
    path = tmp_env("DB_PASS=secret\n")
    result = rename(path, {"DB_PASS": "DATABASE_PASSWORD"})
    assert "DB_PASS -> DATABASE_PASSWORD" in result.summary()


def test_summary_shows_skipped(tmp_env):
    path = tmp_env("FOO=1\n")
    result = rename(path, {"GHOST": "NEW_GHOST"})
    assert "GHOST" in result.summary()


def test_unrelated_keys_unchanged(tmp_env):
    path = tmp_env("FOO=1\nBAR=2\n")
    result = rename(path, {"FOO": "FOO2"})
    assert any("BAR=2" in line for line in result.lines)
