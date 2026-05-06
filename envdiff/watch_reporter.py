"""Format and print :class:`WatchEvent` objects to the terminal."""

from __future__ import annotations

import json
from datetime import datetime
from typing import TextIO
import sys

from envdiff.watcher import WatchEvent
from envdiff.reporter import format_text, format_json


def _timestamp(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def print_text_event(event: WatchEvent, *, stream: TextIO = sys.stdout) -> None:
    """Print a human-readable summary of *event* to *stream*."""
    header = f"[{_timestamp(event.timestamp)}] Change detected: {event.path}"
    stream.write(header + "\n")
    stream.write("-" * len(header) + "\n")
    stream.write(format_text(event.diff))
    stream.write("\n")


def print_json_event(event: WatchEvent, *, stream: TextIO = sys.stdout) -> None:
    """Print a JSON representation of *event* to *stream*."""
    payload = json.loads(format_json(event.diff))
    payload["watched_file"] = event.path
    payload["timestamp"] = _timestamp(event.timestamp)
    stream.write(json.dumps(payload, indent=2) + "\n")


def make_callback(
    fmt: str = "text",
    *,
    stream: TextIO = sys.stdout,
):
    """Return a callback suitable for :func:`~envdiff.watcher.watch`.

    Parameters
    ----------
    fmt:    ``'text'`` or ``'json'``.
    stream: Output stream (default :data:`sys.stdout`).
    """
    if fmt == "json":
        return lambda evt: print_json_event(evt, stream=stream)
    return lambda evt: print_text_event(evt, stream=stream)
