"""Tests for envdiff.scorer."""

import os
import pytest

from envdiff.scorer import score, ScoreResult


@pytest.fixture
def tmp_env(tmp_path):
    return tmp_path


def _write(path, content: str):
    path.write_text(content)
    return str(path)


def test_returns_score_result(tmp_env):
    f = _write(tmp_env / ".env", "APP_NAME=myapp\nDEBUG=true\n")
    result = score(f)
    assert isinstance(result, ScoreResult)


def test_max_score_is_100(tmp_env):
    f = _write(tmp_env / ".env", "APP_NAME=myapp\n")
    result = score(f)
    assert result.max_score == 100


def test_clean_file_scores_high(tmp_env):
    content = "APP_NAME=myapp\nDEBUG=false\nPORT=8080\n"
    f = _write(tmp_env / ".env", content)
    result = score(f)
    # No secrets, no lint errors — should score at least 70
    assert result.total_score >= 70


def test_grade_a_for_perfect_file(tmp_env):
    f = _write(tmp_env / ".env", "APP_NAME=myapp\nPORT=8080\n")
    result = score(f)
    # No secrets, no lint issues, no reference → 40 + 30 + 30 = 100
    assert result.grade == "A"
    assert result.total_score == 100


def test_lint_errors_reduce_score(tmp_env):
    # Missing equals sign triggers a lint error
    f = _write(tmp_env / ".env", "BADLINE\nAPP=ok\n")
    result = score(f)
    assert result.lint_score < 40
    assert any("lint error" in w for w in result.warnings)


def test_secret_with_value_warns(tmp_env):
    f = _write(tmp_env / ".env", "API_KEY=supersecret\n")
    result = score(f)
    assert any("secret" in w.lower() for w in result.warnings)


def test_secret_blanked_no_penalty(tmp_env):
    f = _write(tmp_env / ".env", "API_KEY=\n")
    result = score(f)
    assert result.secret_score == 30


def test_coverage_score_with_matching_reference(tmp_env):
    ref = _write(tmp_env / ".env.ref", "APP=x\nPORT=y\n")
    live = _write(tmp_env / ".env", "APP=hello\nPORT=9000\n")
    result = score(live, reference_path=ref)
    assert result.coverage_score == 30


def test_coverage_score_penalised_for_missing_keys(tmp_env):
    ref = _write(tmp_env / ".env.ref", "APP=x\nPORT=y\nDB_URL=z\n")
    live = _write(tmp_env / ".env", "APP=hello\n")
    result = score(live, reference_path=ref)
    assert result.coverage_score < 30
    assert any("missing" in w for w in result.warnings)


def test_summary_contains_grade(tmp_env):
    f = _write(tmp_env / ".env", "APP=ok\n")
    result = score(f)
    summary = result.summary()
    assert "Grade" in summary
    assert result.grade in summary


def test_summary_lists_warnings(tmp_env):
    f = _write(tmp_env / ".env", "BADLINE\nAPI_KEY=secret\n")
    result = score(f)
    summary = result.summary()
    assert "Warnings" in summary
