"""Tests for envdiff.parser."""

import textwrap
from pathlib import Path

import pytest

from envdiff.parser import parse_env_file


@pytest.fixture()
def env_file(tmp_path: Path):
    """Factory fixture: write content to a temp .env file and return its path."""

    def _write(content: str) -> Path:
        p = tmp_path / ".env"
        p.write_text(textwrap.dedent(content), encoding="utf-8")
        return p

    return _write


def test_basic_key_value(env_file):
    path = env_file("""
        APP_ENV=production
        PORT=8080
    """)
    result = parse_env_file(path)
    assert result == {"APP_ENV": "production", "PORT": "8080"}


def test_quoted_values(env_file):
    path = env_file("""
        SECRET='my secret'
        DSN="postgres://localhost/db"
    """)
    result = parse_env_file(path)
    assert result["SECRET"] == "my secret"
    assert result["DSN"] == "postgres://localhost/db"


def test_comments_and_blank_lines_ignored(env_file):
    path = env_file("""
        # This is a comment
        FOO=bar

        # Another comment
        BAZ=qux
    """)
    result = parse_env_file(path)
    assert result == {"FOO": "bar", "BAZ": "qux"}


def test_empty_value(env_file):
    path = env_file("EMPTY=\n")
    result = parse_env_file(path)
    assert result["EMPTY"] == ""


def test_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError, match=".env file not found"):
        parse_env_file(tmp_path / "missing.env")


def test_invalid_line_raises(env_file):
    path = env_file("THIS IS NOT VALID\n")
    with pytest.raises(ValueError, match="Invalid syntax"):
        parse_env_file(path)


def test_preserves_insertion_order(env_file):
    path = env_file("""
        Z=last
        A=first
        M=middle
    """)
    keys = list(parse_env_file(path).keys())
    assert keys == ["Z", "A", "M"]
