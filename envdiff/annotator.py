"""Annotate .env files with inline comments describing key status."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from envdiff.comparator import DiffResult
from envdiff.masker import is_secret_key


@dataclass
class AnnotatedLine:
    original: str
    annotation: Optional[str] = None

    def render(self) -> str:
        if self.annotation:
            return f"{self.original}  # [{self.annotation}]"
        return self.original


@dataclass
class AnnotationResult:
    path: str
    lines: list[AnnotatedLine] = field(default_factory=list)
    annotated_count: int = 0

    def render(self) -> str:
        return "\n".join(line.render() for line in self.lines)

    def summary(self) -> str:
        return f"{self.annotated_count} key(s) annotated in '{self.path}'"


def annotate(
    env_path: str,
    diff: DiffResult,
    mask_secrets: bool = False,
) -> AnnotationResult:
    """Read *env_path* and return an AnnotationResult with inline annotations
    derived from *diff* (missing / extra / mismatched)."""
    path = Path(env_path)
    raw_lines = path.read_text().splitlines()

    result = AnnotationResult(path=env_path)
    annotated_count = 0

    for raw in raw_lines:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            result.lines.append(AnnotatedLine(original=raw))
            continue

        key, _, _ = stripped.partition("=")
        key = key.strip()
        annotation: Optional[str] = None

        if key in diff.missing_keys:
            annotation = "MISSING in reference"
        elif key in diff.extra_keys:
            annotation = "EXTRA — not in reference"
        elif key in diff.mismatched_keys:
            ref_val = diff.mismatched_keys[key]["reference"]
            if mask_secrets and is_secret_key(key):
                ref_val = "***"
            annotation = f"MISMATCH — reference: {ref_val}"

        if annotation:
            annotated_count += 1

        result.lines.append(AnnotatedLine(original=raw, annotation=annotation))

    result.annotated_count = annotated_count
    return result
