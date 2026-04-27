"""Encrypted .env file storage and retrieval.

This module handles reading, writing, and managing encrypted .env files.
Each .env file is encrypted using the master key from the system keyring.
"""

import json
import os
from pathlib import Path
from typing import Optional

from envault.crypto import decrypt, encrypt, get_or_create_master_key

# Default directory for storing encrypted vault files
DEFAULT_VAULT_DIR = Path.home() / ".envault" / "vaults"

# Extension used for encrypted vault files
VAULT_EXTENSION = ".vault"


def _get_vault_path(name: str, vault_dir: Optional[Path] = None) -> Path:
    """Return the full path for a named vault file.

    Args:
        name: Logical name of the vault (e.g. 'myproject').
        vault_dir: Directory to store vault files. Defaults to DEFAULT_VAULT_DIR.

    Returns:
        Path object pointing to the vault file.
    """
    directory = vault_dir or DEFAULT_VAULT_DIR
    # Sanitise name to avoid path traversal
    safe_name = Path(name).name
    return directory / f"{safe_name}{VAULT_EXTENSION}"


def _ensure_vault_dir(vault_dir: Optional[Path] = None) -> Path:
    """Create the vault directory if it does not exist.

    Args:
        vault_dir: Directory to create. Defaults to DEFAULT_VAULT_DIR.

    Returns:
        The resolved vault directory path.
    """
    directory = vault_dir or DEFAULT_VAULT_DIR
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def save_env(name: str, env_vars: dict[str, str], vault_dir: Optional[Path] = None) -> Path:
    """Encrypt and persist a dictionary of environment variables.

    Args:
        name: Logical name for the vault (used as the filename).
        env_vars: Mapping of variable names to their values.
        vault_dir: Optional override for the vault storage directory.

    Returns:
        Path where the vault file was written.

    Raises:
        ValueError: If *name* is empty or contains only whitespace.
    """
    if not name or not name.strip():
        raise ValueError("Vault name must not be empty.")

    master_key = get_or_create_master_key()
    plaintext = json.dumps(env_vars).encode()
    ciphertext = encrypt(plaintext, master_key)

    _ensure_vault_dir(vault_dir)
    vault_path = _get_vault_path(name, vault_dir)
    vault_path.write_bytes(ciphertext)
    return vault_path


def load_env(name: str, vault_dir: Optional[Path] = None) -> dict[str, str]:
    """Decrypt and return environment variables stored in a named vault.

    Args:
        name: Logical name of the vault to load.
        vault_dir: Optional override for the vault storage directory.

    Returns:
        Dictionary of environment variable names to values.

    Raises:
        FileNotFoundError: If no vault with *name* exists.
        ValueError: If decryption fails or the file content is corrupt.
    """
    vault_path = _get_vault_path(name, vault_dir)
    if not vault_path.exists():
        raise FileNotFoundError(f"No vault named '{name}' found at {vault_path}.")

    master_key = get_or_create_master_key()
    ciphertext = vault_path.read_bytes()

    try:
        plaintext = decrypt(ciphertext, master_key)
        return json.loads(plaintext.decode())
    except Exception as exc:
        raise ValueError(f"Failed to decrypt vault '{name}': {exc}") from exc


def delete_vault(name: str, vault_dir: Optional[Path] = None) -> bool:
    """Remove an encrypted vault file from disk.

    Args:
        name: Logical name of the vault to delete.
        vault_dir: Optional override for the vault storage directory.

    Returns:
        True if the file was deleted, False if it did not exist.
    """
    vault_path = _get_vault_path(name, vault_dir)
    if vault_path.exists():
        vault_path.unlink()
        return True
    return False


def list_vaults(vault_dir: Optional[Path] = None) -> list[str]:
    """List the names of all stored vaults.

    Args:
        vault_dir: Optional override for the vault storage directory.

    Returns:
        Sorted list of vault names (without file extension).
    """
    directory = vault_dir or DEFAULT_VAULT_DIR
    if not directory.exists():
        return []
    return sorted(
        p.stem for p in directory.iterdir() if p.suffix == VAULT_EXTENSION
    )


def inject_into_environment(name: str, vault_dir: Optional[Path] = None) -> dict[str, str]:
    """Load a vault and inject its variables into the current process environment.

    Existing environment variables are *not* overwritten.

    Args:
        name: Logical name of the vault to inject.
        vault_dir: Optional override for the vault storage directory.

    Returns:
        Dictionary of variables that were actually injected (skips existing keys).
    """
    env_vars = load_env(name, vault_dir)
    injected: dict[str, str] = {}
    for key, value in env_vars.items():
        if key not in os.environ:
            os.environ[key] = value
            injected[key] = value
    return injected
