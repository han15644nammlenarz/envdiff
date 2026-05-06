"""Audit log for envdiff: records diff and validation events to a structured log file."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


@dataclass
class AuditEntry:
    timestamp: str
    event: str          # e.g. "diff", "validate", "snapshot"
    files: List[str]
    summary: str
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "event": self.event,
            "files": self.files,
            "summary": self.summary,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEntry":
        return cls(
            timestamp=data["timestamp"],
            event=data["event"],
            files=data["files"],
            summary=data["summary"],
            details=data.get("details", {}),
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def record(log_path: str | Path, entry: AuditEntry) -> None:
    """Append an AuditEntry as a JSON line to *log_path*."""
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry.to_dict()) + "\n")


def load(log_path: str | Path) -> List[AuditEntry]:
    """Return all entries stored in *log_path*."""
    log_path = Path(log_path)
    if not log_path.exists():
        return []
    entries: List[AuditEntry] = []
    with log_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                entries.append(AuditEntry.from_dict(json.loads(line)))
    return entries


def make_diff_entry(files: List[str], summary: str, details: Optional[dict] = None) -> AuditEntry:
    return AuditEntry(
        timestamp=_now(),
        event="diff",
        files=files,
        summary=summary,
        details=details or {},
    )


def make_validate_entry(files: List[str], summary: str, details: Optional[dict] = None) -> AuditEntry:
    return AuditEntry(
        timestamp=_now(),
        event="validate",
        files=files,
        summary=summary,
        details=details or {},
    )
