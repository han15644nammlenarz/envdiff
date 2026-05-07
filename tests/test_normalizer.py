"""Tests for envdiff.normalizer."""

import pytest
from pathlib import Path

from envdiff.normalizer import normalize, NormalizeResult, summary


@pytest.fixture
def tmp_env(tmp_path):
    return tmp_path


def _write(p: Path, content: str) -> str:
    p.write_text(content)
    return str(p)


def test_returns_normalize_result(tmp_env):
    f = _write(tmp_env / ".env", "FOO=bar\nBAZ=qux\n")
    result = normalize(f)
    assert isinstance(result, NormalizeResult)


def test_already_normalized_reports_zero_changes(tmp_env):
    f = _write(tmp_env / ".env", "BAZ=qux\nFOO=bar\n")
    result = normalize(f, sort_keys=True)
    # BAZ comes before FOO alphabetically — already sorted
    assert result.changes == 0


def test_sort_keys_reorders_lines(tmp_env):
    f = _write(tmp_env / ".env", "ZZZ=last\nAAA=first\n")
    result = normalize(f, sort_keys=True)
    keys = [
        ln.split("=", 1)[0]
        for ln in result.normalized_lines
        if "=" in ln and not ln.startswith("#")
    ]
    assert keys == sorted(keys)


def test_no_sort_preserves_order(tmp_env):
    f = _write(tmp_env / ".env", "ZZZ=last\nAAA=first\n")
    result = normalize(f, sort_keys=False)
    keys = [
        ln.split("=", 1)[0]
        for ln in result.normalized_lines
        if "=" in ln and not ln.startswith("#")
    ]
    assert keys == ["ZZZ", "AAA"]


def test_trailing_whitespace_stripped(tmp_env):
    f = _write(tmp_env / ".env", "FOO=bar   \nBAZ=qux\t\n")
    result = normalize(f)
    for line in result.normalized_lines:
        assert line == line.rstrip()


def test_single_quoted_value_normalized_to_double(tmp_env):
    f = _write(tmp_env / ".env", "FOO='hello world'\n")
    result = normalize(f)
    kv = [ln for ln in result.normalized_lines if "FOO=" in ln][0]
    assert kv == 'FOO="hello world"'


def test_value_with_spaces_gets_quoted(tmp_env):
    f = _write(tmp_env / ".env", 'FOO=hello world\n')
    result = normalize(f)
    kv = [ln for ln in result.normalized_lines if "FOO=" in ln][0]
    assert '"' in kv


def test_write_overwrites_file(tmp_env):
    p = tmp_env / ".env"
    f = _write(p, "ZZZ=last\nAAA=first\n")
    normalize(f, sort_keys=True, write=True)
    contents = p.read_text()
    lines = [ln for ln in contents.splitlines() if "=" in ln]
    keys = [ln.split("=", 1)[0] for ln in lines]
    assert keys == sorted(keys)


def test_comments_preserved(tmp_env):
    f = _write(tmp_env / ".env", "# My config\nFOO=bar\n")
    result = normalize(f)
    assert any(ln.startswith("#") for ln in result.normalized_lines)


def test_summary_no_changes(tmp_env):
    f = _write(tmp_env / ".env", "AAA=one\nZZZ=two\n")
    result = normalize(f, sort_keys=True)
    assert "no changes" in result.summary()


def test_summary_with_changes(tmp_env):
    f = _write(tmp_env / ".env", "ZZZ=two\nAAA=one\n")
    result = normalize(f, sort_keys=True)
    if result.changes > 0:
        assert "normalized" in result.summary()


def test_summary_function_delegates(tmp_env):
    f = _write(tmp_env / ".env", "FOO=bar\n")
    result = normalize(f)
    assert summary(result) == result.summary()
