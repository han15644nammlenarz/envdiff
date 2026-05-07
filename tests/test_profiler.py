"""Tests for envdiff.profiler."""
import os
import pytest

from envdiff.profiler import profile, ProfileResult


@pytest.fixture()
def tmp_env(tmp_path):
    return tmp_path


def _write(directory, name, content):
    p = directory / name
    p.write_text(content)
    return str(p)


def test_returns_profile_result(tmp_env):
    path = _write(tmp_env, ".env", "KEY=value\n")
    result = profile(path)
    assert isinstance(result, ProfileResult)


def test_total_keys_count(tmp_env):
    path = _write(tmp_env, ".env", "A=1\nB=2\nC=3\n")
    result = profile(path)
    assert result.total_keys == 3


def test_secret_keys_detected(tmp_env):
    path = _write(tmp_env, ".env", "DB_PASSWORD=secret\nAPI_KEY=abc\nNAME=alice\n")
    result = profile(path)
    assert "DB_PASSWORD" in result.secret_keys
    assert "API_KEY" in result.secret_keys
    assert "NAME" not in result.secret_keys


def test_plain_keys_detected(tmp_env):
    path = _write(tmp_env, ".env", "HOST=localhost\nPORT=5432\nTOKEN=xyz\n")
    result = profile(path)
    assert "HOST" in result.plain_keys
    assert "PORT" in result.plain_keys
    assert "TOKEN" not in result.plain_keys


def test_empty_value_keys(tmp_env):
    path = _write(tmp_env, ".env", "PRESENT=yes\nEMPTY=\n")
    result = profile(path)
    assert "EMPTY" in result.empty_value_keys
    assert "PRESENT" not in result.empty_value_keys


def test_long_value_keys(tmp_env):
    long_val = "x" * 101
    path = _write(tmp_env, ".env", f"SHORT=hi\nLONG={long_val}\n")
    result = profile(path)
    assert "LONG" in result.long_value_keys
    assert "SHORT" not in result.long_value_keys


def test_avg_value_length(tmp_env):
    # values: "ab" (2), "cdef" (4) -> avg 3.0
    path = _write(tmp_env, ".env", "A=ab\nB=cdef\n")
    result = profile(path)
    assert result.avg_value_length == 3.0


def test_avg_value_length_empty_file(tmp_env):
    path = _write(tmp_env, ".env", "# just a comment\n")
    result = profile(path)
    assert result.total_keys == 0
    assert result.avg_value_length == 0.0


def test_key_lengths_populated(tmp_env):
    path = _write(tmp_env, ".env", "FOO=hello\n")
    result = profile(path)
    assert result.key_lengths["FOO"] == 5


def test_custom_secret_keywords(tmp_env):
    path = _write(tmp_env, ".env", "INTERNAL_CERT=abc\nNAME=bob\n")
    result = profile(path, secret_keywords=["cert"])
    assert "INTERNAL_CERT" in result.secret_keys
    assert "NAME" in result.plain_keys


def test_summary_contains_path(tmp_env):
    path = _write(tmp_env, ".env", "X=1\n")
    result = profile(path)
    assert path in result.summary()


def test_summary_contains_counts(tmp_env):
    path = _write(tmp_env, ".env", "A=1\nB=2\n")
    result = profile(path)
    summary = result.summary()
    assert "Total keys" in summary
    assert "2" in summary
