"""Tests for envault.export rendering helpers."""

import json
import pytest

from envault.export import render, render_dotenv, render_export, render_json, _validate_format

SAMPLE: dict[str, str] = {
    "DATABASE_URL": "postgres://user:p@ss@localhost/db",
    "API_KEY": "abc123",
    "GREETING": "hello world",
}


class TestValidateFormat:
    def test_valid_formats(self):
        for fmt in ("export", "dotenv", "json"):
            assert _validate_format(fmt) == fmt

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError, match="Unsupported format"):
            _validate_format("yaml")


class TestRenderExport:
    def test_keys_sorted(self):
        output = render_export(SAMPLE)
        lines = output.splitlines()
        keys = [line.split("=")[0].replace("export ", "") for line in lines]
        assert keys == sorted(keys)

    def test_export_prefix(self):
        output = render_export({"FOO": "bar"})
        assert output == "export FOO='bar'"

    def test_special_chars_quoted(self):
        output = render_export({"URL": "postgres://user:p@ss@localhost/db"})
        assert "export URL=" in output
        # shlex.quote wraps in single quotes when special chars present
        assert "'" in output

    def test_empty_dict(self):
        assert render_export({}) == ""


class TestRenderDotenv:
    def test_no_export_prefix(self):
        output = render_dotenv({"FOO": "bar"})
        assert "export" not in output
        assert output == "FOO='bar'"

    def test_keys_sorted(self):
        output = render_dotenv(SAMPLE)
        lines = output.splitlines()
        keys = [line.split("=")[0] for line in lines]
        assert keys == sorted(keys)

    def test_empty_dict(self):
        assert render_dotenv({}) == ""


class TestRenderJson:
    def test_valid_json(self):
        output = render_json(SAMPLE)
        parsed = json.loads(output)
        assert parsed == SAMPLE

    def test_keys_sorted(self):
        output = render_json(SAMPLE)
        parsed = json.loads(output)
        assert list(parsed.keys()) == sorted(parsed.keys())

    def test_empty_dict(self):
        assert json.loads(render_json({})) == {}


class TestRender:
    def test_default_format_is_export(self):
        output = render({"X": "1"})
        assert output.startswith("export ")

    def test_dotenv_format(self):
        output = render({"X": "1"}, fmt="dotenv")
        assert output == "X='1'"

    def test_json_format(self):
        output = render({"X": "1"}, fmt="json")
        assert json.loads(output) == {"X": "1"}

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError):
            render({"X": "1"}, fmt="toml")
