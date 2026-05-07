"""Sort keys in a .env file alphabetically or by custom order."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envdiff.parser import parse_env_file


@dataclass
class SortResult:
    path: str
    original_lines: List[str]
    sorted_lines: List[str]
    moved_keys: List[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return self.original_lines != self.sorted_lines


def summary(result: SortResult) -> str:
    if not result.changed:
        return f"{result.path}: already sorted, no changes needed."
    return (
        f"{result.path}: {len(result.moved_keys)} key(s) reordered."
    )


def _key_name(line: str) -> Optional[str]:
    """Return the key name from a KEY=VALUE line, or None for comments/blanks."""
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    if "=" in stripped:
        return stripped.split("=", 1)[0].strip()
    return None


def sort_env(path: str, reverse: bool = False, write: bool = False) -> SortResult:
    """Sort the keys of a .env file alphabetically.

    Args:
        path: Path to the .env file.
        reverse: If True, sort in descending order.
        write: If True, overwrite the file with sorted content.

    Returns:
        SortResult with original and sorted lines.
    """
    p = Path(path)
    original_lines = p.read_text().splitlines(keepends=True)

    # Separate leading comments/blanks from key lines
    header: List[str] = []
    key_lines: List[str] = []
    trailer: List[str] = []

    in_header = True
    for line in original_lines:
        if in_header and (not line.strip() or line.strip().startswith("#")):
            header.append(line)
        else:
            in_header = False
            key_lines.append(line)

    # Pull trailing blank lines into trailer
    while key_lines and not key_lines[-1].strip():
        trailer.insert(0, key_lines.pop())

    sorted_key_lines = sorted(
        key_lines,
        key=lambda l: (_key_name(l) or "").lower(),
        reverse=reverse,
    )

    sorted_lines = header + sorted_key_lines + trailer

    original_keys = [_key_name(l) for l in key_lines if _key_name(l)]
    sorted_keys = [_key_name(l) for l in sorted_key_lines if _key_name(l)]
    moved = [k for i, (k, s) in enumerate(zip(original_keys, sorted_keys)) if k != s]

    result = SortResult(
        path=path,
        original_lines=original_lines,
        sorted_lines=sorted_lines,
        moved_keys=moved,
    )

    if write and result.changed:
        p.write_text("".join(sorted_lines))

    return result
