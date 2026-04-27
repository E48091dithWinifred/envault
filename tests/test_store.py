"""Tests for envault/store.py — vault persistence layer."""

import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from envault.store import (
    _get_vault_path,
    _ensure_vault_dir,
    save_env,
    load_env,
    delete_vault,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def vault_dir(tmp_path):
    """Patch the vault base directory to a temporary path for isolation."""
    with patch("envault.store.VAULT_DIR", tmp_path):
        yield tmp_path


@pytest.fixture()
def sample_env():
    return {"DATABASE_URL": "postgres://localhost/db", "SECRET_KEY": "s3cr3t"}


# ---------------------------------------------------------------------------
# _get_vault_path
# ---------------------------------------------------------------------------

class TestGetVaultPath:
    def test_returns_path_object(self, vault_dir):
        path = _get_vault_path("myapp")
        assert isinstance(path, Path)

    def test_path_contains_vault_name(self, vault_dir):
        path = _get_vault_path("myapp")
        assert "myapp" in str(path)

    def test_path_ends_with_json(self, vault_dir):
        path = _get_vault_path("myapp")
        assert path.suffix == ".json"

    def test_path_is_under_vault_dir(self, vault_dir):
        path = _get_vault_path("myapp")
        assert str(path).startswith(str(vault_dir))


# ---------------------------------------------------------------------------
# _ensure_vault_dir
# ---------------------------------------------------------------------------

class TestEnsureVaultDir:
    def test_creates_directory_if_missing(self, tmp_path):
        target = tmp_path / "nested" / "vaults"
        with patch("envault.store.VAULT_DIR", target):
            _ensure_vault_dir()
        assert target.exists()

    def test_does_not_raise_if_already_exists(self, vault_dir):
        # Call twice — second call must not raise
        _ensure_vault_dir()
        _ensure_vault_dir()


# ---------------------------------------------------------------------------
# save_env / load_env round-trip
# ---------------------------------------------------------------------------

class TestSaveAndLoadEnv:
    def test_save_creates_file(self, vault_dir, sample_env):
        save_env("myapp", sample_env)
        path = _get_vault_path("myapp")
        assert path.exists()

    def test_load_returns_original_data(self, vault_dir, sample_env):
        save_env("myapp", sample_env)
        loaded = load_env("myapp")
        assert loaded == sample_env

    def test_save_overwrites_existing(self, vault_dir, sample_env):
        save_env("myapp", sample_env)
        updated = {"NEW_KEY": "new_value"}
        save_env("myapp", updated)
        loaded = load_env("myapp")
        assert loaded == updated

    def test_load_nonexistent_vault_raises(self, vault_dir):
        with pytest.raises(FileNotFoundError):
            load_env("does_not_exist")

    def test_saved_file_is_valid_json(self, vault_dir, sample_env):
        save_env("myapp", sample_env)
        path = _get_vault_path("myapp")
        with open(path) as fh:
            data = json.load(fh)
        assert isinstance(data, dict)


# ---------------------------------------------------------------------------
# delete_vault
# ---------------------------------------------------------------------------

class TestDeleteVault:
    def test_delete_removes_file(self, vault_dir, sample_env):
        save_env("myapp", sample_env)
        delete_vault("myapp")
        path = _get_vault_path("myapp")
        assert not path.exists()

    def test_delete_nonexistent_vault_raises(self, vault_dir):
        with pytest.raises(FileNotFoundError):
            delete_vault("ghost")


# ---------------------------------------------------------------------------
# list_vaults (if present in store.py)
# ---------------------------------------------------------------------------

class TestListVaults:
    def test_empty_dir_returns_empty_list(self, vault_dir):
        from envault.store import list_vaults
        assert list_vaults() == []

    def test_returns_saved_vault_names(self, vault_dir, sample_env):
        from envault.store import list_vaults
        save_env("alpha", sample_env)
        save_env("beta", sample_env)
        names = list_vaults()
        assert set(names) == {"alpha", "beta"}

    def test_ignores_non_json_files(self, vault_dir, sample_env):
        from envault.store import list_vaults
        # Plant a stray file that should not appear in the listing
        (vault_dir / "README.txt").write_text("ignore me")
        save_env("gamma", sample_env)
        names = list_vaults()
        assert names == ["gamma"]
