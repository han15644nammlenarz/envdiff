"""Rename keys across .env files, producing updated content and a rename report."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from envdiff.parser import parse_env_file


@dataclass
class RenameResult:
    """Result of a rename operation on a single file."""

    path: str
    applied: Dict[str, str] = field(default_factory=dict)   # old_key -> new_key
    skipped: List[str] = field(default_factory=list)        # old keys not found
    lines: List[str] = field(default_factory=list)          # updated file lines

    def summary(self) -> str:
        parts = [f"File: {self.path}"]
        if self.applied:
            parts.append("  Renamed:")
            for old, new in self.applied.items():
                parts.append(f"    {old} -> {new}")
        if self.skipped:
            parts.append("  Not found (skipped): " + ", ".join(self.skipped))
        if not self.applied and not self.skipped:
            parts.append("  No changes.")
        return "\n".join(parts)


def rename(
    path: str,
    renames: Dict[str, str],
    write: bool = False,
) -> RenameResult:
    """Rename keys in *path* according to *renames* mapping {old: new}.

    Args:
        path:    Path to the .env file.
        renames: Mapping of old key names to new key names.
        write:   If True, overwrite the file with renamed content.

    Returns:
        A :class:`RenameResult` describing what was changed.
    """
    file_path = Path(path)
    raw_lines: List[str] = file_path.read_text().splitlines(keepends=True)

    existing_keys = set(parse_env_file(path).keys())
    applied: Dict[str, str] = {}
    skipped: List[str] = []

    updated_lines: List[str] = []
    for line in raw_lines:
        stripped = line.lstrip()
        matched = False
        for old_key, new_key in renames.items():
            if stripped.startswith(old_key + "=") or stripped.startswith(old_key + " "):
                line = line.replace(old_key, new_key, 1)
                applied[old_key] = new_key
                matched = True
                break
        updated_lines.append(line)

    for old_key in renames:
        if old_key not in applied and old_key not in existing_keys:
            skipped.append(old_key)

    result = RenameResult(
        path=str(path),
        applied=applied,
        skipped=skipped,
        lines=updated_lines,
    )

    if write and applied:
        file_path.write_text("".join(updated_lines))

    return result
