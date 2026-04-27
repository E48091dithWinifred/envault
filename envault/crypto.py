"""Encryption and decryption utilities for envault using system keyring."""

import os
import base64
import secrets
import keyring
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

SERVICE_NAME = "envault"
KEY_LENGTH = 32  # 256-bit AES key
SALT_LENGTH = 16
NONCE_LENGTH = 12
ITERATIONS = 100_000


def _derive_key(password: bytes, salt: bytes) -> bytes:
    """Derive a 256-bit AES key from a password and salt using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LENGTH,
        salt=salt,
        iterations=ITERATIONS,
    )
    return kdf.derive(password)


def get_or_create_master_key(vault_id: str) -> bytes:
    """Retrieve the master key from the system keyring, creating it if absent."""
    stored = keyring.get_password(SERVICE_NAME, vault_id)
    if stored is None:
        raw_key = secrets.token_bytes(KEY_LENGTH)
        encoded = base64.b64encode(raw_key).decode("utf-8")
        keyring.set_password(SERVICE_NAME, vault_id, encoded)
        return raw_key
    return base64.b64decode(stored.encode("utf-8"))


def delete_master_key(vault_id: str) -> None:
    """Remove the master key from the system keyring."""
    keyring.delete_password(SERVICE_NAME, vault_id)


def encrypt(plaintext: str, vault_id: str) -> bytes:
    """
    Encrypt plaintext using AES-256-GCM.

    Returns bytes in the format: salt (16) + nonce (12) + ciphertext.
    """
    master_key = get_or_create_master_key(vault_id)
    salt = secrets.token_bytes(SALT_LENGTH)
    nonce = secrets.token_bytes(NONCE_LENGTH)
    derived_key = _derive_key(master_key, salt)
    aesgcm = AESGCM(derived_key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return salt + nonce + ciphertext


def decrypt(data: bytes, vault_id: str) -> str:
    """
    Decrypt bytes produced by :func:`encrypt`.

    Returns the original plaintext string.
    """
    if len(data) < SALT_LENGTH + NONCE_LENGTH + 1:
        raise ValueError("Encrypted data is too short or corrupted.")
    salt = data[:SALT_LENGTH]
    nonce = data[SALT_LENGTH:SALT_LENGTH + NONCE_LENGTH]
    ciphertext = data[SALT_LENGTH + NONCE_LENGTH:]
    master_key = get_or_create_master_key(vault_id)
    derived_key = _derive_key(master_key, salt)
    aesgcm = AESGCM(derived_key)
    plaintext_bytes = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext_bytes.decode("utf-8")
