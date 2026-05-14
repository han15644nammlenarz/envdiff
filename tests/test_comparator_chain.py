"""Tests for envdiff.comparator_chain."""
from __future__ import annotations

import pytest
from pathlib import Path

from envdiff.comparator_chain import compare_chain, ChainResult, ChainLink


@pytest.fixture
def tmp_env(tmp_path: Path):
    def _write(name: str, content: str) -> str:
        p = tmp_path / name
        p.write_text(content)
        return str(p)
    return _write


def test_returns_chain_result(tmp_env):
    a = tmp_env("a.env", "KEY=1\n")
    b = tmp_env("b.env", "KEY=1\n")
    result = compare_chain([a, b])
    assert isinstance(result, ChainResult)


def test_single_pair_produces_one_link(tmp_env):
    a = tmp_env("a.env", "KEY=1\n")
    b = tmp_env("b.env", "KEY=1\n")
    result = compare_chain([a, b])
    assert len(result.links) == 1


def test_three_files_produce_two_links(tmp_env):
    a = tmp_env("a.env", "KEY=1\n")
    b = tmp_env("b.env", "KEY=1\n")
    c = tmp_env("c.env", "KEY=1\n")
    result = compare_chain([a, b, c])
    assert len(result.links) == 2


def test_all_clean_when_identical(tmp_env):
    a = tmp_env("a.env", "FOO=bar\nBAZ=qux\n")
    b = tmp_env("b.env", "FOO=bar\nBAZ=qux\n")
    result = compare_chain([a, b])
    assert result.all_clean() is True


def test_detects_missing_key_in_chain(tmp_env):
    a = tmp_env("a.env", "FOO=1\nBAR=2\n")
    b = tmp_env("b.env", "FOO=1\n")
    result = compare_chain([a, b])
    assert not result.all_clean()
    assert "BAR" in result.links[0].result.missing


def test_links_with_differences_filters_correctly(tmp_env):
    a = tmp_env("a.env", "FOO=1\n")
    b = tmp_env("b.env", "FOO=1\n")
    c = tmp_env("c.env", "FOO=1\nEXTRA=2\n")
    result = compare_chain([a, b, c])
    dirty = result.links_with_differences()
    assert len(dirty) == 1
    assert dirty[0].base_path == str(b)


def test_summary_all_clean(tmp_env):
    a = tmp_env("a.env", "X=1\n")
    b = tmp_env("b.env", "X=1\n")
    result = compare_chain([a, b])
    assert "clean" in result.summary().lower()


def test_summary_reports_dirty_count(tmp_env):
    a = tmp_env("a.env", "X=1\n")
    b = tmp_env("b.env", "Y=2\n")
    result = compare_chain([a, b])
    assert "1/1" in result.summary()


def test_raises_when_fewer_than_two_paths(tmp_env):
    a = tmp_env("a.env", "X=1\n")
    with pytest.raises(ValueError, match="at least two"):
        compare_chain([a])


def test_ignore_values_suppresses_mismatch(tmp_env):
    a = tmp_env("a.env", "KEY=old\n")
    b = tmp_env("b.env", "KEY=new\n")
    result = compare_chain([a, b], ignore_values=True)
    assert result.all_clean()


def test_ignore_extra_suppresses_extra_keys(tmp_env):
    a = tmp_env("a.env", "KEY=1\n")
    b = tmp_env("b.env", "KEY=1\nEXTRA=2\n")
    result = compare_chain([a, b], ignore_extra=True)
    assert result.all_clean()
