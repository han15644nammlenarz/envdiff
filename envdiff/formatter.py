"""Formats .env file contents with consistent style rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from envdiff.parser import parse_env_file


@dataclass
class FormatResult:
    path: str
    original_lines: List[str]
    formatted_lines: List[str]
    changes: int = 0

    @property
    def changed(self) -> bool:
        return self.changes > 0


def summary(result: FormatResult) -> str:
    if not result.changed:
        return f"{result.path}: already formatted (no changes)"
    return f"{result.path}: {result.changes} line(s) reformatted"


def _format_line(line: str) -> str:
    """Apply formatting rules to a single line."""
    stripped = line.rstrip("\n").rstrip()
    # Skip comments and blank lines
    if not stripped or stripped.startswith("#"):
        return stripped
    if "=" not in stripped:
        return stripped
    key, _, value = stripped.partition("=")
    key = key.strip()
    value = value.strip()
    # Ensure no spaces around the '='
    return f"{key}={value}"


def format_env(path: str, sort_keys: bool = False) -> FormatResult:
    """Read an .env file and return a FormatResult with normalised lines."""
    src = Path(path)
    raw = src.read_text(encoding="utf-8")
    original_lines = raw.splitlines()

    formatted: List[str] = [_format_line(ln) for ln in original_lines]

    if sort_keys:
        def _sort_key(ln: str) -> str:
            if not ln or ln.startswith("#"):
                return "\x00"  # blanks/comments float to top
            return ln.split("=", 1)[0].lower()

        formatted = sorted(formatted, key=_sort_key)

    changes = sum(1 for a, b in zip(original_lines, formatted) if a != b)
    changes += abs(len(formatted) - len(original_lines))

    return FormatResult(
        path=path,
        original_lines=original_lines,
        formatted_lines=formatted,
        changes=changes,
    )


def write_formatted(result: FormatResult) -> None:
    """Overwrite the source file with the formatted content."""
    content = "\n".join(result.formatted_lines)
    if content and not content.endswith("\n"):
        content += "\n"
    Path(result.path).write_text(content, encoding="utf-8")
