"""Command-line interface for envdiff."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from envdiff.differ import diff_files
from envdiff.reporter import format_text, format_json
from envdiff.validator import validate
from envdiff.linter import lint
from envdiff.exporter import export_json, export_csv, export_markdown
from envdiff.merger import merge


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff",
        description="Compare, validate, lint, and merge .env files.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # --- diff ---
    diff_p = sub.add_parser("diff", help="Compare two .env files")
    diff_p.add_argument("base", help="Base .env file")
    diff_p.add_argument("target", help="Target .env file")
    diff_p.add_argument("--mask-secrets", action="store_true", default=False)
    diff_p.add_argument("--ignore-values", action="store_true", default=False)
    diff_p.add_argument("--format", choices=["text", "json"], default="text")
    diff_p.add_argument("--output", help="Write output to file")

    # --- validate ---
    val_p = sub.add_parser("validate", help="Validate a .env file against a reference")
    val_p.add_argument("reference", help="Reference (template) .env file")
    val_p.add_argument("target", help="Target .env file to validate")

    # --- lint ---
    lint_p = sub.add_parser("lint", help="Lint a .env file for style issues")
    lint_p.add_argument("file", help=".env file to lint")

    # --- export ---
    exp_p = sub.add_parser("export", help="Export diff result to a file")
    exp_p.add_argument("base")
    exp_p.add_argument("target")
    exp_p.add_argument("--format", choices=["json", "csv", "markdown"], default="json")
    exp_p.add_argument("--output", required=True, help="Output file path")
    exp_p.add_argument("--mask-secrets", action="store_true", default=False)

    # --- merge ---
    merge_p = sub.add_parser("merge", help="Merge multiple .env files (last wins)")
    merge_p.add_argument("files", nargs="+", help=".env files to merge in order")
    merge_p.add_argument(
        "--protected",
        nargs="*",
        default=[],
        metavar="KEY",
        help="Keys that must not be overridden by later files",
    )
    merge_p.add_argument("--output", help="Write merged env to file")
    merge_p.add_argument("--summary", action="store_true", default=False)

    return parser


def main(argv: Optional[List[str]] = None) -> int:  # noqa: C901
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "diff":
        result = diff_files(
            args.base,
            args.target,
            ignore_values=args.ignore_values,
        )
        if args.format == "json":
            output = format_json(result, mask_secrets=args.mask_secrets)
        else:
            output = format_text(result, mask_secrets=args.mask_secrets)
        if args.output:
            Path(args.output).write_text(output)
        else:
            print(output)
        return 1 if result.has_differences() else 0

    elif args.command == "validate":
        vresult = validate(args.reference, args.target)
        print(vresult.summary())
        return 0 if vresult.valid else 1

    elif args.command == "lint":
        lresult = lint(args.file)
        for issue in lresult.issues:
            print(issue)
        return 1 if lresult.has_issues() else 0

    elif args.command == "export":
        result = diff_files(args.base, args.target)
        fmt = args.format
        if fmt == "json":
            export_json(result, args.output, mask_secrets=args.mask_secrets)
        elif fmt == "csv":
            export_csv(result, args.output, mask_secrets=args.mask_secrets)
        else:
            export_markdown(result, args.output, mask_secrets=args.mask_secrets)
        return 0

    elif args.command == "merge":
        mresult = merge(args.files, protected=args.protected or None)
        if args.summary:
            print(mresult.summary())
        if args.output:
            lines = [f"{k}={v}" for k, v in mresult.merged.items()]
            from pathlib import Path
            Path(args.output).write_text("\n".join(lines) + "\n")
        else:
            for k, v in mresult.merged.items():
                print(f"{k}={v}")
        return 0

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
