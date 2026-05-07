"""Profile .env files: count keys, detect secrets, measure value lengths."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envdiff.masker import is_secret_key
from envdiff.parser import parse_env_file


@dataclass
class ProfileResult:
    path: str
    total_keys: int
    secret_keys: List[str] = field(default_factory=list)
    plain_keys: List[str] = field(default_factory=list)
    empty_value_keys: List[str] = field(default_factory=list)
    long_value_keys: List[str] = field(default_factory=list)  # values > 100 chars
    avg_value_length: float = 0.0
    key_lengths: Dict[str, int] = field(default_factory=dict)  # key -> value length

    def summary(self) -> str:
        lines = [
            f"Profile: {self.path}",
            f"  Total keys      : {self.total_keys}",
            f"  Secret keys     : {len(self.secret_keys)} ({', '.join(self.secret_keys) or 'none'})",
            f"  Plain keys      : {len(self.plain_keys)}",
            f"  Empty values    : {len(self.empty_value_keys)}",
            f"  Long values     : {len(self.long_value_keys)}",
            f"  Avg value length: {self.avg_value_length:.1f} chars",
        ]
        return "\n".join(lines)


def profile(path: str, secret_keywords: List[str] | None = None) -> ProfileResult:
    """Parse *path* and return a ProfileResult with statistics."""
    env = parse_env_file(path)

    secret_keys: List[str] = []
    plain_keys: List[str] = []
    empty_value_keys: List[str] = []
    long_value_keys: List[str] = []
    key_lengths: Dict[str, int] = {}
    total_length = 0

    for key, value in env.items():
        vlen = len(value)
        key_lengths[key] = vlen
        total_length += vlen

        if is_secret_key(key, secret_keywords):
            secret_keys.append(key)
        else:
            plain_keys.append(key)

        if value == "":
            empty_value_keys.append(key)

        if vlen > 100:
            long_value_keys.append(key)

    n = len(env)
    avg = total_length / n if n > 0 else 0.0

    return ProfileResult(
        path=path,
        total_keys=n,
        secret_keys=sorted(secret_keys),
        plain_keys=sorted(plain_keys),
        empty_value_keys=sorted(empty_value_keys),
        long_value_keys=sorted(long_value_keys),
        avg_value_length=round(avg, 2),
        key_lengths=key_lengths,
    )
