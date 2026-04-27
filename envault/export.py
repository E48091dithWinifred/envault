"""Export decrypted environment variables to shell-compatible formats."""

from __future__ import annotations

import shlex
from typing import Dict, Literal

OutputFormat = Literal["export", "dotenv", "json"]


def _validate_format(fmt: str) -> OutputFormat:
    valid = ("export", "dotenv", "json")
    if fmt not in valid:
        raise ValueError(f"Unsupported format '{fmt}'. Choose from: {', '.join(valid)}")
    return fmt  # type: ignore[return-value]


def render_export(env_vars: Dict[str, str]) -> str:
    """Render variables as shell export statements.

    Example output::

        export FOO='bar'
        export SECRET='p@ssw0rd'
    """
    lines = []
    for key, value in sorted(env_vars.items()):
        quoted = shlex.quote(value)
        lines.append(f"export {key}={quoted}")
    return "\n".join(lines)


def render_dotenv(env_vars: Dict[str, str]) -> str:
    """Render variables in .env file format.

    Example output::

        FOO='bar'
        SECRET='p@ssw0rd'
    """
    lines = []
    for key, value in sorted(env_vars.items()):
        quoted = shlex.quote(value)
        lines.append(f"{key}={quoted}")
    return "\n".join(lines)


def render_json(env_vars: Dict[str, str]) -> str:
    """Render variables as a JSON object."""
    import json

    return json.dumps(env_vars, indent=2, sort_keys=True)


def render(env_vars: Dict[str, str], fmt: str = "export") -> str:
    """Render *env_vars* in the requested *fmt*.

    Parameters
    ----------
    env_vars:
        Mapping of variable names to their values.
    fmt:
        One of ``'export'``, ``'dotenv'``, or ``'json'``.

    Returns
    -------
    str
        The formatted string ready to be printed or written to a file.
    """
    _validate_format(fmt)
    if fmt == "export":
        return render_export(env_vars)
    if fmt == "dotenv":
        return render_dotenv(env_vars)
    return render_json(env_vars)
