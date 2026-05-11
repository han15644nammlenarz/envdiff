"""Encrypt secret values in a .env file using Fernet symmetric encryption."""
from __future__ import annotations

import base64
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envdiff.masker import is_secret_key
from envdiff.parser import parse_env_file

try:
    from cryptography.fernet import Fernet
    _CRYPTO_AVAILABLE = True
except ImportError:  # pragma: no cover
    _CRYPTO_AVAILABLE = False


@dataclass
class EncryptResult:
    path: str
    total_keys: int
    encrypted_keys: List[str] = field(default_factory=list)
    skipped_keys: List[str] = field(default_factory=list)
    lines: List[str] = field(default_factory=list)
    key_used: Optional[str] = None

    def summary(self) -> str:
        return (
            f"{self.path}: {len(self.encrypted_keys)} key(s) encrypted, "
            f"{len(self.skipped_keys)} plain."
        )


def generate_key() -> str:
    """Generate a new Fernet key and return it as a URL-safe base64 string."""
    if not _CRYPTO_AVAILABLE:
        raise RuntimeError("cryptography package is required: pip install cryptography")
    return Fernet.generate_key().decode()


def encrypt(
    path: str | Path,
    fernet_key: str,
    *,
    secret_keywords: Optional[List[str]] = None,
) -> EncryptResult:
    """Encrypt all secret-looking values in *path* and return the result.

    The returned ``EncryptResult.lines`` contains the modified file lines
    ready to be written back to disk.
    """
    if not _CRYPTO_AVAILABLE:
        raise RuntimeError("cryptography package is required: pip install cryptography")

    path = Path(path)
    fernet = Fernet(fernet_key.encode() if isinstance(fernet_key, str) else fernet_key)
    pairs = parse_env_file(path)
    raw_lines = path.read_text(encoding="utf-8").splitlines(keepends=True)

    encrypted_keys: List[str] = []
    skipped_keys: List[str] = []
    out_lines: List[str] = []

    kv_index = {k: v for k, v in pairs}

    for line in raw_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            out_lines.append(line)
            continue

        key, _, value = stripped.partition("=")
        key = key.strip()

        if is_secret_key(key, extra_keywords=secret_keywords) and value:
            token = fernet.encrypt(value.encode()).decode()
            out_lines.append(f"{key}=enc:{token}\n")
            encrypted_keys.append(key)
        else:
            out_lines.append(line)
            skipped_keys.append(key)

    return EncryptResult(
        path=str(path),
        total_keys=len(kv_index),
        encrypted_keys=encrypted_keys,
        skipped_keys=skipped_keys,
        lines=out_lines,
        key_used=fernet_key[:8] + "...",
    )


def write_encrypted(result: EncryptResult, dest: str | Path) -> None:
    """Write the encrypted lines to *dest*."""
    Path(dest).write_text("".join(result.lines), encoding="utf-8")
