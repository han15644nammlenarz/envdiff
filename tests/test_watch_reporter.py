"""Tests for envdiff.watch_reporter."""

from __future__ import annotations

import io
import json
import time

import pytest

from envdiff.comparator import DiffResult
from envdiff.watcher import WatchEvent
from envdiff.watch_reporter import print_text_event, print_json_event, make_callback


@pytest.fixture()
def clean_event() -> WatchEvent:
    return WatchEvent(
        path="/app/.env.staging",
        diff=DiffResult(missing={}, extra={}, mismatched={}),
        timestamp=1_700_000_000.0,
    )


@pytest.fixture()
def diff_event() -> WatchEvent:
    return WatchEvent(
        path="/app/.env.prod",
        diff=DiffResult(
            missing={"DB_HOST": "localhost"},
            extra={"EXTRA_KEY": "val"},
            mismatched={"SECRET": ("abc", "xyz")},
        ),
        timestamp=1_700_000_000.0,
    )


def test_print_text_event_contains_path(clean_event):
    buf = io.StringIO()
    print_text_event(clean_event, stream=buf)
    assert "/app/.env.staging" in buf.getvalue()


def test_print_text_event_contains_timestamp(clean_event):
    buf = io.StringIO()
    print_text_event(clean_event, stream=buf)
    assert "2023" in buf.getvalue()


def test_print_text_event_shows_missing(diff_event):
    buf = io.StringIO()
    print_text_event(diff_event, stream=buf)
    assert "DB_HOST" in buf.getvalue()


def test_print_json_event_is_valid_json(diff_event):
    buf = io.StringIO()
    print_json_event(diff_event, stream=buf)
    data = json.loads(buf.getvalue())
    assert isinstance(data, dict)


def test_print_json_event_contains_watched_file(diff_event):
    buf = io.StringIO()
    print_json_event(diff_event, stream=buf)
    data = json.loads(buf.getvalue())
    assert data["watched_file"] == "/app/.env.prod"


def test_print_json_event_contains_timestamp(diff_event):
    buf = io.StringIO()
    print_json_event(diff_event, stream=buf)
    data = json.loads(buf.getvalue())
    assert "timestamp" in data


def test_make_callback_text_returns_callable(clean_event):
    cb = make_callback("text", stream=io.StringIO())
    assert callable(cb)
    cb(clean_event)  # should not raise


def test_make_callback_json_returns_callable(diff_event):
    buf = io.StringIO()
    cb = make_callback("json", stream=buf)
    cb(diff_event)
    data = json.loads(buf.getvalue())
    assert "missing" in data


def test_make_callback_default_is_text(clean_event):
    buf = io.StringIO()
    cb = make_callback(stream=buf)
    cb(clean_event)
    output = buf.getvalue()
    assert "Change detected" in output
