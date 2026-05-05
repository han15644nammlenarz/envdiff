"""Linter for .env files — checks for common style and correctness issues."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from envdiff.parser import parse_env_file


@dataclass
class LintIssue:
    line_number: int
    key: str
    message: str
    severity: str = "warning"  # "warning" | "error"

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] line {self.line_number}: {self.key!r} — {self.message}"


@dataclass
class LintResult:
    path: str
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return bool(self.issues)

    @property
    def errors(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    def summary(self) -> str:
        if not self.has_issues:
            return f"{self.path}: no lint issues found."
        parts = []
        if self.errors:
            parts.append(f"{len(self.errors)} error(s)")
        if self.warnings:
            parts.append(f"{len(self.warnings)} warning(s)")
        return f"{self.path}: " + ", ".join(parts) + "."


def lint_file(path: str) -> LintResult:
    """Lint a single .env file and return a LintResult."""
    result = LintResult(path=path)
    raw_lines = Path(path).read_text(encoding="utf-8").splitlines()

    seen_keys: dict[str, int] = {}

    for lineno, raw in enumerate(raw_lines, start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if "=" not in stripped:
            result.issues.append(
                LintIssue(lineno, stripped, "line has no '=' separator", severity="error")
            )
            continue

        key, _, value = stripped.partition("=")
        key = key.strip()

        if not key:
            result.issues.append(
                LintIssue(lineno, "", "empty key before '='", severity="error")
            )
            continue

        if key != key.upper():
            result.issues.append(
                LintIssue(lineno, key, "key is not uppercase", severity="warning")
            )

        if " " in key:
            result.issues.append(
                LintIssue(lineno, key, "key contains whitespace", severity="error")
            )

        if key in seen_keys:
            result.issues.append(
                LintIssue(
                    lineno,
                    key,
                    f"duplicate key (first seen on line {seen_keys[key]})",
                    severity="error",
                )
            )
        else:
            seen_keys[key] = lineno

        if value != value.strip():
            result.issues.append(
                LintIssue(lineno, key, "value has leading or trailing whitespace", severity="warning")
            )

    return result
