"""Multi-file diff: compare a reference .env against multiple target files."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envdiff.differ import diff_files
from envdiff.comparator import DiffResult


@dataclass
class MultiDiffResult:
    reference: str
    results: Dict[str, DiffResult] = field(default_factory=dict)

    # ------------------------------------------------------------------ #
    def targets_with_differences(self) -> List[str]:
        """Return paths of targets that differ from the reference."""
        return [path for path, dr in self.results.items() if dr.has_differences()]

    def all_clean(self) -> bool:
        return len(self.targets_with_differences()) == 0

    def summary(self) -> str:
        lines = [f"Reference: {self.reference}"]
        for path, dr in self.results.items():
            status = "OK" if not dr.has_differences() else "DIFF"
            lines.append(
                f"  [{status}] {path}  "
                f"missing={len(dr.missing)}  "
                f"extra={len(dr.extra)}  "
                f"mismatched={len(dr.mismatched)}"
            )
        if self.all_clean():
            lines.append("All targets match the reference.")
        else:
            n = len(self.targets_with_differences())
            lines.append(f"{n} target(s) have differences.")
        return "\n".join(lines)


def diff_multi(
    reference: str | Path,
    targets: List[str | Path],
    *,
    ignore_values: bool = False,
    mask_secrets: bool = False,
) -> MultiDiffResult:
    """Compare *reference* against each path in *targets*.

    Parameters
    ----------
    reference:      The canonical .env file.
    targets:        One or more .env files to compare against the reference.
    ignore_values:  When True, only key presence is checked.
    mask_secrets:   When True, secret values are masked in DiffResult.
    """
    result = MultiDiffResult(reference=str(reference))
    for target in targets:
        dr = diff_files(
            str(reference),
            str(target),
            ignore_values=ignore_values,
            mask_secrets=mask_secrets,
        )
        result.results[str(target)] = dr
    return result
