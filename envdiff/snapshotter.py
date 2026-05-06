"""Snapshot .env files to disk for later diffing against current state."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from envdiff.parser import parse_env_file


@dataclass
class Snapshot:
    path: str
    captured_at: str
    values: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "captured_at": self.captured_at,
            "values": self.values,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Snapshot":
        return cls(
            path=data["path"],
            captured_at=data["captured_at"],
            values=data.get("values", {}),
        )


def capture(env_path: str) -> Snapshot:
    """Parse *env_path* and return a Snapshot with the current timestamp."""
    values = parse_env_file(env_path)
    return Snapshot(
        path=env_path,
        captured_at=datetime.now(timezone.utc).isoformat(),
        values=values,
    )


def save(snapshot: Snapshot, snapshot_path: str) -> None:
    """Persist a Snapshot as JSON to *snapshot_path*."""
    Path(snapshot_path).parent.mkdir(parents=True, exist_ok=True)
    with open(snapshot_path, "w", encoding="utf-8") as fh:
        json.dump(snapshot.to_dict(), fh, indent=2)


def load(snapshot_path: str) -> Snapshot:
    """Load a previously saved Snapshot from *snapshot_path*."""
    with open(snapshot_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return Snapshot.from_dict(data)


def default_snapshot_path(env_path: str, snapshot_dir: Optional[str] = None) -> str:
    """Return a deterministic snapshot filename derived from *env_path*."""
    base = Path(env_path).name.replace(".", "_")
    directory = snapshot_dir or ".envdiff_snapshots"
    return str(Path(directory) / f"{base}.snapshot.json")
