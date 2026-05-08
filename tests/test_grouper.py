"""Tests for envdiff.grouper."""
from __future__ import annotations

import os
import pytest

from envdiff.grouper import group, GroupResult


@pytest.fixture()
def tmp_env(tmp_path):
    return tmp_path


def _write(p, content: str) -> str:
    f = p / ".env"
    f.write_text(content)
    return str(f)


def test_returns_group_result(tmp_env):
    path = _write(tmp_env, "DB_HOST=localhost\nDB_PORT=5432\n")
    result = group(path)
    assert isinstance(result, GroupResult)


def test_keys_grouped_by_prefix(tmp_env):
    path = _write(tmp_env, "DB_HOST=localhost\nDB_PORT=5432\nAPP_NAME=myapp\n")
    result = group(path)
    assert "DB" in result.groups
    assert set(result.groups["DB"]) == {"DB_HOST", "DB_PORT"}
    assert "APP" in result.groups
    assert result.groups["APP"] == ["APP_NAME"]


def test_key_without_separator_is_ungrouped(tmp_env):
    path = _write(tmp_env, "PORT=8080\nDB_HOST=localhost\n")
    result = group(path)
    assert "PORT" in result.ungrouped
    assert "DB_HOST" not in result.ungrouped


def test_custom_separator(tmp_env):
    path = _write(tmp_env, "DB.HOST=localhost\nDB.PORT=5432\n")
    result = group(path, separator=".")
    assert "DB" in result.groups
    assert len(result.groups["DB"]) == 2


def test_min_prefix_length_filters_short_prefixes(tmp_env):
    path = _write(tmp_env, "A_KEY=1\nDB_HOST=localhost\n")
    result = group(path, min_prefix_length=2)
    assert "A" not in result.groups
    assert "A_KEY" in result.ungrouped
    assert "DB" in result.groups


def test_secret_keys_in_group_detected(tmp_env):
    path = _write(tmp_env, "DB_PASSWORD=secret\nDB_HOST=localhost\n")
    result = group(path)
    secrets = result.secret_keys_in_group("DB")
    assert "DB_PASSWORD" in secrets
    assert "DB_HOST" not in secrets


def test_group_names_sorted(tmp_env):
    path = _write(tmp_env, "Z_KEY=1\nA_KEY=2\nM_KEY=3\n")
    result = group(path)
    assert result.group_names() == sorted(result.group_names())


def test_summary_contains_group_name(tmp_env):
    path = _write(tmp_env, "DB_HOST=localhost\nDB_PORT=5432\n")
    result = group(path)
    summary = result.summary()
    assert "DB" in summary
    assert "2 key(s)" in summary


def test_empty_file_produces_no_groups(tmp_env):
    path = _write(tmp_env, "")
    result = group(path)
    assert result.groups == {}
    assert result.ungrouped == []


def test_include_ungrouped_false_hides_ungrouped(tmp_env):
    path = _write(tmp_env, "PORT=8080\nDB_HOST=localhost\n")
    result = group(path, include_ungrouped=False)
    assert result.ungrouped == []
