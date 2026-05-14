"""Chain multiple .env comparisons and aggregate results."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envdiff.comparator import DiffResult, compare
from envdiff.parser import parse_env_file


@dataclass
class ChainLink:
    """A single comparison step in a chain."""
    base_path: str
    target_path: str
    result: DiffResult

    def has_differences(self) -> bool:
        return (
            bool(self.result.missing)
            or bool(self.result.extra)
            or bool(self.result.mismatched)
        )


@dataclass
class ChainResult:
    """Aggregated result of a comparison chain."""
    links: List[ChainLink] = field(default_factory=list)

    def all_clean(self) -> bool:
        return all(not link.has_differences() for link in self.links)

    def links_with_differences(self) -> List[ChainLink]:
        return [lnk for lnk in self.links if lnk.has_differences()]

    def summary(self) -> str:
        total = len(self.links)
        dirty = len(self.links_with_differences())
        if dirty == 0:
            return f"All {total} comparison(s) clean."
        return f"{dirty}/{total} comparison(s) have differences."


def compare_chain(
    paths: List[str],
    *,
    ignore_values: bool = False,
    ignore_extra: bool = False,
) -> ChainResult:
    """Compare each consecutive pair in *paths* and return a ChainResult.

    With three files [A, B, C] two comparisons are performed: A→B and B→C.
    """
    if len(paths) < 2:
        raise ValueError("compare_chain requires at least two paths.")

    result = ChainResult()
    for i in range(len(paths) - 1):
        base_path = paths[i]
        target_path = paths[i + 1]
        base = parse_env_file(Path(base_path))
        target = parse_env_file(Path(target_path))
        diff = compare(
            base,
            target,
            ignore_values=ignore_values,
            ignore_extra=ignore_extra,
        )
        result.links.append(ChainLink(
            base_path=base_path,
            target_path=target_path,
            result=diff,
        ))
    return result
