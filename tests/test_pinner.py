"""Tests for envdiff.pinner."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.pinner import pin, load_pin_file, PinResult


@pytest.fixture()
def tmp_env(tmp_path: Path):
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def test_returns_pin_result(tmp_env):
    f = _write(tmp_env / ".env", "FOO=bar\n")
    result = pin(f)
    assert isinstance(result, PinResult)


def test_total_keys_count(tmp_env):
    f = _write(tmp_env / ".env", "A=1\nB=2\nC=3\n")
    result = pin(f)
    assert result.total_keys == 3


def test_plain_values_retained(tmp_env):
    f = _write(tmp_env / ".env", "HOST=localhost\nPORT=5432\n")
    result = pin(f)
    assert result.pinned["HOST"] == "localhost"
    assert result.pinned["PORT"] == "5432"


def test_secret_value_masked_by_default(tmp_env):
    f = _write(tmp_env / ".env", "DB_PASSWORD=supersecret\n")
    result = pin(f)
    assert result.pinned["DB_PASSWORD"] == ""
    assert "DB_PASSWORD" in result.secret_keys


def test_secret_value_retained_when_mask_false(tmp_env):
    f = _write(tmp_env / ".env", "API_KEY=abc123\n")
    result = pin(f, mask_secrets=False)
    assert result.pinned["API_KEY"] == "abc123"


def test_secret_keys_list_populated(tmp_env):
    content = "TOKEN=tok\nHOST=localhost\nSECRET=shh\n"
    f = _write(tmp_env / ".env", content)
    result = pin(f)
    assert set(result.secret_keys) == {"TOKEN", "SECRET"}


def test_comments_and_blanks_ignored(tmp_env):
    content = "# comment\n\nFOO=bar\n"
    f = _write(tmp_env / ".env", content)
    result = pin(f)
    assert result.total_keys == 1
    assert "FOO" in result.pinned


def test_write_pin_file(tmp_env):
    f = _write(tmp_env / ".env", "HOST=localhost\nDB_PASSWORD=secret\n")
    out = tmp_env / "env.pin.json"
    pin(f, output_path=out)
    assert out.exists()
    data = json.loads(out.read_text())
    assert "pinned" in data
    assert data["total_keys"] == 2


def test_load_pin_file_roundtrip(tmp_env):
    f = _write(tmp_env / ".env", "HOST=localhost\nPORT=5432\n")
    out = tmp_env / "env.pin.json"
    pin(f, output_path=out, mask_secrets=False)
    loaded = load_pin_file(out)
    assert loaded["HOST"] == "localhost"
    assert loaded["PORT"] == "5432"


def test_summary_contains_key_count(tmp_env):
    f = _write(tmp_env / ".env", "A=1\nB=2\n")
    result = pin(f)
    assert "2" in result.summary()


def test_source_recorded_in_result(tmp_env):
    f = _write(tmp_env / ".env", "X=1\n")
    result = pin(f)
    assert str(f) == result.source
