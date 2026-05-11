"""CLI sub-command: encrypt secret values in a .env file."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.encryptor import EncryptResult, encrypt, generate_key, write_encrypted


def add_encrypt_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "encrypt",
        help="Encrypt secret values in a .env file.",
    )
    p.add_argument("file", help="Path to the .env file to encrypt.")
    p.add_argument(
        "--key",
        default=None,
        help="Fernet key (base64). Omit to auto-generate and print a new key.",
    )
    p.add_argument(
        "--out",
        default=None,
        help="Output path. Defaults to overwriting the input file.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be encrypted without writing.",
    )
    p.add_argument(
        "--generate-key",
        action="store_true",
        help="Generate and print a new Fernet key, then exit.",
    )
    p.set_defaults(func=run_encrypt)


def run_encrypt(args: argparse.Namespace) -> int:
    if getattr(args, "generate_key", False):
        print(generate_key())
        return 0

    if not Path(args.file).exists():
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        return 1

    fernet_key: str
    if args.key:
        fernet_key = args.key
    else:
        fernet_key = generate_key()
        print(f"Generated key (save this!): {fernet_key}")

    try:
        result: EncryptResult = encrypt(args.file, fernet_key)
    except Exception as exc:  # pragma: no cover
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(result.summary())
    if result.encrypted_keys:
        print("  Encrypted:", ", ".join(result.encrypted_keys))
    if result.skipped_keys:
        print("  Plain:    ", ", ".join(result.skipped_keys))

    if not args.dry_run:
        dest = args.out or args.file
        write_encrypted(result, dest)
        print(f"Written to {dest}")

    return 0
