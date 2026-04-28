"""Audit log for tracking vault access and modification events."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

AUDIT_LOG_FILENAME = "audit.log"


def _get_audit_log_path(vault_dir: Path) -> Path:
    """Return the path to the audit log file within the vault directory."""
    return vault_dir / AUDIT_LOG_FILENAME


def record_event(
    vault_dir: Path,
    action: str,
    vault_name: str,
    success: bool = True,
    detail: Optional[str] = None,
) -> None:
    """Append a structured audit event to the log file.

    Args:
        vault_dir: Directory where the audit log is stored.
        action: One of 'set', 'get', 'delete', 'list'.
        vault_name: Name of the vault being acted upon.
        success: Whether the operation succeeded.
        detail: Optional extra information (e.g. error message).
    """
    log_path = _get_audit_log_path(vault_dir)
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "vault": vault_name,
        "success": success,
    }
    if detail:
        event["detail"] = detail

    with open(log_path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(event) + "\n")


def read_events(vault_dir: Path) -> list[dict]:
    """Read and parse all audit events from the log file.

    Returns an empty list if no log file exists yet.
    """
    log_path = _get_audit_log_path(vault_dir)
    if not log_path.exists():
        return []

    events = []
    with open(log_path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


def clear_events(vault_dir: Path) -> None:
    """Delete the audit log file entirely."""
    log_path = _get_audit_log_path(vault_dir)
    if log_path.exists():
        os.remove(log_path)
