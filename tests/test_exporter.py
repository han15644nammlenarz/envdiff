"""Tests for envdiff.exporter module."""

from __future__ import annotations

import csv
import io
import json

import pytest

from envdiff.comparator import DiffResult
from envdiff.exporter import export_csv, export_json, export_markdown


@pytest.fixture()
def clean_result() -> DiffResult:
    return DiffResult(missing=set(), extra=set(), mismatched={})


@pytest.fixture()
def diff_result() -> DiffResult:
    return DiffResult(
        missing={"DB_HOST"},
        extra={"OLD_KEY"},
        mismatched={"APP_ENV": ("production", "staging")},
    )


# --- export_json ---

def test_export_json_no_differences(clean_result: DiffResult) -> None:
    data = json.loads(export_json(clean_result))
    assert data["missing"] == []
    assert data["extra"] == []
    assert data["mismatched"] == {}


def test_export_json_contains_all_sections(diff_result: DiffResult) -> None:
    data = json.loads(export_json(diff_result))
    assert "DB_HOST" in data["missing"]
    assert "OLD_KEY" in data["extra"]
    assert "APP_ENV" in data["mismatched"]
    assert data["mismatched"]["APP_ENV"]["base"] == "production"
    assert data["mismatched"]["APP_ENV"]["compare"] == "staging"


def test_export_json_masks_secrets() -> None:
    result = DiffResult(
        missing=set(),
        extra=set(),
        mismatched={"SECRET_KEY": ("abc123", "xyz789")},
    )
    data = json.loads(export_json(result, mask_secrets=True))
    assert data["mismatched"]["SECRET_KEY"]["base"] != "abc123"
    assert data["mismatched"]["SECRET_KEY"]["compare"] != "xyz789"


# --- export_csv ---

def test_export_csv_headers(clean_result: DiffResult) -> None:
    output = export_csv(clean_result)
    reader = csv.reader(io.StringIO(output))
    headers = next(reader)
    assert headers == ["category", "key", "base_value", "compare_value"]


def test_export_csv_rows(diff_result: DiffResult) -> None:
    output = export_csv(diff_result)
    reader = csv.DictReader(io.StringIO(output))
    rows = list(reader)
    categories = {r["category"] for r in rows}
    keys = {r["key"] for r in rows}
    assert "missing" in categories
    assert "extra" in categories
    assert "mismatched" in categories
    assert "DB_HOST" in keys
    assert "OLD_KEY" in keys
    assert "APP_ENV" in keys


def test_export_csv_masks_secrets() -> None:
    result = DiffResult(
        missing=set(),
        extra=set(),
        mismatched={"API_KEY": ("real", "other")},
    )
    output = export_csv(result, mask_secrets=True)
    assert "real" not in output
    assert "other" not in output


# --- export_markdown ---

def test_export_markdown_contains_sections(diff_result: DiffResult) -> None:
    md = export_markdown(diff_result)
    assert "## Missing Keys" in md
    assert "## Extra Keys" in md
    assert "## Mismatched Values" in md


def test_export_markdown_lists_keys(diff_result: DiffResult) -> None:
    md = export_markdown(diff_result)
    assert "`DB_HOST`" in md
    assert "`OLD_KEY`" in md
    assert "`APP_ENV`" in md


def test_export_markdown_none_when_empty(clean_result: DiffResult) -> None:
    md = export_markdown(clean_result)
    assert md.count("_None_") == 3


def test_export_markdown_masks_secrets() -> None:
    result = DiffResult(
        missing=set(),
        extra=set(),
        mismatched={"DB_PASSWORD": ("secret", "other")},
    )
    md = export_markdown(result, mask_secrets=True)
    assert "secret" not in md
    assert "other" not in md
