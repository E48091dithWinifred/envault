"""Tests for envault.audit — audit log recording and retrieval."""

import json
import pytest
from pathlib import Path

from envault.audit import (
    _get_audit_log_path,
    record_event,
    read_events,
    clear_events,
    AUDIT_LOG_FILENAME,
)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


class TestGetAuditLogPath:
    def test_returns_path_inside_vault_dir(self, vault_dir):
        path = _get_audit_log_path(vault_dir)
        assert path.parent == vault_dir

    def test_filename_is_audit_log(self, vault_dir):
        path = _get_audit_log_path(vault_dir)
        assert path.name == AUDIT_LOG_FILENAME


class TestRecordEvent:
    def test_creates_log_file(self, vault_dir):
        record_event(vault_dir, "set", "myapp")
        assert _get_audit_log_path(vault_dir).exists()

    def test_event_is_valid_json(self, vault_dir):
        record_event(vault_dir, "get", "myapp")
        log_path = _get_audit_log_path(vault_dir)
        line = log_path.read_text().strip()
        event = json.loads(line)
        assert isinstance(event, dict)

    def test_event_contains_required_fields(self, vault_dir):
        record_event(vault_dir, "delete", "myapp", success=False, detail="not found")
        events = read_events(vault_dir)
        event = events[0]
        assert event["action"] == "delete"
        assert event["vault"] == "myapp"
        assert event["success"] is False
        assert event["detail"] == "not found"
        assert "timestamp" in event

    def test_multiple_events_appended(self, vault_dir):
        record_event(vault_dir, "set", "app1")
        record_event(vault_dir, "get", "app2")
        events = read_events(vault_dir)
        assert len(events) == 2

    def test_event_without_detail_has_no_detail_key(self, vault_dir):
        record_event(vault_dir, "list", "*")
        events = read_events(vault_dir)
        assert "detail" not in events[0]


class TestReadEvents:
    def test_returns_empty_list_when_no_log(self, vault_dir):
        events = read_events(vault_dir)
        assert events == []

    def test_returns_all_events_in_order(self, vault_dir):
        for i in range(3):
            record_event(vault_dir, "set", f"vault{i}")
        events = read_events(vault_dir)
        assert [e["vault"] for e in events] == ["vault0", "vault1", "vault2"]


class TestClearEvents:
    def test_removes_log_file(self, vault_dir):
        record_event(vault_dir, "set", "myapp")
        clear_events(vault_dir)
        assert not _get_audit_log_path(vault_dir).exists()

    def test_clear_on_missing_log_does_not_raise(self, vault_dir):
        clear_events(vault_dir)  # should not raise
