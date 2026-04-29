"""Tests for envdiff.validator."""

import os
import pytest

from envdiff.validator import validate, ValidationResult


@pytest.fixture
def tmp_env(tmp_path):
    """Helper that writes a dict to a temp .env file and returns its path."""

    def _write(name: str, data: dict) -> str:
        p = tmp_path / name
        lines = [f"{k}={v}" for k, v in data.items()]
        p.write_text("\n".join(lines) + "\n")
        return str(p)

    return _write


# ---------------------------------------------------------------------------
# Happy-path
# ---------------------------------------------------------------------------

def test_valid_when_all_keys_present(tmp_env):
    ref = tmp_env("ref.env", {"HOST": "localhost", "PORT": "8080"})
    tgt = tmp_env("tgt.env", {"HOST": "prod.example.com", "PORT": "443"})
    result = validate(ref, tgt, ignore_values=True)
    assert result.is_valid
    assert result.missing_keys == []
    assert result.extra_keys == []


def test_summary_valid(tmp_env):
    ref = tmp_env("ref.env", {"KEY": "val"})
    tgt = tmp_env("tgt.env", {"KEY": "other"})
    result = validate(ref, tgt, ignore_values=True)
    assert "valid" in result.summary().lower()
    assert "INVALID" not in result.summary()


# ---------------------------------------------------------------------------
# Missing keys
# ---------------------------------------------------------------------------

def test_invalid_when_missing_keys(tmp_env):
    ref = tmp_env("ref.env", {"HOST": "localhost", "SECRET": "x"})
    tgt = tmp_env("tgt.env", {"HOST": "prod"})
    result = validate(ref, tgt)
    assert not result.is_valid
    assert "SECRET" in result.missing_keys


def test_summary_reports_missing(tmp_env):
    ref = tmp_env("ref.env", {"A": "1", "B": "2"})
    tgt = tmp_env("tgt.env", {"A": "1"})
    result = validate(ref, tgt)
    assert "missing" in result.summary()


# ---------------------------------------------------------------------------
# Extra keys
# ---------------------------------------------------------------------------

def test_extra_keys_invalid_by_default(tmp_env):
    ref = tmp_env("ref.env", {"HOST": "localhost"})
    tgt = tmp_env("tgt.env", {"HOST": "prod", "EXTRA": "surprise"})
    result = validate(ref, tgt, ignore_extra=False)
    assert not result.is_valid
    assert "EXTRA" in result.extra_keys


def test_extra_keys_ignored_when_flag_set(tmp_env):
    ref = tmp_env("ref.env", {"HOST": "localhost"})
    tgt = tmp_env("tgt.env", {"HOST": "prod", "EXTRA": "surprise"})
    result = validate(ref, tgt, ignore_extra=True)
    assert result.is_valid


# ---------------------------------------------------------------------------
# File errors
# ---------------------------------------------------------------------------

def test_missing_reference_file_returns_error(tmp_env):
    tgt = tmp_env("tgt.env", {"KEY": "val"})
    result = validate("/nonexistent/.env.example", tgt)
    assert not result.is_valid
    assert result.errors
    assert "reference" in result.errors[0].lower()


def test_missing_target_file_returns_error(tmp_env):
    ref = tmp_env("ref.env", {"KEY": "val"})
    result = validate(ref, "/nonexistent/.env")
    assert not result.is_valid
    assert result.errors
    assert "target" in result.errors[0].lower()


# ---------------------------------------------------------------------------
# ValidationResult dataclass helpers
# ---------------------------------------------------------------------------

def test_validation_result_summary_invalid():
    vr = ValidationResult(
        reference_path=".env.example",
        target_path=".env",
        is_valid=False,
        missing_keys=["SECRET"],
        extra_keys=["JUNK"],
        mismatched_keys=[],
    )
    summary = vr.summary()
    assert "INVALID" in summary
    assert "missing" in summary
    assert "extra" in summary
