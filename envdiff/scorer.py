"""Scores .env file health based on linting, secrets exposure, and key coverage."""

from dataclasses import dataclass, field
from typing import List

from envdiff.linter import lint, LintResult
from envdiff.profiler import profile, ProfileResult


@dataclass
class ScoreResult:
    total_score: int
    max_score: int
    lint_score: int
    secret_score: int
    coverage_score: int
    warnings: List[str] = field(default_factory=list)

    @property
    def grade(self) -> str:
        pct = self.total_score / self.max_score if self.max_score else 0
        if pct >= 0.90:
            return "A"
        elif pct >= 0.75:
            return "B"
        elif pct >= 0.60:
            return "C"
        elif pct >= 0.40:
            return "D"
        return "F"

    def summary(self) -> str:
        lines = [
            f"Score: {self.total_score}/{self.max_score} (Grade: {self.grade})",
            f"  Lint:     {self.lint_score}/40",
            f"  Secrets:  {self.secret_score}/30",
            f"  Coverage: {self.coverage_score}/30",
        ]
        if self.warnings:
            lines.append("Warnings:")
            for w in self.warnings:
                lines.append(f"  - {w}")
        return "\n".join(lines)


def score(path: str, reference_path: str = None) -> ScoreResult:
    """Score a .env file for overall health.

    Args:
        path: Path to the .env file to score.
        reference_path: Optional reference .env file for coverage scoring.

    Returns:
        A ScoreResult with component scores and a letter grade.
    """
    warnings: List[str] = []

    # --- Lint score (0-40) ---
    lint_result: LintResult = lint(path)
    error_count = len(lint_result.errors())
    warning_count = len(lint_result.warnings())
    lint_score = max(0, 40 - (error_count * 10) - (warning_count * 3))
    if error_count:
        warnings.append(f"{error_count} lint error(s) found")
    if warning_count:
        warnings.append(f"{warning_count} lint warning(s) found")

    # --- Secret score (0-30): penalise plaintext secrets ---
    prof: ProfileResult = profile(path)
    secret_ratio = prof.secret_keys / prof.total_keys if prof.total_keys else 0
    blank_secret_ratio = (
        prof.blank_secret_values / prof.secret_keys if prof.secret_keys else 0
    )
    # Reward blanked/placeholder secrets, penalise populated ones
    secret_score = int(30 * blank_secret_ratio) if prof.secret_keys else 30
    if secret_ratio > 0 and blank_secret_ratio < 1.0:
        warnings.append("Some secret keys have non-blank values")

    # --- Coverage score (0-30): keys present vs reference ---
    if reference_path:
        from envdiff.differ import diff_files
        diff = diff_files(path, reference_path)
        missing = len(diff.missing_keys)
        extra = len(diff.extra_keys)
        ref_prof: ProfileResult = profile(reference_path)
        total_ref = ref_prof.total_keys or 1
        coverage_score = max(0, int(30 * (1 - missing / total_ref)))
        if missing:
            warnings.append(f"{missing} key(s) missing vs reference")
        if extra:
            warnings.append(f"{extra} extra key(s) not in reference")
    else:
        coverage_score = 30  # no reference — full marks by default

    total = lint_score + secret_score + coverage_score
    return ScoreResult(
        total_score=total,
        max_score=100,
        lint_score=lint_score,
        secret_score=secret_score,
        coverage_score=coverage_score,
        warnings=warnings,
    )
