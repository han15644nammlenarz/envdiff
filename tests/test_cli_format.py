"""Tests for envdiff.cli_format."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envdiff.cli_format import add_format_subcommand, run_format


@pytest.fixture
def tmp_env(tmp_path: Path):
    def _write(name: str, content: str) -> str:
        p = tmp_path / name
        p.write_text(content, encoding="utf-8")
        return str(p)
    return _write


def _make_args(files, sort=False, check=False) -> argparse.Namespace:
    return argparse.Namespace(files=files, sort=sort, check=check)


def test_run_format_returns_zero_on_clean_file(tmp_env):
    path = tmp_env("a.env", "KEY=value\n")
    rc = run_format(_make_args([path]))
    assert rc == 0


def test_run_format_returns_zero_after_fixing(tmp_env):
    path = tmp_env("b.env", "KEY = value\n")
    rc = run_format(_make_args([path]))
    assert rc == 0
    content = Path(path).read_text()
    assert "KEY=value" in content


def test_run_format_check_returns_one_when_changes_needed(tmp_env):
    path = tmp_env("c.env", "KEY = value\n")
    rc = run_format(_make_args([path], check=True))
    assert rc == 1


def test_run_format_check_does_not_write_file(tmp_env):
    path = tmp_env("d.env", "KEY = value\n")
    run_format(_make_args([path], check=True))
    content = Path(path).read_text()
    # File must remain unchanged in check mode
    assert "KEY = value" in content


def test_run_format_returns_one_for_missing_file(tmp_path):
    rc = run_format(_make_args([str(tmp_path / "missing.env")]))
    assert rc == 1


def test_run_format_sort_flag(tmp_env):
    path = tmp_env("e.env", "ZEBRA=1\nAPPLE=2\n")
    rc = run_format(_make_args([path], sort=True))
    assert rc == 0
    content = Path(path).read_text()
    assert content.index("APPLE") < content.index("ZEBRA")


def test_add_format_subcommand_registers_parser():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_format_subcommand(sub)
    args = parser.parse_args(["format", "some.env"])
    assert args.files == ["some.env"]
    assert args.sort is False
    assert args.check is False
