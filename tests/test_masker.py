"""Tests for envdiff.masker."""

import pytest
from envdiff.masker import is_secret_key, mask_dict, mask_value, MASK_PLACEHOLDER


def test_is_secret_key_password():
    assert is_secret_key("DB_PASSWORD")


def test_is_secret_key_token():
    assert is_secret_key("GITHUB_TOKEN")


def test_is_secret_key_api_key():
    assert is_secret_key("STRIPE_API_KEY")


def test_is_secret_key_not_secret():
    assert not is_secret_key("APP_NAME")
    assert not is_secret_key("DEBUG")
    assert not is_secret_key("PORT")


def test_is_secret_key_custom_keywords():
    assert is_secret_key("MY_CUSTOM_FIELD", keywords=["custom"])
    assert not is_secret_key("MY_CUSTOM_FIELD", keywords=["password"])


def test_mask_dict_replaces_secrets():
    env = {"APP_NAME": "myapp", "DB_PASSWORD": "s3cr3t", "PORT": "8080"}
    masked = mask_dict(env)
    assert masked["APP_NAME"] == "myapp"
    assert masked["PORT"] == "8080"
    assert masked["DB_PASSWORD"] == MASK_PLACEHOLDER


def test_mask_dict_does_not_mutate_original():
    env = {"DB_PASSWORD": "s3cr3t"}
    masked = mask_dict(env)
    assert env["DB_PASSWORD"] == "s3cr3t"
    assert masked["DB_PASSWORD"] == MASK_PLACEHOLDER


def test_mask_dict_empty():
    assert mask_dict({}) == {}


def test_mask_value_secret():
    assert mask_value("AUTH_TOKEN", "my-token") == MASK_PLACEHOLDER


def test_mask_value_non_secret():
    assert mask_value("LOG_LEVEL", "info") == "info"


def test_mask_dict_custom_placeholder():
    env = {"SECRET_KEY": "abc123"}
    masked = mask_dict(env, placeholder="[REDACTED]")
    assert masked["SECRET_KEY"] == "[REDACTED]"
