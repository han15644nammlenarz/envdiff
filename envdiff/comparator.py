"""Core comparison logic for envdiff."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class DiffResult:
    """Holds the result of comparing two .env files."""

    base_name: str
    target_name: str
    missing_keys: List[str] = field(default_factory=list)
    extra_keys: List[str] = field(default_factory=list)
    mismatched_keys: Dict[str, tuple] = field(default_factory=dict)

    @property
    def has_differences(self) -> bool:
        return bool(self.missing_keys or self.extra_keys or self.mismatched_keys)

    def summary(self) -> str:
        lines = [f"Comparing '{self.base_name}' (base) vs '{self.target_name}' (target):"]
        if not self.has_differences:
            lines.append("  No differences found.")
            return "\n".join(lines)
        if self.missing_keys:
            lines.append(f"  Missing keys ({len(self.missing_keys)}):")
            for key in sorted(self.missing_keys):
                lines.append(f"    - {key}")
        if self.extra_keys:
            lines.append(f"  Extra keys ({len(self.extra_keys)}):")
            for key in sorted(self.extra_keys):
                lines.append(f"    + {key}")
        if self.mismatched_keys:
            lines.append(f"  Mismatched values ({len(self.mismatched_keys)}):")
            for key in sorted(self.mismatched_keys):
                base_val, target_val = self.mismatched_keys[key]
                lines.append(f"    ~ {key}: '{base_val}' -> '{target_val}'")
        return "\n".join(lines)


def compare(
    base: Dict[str, str],
    target: Dict[str, str],
    base_name: str = "base",
    target_name: str = "target",
    ignore_values: bool = False,
    mask_secrets: bool = False,
    secret_keywords: Optional[List[str]] = None,
) -> DiffResult:
    """Compare two parsed env dicts and return a DiffResult."""
    if secret_keywords is None:
        secret_keywords = ["password", "secret", "token", "key", "api", "auth"]

    base_keys = set(base.keys())
    target_keys = set(target.keys())

    result = DiffResult(
        base_name=base_name,
        target_name=target_name,
        missing_keys=sorted(base_keys - target_keys),
        extra_keys=sorted(target_keys - base_keys),
    )

    if not ignore_values:
        for key in base_keys & target_keys:
            if base[key] != target[key]:
                base_val = base[key]
                target_val = target[key]
                if mask_secrets and _is_secret(key, secret_keywords):
                    base_val = "***"
                    target_val = "***"
                result.mismatched_keys[key] = (base_val, target_val)

    return result


def _is_secret(key: str, secret_keywords: List[str]) -> bool:
    """Return True if the key name suggests it holds a secret value."""
    lower_key = key.lower()
    return any(kw in lower_key for kw in secret_keywords)
