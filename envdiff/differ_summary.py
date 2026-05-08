"""differ_summary.py — Produces a human-readable or machine-readable summary
of differences across multiple .env file pairs in a single pass.

Useful when comparing several environment pairs (e.g. dev vs staging,
staging vs prod) and wanting a consolidated report.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.differ import diff_files
from envdiff.comparator import DiffResult


@dataclass
class PairSummary:
    """Summary for a single file-pair comparison."""

    label: str
    base: str
    target: str
    missing: List[str] = field(default_factory=list)
    extra: List[str] = field(default_factory=list)
    mismatched: List[str] = field(default_factory=list)

    @property
    def has_differences(self) -> bool:
        return bool(self.missing or self.extra or self.mismatched)

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "base": self.base,
            "target": self.target,
            "missing": self.missing,
            "extra": self.extra,
            "mismatched": self.mismatched,
            "has_differences": self.has_differences,
        }


@dataclass
class MultiDiffSummary:
    """Aggregated summary across all compared pairs."""

    pairs: List[PairSummary] = field(default_factory=list)

    @property
    def total_pairs(self) -> int:
        return len(self.pairs)

    @property
    def pairs_with_differences(self) -> int:
        return sum(1 for p in self.pairs if p.has_differences)

    @property
    def clean(self) -> bool:
        return self.pairs_with_differences == 0

    def summary(self) -> str:
        """Return a concise text summary of all pairs."""
        lines = [f"Compared {self.total_pairs} pair(s): "
                 f"{self.pairs_with_differences} with differences."]
        for pair in self.pairs:
            status = "DIFF" if pair.has_differences else "OK"
            lines.append(
                f"  [{status}] {pair.label}: "
                f"{len(pair.missing)} missing, "
                f"{len(pair.extra)} extra, "
                f"{len(pair.mismatched)} mismatched"
            )
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "total_pairs": self.total_pairs,
            "pairs_with_differences": self.pairs_with_differences,
            "clean": self.clean,
            "pairs": [p.to_dict() for p in self.pairs],
        }


def compare_many(
    pairs: List[tuple],
    ignore_values: bool = False,
    ignore_keys: Optional[List[str]] = None,
) -> MultiDiffSummary:
    """Compare multiple (label, base_path, target_path) pairs.

    Args:
        pairs: Sequence of (label, base_file, target_file) tuples.
        ignore_values: When True, only key presence is checked.
        ignore_keys: Keys to exclude from all comparisons.

    Returns:
        A MultiDiffSummary collecting results for every pair.
    """
    result = MultiDiffSummary()
    ignore_keys = ignore_keys or []

    for label, base, target in pairs:
        diff: DiffResult = diff_files(
            base,
            target,
            ignore_values=ignore_values,
            ignore_keys=ignore_keys,
        )
        pair_summary = PairSummary(
            label=label,
            base=base,
            target=target,
            missing=list(diff.missing),
            extra=list(diff.extra),
            mismatched=list(diff.mismatched.keys()),
        )
        result.pairs.append(pair_summary)

    return result
