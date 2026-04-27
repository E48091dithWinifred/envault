"""Tests for envault.crypto encryption/decryption utilities."""

import base64
import pytest
from unittest.mock import patch, MagicMock

from envault.crypto import (
    encrypt,
    decrypt,
    get_or_create_master_key,
    delete_master_key,
    SERVICE_NAME,
    KEY_LENGTH,
)

VAULT_ID = "test-vault"


@pytest.fixture(autouse=True)
def mock_keyring(monkeypatch):
    """Patch keyring so tests never touch the real system keyring."""
    store: dict[str, str] = {}

    def fake_get(service, username):
        return store.get(f"{service}:{username}")

    def fake_set(service, username, password):
        store[f"{service}:{username}"] = password

    def fake_delete(service, username):
        key = f"{service}:{username}"
        if key not in store:
            raise KeyError(key)
        del store[key]

    monkeypatch.setattr("envault.crypto.keyring.get_password", fake_get)
    monkeypatch.setattr("envault.crypto.keyring.set_password", fake_set)
    monkeypatch.setattr("envault.crypto.keyring.delete_password", fake_delete)
    return store


class TestGetOrCreateMasterKey:
    def test_creates_key_when_absent(self):
        key = get_or_create_master_key(VAULT_ID)
        assert isinstance(key, bytes)
        assert len(key) == KEY_LENGTH

    def test_returns_same_key_on_second_call(self):
        key1 = get_or_create_master_key(VAULT_ID)
        key2 = get_or_create_master_key(VAULT_ID)
        assert key1 == key2

    def test_different_vault_ids_produce_different_keys(self):
        key_a = get_or_create_master_key("vault-a")
        key_b = get_or_create_master_key("vault-b")
        assert key_a != key_b


class TestDeleteMasterKey:
    def test_delete_removes_key(self, mock_keyring):
        get_or_create_master_key(VAULT_ID)
        delete_master_key(VAULT_ID)
        assert f"{SERVICE_NAME}:{VAULT_ID}" not in mock_keyring


class TestEncryptDecrypt:
    def test_roundtrip(self):
        plaintext = "SECRET_KEY=super_secret_value"
        ciphertext = encrypt(plaintext, VAULT_ID)
        result = decrypt(ciphertext, VAULT_ID)
        assert result == plaintext

    def test_encrypted_output_is_bytes(self):
        ciphertext = encrypt("FOO=bar", VAULT_ID)
        assert isinstance(ciphertext, bytes)

    def test_same_plaintext_produces_different_ciphertexts(self):
        plaintext = "FOO=bar"
        ct1 = encrypt(plaintext, VAULT_ID)
        ct2 = encrypt(plaintext, VAULT_ID)
        assert ct1 != ct2  # different nonce/salt each time

    def test_decrypt_raises_on_tampered_data(self):
        ciphertext = bytearray(encrypt("FOO=bar", VAULT_ID))
        ciphertext[-1] ^= 0xFF  # flip a bit in the auth tag
        with pytest.raises(Exception):
            decrypt(bytes(ciphertext), VAULT_ID)

    def test_decrypt_raises_on_too_short_data(self):
        with pytest.raises(ValueError, match="too short or corrupted"):
            decrypt(b"short", VAULT_ID)

    def test_multiline_env_content(self):
        content = "DB_URL=postgres://user:pass@localhost/db\nAPI_KEY=abc123\nDEBUG=true"
        assert decrypt(encrypt(content, VAULT_ID), VAULT_ID) == content
