"""Compute statistics across a diff result or multiple diff results."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envdiff.comparator import DiffResult


@dataclass
class DiffStats:
    """Aggregated statistics derived from one or more DiffResult objects."""

    total_missing: int = 0
    total_extra: int = 0
    total_mismatched: int = 0
    total_clean: int = 0
    total_compared: int = 0
    files_with_differences: List[str] = field(default_factory=list)

    @property
    def total_issues(self) -> int:
        return self.total_missing + self.total_extra + self.total_mismatched

    @property
    def health_ratio(self) -> float:
        """Fraction of comparisons that were clean (0.0 – 1.0)."""
        if self.total_compared == 0:
            return 1.0
        return self.total_clean / self.total_compared

    def summary(self) -> str:
        pct = f"{self.health_ratio * 100:.1f}"
        return (
            f"Compared {self.total_compared} pair(s): "
            f"{self.total_clean} clean, "
            f"{len(self.files_with_differences)} with differences | "
            f"missing={self.total_missing} extra={self.total_extra} "
            f"mismatched={self.total_mismatched} | "
            f"health={pct}%"
        )

    def to_dict(self) -> dict:
        return {
            "total_compared": self.total_compared,
            "total_clean": self.total_clean,
            "total_missing": self.total_missing,
            "total_extra": self.total_extra,
            "total_mismatched": self.total_mismatched,
            "total_issues": self.total_issues,
            "health_ratio": round(self.health_ratio, 4),
            "files_with_differences": self.files_with_differences,
        }


def compute_stats(
    results: List[DiffResult],
    labels: List[str] | None = None,
) -> DiffStats:
    """Aggregate statistics from a list of DiffResult objects.

    Args:
        results: One or more DiffResult instances to aggregate.
        labels:  Optional human-readable label for each result (e.g. file path).
                 When provided must be the same length as *results*.

    Returns:
        A populated DiffStats instance.
    """
    if labels is not None and len(labels) != len(results):
        raise ValueError("labels must be the same length as results")

    stats = DiffStats()
    for idx, result in enumerate(results):
        stats.total_compared += 1
        stats.total_missing += len(result.missing)
        stats.total_extra += len(result.extra)
        stats.total_mismatched += len(result.mismatched)
        has_diff = bool(result.missing or result.extra or result.mismatched)
        if has_diff:
            label = labels[idx] if labels else str(idx)
            stats.files_with_differences.append(label)
        else:
            stats.total_clean += 1
    return stats
