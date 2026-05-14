"""Aliaser: rename keys in a .env file using an alias mapping.

Given a mapping of {old_key: new_key}, produces a new set of lines
where matching keys are renamed. Keys not in the mapping are left
unchanged. Duplicate aliases (two old keys mapping to the same new
key) are flagged as conflicts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from envdiff.parser import parse_env_file


@dataclass
class AliasResult:
    source: str
    aliases: Dict[str, str]          # old -> new
    renamed: Dict[str, str]          # old -> new  (actually applied)
    conflicts: List[str]             # new keys that would be duplicated
    lines: List[str]                 # final output lines

    def summary(self) -> str:
        parts = [f"source={self.source}"]
        parts.append(f"renamed={len(self.renamed)}")
        if self.conflicts:
            parts.append(f"conflicts={len(self.conflicts)}")
        return ", ".join(parts)


def alias(path: str, aliases: Dict[str, str]) -> AliasResult:
    """Apply *aliases* to *path*, returning an AliasResult.

    Parameters
    ----------
    path:    path to the .env file
    aliases: mapping of old_key -> new_key
    """
    raw_lines = Path(path).read_text().splitlines(keepends=True)
    existing_keys = set(parse_env_file(path).keys())

    # Detect conflicts: two old keys map to the same new key
    new_key_counts: Dict[str, int] = {}
    for new_key in aliases.values():
        new_key_counts[new_key] = new_key_counts.get(new_key, 0) + 1
    conflicts = [nk for nk, cnt in new_key_counts.items() if cnt > 1]

    conflict_new_keys = set(conflicts)
    renamed: Dict[str, str] = {}
    out_lines: List[str] = []

    for raw in raw_lines:
        stripped = raw.rstrip("\n")
        # Skip comments and blank lines unchanged
        if not stripped or stripped.lstrip().startswith("#"):
            out_lines.append(raw)
            continue

        if "=" not in stripped:
            out_lines.append(raw)
            continue

        key, _, rest = stripped.partition("=")
        key = key.strip()

        if key in aliases:
            new_key = aliases[key]
            if new_key not in conflict_new_keys:
                renamed[key] = new_key
                out_lines.append(f"{new_key}={rest}\n")
                continue

        out_lines.append(raw)

    return AliasResult(
        source=str(path),
        aliases=aliases,
        renamed=renamed,
        conflicts=conflicts,
        lines=out_lines,
    )


def write_aliased(result: AliasResult, dest: str) -> None:
    """Write the aliased lines to *dest*."""
    Path(dest).write_text("".join(result.lines))
