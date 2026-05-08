"""Pin the current values of an env file, producing a lockfile-style snapshot."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envdiff.parser import parse_env_file
from envdiff.masker import is_secret_key


@dataclass
class PinResult:
    source: str
    pinned: Dict[str, str] = field(default_factory=dict)
    secret_keys: List[str] = field(default_factory=list)
    total_keys: int = 0

    def summary(self) -> str:
        lines = [
            f"Pinned {self.total_keys} key(s) from '{self.source}'.",
            f"  Secret keys detected : {len(self.secret_keys)}",
        ]
        if self.secret_keys:
            lines.append("  Secrets : " + ", ".join(self.secret_keys))
        return "\n".join(lines)


def pin(
    env_path: str | Path,
    output_path: Optional[str | Path] = None,
    mask_secrets: bool = True,
) -> PinResult:
    """Read *env_path*, record every key=value pair and optionally write a JSON
    pin-file to *output_path*.

    Secret values are replaced with an empty string when *mask_secrets* is True
    so the lockfile is safe to commit.
    """
    env_path = Path(env_path)
    raw: Dict[str, str] = parse_env_file(env_path)

    pinned: Dict[str, str] = {}
    secret_keys: List[str] = []

    for key, value in raw.items():
        if is_secret_key(key):
            secret_keys.append(key)
            pinned[key] = "" if mask_secrets else value
        else:
            pinned[key] = value

    result = PinResult(
        source=str(env_path),
        pinned=pinned,
        secret_keys=sorted(secret_keys),
        total_keys=len(pinned),
    )

    if output_path is not None:
        _write_pin_file(result, Path(output_path))

    return result


def _write_pin_file(result: PinResult, path: Path) -> None:
    payload = {
        "source": result.source,
        "total_keys": result.total_keys,
        "secret_keys": result.secret_keys,
        "pinned": result.pinned,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_pin_file(path: str | Path) -> Dict[str, str]:
    """Return the pinned key/value mapping from a previously saved pin-file."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data.get("pinned", {})
