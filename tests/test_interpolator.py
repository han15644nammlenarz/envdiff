"""Tests for envdiff.interpolator."""
import pytest
from envdiff.interpolator import interpolate, _extract_refs, InterpolationResult


def test_returns_interpolation_result():
    result = interpolate({"FOO": "bar"})
    assert isinstance(result, InterpolationResult)


def test_plain_values_pass_through():
    env = {"A": "hello", "B": "world"}
    result = interpolate(env)
    assert result.resolved["A"] == "hello"
    assert result.resolved["B"] == "world"
    assert not result.unresolved


def test_simple_reference_resolved():
    env = {"BASE": "/app", "DATA": "${BASE}/data"}
    result = interpolate(env)
    assert result.resolved["DATA"] == "/app/data"


def test_bare_dollar_reference_resolved():
    env = {"HOST": "localhost", "URL": "http://$HOST:8080"}
    result = interpolate(env)
    assert result.resolved["URL"] == "http://localhost:8080"


def test_chained_references_resolved():
    env = {"A": "foo", "B": "${A}_bar", "C": "${B}_baz"}
    result = interpolate(env)
    assert result.resolved["C"] == "foo_bar_baz"


def test_missing_reference_reported():
    env = {"KEY": "${MISSING_VAR}"}
    result = interpolate(env)
    assert "KEY" in result.unresolved
    assert "MISSING_VAR" in result.unresolved["KEY"]


def test_references_map_populated():
    env = {"BASE": "/x", "FULL": "${BASE}/y"}
    result = interpolate(env)
    assert "FULL" in result.references
    assert "BASE" in result.references["FULL"]


def test_no_references_empty_references_map():
    env = {"A": "1", "B": "2"}
    result = interpolate(env)
    assert result.references == {}


def test_extract_refs_curly():
    assert _extract_refs("${FOO} and ${BAR}") == ["FOO", "BAR"]


def test_extract_refs_bare():
    assert _extract_refs("$FOO/$BAR") == ["FOO", "BAR"]


def test_extract_refs_empty():
    assert _extract_refs("no refs here") == []


def test_summary_all_resolved():
    result = interpolate({"A": "hello"})
    assert "resolved successfully" in result.summary()


def test_summary_with_unresolved():
    result = interpolate({"A": "${GHOST}"})
    assert "Unresolved" in result.summary()
    assert "A" in result.summary()


def test_multiple_refs_in_one_value():
    env = {"H": "host", "P": "8080", "ADDR": "${H}:${P}"}
    result = interpolate(env)
    assert result.resolved["ADDR"] == "host:8080"
    assert len(result.references["ADDR"]) == 2
