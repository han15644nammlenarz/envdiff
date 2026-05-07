"""Tests for envdiff.cli_redact."""
from __future__ import annotations

import argparse
import pytest
from pathlib import Path

from envdiff.cli_redact import add_redact_subcommand, run_redact


@pytest.fixture
def tmp_env(tmp_path: Path) -> Path:
    return tmp_path / ".env"


def _write(p: Path, content: str) -> Path:
    p.write_text(content, encoding="utf-8")
    return p


def _make_args(source, output=None, keywords=None, quiet=False):
    ns = argparse.Namespace(
        source=str(source),
        output=str(output) if output else None,
        keywords=keywords or ["password", "secret", "token", "key", "api"],
        quiet=quiet,
    )
    return ns


def test_run_redact_returns_zero_on_success(tmp_env):
    _write(tmp_env, "APP_NAME=myapp\n")
    args = _make_args(tmp_env, quiet=True)
    assert run_redact(args) == 0


def test_run_redact_returns_one_when_missing(tmp_env):
    args = _make_args(tmp_env, quiet=True)  # file not written
    assert run_redact(args) == 1


def test_run_redact_creates_output_file(tmp_env, tmp_path):
    _write(tmp_env, "DB_PASSWORD=secret\n")
    dest = tmp_path / "out.env"
    args = _make_args(tmp_env, output=dest, quiet=True)
    run_redact(args)
    assert dest.exists()


def test_run_redact_default_output_name(tmp_env, tmp_path):
    _write(tmp_env, "APP_NAME=myapp\n")
    args = _make_args(tmp_env, quiet=True)
    run_redact(args)
    expected = tmp_env.with_suffix(".redacted")
    assert expected.exists()


def test_add_redact_subcommand_registers(tmp_env):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_redact_subcommand(sub)
    parsed = parser.parse_args(["redact", str(tmp_env), "--quiet"])
    assert parsed.quiet is True
