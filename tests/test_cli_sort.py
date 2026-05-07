"""Tests for envdiff.cli_sort."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envdiff.cli_sort import add_sort_subcommand, run_sort


@pytest.fixture
def tmp_env(tmp_path):
    return tmp_path / ".env"


def _write(p: Path, content: str) -> None:
    p.write_text(content)


def _make_args(file: str, reverse: bool = False, write: bool = False, check: bool = False):
    ns = argparse.Namespace()
    ns.file = file
    ns.reverse = reverse
    ns.write = write
    ns.check = check
    return ns


def test_run_sort_returns_zero_on_clean_file(tmp_env):
    _write(tmp_env, "ALPHA=1\nBETA=2\n")
    args = _make_args(str(tmp_env))
    assert run_sort(args) == 0


def test_run_sort_returns_zero_when_changed_no_check(tmp_env):
    _write(tmp_env, "ZEBRA=1\nAPPLE=2\n")
    args = _make_args(str(tmp_env))
    assert run_sort(args) == 0


def test_run_sort_check_returns_one_when_unsorted(tmp_env):
    _write(tmp_env, "ZEBRA=1\nAPPLE=2\n")
    args = _make_args(str(tmp_env), check=True)
    assert run_sort(args) == 1


def test_run_sort_check_returns_zero_when_sorted(tmp_env):
    _write(tmp_env, "APPLE=1\nZEBRA=2\n")
    args = _make_args(str(tmp_env), check=True)
    assert run_sort(args) == 0


def test_run_sort_write_modifies_file(tmp_env):
    _write(tmp_env, "ZEBRA=1\nAPPLE=2\n")
    args = _make_args(str(tmp_env), write=True)
    run_sort(args)
    lines = [l for l in tmp_env.read_text().splitlines() if "=" in l]
    keys = [l.split("=")[0] for l in lines]
    assert keys == sorted(keys)


def test_run_sort_returns_one_on_missing_file(tmp_path):
    args = _make_args(str(tmp_path / "missing.env"))
    assert run_sort(args) == 1


def test_add_sort_subcommand_registers_parser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    add_sort_subcommand(subparsers)
    args = parser.parse_args(["sort", "some.env"])
    assert args.file == "some.env"
    assert not args.reverse
    assert not args.write
    assert not args.check
