"""Tests for envdiff.linter."""

import pytest
from pathlib import Path

from envdiff.linter import lint_file, LintIssue, LintResult


@pytest.fixture
def tmp_env(tmp_path):
    def _write(name: str, content: str) -> str:
        p = tmp_path / name
        p.write_text(content, encoding="utf-8")
        return str(p)
    return _write


def test_clean_file_no_issues(tmp_env):
    path = tmp_env(".env", "HOST=localhost\nPORT=5432\nDEBUG=false\n")
    result = lint_file(path)
    assert not result.has_issues


def test_lowercase_key_warning(tmp_env):
    path = tmp_env(".env", "host=localhost\n")
    result = lint_file(path)
    assert result.has_issues
    assert any("uppercase" in i.message for i in result.warnings)


def test_missing_equals_error(tmp_env):
    path = tmp_env(".env", "BADLINE\n")
    result = lint_file(path)
    assert any(i.severity == "error" and "no '='" in i.message for i in result.issues)


def test_empty_key_error(tmp_env):
    path = tmp_env(".env", "=value\n")
    result = lint_file(path)
    assert any(i.severity == "error" and "empty key" in i.message for i in result.issues)


def test_duplicate_key_error(tmp_env):
    path = tmp_env(".env", "HOST=a\nHOST=b\n")
    result = lint_file(path)
    errors = [i for i in result.issues if "duplicate" in i.message]
    assert len(errors) == 1
    assert errors[0].severity == "error"


def test_whitespace_in_key_error(tmp_env):
    path = tmp_env(".env", "MY KEY=value\n")
    result = lint_file(path)
    assert any("whitespace" in i.message and i.severity == "error" for i in result.issues)


def test_value_trailing_whitespace_warning(tmp_env):
    path = tmp_env(".env", "HOST=localhost  \n")
    result = lint_file(path)
    assert any("trailing" in i.message for i in result.warnings)


def test_comments_and_blanks_ignored(tmp_env):
    path = tmp_env(".env", "# comment\n\nHOST=localhost\n")
    result = lint_file(path)
    assert not result.has_issues


def test_summary_no_issues(tmp_env):
    path = tmp_env(".env", "HOST=localhost\n")
    result = lint_file(path)
    assert "no lint issues" in result.summary()


def test_summary_with_issues(tmp_env):
    path = tmp_env(".env", "host=bad\nHOST=good\nHOST=dup\n")
    result = lint_file(path)
    summary = result.summary()
    assert "error" in summary or "warning" in summary


def test_lint_issue_str():
    issue = LintIssue(line_number=3, key="MY_KEY", message="test msg", severity="warning")
    text = str(issue)
    assert "WARNING" in text
    assert "MY_KEY" in text
    assert "3" in text


def test_lint_issue_str_error_severity():
    """Ensure LintIssue.__str__ correctly uppercases the 'error' severity label."""
    issue = LintIssue(line_number=1, key="BAD_KEY", message="something wrong", severity="error")
    text = str(issue)
    assert "ERROR" in text
    assert "BAD_KEY" in text
    assert "1" in text
