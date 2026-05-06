"""Watch .env files for changes and report diffs automatically."""

from __future__ import annotations

import time
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional

from envdiff.differ import diff_files
from envdiff.comparator import DiffResult


@dataclass
class WatchEvent:
    """Emitted when a watched file changes."""

    path: str
    diff: DiffResult
    timestamp: float = field(default_factory=time.time)


def _mtime(path: str) -> float:
    """Return the last-modified time of *path*, or 0.0 if missing."""
    try:
        return os.path.getmtime(path)
    except FileNotFoundError:
        return 0.0


def watch(
    base_file: str,
    target_files: List[str],
    callback: Callable[[WatchEvent], None],
    *,
    interval: float = 1.0,
    max_iterations: Optional[int] = None,
    mask_secrets: bool = True,
    ignore_values: bool = False,
) -> None:
    """Poll *target_files* for changes and invoke *callback* on each diff.

    Parameters
    ----------
    base_file:      The reference .env file.
    target_files:   One or more .env files to watch for changes.
    callback:       Called with a :class:`WatchEvent` whenever a file changes.
    interval:       Polling interval in seconds (default 1.0).
    max_iterations: Stop after this many poll cycles (``None`` = run forever).
    mask_secrets:   Forward to :func:`diff_files`.
    ignore_values:  Forward to :func:`diff_files`.
    """
    mtimes: Dict[str, float] = {p: _mtime(p) for p in target_files}
    iterations = 0

    while max_iterations is None or iterations < max_iterations:
        for path in target_files:
            current = _mtime(path)
            if current != mtimes[path]:
                mtimes[path] = current
                result = diff_files(
                    base_file,
                    path,
                    mask_secrets=mask_secrets,
                    ignore_values=ignore_values,
                )
                callback(WatchEvent(path=path, diff=result))
        time.sleep(interval)
        iterations += 1
