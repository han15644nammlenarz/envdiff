"""Tests for envdiff.comparator."""

import pytest
from envdiff.comparator import compare, DiffResult, _is_secret


BASE = {
    "APP_NAME": "myapp",
    "DEBUG": "true",
    "DB_HOST": "localhost",
    "DB_PASSWORD": "secret123",
    "API_KEY": "abc",
}

TARGET = {
    "APP_NAME": "myapp",
    "DEBUG": "false",
    "DB_HOST": "prod.db",
    "DB_PASSWORD": "hunter2",
    "EXTRA_KEY": "extra",
}


def test_missing_keys():
    result = compare(BASE, TARGET)
    assert "API_KEY" in result.missing_keys


def test_extra_keys():
    result = compare(BASE, TARGET)
    assert "EXTRA_KEY" in result.extra_keys


def test_mismatched_values():
    result = compare(BASE, TARGET)
    assert "DEBUG" in result.mismatched_keys
    assert result.mismatched_keys["DEBUG"] == ("true", "false")


def test_no_differences_identical():
    result = compare(BASE, BASE, base_name="a", target_name="b")
    assert not result.has_differences


def test_ignore_values_skips_mismatch():
    result = compare(BASE, TARGET, ignore_values=True)
    assert not result.mismatched_keys
    assert "API_KEY" in result.missing_keys


def test_mask_secrets_replaces_values():
    result = compare(BASE, TARGET, mask_secrets=True)
    assert "DB_PASSWORD" in result.mismatched_keys
    base_val, target_val = result.mismatched_keys["DB_PASSWORD"]
    assert base_val == "***"
    assert target_val == "***"


def test_mask_secrets_non_secret_unchanged():
    result = compare(BASE, TARGET, mask_secrets=True)
    assert result.mismatched_keys["DEBUG"] == ("true", "false")


def test_summary_no_differences():
    result = compare(BASE, BASE)
    assert "No differences found" in result.summary()


def test_summary_contains_sections():
    result = compare(BASE, TARGET)
    summary = result.summary()
    assert "Missing keys" in summary
    assert "Extra keys" in summary
    assert "Mismatched values" in summary


def test_is_secret_detects_keywords():
    assert _is_secret("DB_PASSWORD", ["password"])
    assert _is_secret("API_TOKEN", ["token"])
    assert not _is_secret("APP_NAME", ["password", "token"])


def test_custom_secret_keywords():
    result = compare(
        {"CUSTOM_HIDDEN": "val1"},
        {"CUSTOM_HIDDEN": "val2"},
        mask_secrets=True,
        secret_keywords=["hidden"],
    )
    assert result.mismatched_keys["CUSTOM_HIDDEN"] == ("***", "***")
