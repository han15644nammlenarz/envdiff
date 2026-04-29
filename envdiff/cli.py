"""Command-line interface for envdiff."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import argparse

from envdiff.comparator import compare
from envdiff.parser import parse_env_file
from envdiff.reporter import format_json, format_text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff",
        description="Compare .env files across environments.",
    )
    parser.add_argument("base", type=Path, help="Base .env file (e.g. .env.example)")
    parser.add_argument("target", type=Path, help="Target .env file to compare against base")
    parser.add_argument(
        "--mask-secrets",
        action="store_true",
        default=False,
        help="Mask secret values in the output",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="output_format",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--ignore-values",
        action="store_true",
        default=False,
        help="Only report missing/extra keys; ignore value differences",
    )
    parser.add_argument(
        "--base-label",
        default="base",
        help="Label for the base file in output (default: base)",
    )
    parser.add_argument(
        "--target-label",
        default="target",
        help="Label for the target file in output (default: target)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        base_env = parse_env_file(args.base)
    except FileNotFoundError:
        print(f"Error: base file not found: {args.base}", file=sys.stderr)
        return 2

    try:
        target_env = parse_env_file(args.target)
    except FileNotFoundError:
        print(f"Error: target file not found: {args.target}", file=sys.stderr)
        return 2

    result = compare(base_env, target_env, ignore_values=args.ignore_values)

    if args.output_format == "json":
        data = format_json(
            result,
            base_label=args.base_label,
            target_label=args.target_label,
            mask_secrets=args.mask_secrets,
        )
        print(json.dumps(data, indent=2))
    else:
        output = format_text(
            result,
            base_label=args.base_label,
            target_label=args.target_label,
            mask_secrets=args.mask_secrets,
        )
        print(output)

    return 1 if result.has_differences else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
