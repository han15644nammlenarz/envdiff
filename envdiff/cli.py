"""CLI entry point for envdiff."""

from __future__ import annotations

import argparse
import sys

from envdiff.differ import diff_files
from envdiff.reporter import format_text, format_json
from envdiff.exporter import export_json, export_csv, export_markdown
from envdiff.validator import validate
from envdiff.linter import lint_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff",
        description="Compare .env files across environments.",
    )
    sub = parser.add_subparsers(dest="command")

    # diff command
    diff_p = sub.add_parser("diff", help="Compare two .env files")
    diff_p.add_argument("base", help="Base .env file")
    diff_p.add_argument("target", help="Target .env file")
    diff_p.add_argument("--mask-secrets", action="store_true", help="Mask secret values")
    diff_p.add_argument("--ignore-values", action="store_true", help="Ignore value mismatches")
    diff_p.add_argument("--format", choices=["text", "json"], default="text")
    diff_p.add_argument("--export", choices=["json", "csv", "markdown"], help="Export results")
    diff_p.add_argument("--output", help="Output file for export")

    # validate command
    val_p = sub.add_parser("validate", help="Validate a .env file against a reference")
    val_p.add_argument("reference", help="Reference .env file (e.g. .env.example)")
    val_p.add_argument("target", help="Target .env file to validate")
    val_p.add_argument("--mask-secrets", action="store_true")

    # lint command
    lint_p = sub.add_parser("lint", help="Lint a .env file for style issues")
    lint_p.add_argument("file", help=".env file to lint")
    lint_p.add_argument("--strict", action="store_true", help="Exit non-zero on warnings too")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "diff":
        result = diff_files(
            args.base,
            args.target,
            mask_secrets=args.mask_secrets,
            ignore_values=args.ignore_values,
        )
        if args.export:
            output = args.output or f"envdiff_report.{args.export}"
            if args.export == "json":
                export_json(result, output, mask_secrets=args.mask_secrets)
            elif args.export == "csv":
                export_csv(result, output, mask_secrets=args.mask_secrets)
            elif args.export == "markdown":
                export_markdown(result, output, mask_secrets=args.mask_secrets)
            print(f"Report exported to {output}")
        else:
            if args.format == "json":
                print(format_json(result, mask_secrets=args.mask_secrets))
            else:
                print(format_text(result, mask_secrets=args.mask_secrets))
        return 1 if result.has_differences else 0

    elif args.command == "validate":
        vresult = validate(
            args.reference,
            args.target,
            mask_secrets=args.mask_secrets,
        )
        print(vresult.summary())
        return 0 if vresult.is_valid else 1

    elif args.command == "lint":
        lresult = lint_file(args.file)
        print(lresult.summary())
        for issue in lresult.issues:
            print(f"  {issue}")
        if args.strict:
            return 1 if lresult.has_issues else 0
        return 1 if lresult.errors else 0

    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
