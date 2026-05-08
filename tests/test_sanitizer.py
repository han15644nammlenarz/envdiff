"""Tests for envdiff.sanitizer."""
import pytest
from pathlib import Path

from envdiff.sanitizer import sanitize, write_sanitized, SanitizeResult


@pytest.fixture
def tmp_env(tmp_path):
    return tmp_path


def _write(p: Path, content: str) -> str:
    p.write_text(content, encoding="utf-8")
    return str(p)


def test_returns_sanitize_result(tmp_env):
    f = _write(tmp_env / ".env", "APP_NAME=myapp\n")
    result = sanitize(f)
    assert isinstance(result, SanitizeResult)


def test_secret_key_value_is_replaced(tmp_env):
    f = _write(tmp_env / ".env", "DB_PASSWORD=supersecret\n")
    result = sanitize(f)
    assert "DB_PASSWORD" in result.sanitized_keys
    assert any("REDACTED" in line for line in result.lines)


def test_plain_value_is_retained(tmp_env):
    f = _write(tmp_env / ".env", "APP_ENV=production\n")
    result = sanitize(f)
    assert "APP_ENV" not in result.sanitized_keys
    assert any("production" in line for line in result.lines)


def test_comments_are_preserved(tmp_env):
    f = _write(tmp_env / ".env", "# comment\nAPP_NAME=test\n")
    result = sanitize(f)
    assert result.lines[0] == "# comment"


def test_blank_lines_are_preserved(tmp_env):
    f = _write(tmp_env / ".env", "\nAPP_NAME=test\n")
    result = sanitize(f)
    assert result.lines[0] == ""


def test_custom_replacement_string(tmp_env):
    f = _write(tmp_env / ".env", "API_SECRET=abc123\n")
    result = sanitize(f, replacement="***")
    assert any("***" in line for line in result.lines)
    assert result.replacement == "***"


def test_long_hex_value_is_sanitized(tmp_env):
    hex_val = "a" * 40
    f = _write(tmp_env / ".env", f"SOME_KEY={hex_val}\n")
    result = sanitize(f)
    assert "SOME_KEY" in result.sanitized_keys


def test_extra_keywords_trigger_sanitize(tmp_env):
    f = _write(tmp_env / ".env", "DB_CREDENTIAL=hunter2\n")
    result = sanitize(f, extra_keywords=["credential"])
    assert "DB_CREDENTIAL" in result.sanitized_keys


def test_summary_no_issues(tmp_env):
    f = _write(tmp_env / ".env", "APP_NAME=myapp\n")
    result = sanitize(f)
    assert "no sensitive" in result.summary()


def test_summary_with_sanitized_keys(tmp_env):
    f = _write(tmp_env / ".env", "DB_PASSWORD=secret\n")
    result = sanitize(f)
    assert "sanitized" in result.summary()
    assert "DB_PASSWORD" in result.summary()


def test_write_sanitized_creates_file(tmp_env):
    src = _write(tmp_env / ".env", "API_TOKEN=abc123abc123abc123abc123abc123abc123abc123\n")
    result = sanitize(src)
    dest = str(tmp_env / ".env.sanitized")
    write_sanitized(result, dest)
    content = Path(dest).read_text(encoding="utf-8")
    assert "REDACTED" in content


def test_write_sanitized_preserves_plain_values(tmp_env):
    src = _write(tmp_env / ".env", "APP_NAME=hello\n")
    result = sanitize(src)
    dest = str(tmp_env / ".env.sanitized")
    write_sanitized(result, dest)
    content = Path(dest).read_text(encoding="utf-8")
    assert "hello" in content
