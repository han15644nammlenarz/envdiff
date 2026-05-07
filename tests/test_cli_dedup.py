"""Tests for envdiff.cli_dedup."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from envdiff.cli_dedup import add_dedup_subcommand, run_dedup


@pytest.fixture
def tmp_env(tmp_path: Path):
    return tmp_path / ".env"


def _write(p: Path, content: str) -> None:
    p.write_text(content, encoding="utf-8")


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"fix": False, "output_format": "text"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_run_dedup_returns_zero_on_clean_file(tmp_env):
    _write(tmp_env, "A=1\nB=2\n")
    args = _make_args(file=str(tmp_env))
    assert run_dedup(args) == 0


def test_run_dedup_returns_one_when_duplicates(tmp_env):
    _write(tmp_env, "KEY=1\nKEY=2\n")
    args = _make_args(file=str(tmp_env))
    assert run_dedup(args) == 1


def test_run_dedup_returns_one_on_missing_file(tmp_path):
    args = _make_args(file=str(tmp_path / "nonexistent.env"))
    assert run_dedup(args) == 1


def test_run_dedup_json_output_no_duplicates(tmp_env, capsys):
    _write(tmp_env, "A=1\nB=2\n")
    args = _make_args(file=str(tmp_env), output_format="json")
    run_dedup(args)
    captured = capsys.readouterr().out
    data = json.loads(captured)
    assert data["has_duplicates"] is False
    assert data["duplicates"] == {}


def test_run_dedup_json_output_with_duplicates(tmp_env, capsys):
    _write(tmp_env, "KEY=1\nKEY=2\n")
    args = _make_args(file=str(tmp_env), output_format="json")
    run_dedup(args)
    captured = capsys.readouterr().out
    data = json.loads(captured)
    assert data["has_duplicates"] is True
    assert "KEY" in data["duplicates"]


def test_run_dedup_fix_rewrites_file(tmp_env):
    _write(tmp_env, "KEY=first\nKEY=second\n")
    args = _make_args(file=str(tmp_env), fix=True)
    run_dedup(args)
    content = tmp_env.read_text(encoding="utf-8")
    assert "KEY=second" in content
    assert "KEY=first" not in content


def test_add_dedup_subcommand_registers(tmp_env):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_dedup_subcommand(sub)
    args = parser.parse_args(["dedup", str(tmp_env)])
    assert args.file == str(tmp_env)
    assert args.fix is False
