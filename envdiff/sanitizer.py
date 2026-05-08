"""Sanitizer: remove or replace values that match dangerous patterns."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .masker import is_secret_key
from .parser import parse_env_file

# Patterns considered dangerous regardless of key name
_DANGEROUS_VALUE_PATTERNS: List[re.Pattern] = [
    re.compile(r"(?i)(password|secret|token|key)\s*="),  # embedded credential
    re.compile(r"[A-Za-z0-9+/]{40,}={0,2}$"),            # long base64-like string
    re.compile(r"^[0-9a-fA-F]{32,}$"),                   # hex token
]


@dataclass
class SanitizeResult:
    source: str
    lines: List[str]
    sanitized_keys: List[str] = field(default_factory=list)
    replacement: str = "REDACTED"

    def summary(self) -> str:
        if not self.sanitized_keys:
            return f"{self.source}: no sensitive values found"
        keys = ", ".join(self.sanitized_keys)
        return f"{self.source}: sanitized {len(self.sanitized_keys)} key(s): {keys}"


def _value_is_dangerous(value: str) -> bool:
    for pattern in _DANGEROUS_VALUE_PATTERNS:
        if pattern.search(value):
            return True
    return False


def sanitize(
    path: str,
    replacement: str = "REDACTED",
    extra_keywords: Optional[List[str]] = None,
) -> SanitizeResult:
    """Read *path*, blank out sensitive values, return a SanitizeResult."""
    source = Path(path)
    raw_lines = source.read_text(encoding="utf-8").splitlines()
    env = parse_env_file(path)

    sanitized_keys: List[str] = []
    out_lines: List[str] = []

    for line in raw_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            out_lines.append(line)
            continue

        if "=" not in stripped:
            out_lines.append(line)
            continue

        key, _, value = stripped.partition("=")
        key = key.strip()
        value = value.strip()

        should_sanitize = is_secret_key(key, extra_keywords=extra_keywords) or (
            value and _value_is_dangerous(value)
        )

        if should_sanitize:
            sanitized_keys.append(key)
            out_lines.append(f"{key}={replacement}")
        else:
            out_lines.append(line)

    return SanitizeResult(
        source=str(path),
        lines=out_lines,
        sanitized_keys=sanitized_keys,
        replacement=replacement,
    )


def write_sanitized(result: SanitizeResult, dest: str) -> None:
    """Write sanitized lines to *dest*."""
    Path(dest).write_text("\n".join(result.lines) + "\n", encoding="utf-8")
