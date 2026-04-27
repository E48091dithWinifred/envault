"""Tests for the envault CLI."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from envault.cli import cli

SAMPLE_ENV = "DB_HOST=localhost\nDB_PORT=5432\nSECRET_KEY=abc123\n"


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text(SAMPLE_ENV, encoding="utf-8")
    return f


class TestSetCommand:
    def test_set_success(self, runner, env_file):
        with patch("envault.cli.save_env") as mock_save:
            result = runner.invoke(cli, ["set", "myapp", str(env_file)])
        assert result.exit_code == 0
        assert "myapp" in result.output
        mock_save.assert_called_once_with("myapp", SAMPLE_ENV)

    def test_set_save_error(self, runner, env_file):
        with patch("envault.cli.save_env", side_effect=RuntimeError("encrypt fail")):
            result = runner.invoke(cli, ["set", "myapp", str(env_file)])
        assert result.exit_code == 1
        assert "Error" in result.output


class TestGetCommand:
    def test_get_success(self, runner):
        with patch("envault.cli.load_env", return_value=SAMPLE_ENV):
            result = runner.invoke(cli, ["get", "myapp"])
        assert result.exit_code == 0
        assert "DB_HOST=localhost" in result.output

    def test_get_export_flag(self, runner):
        with patch("envault.cli.load_env", return_value=SAMPLE_ENV):
            result = runner.invoke(cli, ["get", "myapp", "--export"])
        assert result.exit_code == 0
        assert "export DB_HOST=localhost" in result.output

    def test_get_not_found(self, runner):
        with patch("envault.cli.load_env", side_effect=FileNotFoundError):
            result = runner.invoke(cli, ["get", "missing"])
        assert result.exit_code == 1
        assert "not found" in result.output


class TestDeleteCommand:
    def test_delete_success(self, runner):
        with patch("envault.cli.delete_vault") as mock_del:
            result = runner.invoke(cli, ["delete", "myapp"], input="y\n")
        assert result.exit_code == 0
        assert "deleted" in result.output
        mock_del.assert_called_once_with("myapp")

    def test_delete_not_found(self, runner):
        with patch("envault.cli.delete_vault", side_effect=FileNotFoundError):
            result = runner.invoke(cli, ["delete", "missing"], input="y\n")
        assert result.exit_code == 1


class TestListCommand:
    def test_list_with_vaults(self, runner):
        with patch("envault.cli.list_vaults", return_value=["app1", "app2"]):
            result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        assert "app1" in result.output
        assert "app2" in result.output

    def test_list_empty(self, runner):
        with patch("envault.cli.list_vaults", return_value=[]):
            result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        assert "No vaults" in result.output


class TestPurgeCommand:
    def test_purge_success(self, runner):
        with patch("envault.cli.delete_master_key") as mock_purge:
            result = runner.invoke(cli, ["purge"], input="y\n")
        assert result.exit_code == 0
        assert "Master key removed" in result.output
        mock_purge.assert_called_once()
