"""Merge multiple .env files into a single unified output.

Later files take precedence over earlier ones unless a key is marked
as protected.  The result is an ordered dict plus metadata about which
file each key originated from and whether any key was overridden.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

from envdiff.parser import parse_env_file


@dataclass
class MergeResult:
    """Outcome of merging two or more .env files."""

    merged: Dict[str, str] = field(default_factory=dict)
    # key -> list of (filename, value) in the order they were encountered
    origins: Dict[str, List[tuple]] = field(default_factory=dict)
    # keys whose value was overridden at least once
    overridden: List[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [f"Merged keys   : {len(self.merged)}"]
        if self.overridden:
            lines.append(f"Overridden keys: {len(self.overridden)}")
            for key in self.overridden:
                history = ", ".join(
                    f"{fname}={val!r}" for fname, val in self.origins[key]
                )
                lines.append(f"  {key}: {history}")
        else:
            lines.append("No keys were overridden.")
        return "\n".join(lines)


def merge(
    paths: Sequence[str],
    protected: Optional[Sequence[str]] = None,
) -> MergeResult:
    """Merge env files in *paths* order (last wins) into a :class:`MergeResult`.

    Parameters
    ----------
    paths:
        Ordered list of .env file paths.  Files later in the list override
        keys from earlier files.
    protected:
        Keys that must NOT be overridden by later files.  If a later file
        tries to override a protected key the earlier value is kept.
    """
    protected_set = set(protected or [])
    result = MergeResult()

    for path in paths:
        data = parse_env_file(path)
        for key, value in data.items():
            if key not in result.origins:
                result.origins[key] = []
            result.origins[key].append((path, value))

            if key in result.merged and key in protected_set:
                # keep original value — do not override
                continue

            if key in result.merged and result.merged[key] != value:
                if key not in result.overridden:
                    result.overridden.append(key)

            result.merged[key] = value

    return result
