"""Groups .env keys by prefix or custom rules and reports group-level statistics."""
from __future__ import annotations

from dataclasses import dataclass, field
from collections import defaultdict
from typing import Dict, List, Optional

from envdiff.parser import parse_env_file
from envdiff.masker import is_secret_key


@dataclass
class GroupResult:
    """Result of grouping a .env file by key prefix."""
    path: str
    separator: str
    groups: Dict[str, List[str]] = field(default_factory=dict)
    ungrouped: List[str] = field(default_factory=list)

    def group_names(self) -> List[str]:
        return sorted(self.groups.keys())

    def secret_keys_in_group(self, group: str) -> List[str]:
        return [k for k in self.groups.get(group, []) if is_secret_key(k)]

    def summary(self) -> str:
        lines = [f"Groups in '{self.path}' (separator='{self.separator}'):"]
        for name in self.group_names():
            keys = self.groups[name]
            secrets = len(self.secret_keys_in_group(name))
            lines.append(f"  [{name}] {len(keys)} key(s), {secrets} secret(s)")
        if self.ungrouped:
            lines.append(f"  [ungrouped] {len(self.ungrouped)} key(s)")
        return "\n".join(lines)


def group(
    path: str,
    separator: str = "_",
    min_prefix_length: int = 1,
    include_ungrouped: bool = True,
) -> GroupResult:
    """Parse *path* and bucket keys by the prefix before *separator*.

    Keys whose prefix (split on the first occurrence of *separator*) is shorter
    than *min_prefix_length* characters land in ``ungrouped``.
    """
    env = parse_env_file(path)
    buckets: Dict[str, List[str]] = defaultdict(list)
    ungrouped: List[str] = []

    for key in env:
        if separator in key:
            prefix = key.split(separator, 1)[0]
            if len(prefix) >= min_prefix_length:
                buckets[prefix].append(key)
                continue
        ungrouped.append(key)

    return GroupResult(
        path=path,
        separator=separator,
        groups=dict(buckets),
        ungrouped=ungrouped if include_ungrouped else [],
    )
