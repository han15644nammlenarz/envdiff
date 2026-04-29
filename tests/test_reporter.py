"""Tests for envdiff.reporter."""

import pytest

from envdiff.comparator import DiffResult
from envdiff.reporter import format_json, format_text


@pytest.fixture()
def clean_result() -> DiffResult:
    return DiffResult(
        missing_keys=set(),
        extra_keys=set(),
        mismatched_keys=set(),
        base_values={"KEY": "val"},
        target_values={"KEY": "val"},
    )


@pytest.fixture()
def diff_result() -> DiffResult:
    return DiffResult(
        missing_keys={"MISSING"},
        extra_keys={"EXTRA"},
        mismatched_keys={"CHANGED"},
        base_values={"MISSING": "old", "CHANGED": "before"},
        target_values={"EXTRA": "new", "CHANGED": "after"},
    )


def test_format_text_no_differences(clean_result):
    output = format_text(clean_result)
    assert "No differences found." in output


def test_format_text_missing_keys(diff_result):
    output = format_text(diff_result)
    assert "Missing in target" in output
    assert "MISSING" in output


def test_format_text_extra_keys(diff_result):
    output = format_text(diff_result)
    assert "Extra in target" in output
    assert "EXTRA" in output


def test_format_text_mismatched_keys(diff_result):
    output = format_text(diff_result)
    assert "Mismatched values:" in output
    assert "CHANGED" in output
    assert "before" in output
    assert "after" in output


def test_format_text_custom_labels(diff_result):
    output = format_text(diff_result, base_label="prod", target_label="staging")
    assert "prod" in output
    assert "staging" in output


def test_format_text_mask_secrets():
    result = DiffResult(
        missing_keys=set(),
        extra_keys=set(),
        mismatched_keys={"DB_PASSWORD"},
        base_values={"DB_PASSWORD": "secret123"},
        target_values={"DB_PASSWORD": "other_secret"},
    )
    output = format_text(result, mask_secrets=True)
    assert "secret123" not in output
    assert "other_secret" not in output
    assert "DB_PASSWORD" in output


def test_format_json_structure(diff_result):
    data = format_json(diff_result)
    assert "missing" in data
    assert "extra" in data
    assert "mismatched" in data
    assert "has_differences" in data
    assert data["has_differences"] is True


def test_format_json_no_differences(clean_result):
    data = format_json(clean_result)
    assert data["missing"] == []
    assert data["extra"] == []
    assert data["mismatched"] == []
    assert data["has_differences"] is False


def test_format_json_mask_secrets():
    result = DiffResult(
        missing_keys=set(),
        extra_keys=set(),
        mismatched_keys={"API_TOKEN"},
        base_values={"API_TOKEN": "tok_abc"},
        target_values={"API_TOKEN": "tok_xyz"},
    )
    data = format_json(result, mask_secrets=True)
    mismatch = data["mismatched"][0]
    assert mismatch["base"] != "tok_abc"
    assert mismatch["target"] != "tok_xyz"
