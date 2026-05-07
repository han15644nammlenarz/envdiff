"""Normalizes .env file content: sorts keys, strips trailing whitespace,
and enforces consistent quoting style."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envdiff.parser import parse_env_file


@dataclass
class NormalizeResult:
    path: str
    original_lines: List[str]
    normalized_lines: List[str]
    changes: int

    def summary(self) -> str:
        if self.changes == 0:
            return f"{self.path}: already normalized (no changes)"
        return f"{self.path}: {self.changes} line(s) normalized"


def summary(result: NormalizeResult) -> str:
    return result.summary()


def _normalize_line(line: str) -> Optional[str]:
    """Return a normalized version of a key=value line, or None if not applicable."""
    stripped = line.rstrip()
    if not stripped or stripped.startswith("#"):
        return stripped

    if "=" not in stripped:
        return stripped

    key, _, value = stripped.partition("=")
    key = key.strip()
    value = value.strip()

    # Remove surrounding quotes for normalization, then re-apply only if needed
    if len(value) >= 2 and value[0] in ('"', "'") and value[-1] == value[0]:
        inner = value[1:-1]
    else:
        inner = value

    # Re-quote with double quotes if value contains spaces or special chars
    if " " in inner or "#" in inner or not inner:
        normalized_value = f'"{inner}"'
    else:
        normalized_value = inner

    return f"{key}={normalized_value}"


def normalize(
    path: str,
    sort_keys: bool = True,
    write: bool = False,
) -> NormalizeResult:
    """Normalize a .env file.

    Args:
        path: Path to the .env file.
        sort_keys: Whether to sort keys alphabetically.
        write: If True, overwrite the file with normalized content.

    Returns:
        NormalizeResult with original and normalized lines.
    """
    p = Path(path)
    original_lines = p.read_text().splitlines()

    normalized: List[str] = []
    kv_lines: List[str] = []
    header: List[str] = []
    collecting_kv = False

    for line in original_lines:
        norm = _normalize_line(line)
        if norm is not None and "=" in (norm or "") and not (norm or "").startswith("#"):
            kv_lines.append(norm)
            collecting_kv = True
        else:
            if not collecting_kv:
                header.append(norm if norm is not None else "")
            else:
                kv_lines.append(norm if norm is not None else "")

    if sort_keys:
        def _sort_key(ln: str) -> str:
            if not ln or ln.startswith("#") or "=" not in ln:
                return "\xff" + ln
            return ln.split("=", 1)[0].upper()

        kv_lines.sort(key=_sort_key)

    normalized = header + kv_lines

    changes = sum(1 for a, b in zip(original_lines, normalized) if a != b)
    changes += abs(len(original_lines) - len(normalized))

    if write:
        p.write_text("\n".join(normalized) + "\n")

    return NormalizeResult(
        path=path,
        original_lines=original_lines,
        normalized_lines=normalized,
        changes=changes,
    )
