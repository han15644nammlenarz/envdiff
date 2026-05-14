"""Tests for envdiff.flattener."""
from __future__ import annotations

import pathlib
import pytest

from envdiff.flattener import flatten, FlattenResult


@pytest.fixture()
def tmp_env(tmp_path: pathlib.Path):
    return tmp_path


def _write(directory: pathlib.Path, name: str, content: str) -> pathlib.Path:
    p = directory / name
    p.write_text(content)
    return p


def test_returns_flatten_result(tmp_env):
    f = _write(tmp_env, ".env", "APP_NAME=myapp\n")
    result = flatten(str(f))
    assert isinstance(result, FlattenResult)


def test_simple_key_no_separator_becomes_top_level(tmp_env):
    f = _write(tmp_env, ".env", "NAME=alice\n")
    result = flatten(str(f))
    assert result.tree == {"NAME": "alice"}


def test_underscore_separator_builds_nested_tree(tmp_env):
    f = _write(tmp_env, ".env", "DB_HOST=localhost\nDB_PORT=5432\n")
    result = flatten(str(f))
    assert isinstance(result.tree.get("DB"), dict)
    assert result.tree["DB"]["HOST"] == "localhost"  # type: ignore[index]
    assert result.tree["DB"]["PORT"] == "5432"  # type: ignore[index]


def test_three_level_nesting(tmp_env):
    f = _write(tmp_env, ".env", "AWS_S3_BUCKET=my-bucket\n")
    result = flatten(str(f))
    assert result.get("AWS", "S3", "BUCKET") == "my-bucket"


def test_max_depth_limits_split(tmp_env):
    f = _write(tmp_env, ".env", "AWS_S3_BUCKET=my-bucket\n")
    result = flatten(str(f), max_depth=1)
    # With max_depth=1, splits into ["AWS", "S3_BUCKET"]
    assert isinstance(result.tree.get("AWS"), dict)
    assert result.tree["AWS"].get("S3_BUCKET") == "my-bucket"  # type: ignore[union-attr]


def test_keys_list_matches_original_keys(tmp_env):
    f = _write(tmp_env, ".env", "FOO=1\nBAR=2\nBAZ=3\n")
    result = flatten(str(f))
    assert set(result.keys) == {"FOO", "BAR", "BAZ"}


def test_groups_returns_top_level_segments(tmp_env):
    f = _write(tmp_env, ".env", "DB_HOST=h\nDB_PORT=p\nAPP_NAME=n\n")
    result = flatten(str(f))
    groups = result.groups()
    assert "DB" in groups
    assert "APP" in groups


def test_custom_separator(tmp_env):
    f = _write(tmp_env, ".env", "DB.HOST=localhost\n")
    result = flatten(str(f), separator=".")
    assert result.get("DB", "HOST") == "localhost"


def test_summary_contains_source_and_counts(tmp_env):
    f = _write(tmp_env, ".env", "DB_HOST=h\nDB_PORT=p\n")
    result = flatten(str(f))
    s = result.summary()
    assert "2 keys" in s
    assert "DB" in s


def test_get_returns_none_for_missing_path(tmp_env):
    f = _write(tmp_env, ".env", "FOO=bar\n")
    result = flatten(str(f))
    assert result.get("MISSING", "KEY") is None


def test_file_not_found_raises(tmp_env):
    with pytest.raises(FileNotFoundError):
        flatten(str(tmp_env / "nonexistent.env"))
