"""Tests for envdiff.encryptor."""
from __future__ import annotations

import pytest
from pathlib import Path

pytest.importorskip("cryptography")  # skip entire module if cryptography missing

from envdiff.encryptor import EncryptResult, encrypt, generate_key, write_encrypted


@pytest.fixture()
def tmp_env(tmp_path: Path) -> Path:
    return tmp_path / ".env"


def _write(p: Path, content: str) -> None:
    p.write_text(content, encoding="utf-8")


def test_generate_key_returns_string():
    key = generate_key()
    assert isinstance(key, str)
    assert len(key) > 20


def test_returns_encrypt_result(tmp_env):
    _write(tmp_env, "API_KEY=secret123\nHOST=localhost\n")
    key = generate_key()
    result = encrypt(tmp_env, key)
    assert isinstance(result, EncryptResult)


def test_secret_key_is_encrypted(tmp_env):
    _write(tmp_env, "API_KEY=secret123\n")
    key = generate_key()
    result = encrypt(tmp_env, key)
    assert "API_KEY" in result.encrypted_keys
    # The output line should start with enc:
    enc_line = next(l for l in result.lines if l.startswith("API_KEY="))
    assert "enc:" in enc_line


def test_plain_key_is_not_encrypted(tmp_env):
    _write(tmp_env, "HOST=localhost\n")
    key = generate_key()
    result = encrypt(tmp_env, key)
    assert "HOST" in result.skipped_keys
    assert result.lines[0].strip() == "HOST=localhost"


def test_total_keys_count(tmp_env):
    _write(tmp_env, "API_KEY=s\nDB_PASSWORD=p\nHOST=h\n")
    key = generate_key()
    result = encrypt(tmp_env, key)
    assert result.total_keys == 3


def test_comments_and_blanks_preserved(tmp_env):
    _write(tmp_env, "# comment\n\nHOST=localhost\n")
    key = generate_key()
    result = encrypt(tmp_env, key)
    assert result.lines[0].strip() == "# comment"
    assert result.lines[1].strip() == ""


def test_summary_string(tmp_env):
    _write(tmp_env, "TOKEN=abc\nHOST=localhost\n")
    key = generate_key()
    result = encrypt(tmp_env, key)
    s = result.summary()
    assert "encrypted" in s
    assert "plain" in s


def test_write_encrypted_creates_file(tmp_env, tmp_path):
    _write(tmp_env, "SECRET_KEY=abc\n")
    key = generate_key()
    result = encrypt(tmp_env, key)
    out = tmp_path / "out.env"
    write_encrypted(result, out)
    assert out.exists()
    content = out.read_text()
    assert "enc:" in content


def test_key_used_is_truncated(tmp_env):
    _write(tmp_env, "PASSWORD=hunter2\n")
    key = generate_key()
    result = encrypt(tmp_env, key)
    assert result.key_used is not None
    assert result.key_used.endswith("...")
    assert len(result.key_used) < len(key)


def test_empty_value_not_encrypted(tmp_env):
    _write(tmp_env, "API_KEY=\n")
    key = generate_key()
    result = encrypt(tmp_env, key)
    # empty value — nothing to encrypt
    assert "API_KEY" not in result.encrypted_keys
