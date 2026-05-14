"""Tests for envdiff.cli_chain."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from envdiff.cli_chain import add_chain_subcommand, run_chain


@pytest.fixture
def tmp_env(tmp_path: Path):
    def _write(name: str, content: str) -> str:
        p = tmp_path / name
        p.write_text(content)
        return str(p)
    return _write


def _make_args(files, *, ignore_values=False, ignore_extra=False, fmt="text"):
    ns = argparse.Namespace(
        files=files,
        ignore_values=ignore_values,
        ignore_extra=ignore_extra,
        output_format=fmt,
    )
    return ns


def test_run_chain_returns_zero_when_clean(tmp_env):
    a = tmp_env("a.env", "KEY=1\n")
    b = tmp_env("b.env", "KEY=1\n")
    args = _make_args([a, b])
    assert run_chain(args) == 0


def test_run_chain_returns_one_when_diff(tmp_env):
    a = tmp_env("a.env", "KEY=1\nSECRET=x\n")
    b = tmp_env("b.env", "KEY=1\n")
    args = _make_args([a, b])
    assert run_chain(args) == 1


def test_run_chain_returns_two_for_single_file(tmp_env):
    a = tmp_env("a.env", "KEY=1\n")
    args = _make_args([a])
    assert run_chain(args) == 2


def test_run_chain_json_output_is_valid(tmp_env, capsys):
    a = tmp_env("a.env", "KEY=1\n")
    b = tmp_env("b.env", "KEY=1\n")
    args = _make_args([a, b], fmt="json")
    run_chain(args)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "links" in data
    assert "all_clean" in data


def test_run_chain_json_contains_link_paths(tmp_env, capsys):
    a = tmp_env("a.env", "KEY=1\n")
    b = tmp_env("b.env", "KEY=2\n")
    args = _make_args([a, b], fmt="json")
    run_chain(args)
    data = json.loads(capsys.readouterr().out)
    link = data["links"][0]
    assert link["base"] == a
    assert link["target"] == b


def test_add_chain_subcommand_registers(tmp_env):
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    add_chain_subcommand(subs)
    args = parser.parse_args(["chain", tmp_env("a.env", ""), tmp_env("b.env", "")])
    assert hasattr(args, "func")


def test_text_output_mentions_missing_key(tmp_env, capsys):
    a = tmp_env("a.env", "MISSING_KEY=1\n")
    b = tmp_env("b.env", "OTHER=2\n")
    args = _make_args([a, b])
    run_chain(args)
    out = capsys.readouterr().out
    assert "MISSING_KEY" in out or "OTHER" in out
