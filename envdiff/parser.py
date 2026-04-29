"""Parser for .env files."""

import re
from pathlib import Path
from typing import Dict, Optional


_COMMENT_RE = re.compile(r"^\s*#.*$")
_BLANK_RE = re.compile(r"^\s*$")
_KEY_VALUE_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$")


def _strip_quotes(value: str) -> str:
    """Remove surrounding single or double quotes from a value."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        return value[1:-1]
    return value


def parse_env_file(path: str | Path) -> Dict[str, Optional[str]]:
    """
    Parse a .env file and return a dict of key-value pairs.

    - Blank lines and comment lines (starting with #) are ignored.
    - Values may optionally be quoted with single or double quotes.
    - Keys without a value (e.g. ``FOO=``) map to an empty string.

    Args:
        path: Path to the .env file.

    Returns:
        Ordered dict mapping variable names to their string values.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If a line cannot be parsed.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f".env file not found: {path}")

    result: Dict[str, Optional[str]] = {}

    with path.open(encoding="utf-8") as fh:
        for lineno, raw_line in enumerate(fh, start=1):
            line = raw_line.rstrip("\n")

            if _BLANK_RE.match(line) or _COMMENT_RE.match(line):
                continue

            match = _KEY_VALUE_RE.match(line)
            if not match:
                raise ValueError(
                    f"Invalid syntax at {path}:{lineno}: {line!r}"
                )

            key, value = match.group(1), match.group(2).strip()
            result[key] = _strip_quotes(value)

    return result
