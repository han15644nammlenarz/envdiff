"""Redactor: produce a redacted copy of a .env file, blanking secret values."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

from envdiff.masker import is_secret_key
from envdiff.parser import parse_env_file


@dataclass
class RedactResult:
    source: Path
    lines: List[str] = field(default_factory=list)   # final output lines
    redacted_keys: List[str] = field(default_factory=list)
    retained_keys: List[str] = field(default_factory=list)

    def summary(self) -> str:
        return (
            f"Redacted {len(self.redacted_keys)} secret key(s), "
            f"retained {len(self.retained_keys)} plain key(s)."
        )


def _redact_line(line: str, secret_keywords: Tuple[str, ...]) -> Tuple[str, str | None]:
    """Return (output_line, key_if_redacted_else_None)."""
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return line, None
    if "=" not in stripped:
        return line, None
    key, _ = stripped.split("=", 1)
    key = key.strip()
    if is_secret_key(key, list(secret_keywords)):
        return f"{key}=\n", key
    return line, None


def redact(
    source: Path,
    secret_keywords: Tuple[str, ...] = ("password", "secret", "token", "key", "api"),
) -> RedactResult:
    """Read *source*, blank secret values, and return a RedactResult."""
    result = RedactResult(source=source)
    raw_lines = source.read_text(encoding="utf-8").splitlines(keepends=True)
    parsed = parse_env_file(source)

    for line in raw_lines:
        out_line, redacted_key = _redact_line(line, secret_keywords)
        result.lines.append(out_line)
        if redacted_key:
            result.redacted_keys.append(redacted_key)

    result.retained_keys = [
        k for k in parsed if k not in result.redacted_keys
    ]
    return result


def write_redacted(result: RedactResult, dest: Path) -> None:
    """Write the redacted lines to *dest*."""
    dest.write_text("".join(result.lines), encoding="utf-8")
