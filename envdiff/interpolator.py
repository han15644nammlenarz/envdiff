"""Detect and resolve variable interpolation references in .env files."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_REF_RE = re.compile(r"\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)")


@dataclass
class InterpolationResult:
    resolved: Dict[str, str] = field(default_factory=dict)
    unresolved: Dict[str, List[str]] = field(default_factory=dict)  # key -> missing refs
    references: Dict[str, List[str]] = field(default_factory=dict)  # key -> refs it uses

    def summary(self) -> str:
        lines = []
        if self.unresolved:
            lines.append(f"Unresolved references in {len(self.unresolved)} key(s):")
            for key, refs in self.unresolved.items():
                lines.append(f"  {key}: missing {refs}")
        else:
            lines.append("All variable references resolved successfully.")
        return "\n".join(lines)


def _extract_refs(value: str) -> List[str]:
    """Return all variable names referenced in *value*."""
    return [
        m.group(1) or m.group(2)
        for m in _REF_RE.finditer(value)
    ]


def _resolve_value(value: str, env: Dict[str, str], seen: Optional[set] = None) -> Optional[str]:
    """Recursively resolve a value; return None if any reference is missing."""
    if seen is None:
        seen = set()

    def replacer(m: re.Match) -> str:
        ref = m.group(1) or m.group(2)
        if ref in seen:
            raise RecursionError(f"Circular reference: {ref}")
        if ref not in env:
            raise KeyError(ref)
        return _resolve_value(env[ref], env, seen | {ref})  # type: ignore[arg-type]

    try:
        return _REF_RE.sub(replacer, value)
    except (KeyError, RecursionError):
        return None


def interpolate(env: Dict[str, str]) -> InterpolationResult:
    """Resolve all interpolation references in *env* and return an InterpolationResult."""
    result = InterpolationResult()

    for key, raw_value in env.items():
        refs = _extract_refs(raw_value)
        if refs:
            result.references[key] = refs

        resolved = _resolve_value(raw_value, env)
        if resolved is not None:
            result.resolved[key] = resolved
        else:
            missing = [r for r in refs if r not in env]
            result.unresolved[key] = missing
            result.resolved[key] = raw_value  # keep original

    # Keys with no references resolve trivially
    for key, value in env.items():
        if key not in result.resolved:
            result.resolved[key] = value

    return result
