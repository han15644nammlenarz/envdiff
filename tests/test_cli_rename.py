"""Tests for envdiff.cli_rename."""

import argparse
import pytest
from pathlib import Path

from envdiff.cli_rename import add_rename_subcommand, run_rename


@pytest.fixture
def tmp_env(tmp_path: Path):
    def _write(content: str, name: str = ".env") -> str:
        p = tmp_path / name
        p.write_text(content)
        return str(p)

    return _write


def _make_args(files, old_key, new_key, write=False):
    ns = argparse.Namespace(
        files=files,
        old_key=old_key,
        new_key=new_key,
        write=write,
    )
    return ns


def test_run_rename_returns_zero_on_success(tmp_env):
    path = tmp_env("MY_KEY=hello\n")
    args = _make_args([path], "MY_KEY", "NEW_KEY")
    assert run_rename(args) == 0


def test_run_rename_returns_one_when_key_missing(tmp_env):
    path = tmp_env("OTHER=val\n")
    args = _make_args([path], "MISSING_KEY", "NEW_KEY")
    assert run_rename(args) == 1


def test_run_rename_returns_one_for_missing_file():
    args = _make_args(["/nonexistent/.env"], "FOO", "BAR")
    assert run_rename(args) == 1


def test_run_rename_with_write_modifies_file(tmp_env):
    path = tmp_env("TOKEN=abc\n")
    args = _make_args([path], "TOKEN", "API_TOKEN", write=True)
    run_rename(args)
    assert "API_TOKEN=abc" in Path(path).read_text()


def test_add_rename_subcommand_registers_command():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    add_rename_subcommand(subparsers)
    parsed = parser.parse_args(["rename", "file.env", "--from", "A", "--to", "B"])
    assert parsed.old_key == "A"
    assert parsed.new_key == "B"
    assert parsed.files == ["file.env"]


def test_add_rename_subcommand_write_flag_default_false():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    add_rename_subcommand(subparsers)
    parsed = parser.parse_args(["rename", "f.env", "--from", "X", "--to", "Y"])
    assert parsed.write is False


def test_run_rename_multiple_files(tmp_env):
    p1 = tmp_env("FOO=1\n", "a.env")
    p2 = tmp_env("FOO=2\n", "b.env")
    args = _make_args([p1, p2], "FOO", "BAR", write=True)
    code = run_rename(args)
    assert code == 0
    assert "BAR=1" in Path(p1).read_text()
    assert "BAR=2" in Path(p2).read_text()
