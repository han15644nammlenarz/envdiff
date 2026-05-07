"""Tests for envdiff.annotator."""
from __future__ import annotations

import pytest
from pathlib import Path

from envdiff.annotator import annotate, AnnotatedLine, AnnotationResult
from envdiff.comparator import DiffResult


@pytest.fixture()
def tmp_env(tmp_path: Path):
    def _write(name: str, content: str) -> Path:
        p = tmp_path / name
        p.write_text(content)
        return p
    return _write


def _make_diff(
    missing=None, extra=None, mismatched=None
) -> DiffResult:
    return DiffResult(
        missing_keys=missing or [],
        extra_keys=extra or [],
        mismatched_keys=mismatched or {},
    )


def test_returns_annotation_result(tmp_env):
    p = tmp_env("a.env", "KEY=value\n")
    diff = _make_diff()
    result = annotate(str(p), diff)
    assert isinstance(result, AnnotationResult)


def test_clean_file_no_annotations(tmp_env):
    p = tmp_env("a.env", "KEY=value\nFOO=bar\n")
    diff = _make_diff()
    result = annotate(str(p), diff)
    assert result.annotated_count == 0
    assert "[" not in result.render()


def test_missing_key_annotated(tmp_env):
    p = tmp_env("a.env", "KEY=value\n")
    diff = _make_diff(missing=["KEY"])
    result = annotate(str(p), diff)
    assert result.annotated_count == 1
    assert "MISSING" in result.render()


def test_extra_key_annotated(tmp_env):
    p = tmp_env("a.env", "EXTRA_KEY=oops\n")
    diff = _make_diff(extra=["EXTRA_KEY"])
    result = annotate(str(p), diff)
    assert "EXTRA" in result.render()
    assert result.annotated_count == 1


def test_mismatched_key_annotated(tmp_env):
    p = tmp_env("a.env", "DB_HOST=prod.db\n")
    diff = _make_diff(
        mismatched={"DB_HOST": {"reference": "localhost", "target": "prod.db"}}
    )
    result = annotate(str(p), diff)
    assert "MISMATCH" in result.render()
    assert "localhost" in result.render()


def test_secret_value_masked_in_mismatch(tmp_env):
    p = tmp_env("a.env", "SECRET_TOKEN=abc123\n")
    diff = _make_diff(
        mismatched={"SECRET_TOKEN": {"reference": "ref-secret", "target": "abc123"}}
    )
    result = annotate(str(p), diff, mask_secrets=True)
    rendered = result.render()
    assert "ref-secret" not in rendered
    assert "***" in rendered


def test_comments_and_blank_lines_preserved(tmp_env):
    content = "# a comment\n\nKEY=value\n"
    p = tmp_env("a.env", content)
    diff = _make_diff()
    result = annotate(str(p), diff)
    rendered = result.render()
    assert "# a comment" in rendered


def test_summary_message(tmp_env):
    p = tmp_env("a.env", "KEY=value\n")
    diff = _make_diff(missing=["KEY"])
    result = annotate(str(p), diff)
    assert "1" in result.summary()
    assert "annotated" in result.summary()


def test_annotated_line_render_without_annotation():
    line = AnnotatedLine(original="KEY=val")
    assert line.render() == "KEY=val"


def test_annotated_line_render_with_annotation():
    line = AnnotatedLine(original="KEY=val", annotation="MISSING")
    assert line.render() == "KEY=val  # [MISSING]"
