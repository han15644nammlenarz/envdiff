"""Convenience helpers that wrap differ/validator and record audit entries."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from envdiff.auditor import record, make_diff_entry, make_validate_entry
from envdiff.differ import diff_files
from envdiff.comparator import summary as diff_summary
from envdiff.validator import validate
from envdiff.validator import summary as val_summary

_DEFAULT_LOG = ".envdiff_audit.log"


def audited_diff(
    base: str | Path,
    *others: str | Path,
    log_path: str | Path = _DEFAULT_LOG,
    ignore_values: bool = False,
    ignore_keys: Optional[List[str]] = None,
):
    """Run diff_files and record the result in the audit log."""
    result = diff_files(
        str(base),
        *[str(o) for o in others],
        ignore_values=ignore_values,
        ignore_keys=ignore_keys or [],
    )
    files = [str(base)] + [str(o) for o in others]
    entry = make_diff_entry(
        files=files,
        summary=diff_summary(result),
        details={
            "missing": list(result.missing_keys),
            "extra": list(result.extra_keys),
            "mismatched": list(result.mismatched_keys.keys()),
        },
    )
    record(log_path, entry)
    return result


def audited_validate(
    reference: str | Path,
    target: str | Path,
    log_path: str | Path = _DEFAULT_LOG,
):
    """Run validate and record the result in the audit log."""
    result = validate(str(reference), str(target))
    files = [str(reference), str(target)]
    entry = make_validate_entry(
        files=files,
        summary=val_summary(result),
        details={
            "missing": list(result.missing_keys),
            "extra": list(result.extra_keys),
        },
    )
    record(log_path, entry)
    return result
