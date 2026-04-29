"""Utilities for masking secret values in env dicts."""

from typing import Dict, List, Optional

DEFAULT_SECRET_KEYWORDS: List[str] = [
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "auth",
    "credential",
    "private",
]

MASK_PLACEHOLDER = "***"


def is_secret_key(key: str, keywords: Optional[List[str]] = None) -> bool:
    """Determine whether a key name looks like it holds a secret."""
    if keywords is None:
        keywords = DEFAULT_SECRET_KEYWORDS
    lower = key.lower()
    return any(kw in lower for kw in keywords)


def mask_dict(
    env: Dict[str, str],
    keywords: Optional[List[str]] = None,
    placeholder: str = MASK_PLACEHOLDER,
) -> Dict[str, str]:
    """Return a copy of *env* with secret values replaced by *placeholder*."""
    return {
        k: (placeholder if is_secret_key(k, keywords) else v)
        for k, v in env.items()
    }


def mask_value(key: str, value: str, keywords: Optional[List[str]] = None) -> str:
    """Return the masked value for *key* if it looks like a secret."""
    return MASK_PLACEHOLDER if is_secret_key(key, keywords) else value
