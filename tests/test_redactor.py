"""Tests for envdiff.redactor."""
from __future__ import annotations

import pytest
from pathlib import Path

from envdiff.redactor import redact, write_redacted, RedactResult


@pytest.fixture
def tmp_env(tmp_path: Path) -> Path:
    return tmp_path / ".env"


def _write(p: Path, content: str) -> Path:
    p.write_text(content, encoding="utf-8")
    return p


def test_returns_redact_result(tmp_env):
    _write(tmp_env, "APP_NAME=myapp\n")
    result = redact(tmp_env)
    assert isinstance(result, RedactResult)


def test_secret_value_is_blanked(tmp_env):
    _write(tmp_env, "DB_PASSWORD=supersecret\n")
    result = redact(tmp_env)
    assert "DB_PASSWORD" in result.redacted_keys
    assert any("DB_PASSWORD=" in line and "supersecret" not in line for line in result.lines)


def test_plain_value_is_retained(tmp_env):
    _write(tmp_env, "APP_NAME=myapp\n")
    result = redact(tmp_env)
    assert "APP_NAME" in result.retained_keys
    assert any("APP_NAME=myapp" in line for line in result.lines)


def test_comments_preserved(tmp_env):
    _write(tmp_env, "# a comment\nAPP_NAME=myapp\n")
    result = redact(tmp_env)
    assert any(line.startswith("#") for line in result.lines)


def test_blank_lines_preserved(tmp_env):
    _write(tmp_env, "APP_NAME=myapp\n\nDB_PASSWORD=secret\n")
    result = redact(tmp_env)
    assert "" in [line.strip() for line in result.lines]


def test_summary_message(tmp_env):
    _write(tmp_env, "DB_PASSWORD=s\nAPP_NAME=a\n")
    result = redact(tmp_env)
    summary = result.summary()
    assert "1" in summary
    assert "secret" in summary.lower()


def test_write_redacted_creates_file(tmp_env, tmp_path):
    _write(tmp_env, "DB_PASSWORD=secret\n")
    result = redact(tmp_env)
    dest = tmp_path / ".env.redacted"
    write_redacted(result, dest)
    assert dest.exists()
    assert "secret" not in dest.read_text()


def test_custom_keywords(tmp_env):
    _write(tmp_env, "INTERNAL_PASS=abc\nAPP_NAME=myapp\n")
    result = redact(tmp_env, secret_keywords=("pass",))
    assert "INTERNAL_PASS" in result.redacted_keys
    assert "APP_NAME" in result.retained_keys


def test_multiple_secrets_all_blanked(tmp_env):
    _write(tmp_env, "API_KEY=xyz\nSECRET_TOKEN=abc\nAPP_NAME=hello\n")
    result = redact(tmp_env)
    assert len(result.redacted_keys) == 2
    assert len(result.retained_keys) == 1
