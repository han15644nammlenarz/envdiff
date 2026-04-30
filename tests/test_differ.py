"""Tests for envdiff.differ.diff_files."""

import pytest
from pathlib import Path

from envdiff.differ import diff_files


@pytest.fixture()
def tmp_env(tmp_path):
    """Return a helper that writes a .env file and returns its path."""

    def _write(name: str, content: str) -> Path:
        p = tmp_path / name
        p.write_text(content)
        return p

    return _write


def test_identical_files_no_differences(tmp_env):
    base = tmp_env(".env.base", "KEY1=value1\nKEY2=value2\n")
    target = tmp_env(".env.target", "KEY1=value1\nKEY2=value2\n")
    result = diff_files(base, target)
    assert not result.missing_keys
    assert not result.extra_keys
    assert not result.mismatched_keys


def test_missing_key_detected(tmp_env):
    base = tmp_env(".env.base", "KEY1=value1\nKEY2=value2\n")
    target = tmp_env(".env.target", "KEY1=value1\n")
    result = diff_files(base, target)
    assert "KEY2" in result.missing_keys


def test_extra_key_detected(tmp_env):
    base = tmp_env(".env.base", "KEY1=value1\n")
    target = tmp_env(".env.target", "KEY1=value1\nEXTRA=oops\n")
    result = diff_files(base, target)
    assert "EXTRA" in result.extra_keys


def test_mismatched_value_detected(tmp_env):
    base = tmp_env(".env.base", "KEY1=hello\n")
    target = tmp_env(".env.target", "KEY1=world\n")
    result = diff_files(base, target)
    assert "KEY1" in result.mismatched_keys


def test_ignore_values_suppresses_mismatch(tmp_env):
    base = tmp_env(".env.base", "KEY1=hello\n")
    target = tmp_env(".env.target", "KEY1=world\n")
    result = diff_files(base, target, ignore_values=True)
    assert not result.mismatched_keys


def test_ignore_keys_excludes_key(tmp_env):
    base = tmp_env(".env.base", "KEY1=value1\nSECRET=abc\n")
    target = tmp_env(".env.target", "KEY1=value1\n")
    result = diff_files(base, target, ignore_keys=["SECRET"])
    assert "SECRET" not in result.missing_keys


def test_missing_base_file_raises(tmp_path, tmp_env):
    target = tmp_env(".env.target", "KEY1=val\n")
    with pytest.raises(FileNotFoundError, match="Base env file not found"):
        diff_files(tmp_path / "nonexistent.env", target)


def test_missing_target_file_raises(tmp_path, tmp_env):
    base = tmp_env(".env.base", "KEY1=val\n")
    with pytest.raises(FileNotFoundError, match="Target env file not found"):
        diff_files(base, tmp_path / "nonexistent.env")


def test_returns_diff_result_type(tmp_env):
    from envdiff.comparator import DiffResult

    base = tmp_env(".env.base", "A=1\n")
    target = tmp_env(".env.target", "A=1\n")
    result = diff_files(base, target)
    assert isinstance(result, DiffResult)
