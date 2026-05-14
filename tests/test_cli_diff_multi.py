"""Tests for envdiff.cli_diff_multi."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from envdiff.cli_diff_multi import add_diff_multi_subcommand, run_diff_multi


@pytest.fixture()
def tmp_env(tmp_path: Path):
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


def _make_args(tmp_env, ref_content, target_contents, **kwargs):
    ref = _write(tmp_env / "ref.env", ref_content)
    targets = [
        _write(tmp_env / f"t{i}.env", c)
        for i, c in enumerate(target_contents)
    ]
    ns = argparse.Namespace(
        reference=str(ref),
        targets=[str(t) for t in targets],
        ignore_values=kwargs.get("ignore_values", False),
        mask_secrets=kwargs.get("mask_secrets", False),
        format=kwargs.get("format", "text"),
        func=run_diff_multi,
    )
    return ns


def test_run_diff_multi_returns_zero_when_clean(tmp_env, capsys):
    args = _make_args(tmp_env, "A=1\n", ["A=1\n"])
    assert run_diff_multi(args) == 0


def test_run_diff_multi_returns_one_when_diff(tmp_env, capsys):
    args = _make_args(tmp_env, "A=1\nB=2\n", ["A=1\n"])
    assert run_diff_multi(args) == 1


def test_text_output_contains_reference(tmp_env, capsys):
    args = _make_args(tmp_env, "A=1\n", ["A=1\n"])
    run_diff_multi(args)
    out = capsys.readouterr().out
    assert "ref.env" in out


def test_json_output_is_valid_json(tmp_env, capsys):
    args = _make_args(tmp_env, "A=1\n", ["A=1\n"], format="json")
    run_diff_multi(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "reference" in data
    assert "targets" in data


def test_json_output_all_clean_flag(tmp_env, capsys):
    args = _make_args(tmp_env, "A=1\n", ["A=1\n"], format="json")
    run_diff_multi(args)
    data = json.loads(capsys.readouterr().out)
    assert data["all_clean"] is True


def test_json_output_missing_key_listed(tmp_env, capsys):
    args = _make_args(tmp_env, "A=1\nB=2\n", ["A=1\n"], format="json")
    run_diff_multi(args)
    data = json.loads(capsys.readouterr().out)
    target_key = list(data["targets"].keys())[0]
    assert "B" in data["targets"][target_key]["missing"]


def test_subcommand_registered(tmp_env):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_diff_multi_subcommand(sub)
    args = parser.parse_args(["multi-diff", "ref.env", "t1.env"])
    assert args.reference == "ref.env"
    assert args.targets == ["t1.env"]
