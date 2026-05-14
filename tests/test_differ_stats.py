"""Tests for envdiff.differ_stats."""
import pytest

from envdiff.comparator import DiffResult
from envdiff.differ_stats import DiffStats, compute_stats


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _result(
    missing=None,
    extra=None,
    mismatched=None,
) -> DiffResult:
    return DiffResult(
        missing=missing or [],
        extra=extra or [],
        mismatched=mismatched or [],
    )


# ---------------------------------------------------------------------------
# compute_stats
# ---------------------------------------------------------------------------

def test_returns_diff_stats_instance():
    stats = compute_stats([_result()])
    assert isinstance(stats, DiffStats)


def test_empty_results_list():
    stats = compute_stats([])
    assert stats.total_compared == 0
    assert stats.total_issues == 0
    assert stats.health_ratio == 1.0


def test_single_clean_result():
    stats = compute_stats([_result()])
    assert stats.total_clean == 1
    assert stats.total_compared == 1
    assert stats.files_with_differences == []


def test_missing_keys_counted():
    stats = compute_stats([_result(missing=["FOO", "BAR"])])
    assert stats.total_missing == 2


def test_extra_keys_counted():
    stats = compute_stats([_result(extra=["EXTRA"])])
    assert stats.total_extra == 1


def test_mismatched_keys_counted():
    stats = compute_stats([_result(mismatched=[("KEY", "a", "b")])])
    assert stats.total_mismatched == 1


def test_files_with_differences_populated():
    results = [_result(missing=["X"]), _result()]
    labels = ["prod.env", "staging.env"]
    stats = compute_stats(results, labels=labels)
    assert "prod.env" in stats.files_with_differences
    assert "staging.env" not in stats.files_with_differences


def test_labels_default_to_index():
    stats = compute_stats([_result(extra=["Y"])])
    assert "0" in stats.files_with_differences


def test_health_ratio_all_clean():
    stats = compute_stats([_result(), _result()])
    assert stats.health_ratio == 1.0


def test_health_ratio_partial():
    stats = compute_stats([_result(missing=["A"]), _result()])
    assert stats.health_ratio == pytest.approx(0.5)


def test_total_issues_sum():
    r = _result(missing=["A"], extra=["B"], mismatched=[("C", "x", "y")])
    stats = compute_stats([r])
    assert stats.total_issues == 3


def test_summary_contains_health():
    stats = compute_stats([_result()])
    assert "health=" in stats.summary()


def test_to_dict_keys():
    stats = compute_stats([_result()])
    d = stats.to_dict()
    for key in ("total_compared", "total_clean", "total_missing",
                "total_extra", "total_mismatched", "total_issues",
                "health_ratio", "files_with_differences"):
        assert key in d


def test_labels_length_mismatch_raises():
    with pytest.raises(ValueError):
        compute_stats([_result(), _result()], labels=["only_one"])
