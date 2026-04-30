"""Export diff results to various file formats (JSON, CSV, Markdown)."""

from __future__ import annotations

import csv
import io
import json
from typing import Optional

from envdiff.comparator import DiffResult
from envdiff.masker import is_secret_key, mask_value


def _mask_if_needed(key: str, value: str, mask_secrets: bool) -> str:
    if mask_secrets and is_secret_key(key):
        return mask_value(value)
    return value


def export_json(
    result: DiffResult,
    mask_secrets: bool = False,
    indent: int = 2,
) -> str:
    """Serialize a DiffResult to a JSON string."""
    payload: dict = {
        "missing": list(result.missing),
        "extra": list(result.extra),
        "mismatched": {
            key: {
                "base": _mask_if_needed(key, base_val, mask_secrets),
                "compare": _mask_if_needed(key, cmp_val, mask_secrets),
            }
            for key, (base_val, cmp_val) in result.mismatched.items()
        },
    }
    return json.dumps(payload, indent=indent)


def export_csv(result: DiffResult, mask_secrets: bool = False) -> str:
    """Serialize a DiffResult to a CSV string.

    Columns: category, key, base_value, compare_value
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["category", "key", "base_value", "compare_value"])

    for key in sorted(result.missing):
        writer.writerow(["missing", key, "", ""])

    for key in sorted(result.extra):
        writer.writerow(["extra", key, "", ""])

    for key, (base_val, cmp_val) in sorted(result.mismatched.items()):
        writer.writerow([
            "mismatched",
            key,
            _mask_if_needed(key, base_val, mask_secrets),
            _mask_if_needed(key, cmp_val, mask_secrets),
        ])

    return output.getvalue()


def export_markdown(result: DiffResult, mask_secrets: bool = False) -> str:
    """Serialize a DiffResult to a Markdown report string."""
    lines: list[str] = ["# Env Diff Report", ""]

    lines.append("## Missing Keys")
    if result.missing:
        for key in sorted(result.missing):
            lines.append(f"- `{key}`")
    else:
        lines.append("_None_")
    lines.append("")

    lines.append("## Extra Keys")
    if result.extra:
        for key in sorted(result.extra):
            lines.append(f"- `{key}`")
    else:
        lines.append("_None_")
    lines.append("")

    lines.append("## Mismatched Values")
    if result.mismatched:
        lines.append("| Key | Base | Compare |")
        lines.append("|-----|------|---------|")
        for key, (base_val, cmp_val) in sorted(result.mismatched.items()):
            b = _mask_if_needed(key, base_val, mask_secrets)
            c = _mask_if_needed(key, cmp_val, mask_secrets)
            lines.append(f"| `{key}` | `{b}` | `{c}` |")
    else:
        lines.append("_None_")
    lines.append("")

    return "\n".join(lines)
