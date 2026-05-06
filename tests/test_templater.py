"""Tests for envdiff.templater."""

from __future__ import annotations

import pytest
from pathlib import Path

from envdiff.templater import generate_template, TemplateResult


@pytest.fixture()
def tmp_env(tmp_path: Path):
    """Return a helper that writes a .env file and yields its path string."""
    def _write(content: str, name: str = ".env") -> str:
        p = tmp_path / name
        p.write_text(content, encoding="utf-8")
        return str(p)

    return _write


def test_returns_template_result(tmp_env, tmp_path):
    src = tmp_env("APP_NAME=myapp\nDB_PASSWORD=secret\n")
    out = str(tmp_path / ".env.example")
    result = generate_template(src, output=out)
    assert isinstance(result, TemplateResult)


def test_secret_value_is_blanked(tmp_env, tmp_path):
    src = tmp_env("DB_PASSWORD=hunter2\n")
    out = str(tmp_path / ".env.example")
    generate_template(src, output=out)
    content = Path(out).read_text()
    assert "DB_PASSWORD=" in content
    assert "hunter2" not in content


def test_non_secret_value_retained(tmp_env, tmp_path):
    src = tmp_env("APP_NAME=myapp\n")
    out = str(tmp_path / ".env.example")
    generate_template(src, output=out)
    content = Path(out).read_text()
    assert "APP_NAME=myapp" in content


def test_keys_blanked_list_populated(tmp_env, tmp_path):
    src = tmp_env("SECRET_KEY=abc\nAPI_TOKEN=xyz\nAPP_ENV=prod\n")
    out = str(tmp_path / ".env.example")
    result = generate_template(src, output=out)
    assert "SECRET_KEY" in result.keys_blanked
    assert "API_TOKEN" in result.keys_blanked
    assert "APP_ENV" in result.keys_written


def test_custom_placeholder(tmp_env, tmp_path):
    src = tmp_env("DB_PASSWORD=secret\n")
    out = str(tmp_path / ".env.example")
    generate_template(src, output=out, placeholder="CHANGE_ME")
    content = Path(out).read_text()
    assert "DB_PASSWORD=CHANGE_ME" in content


def test_default_output_path_is_dot_example(tmp_env, tmp_path):
    src = tmp_env("X=1\n", name="staging.env")
    result = generate_template(src)
    assert result.path.endswith(".example")
    assert Path(result.path).exists()


def test_header_comment_written_by_default(tmp_env, tmp_path):
    src = tmp_env("X=1\n")
    out = str(tmp_path / ".env.example")
    generate_template(src, output=out)
    content = Path(out).read_text()
    assert "envdiff" in content


def test_keep_comments_false_omits_header(tmp_env, tmp_path):
    src = tmp_env("X=1\n")
    out = str(tmp_path / ".env.example")
    generate_template(src, output=out, keep_comments=False)
    content = Path(out).read_text()
    assert "envdiff" not in content


def test_summary_contains_path_and_counts(tmp_env, tmp_path):
    src = tmp_env("APP=x\nDB_PASSWORD=s\n")
    out = str(tmp_path / ".env.example")
    result = generate_template(src, output=out)
    s = result.summary()
    assert result.path in s
    assert "1 blanked" in s


def test_custom_secret_keywords(tmp_env, tmp_path):
    src = tmp_env("INTERNAL_CERT=abc\nAPP_NAME=myapp\n")
    out = str(tmp_path / ".env.example")
    result = generate_template(src, output=out, secret_keywords=["cert"])
    assert "INTERNAL_CERT" in result.keys_blanked
    assert "APP_NAME" in result.keys_written
