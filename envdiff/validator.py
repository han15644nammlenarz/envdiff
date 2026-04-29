"""Validator module for envdiff.

Provides validation utilities to check .env files against a reference
(e.g., a .env.example) and return structured validation results.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.comparator import compare, DiffResult
from envdiff.parser import parse_env_file


@dataclass
class ValidationResult:
    """Holds the outcome of validating an env file against a reference."""

    reference_path: str
    target_path: str
    is_valid: bool
    missing_keys: List[str] = field(default_factory=list)
    extra_keys: List[str] = field(default_factory=list)
    mismatched_keys: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def summary(self) -> str:
        """Return a human-readable one-line summary."""
        if self.is_valid:
            return f"{self.target_path} is valid against {self.reference_path}."
        issues = []
        if self.missing_keys:
            issues.append(f"{len(self.missing_keys)} missing")
        if self.extra_keys:
            issues.append(f"{len(self.extra_keys)} extra")
        if self.mismatched_keys:
            issues.append(f"{len(self.mismatched_keys)} mismatched")
        return (
            f"{self.target_path} is INVALID against {self.reference_path}: "
            + ", ".join(issues)
            + "."
        )


def validate(
    reference_path: str,
    target_path: str,
    ignore_extra: bool = False,
    ignore_values: bool = True,
) -> ValidationResult:
    """Validate *target_path* against *reference_path*.

    Args:
        reference_path: Path to the reference .env file (e.g. .env.example).
        target_path: Path to the env file being validated.
        ignore_extra: When True, extra keys in target are not treated as errors.
        ignore_values: When True, value mismatches are not treated as errors
                       (useful when the reference uses placeholder values).

    Returns:
        A :class:`ValidationResult` describing the outcome.
    """
    errors: List[str] = []

    try:
        reference = parse_env_file(reference_path)
    except (OSError, IOError) as exc:
        return ValidationResult(
            reference_path=reference_path,
            target_path=target_path,
            is_valid=False,
            errors=[f"Cannot read reference file: {exc}"],
        )

    try:
        target = parse_env_file(target_path)
    except (OSError, IOError) as exc:
        return ValidationResult(
            reference_path=reference_path,
            target_path=target_path,
            is_valid=False,
            errors=[f"Cannot read target file: {exc}"],
        )

    diff: DiffResult = compare(reference, target, ignore_values=ignore_values)

    effective_extra = [] if ignore_extra else diff.extra_keys
    effective_mismatch = [] if ignore_values else diff.mismatched_keys

    is_valid = (
        not diff.missing_keys
        and not effective_extra
        and not effective_mismatch
        and not errors
    )

    return ValidationResult(
        reference_path=reference_path,
        target_path=target_path,
        is_valid=is_valid,
        missing_keys=diff.missing_keys,
        extra_keys=diff.extra_keys,
        mismatched_keys=diff.mismatched_keys,
        errors=errors,
    )
