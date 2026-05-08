"""Tests for envdiff.tagger."""
import pytest
from pathlib import Path

from envdiff.tagger import tag, TagResult


@pytest.fixture
def tmp_env(tmp_path):
    return tmp_path


def _write(p: Path, content: str) -> Path:
    p.write_text(content)
    return p


def test_returns_tag_result(tmp_env):
    f = _write(tmp_env / ".env", "NAME=alice\n")
    result = tag(f)
    assert isinstance(result, TagResult)


def test_total_keys_count(tmp_env):
    f = _write(tmp_env / ".env", "A=1\nB=2\nC=3\n")
    result = tag(f)
    assert result.total_keys == 3


def test_secret_key_tagged(tmp_env):
    f = _write(tmp_env / ".env", "API_KEY=abc123\n")
    result = tag(f)
    assert "secret" in result.tags_for_key("API_KEY")


def test_empty_value_tagged(tmp_env):
    f = _write(tmp_env / ".env", "EMPTY_VAR=\n")
    result = tag(f)
    assert "empty" in result.tags_for_key("EMPTY_VAR")


def test_url_value_tagged(tmp_env):
    f = _write(tmp_env / ".env", "DATABASE_URL=https://db.example.com\n")
    result = tag(f)
    assert "url" in result.tags_for_key("DATABASE_URL")


def test_numeric_value_tagged(tmp_env):
    f = _write(tmp_env / ".env", "PORT=8080\n")
    result = tag(f)
    assert "numeric" in result.tags_for_key("PORT")


def test_boolean_value_tagged(tmp_env):
    f = _write(tmp_env / ".env", "DEBUG=true\n")
    result = tag(f)
    assert "boolean" in result.tags_for_key("DEBUG")


def test_plain_key_not_tagged(tmp_env):
    f = _write(tmp_env / ".env", "APP_NAME=myapp\n")
    result = tag(f)
    assert result.tags_for_key("APP_NAME") == []


def test_keys_for_tag_returns_correct_keys(tmp_env):
    content = "API_KEY=secret\nDB_PASSWORD=pass\nNAME=bob\n"
    f = _write(tmp_env / ".env", content)
    result = tag(f)
    secret_keys = result.keys_for_tag("secret")
    assert "API_KEY" in secret_keys
    assert "DB_PASSWORD" in secret_keys
    assert "NAME" not in secret_keys


def test_custom_extra_rule(tmp_env):
    f = _write(tmp_env / ".env", "REGION=us-east-1\nOTHER=foo\n")
    custom = [("region", lambda k, v: "us-" in v or "eu-" in v)]
    result = tag(f, extra_rules=custom)
    assert "region" in result.tags_for_key("REGION")
    assert "region" not in result.tags_for_key("OTHER")


def test_total_tagged_count(tmp_env):
    content = "SECRET_KEY=xyz\nPLAIN=hello\nPORT=3000\n"
    f = _write(tmp_env / ".env", content)
    result = tag(f)
    # SECRET_KEY -> secret; PORT -> numeric
    assert result.total_tagged == 2


def test_summary_contains_path(tmp_env):
    f = _write(tmp_env / ".env", "A=1\n")
    result = tag(f)
    assert str(f) in result.summary()


def test_summary_contains_tag_counts(tmp_env):
    f = _write(tmp_env / ".env", "TOKEN=abc\nPORT=80\n")
    result = tag(f)
    summary = result.summary()
    assert "secret" in summary
    assert "numeric" in summary


def test_comments_ignored(tmp_env):
    content = "# this is a comment\nNAME=alice\n"
    f = _write(tmp_env / ".env", content)
    result = tag(f)
    assert result.total_keys == 1
