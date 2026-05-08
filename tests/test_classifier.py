"""Tests for envdiff.classifier."""

from __future__ import annotations

import pathlib
import pytest

from envdiff.classifier import classify, ClassifyResult, _classify_key


@pytest.fixture()
def tmp_env(tmp_path: pathlib.Path):
    return tmp_path


def _write(p: pathlib.Path, content: str) -> str:
    p.write_text(content)
    return str(p)


# --- unit tests for _classify_key ---

def test_classify_secret_password():
    assert _classify_key("DB_PASSWORD", "hunter2") == "secret"


def test_classify_secret_token():
    assert _classify_key("API_TOKEN", "abc123") == "secret"


def test_classify_url():
    assert _classify_key("DATABASE_URL", "postgres://localhost/db") == "url"


def test_classify_port():
    assert _classify_key("APP_PORT", "8080") == "port"


def test_classify_flag_by_suffix():
    assert _classify_key("DEBUG_ENABLED", "true") == "flag"


def test_classify_flag_by_value():
    assert _classify_key("SOME_KEY", "true") == "flag"
    assert _classify_key("ANOTHER", "false") == "flag"


def test_classify_path():
    assert _classify_key("LOG_PATH", "/var/log/app") == "path"


def test_classify_general():
    assert _classify_key("APP_NAME", "myapp") == "general"


# --- integration tests for classify() ---

def test_returns_classify_result(tmp_env):
    path = _write(tmp_env / ".env", "APP_NAME=myapp\n")
    result = classify(path)
    assert isinstance(result, ClassifyResult)


def test_path_stored_on_result(tmp_env):
    path = _write(tmp_env / ".env", "APP_NAME=myapp\n")
    result = classify(path)
    assert result.path == path


def test_secret_key_categorised(tmp_env):
    path = _write(tmp_env / ".env", "SECRET_KEY=abc\nAPP_NAME=x\n")
    result = classify(path)
    assert "SECRET_KEY" in result.keys_in("secret")


def test_url_key_categorised(tmp_env):
    path = _write(tmp_env / ".env", "DATABASE_URL=postgres://localhost\n")
    result = classify(path)
    assert "DATABASE_URL" in result.keys_in("url")


def test_multiple_categories_populated(tmp_env):
    content = "DB_PASSWORD=s3cr3t\nAPP_PORT=5432\nLOG_PATH=/tmp\nAPP_NAME=x\n"
    path = _write(tmp_env / ".env", content)
    result = classify(path)
    assert "secret" in result.categories
    assert "port" in result.categories
    assert "path" in result.categories
    assert "general" in result.categories


def test_keys_in_returns_empty_for_unknown_category(tmp_env):
    path = _write(tmp_env / ".env", "APP_NAME=x\n")
    result = classify(path)
    assert result.keys_in("nonexistent") == []


def test_summary_contains_path(tmp_env):
    path = _write(tmp_env / ".env", "APP_NAME=x\n")
    result = classify(path)
    assert path in result.summary()


def test_key_category_mapping(tmp_env):
    path = _write(tmp_env / ".env", "APP_PORT=8080\n")
    result = classify(path)
    assert result.key_category["APP_PORT"] == "port"
