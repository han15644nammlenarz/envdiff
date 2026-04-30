"""High-level diff orchestration: parse two env files and return a DiffResult."""

from pathlib import Path
from typing import Optional, List

from envdiff.parser import parse_env_file
from envdiff.comparator import DiffResult, compare


def diff_files(
    base_path: str | Path,
    target_path: str | Path,
    ignore_values: bool = False,
    ignore_keys: Optional[List[str]] = None,
) -> DiffResult:
    """Parse *base_path* and *target_path* then return a :class:`DiffResult`.

    Parameters
    ----------
    base_path:
        Path to the reference .env file (e.g. ``.env.example``).
    target_path:
        Path to the environment-specific .env file being validated.
    ignore_values:
        When ``True`` value mismatches are not reported.
    ignore_keys:
        Optional list of key names to exclude from comparison entirely.

    Raises
    ------
    FileNotFoundError
        If either path does not exist.
    """
    base_path = Path(base_path)
    target_path = Path(target_path)

    if not base_path.exists():
        raise FileNotFoundError(f"Base env file not found: {base_path}")
    if not target_path.exists():
        raise FileNotFoundError(f"Target env file not found: {target_path}")

    base_vars = parse_env_file(base_path)
    target_vars = parse_env_file(target_path)

    return compare(
        base_vars,
        target_vars,
        ignore_values=ignore_values,
        ignore_keys=ignore_keys or [],
    )
