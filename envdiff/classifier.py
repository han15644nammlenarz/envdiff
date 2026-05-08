"""Classify .env keys into categories based on naming conventions and value patterns."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envdiff.masker import is_secret_key
from envdiff.parser import parse_env_file

_URL_SUFFIXES = ("_URL", "_URI", "_ENDPOINT", "_HOST")
_PORT_SUFFIXES = ("_PORT",)
_FLAG_SUFFIXES = ("_ENABLED", "_DISABLED", "_DEBUG", "_VERBOSE", "_FLAG")
_PATH_SUFFIXES = ("_PATH", "_DIR", "_DIRECTORY", "_FILE", "_FOLDER")
_FLAG_VALUES = {"true", "false", "1", "0", "yes", "no"}


def _classify_key(key: str, value: str) -> str:
    upper = key.upper()
    if is_secret_key(key):
        return "secret"
    if any(upper.endswith(s) for s in _URL_SUFFIXES):
        return "url"
    if any(upper.endswith(s) for s in _PORT_SUFFIXES):
        return "port"
    if any(upper.endswith(s) for s in _FLAG_SUFFIXES) or value.lower() in _FLAG_VALUES:
        return "flag"
    if any(upper.endswith(s) for s in _PATH_SUFFIXES):
        return "path"
    return "general"


@dataclass
class ClassifyResult:
    path: str
    categories: Dict[str, List[str]] = field(default_factory=dict)
    key_category: Dict[str, str] = field(default_factory=dict)

    def keys_in(self, category: str) -> List[str]:
        return self.categories.get(category, [])

    def summary(self) -> str:
        lines = [f"Classification: {self.path}"]
        for cat, keys in sorted(self.categories.items()):
            lines.append(f"  {cat} ({len(keys)}): {', '.join(sorted(keys))}")
        return "\n".join(lines)


def classify(path: str) -> ClassifyResult:
    """Parse *path* and classify every key into a named category."""
    env = parse_env_file(path)
    result = ClassifyResult(path=path)
    for key, value in env.items():
        cat = _classify_key(key, value)
        result.key_category[key] = cat
        result.categories.setdefault(cat, []).append(key)
    return result
