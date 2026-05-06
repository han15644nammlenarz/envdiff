"""High-level helper that diffs two .env files end-to-end."""

from __future__ import annotations

from envdiff.parser import parse_env_file
from envdiff.comparator import compare, DiffResult


def diff_files(
    base_path: str,
    target_path: str,
    *,
    mask_secrets: bool = True,
    ignore_values: bool = False,
) -> DiffResult:
    """Parse *base_path* and *target_path* then return a :class:`DiffResult`.

    Parameters
    ----------
    base_path:     Path to the reference .env file.
    target_path:   Path to the .env file being compared.
    mask_secrets:  When ``True`` secret values are replaced with ``***``.
    ignore_values: When ``True`` only key presence is checked, not values.
    """
    base = parse_env_file(base_path)
    target = parse_env_file(target_path)
    return compare(base, target, mask_secrets=mask_secrets, ignore_values=ignore_values)
