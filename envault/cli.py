"""Command-line interface for envault."""

import sys
import click
from pathlib import Path

from envault.store import save_env, load_env, delete_vault, list_vaults
from envault.crypto import delete_master_key


@click.group()
def cli():
    """envault — secure local environment variable manager."""
    pass


@cli.command("set")
@click.argument("vault_name")
@click.argument("env_file", type=click.Path(exists=True, path_type=Path))
def set_vault(vault_name: str, env_file: Path):
    """Encrypt and store an .env file under VAULT_NAME."""
    try:
        raw = env_file.read_text(encoding="utf-8")
        save_env(vault_name, raw)
        click.echo(f"✓ Vault '{vault_name}' saved successfully.")
    except Exception as exc:
        click.echo(f"Error saving vault: {exc}", err=True)
        sys.exit(1)


@cli.command("get")
@click.argument("vault_name")
@click.option("--export", is_flag=True, help="Print as export statements.")
def get_vault(vault_name: str, export: bool):
    """Decrypt and print the contents of VAULT_NAME."""
    try:
        contents = load_env(vault_name)
        if export:
            for line in contents.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    click.echo(f"export {line}")
        else:
            click.echo(contents)
    except FileNotFoundError:
        click.echo(f"Vault '{vault_name}' not found.", err=True)
        sys.exit(1)
    except Exception as exc:
        click.echo(f"Error loading vault: {exc}", err=True)
        sys.exit(1)


@cli.command("delete")
@click.argument("vault_name")
@click.confirmation_option(prompt="Are you sure you want to delete this vault?")
def delete_vault_cmd(vault_name: str):
    """Delete the encrypted vault for VAULT_NAME."""
    try:
        delete_vault(vault_name)
        click.echo(f"✓ Vault '{vault_name}' deleted.")
    except FileNotFoundError:
        click.echo(f"Vault '{vault_name}' not found.", err=True)
        sys.exit(1)


@cli.command("list")
def list_vaults_cmd():
    """List all stored vault names."""
    vaults = list_vaults()
    if not vaults:
        click.echo("No vaults found.")
    else:
        click.echo("Stored vaults:")
        for name in sorted(vaults):
            click.echo(f"  • {name}")


@cli.command("purge")
@click.confirmation_option(prompt="Delete master key from keyring? This cannot be undone.")
def purge_master_key():
    """Remove the master encryption key from the system keyring."""
    try:
        delete_master_key()
        click.echo("✓ Master key removed from keyring.")
    except Exception as exc:
        click.echo(f"Error removing master key: {exc}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
