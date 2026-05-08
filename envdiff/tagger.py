"""Tag keys in a .env file with custom labels and query by tag."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envdiff.parser import parse_env_file
from envdiff.masker import is_secret_key


@dataclass
class TagResult:
    path: str
    tags: Dict[str, List[str]]          # key -> list of tag labels
    tagged_keys: Dict[str, List[str]]   # tag -> list of keys
    total_keys: int
    total_tagged: int

    def keys_for_tag(self, tag: str) -> List[str]:
        """Return all keys that carry *tag*."""
        return self.tagged_keys.get(tag, [])

    def tags_for_key(self, key: str) -> List[str]:
        """Return all tags applied to *key*."""
        return self.tags.get(key, [])

    def summary(self) -> str:
        all_tags = sorted(self.tagged_keys.keys())
        parts = [f"{t}({len(self.tagged_keys[t])})" for t in all_tags]
        tag_summary = ", ".join(parts) if parts else "none"
        return (
            f"{self.path}: {self.total_keys} keys, "
            f"{self.total_tagged} tagged — tags: {tag_summary}"
        )


_BUILTIN_RULES: List[tuple] = [
    ("secret", lambda k, _v: is_secret_key(k)),
    ("empty",  lambda _k, v: v == ""),
    ("url",    lambda _k, v: v.startswith(("http://", "https://", "ftp://"))),
    ("numeric", lambda _k, v: v.lstrip("-").replace(".", "", 1).isdigit() and v != ""),
    ("boolean", lambda _k, v: v.lower() in {"true", "false", "1", "0", "yes", "no"}),
]


def tag(
    path: str | Path,
    extra_rules: Optional[List[tuple]] = None,
    secret_keywords: Optional[List[str]] = None,
) -> TagResult:
    """Parse *path* and apply built-in + optional custom tagging rules.

    *extra_rules* is a list of ``(tag_label, predicate)`` pairs where
    ``predicate(key, value) -> bool``.
    """
    env = parse_env_file(str(path))
    rules = list(_BUILTIN_RULES)
    if extra_rules:
        rules.extend(extra_rules)

    tags: Dict[str, List[str]] = {}
    tagged_keys: Dict[str, List[str]] = {}

    for key, value in env.items():
        key_tags: List[str] = []
        for label, predicate in rules:
            try:
                hit = predicate(key, value)
            except Exception:
                hit = False
            if hit:
                key_tags.append(label)
                tagged_keys.setdefault(label, []).append(key)
        if key_tags:
            tags[key] = key_tags

    return TagResult(
        path=str(path),
        tags=tags,
        tagged_keys=tagged_keys,
        total_keys=len(env),
        total_tagged=len(tags),
    )
