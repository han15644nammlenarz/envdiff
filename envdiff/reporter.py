"""Formats and outputs diff results for human or machine consumption."""

from __future__ import annotations

from typing import Literal

from envdiff.comparator import DiffResult
from envdiff.masker import mask_dict

OutputFormat = Literal["text", "json"]


def _mask_if_needed(
    data: dict[str, str],
    mask_secrets: bool,
    secret_keywords: list[str] | None = None,
) -> dict[str, str]:
    if mask_secrets:
        return mask_dict(data, secret_keywords=secret_keywords)
    return data


def format_text(
    result: DiffResult,
    base_label: str = "base",
    target_label: str = "target",
    mask_secrets: bool = False,
    secret_keywords: list[str] | None = None,
) -> str:
    """Return a human-readable text report of the diff."""
    lines: list[str] = []

    if result.missing_keys:
        lines.append(f"Missing in {target_label} (present in {base_label}):")
        for key in sorted(result.missing_keys):
            lines.append(f"  - {key}")

    if result.extra_keys:
        lines.append(f"Extra in {target_label} (not in {base_label}):")
        for key in sorted(result.extra_keys):
            lines.append(f"  + {key}")

    if result.mismatched_keys:
        lines.append("Mismatched values:")
        base_masked = _mask_if_needed(result.base_values, mask_secrets, secret_keywords)
        target_masked = _mask_if_needed(result.target_values, mask_secrets, secret_keywords)
        for key in sorted(result.mismatched_keys):
            base_val = base_masked.get(key, "")
            target_val = target_masked.get(key, "")
            lines.append(f"  ~ {key}: {base_label}={base_val!r} | {target_label}={target_val!r}")

    if not lines:
        lines.append("No differences found.")

    return "\n".join(lines)


def format_json(
    result: DiffResult,
    base_label: str = "base",
    target_label: str = "target",
    mask_secrets: bool = False,
    secret_keywords: list[str] | None = None,
) -> dict:
    """Return a structured dict representation of the diff (JSON-serialisable)."""
    base_masked = _mask_if_needed(result.base_values, mask_secrets, secret_keywords)
    target_masked = _mask_if_needed(result.target_values, mask_secrets, secret_keywords)

    mismatches = [
        {
            "key": key,
            base_label: base_masked.get(key, ""),
            target_label: target_masked.get(key, ""),
        }
        for key in sorted(result.mismatched_keys)
    ]

    return {
        "missing": sorted(result.missing_keys),
        "extra": sorted(result.extra_keys),
        "mismatched": mismatches,
        "has_differences": result.has_differences,
    }
