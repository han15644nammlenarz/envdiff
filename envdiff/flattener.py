"""Flatten nested or prefixed .env keys into a structured dict tree."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.parser import parse_env_file


@dataclass
class FlattenResult:
    source: str
    tree: Dict[str, object] = field(default_factory=dict)
    keys: List[str] = field(default_factory=list)
    separator: str = "_"

    def groups(self) -> List[str]:
        """Return top-level group names (first segment of each key)."""
        seen = []
        for k in self.keys:
            top = k.split(self.separator, 1)[0]
            if top not in seen:
                seen.append(top)
        return seen

    def get(self, *path: str) -> Optional[str]:
        """Retrieve a value by traversing the tree with the given path segments."""
        node = self.tree
        for segment in path:
            if not isinstance(node, dict):
                return None
            node = node.get(segment)
        return node if isinstance(node, str) else None

    def summary(self) -> str:
        groups = self.groups()
        return (
            f"{self.source}: {len(self.keys)} keys, "
            f"{len(groups)} top-level group(s): {', '.join(groups) or 'none'}"
        )


def _insert(tree: Dict[str, object], segments: List[str], value: str) -> None:
    """Recursively insert *value* at the path defined by *segments* in *tree*."""
    if len(segments) == 1:
        tree[segments[0]] = value
        return
    head, rest = segments[0], segments[1:]
    if head not in tree or not isinstance(tree[head], dict):
        tree[head] = {}
    _insert(tree[head], rest, value)  # type: ignore[arg-type]


def flatten(path: str, separator: str = "_", max_depth: int = 0) -> FlattenResult:
    """Parse *path* and build a nested tree by splitting keys on *separator*.

    Parameters
    ----------
    path:       Path to the .env file.
    separator:  Character used to split key segments (default ``_``).
    max_depth:  If > 0, only split up to this many times (0 = unlimited).
    """
    env = parse_env_file(path)
    tree: Dict[str, object] = {}
    keys: List[str] = list(env.keys())

    for key, value in env.items():
        if separator and separator in key:
            maxsplit = max_depth if max_depth > 0 else -1
            segments = key.split(separator, maxsplit)
        else:
            segments = [key]
        _insert(tree, segments, value)

    return FlattenResult(source=path, tree=tree, keys=keys, separator=separator)
