"""Detect and remove duplicate keys within a .env file."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass
class DeduplicateResult:
    path: str
    duplicates: Dict[str, List[int]]  # key -> list of line numbers (1-based)
    kept_lines: List[str]             # lines after deduplication (last wins)
    original_line_count: int

    def summary(self) -> str:
        if not self.duplicates:
            return f"{self.path}: no duplicate keys found."
        parts = [f"{self.path}: {len(self.duplicates)} duplicate key(s) found."]
        for key, lines in self.duplicates.items():
            parts.append(f"  {key}: defined on lines {lines}, kept last occurrence")
        return "\n".join(parts)

    @property
    def has_duplicates(self) -> bool:
        return bool(self.duplicates)


def deduplicate(path: str | Path, write: bool = False) -> DeduplicateResult:
    """Scan *path* for duplicate keys.

    If *write* is True the file is rewritten keeping only the last
    occurrence of each key (comments and blank lines are preserved).
    """
    p = Path(path)
    raw_lines: List[str] = p.read_text(encoding="utf-8").splitlines(keepends=True)

    # First pass: collect all (key, line_index) pairs
    key_occurrences: Dict[str, List[int]] = {}  # key -> [0-based indices]
    for idx, line in enumerate(raw_lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key = stripped.split("=", 1)[0].strip()
        key_occurrences.setdefault(key, []).append(idx)

    duplicates: Dict[str, List[int]] = {
        k: [i + 1 for i in idxs]  # convert to 1-based
        for k, idxs in key_occurrences.items()
        if len(idxs) > 1
    }

    # Build kept_lines: drop all but the last occurrence of each duplicate key
    indices_to_drop = set()
    for key, idxs in key_occurrences.items():
        if len(idxs) > 1:
            # drop all but the last
            for idx in idxs[:-1]:
                indices_to_drop.add(idx)

    kept_lines = [
        line for idx, line in enumerate(raw_lines)
        if idx not in indices_to_drop
    ]

    if write and duplicates:
        p.write_text("".join(kept_lines), encoding="utf-8")

    return DeduplicateResult(
        path=str(p),
        duplicates=duplicates,
        kept_lines=kept_lines,
        original_line_count=len(raw_lines),
    )
