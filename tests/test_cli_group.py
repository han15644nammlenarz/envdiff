"""Tests for envdiff.cli_group."""
from __future__ import annotations

import argparse
import json
import pytest

from envdiff.cli_group import add_group_subcommand, run_group


@pytest.fixture()
def tmp_env(tmp_path):
    return tmp_path


def _write(p, content: str) -> str:
    f = p / ".env"
    f.write_text(content)
    return str(f)


def _make_args(file, separator="_", min_prefix=1, fmt="text"):
    ns = argparse.Namespace(
        file=file,
        separator=separator,
        min_prefix=min_prefix,
        fmt=fmt,
    )
    return ns


def test_run_group_returns_zero(tmp_env):
    path = _write(tmp_env, "DB_HOST=localhost\nDB_PORT=5432\n")
    assert run_group(_make_args(path)) == 0


def test_run_group_text_output(tmp_env, capsys):
    path = _write(tmp_env, "DB_HOST=localhost\nDB_PORT=5432\n")
    run_group(_make_args(path))
    out = capsys.readouterr().out
    assert "DB" in out
    assert "2 key(s)" in out


def test_run_group_json_output(tmp_env, capsys):
    path = _write(tmp_env, "DB_HOST=localhost\nDB_PORT=5432\n")
    run_group(_make_args(path, fmt="json"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "groups" in data
    assert "DB" in data["groups"]


def test_run_group_json_includes_secret_count(tmp_env, capsys):
    path = _write(tmp_env, "DB_PASSWORD=secret\nDB_HOST=localhost\n")
    run_group(_make_args(path, fmt="json"))
    data = json.loads(capsys.readouterr().out)
    assert data["groups"]["DB"]["secret_count"] == 1


def test_run_group_json_ungrouped_present(tmp_env, capsys):
    path = _write(tmp_env, "PORT=8080\nDB_HOST=localhost\n")
    run_group(_make_args(path, fmt="json"))
    data = json.loads(capsys.readouterr().out)
    assert "PORT" in data["ungrouped"]


def test_add_group_subcommand_registers(tmp_env):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_group_subcommand(sub)
    args = parser.parse_args(["group", _write(tmp_env, "A_B=1\n")])
    assert hasattr(args, "func")
