"""Tests for envdiff.watcher."""

from __future__ import annotations

import time
from pathlib import Path
from typing import List

import pytest

from envdiff.watcher import WatchEvent, watch, _mtime


@pytest.fixture()
def tmp_env(tmp_path: Path):
    """Return a helper that writes an .env file and returns its path."""

    def _write(name: str, content: str) -> str:
        p = tmp_path / name
        p.write_text(content)
        return str(p)

    return _write


def _collect(
    base: str,
    targets: list,
    *,
    iterations: int = 3,
    interval: float = 0.01,
    **kwargs,
) -> List[WatchEvent]:
    events: List[WatchEvent] = []
    watch(
        base,
        targets,
        events.append,
        interval=interval,
        max_iterations=iterations,
        **kwargs,
    )
    return events


def test_no_change_no_events(tmp_env):
    base = tmp_env("base.env", "KEY=value\n")
    target = tmp_env("target.env", "KEY=value\n")
    events = _collect(base, [target])
    assert events == []


def test_event_emitted_on_file_change(tmp_env):
    base = tmp_env("base.env", "KEY=value\n")
    target = tmp_env("target.env", "KEY=value\n")

    events: List[WatchEvent] = []

    def callback(evt: WatchEvent) -> None:
        events.append(evt)

    # Modify the target between iterations using a thread-free trick:
    # run one iteration to record initial mtime, then mutate, then run more.
    watch(base, [target], callback, interval=0.01, max_iterations=1)
    Path(target).write_text("KEY=changed\n")
    watch(base, [target], callback, interval=0.01, max_iterations=1)

    assert len(events) == 1
    assert events[0].path == target


def test_event_diff_contains_mismatch(tmp_env):
    base = tmp_env("base.env", "KEY=original\n")
    target = tmp_env("target.env", "KEY=original\n")

    events: List[WatchEvent] = []
    watch(base, [target], events.append, interval=0.01, max_iterations=1)
    Path(target).write_text("KEY=different\n")
    watch(base, [target], events.append, interval=0.01, max_iterations=1)

    assert events
    diff = events[0].diff
    assert "KEY" in diff.mismatched


def test_missing_file_returns_zero_mtime(tmp_path):
    assert _mtime(str(tmp_path / "nonexistent.env")) == 0.0


def test_watch_event_has_timestamp(tmp_env):
    base = tmp_env("base.env", "A=1\n")
    target = tmp_env("target.env", "A=1\n")

    events: List[WatchEvent] = []
    watch(base, [target], events.append, interval=0.01, max_iterations=1)
    Path(target).write_text("A=2\n")
    before = time.time()
    watch(base, [target], events.append, interval=0.01, max_iterations=1)
    after = time.time()

    assert events
    assert before <= events[0].timestamp <= after + 0.1


def test_multiple_targets_independent(tmp_env):
    base = tmp_env("base.env", "X=1\nY=2\n")
    t1 = tmp_env("t1.env", "X=1\nY=2\n")
    t2 = tmp_env("t2.env", "X=1\nY=2\n")

    events: List[WatchEvent] = []
    watch(base, [t1, t2], events.append, interval=0.01, max_iterations=1)
    Path(t2).write_text("X=1\n")
    watch(base, [t1, t2], events.append, interval=0.01, max_iterations=1)

    assert len(events) == 1
    assert events[0].path == t2
