"""Tests for fetch_claude_usage module."""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from zyclaude.fetch_claude_usage import (
    CACHE_TTL_SECONDS,
    get_token,
    get_usage,
    read_cache,
    read_token_from_credentials_file,
    read_token_from_keychain,
    write_cache,
)

# --- Token reading tests ---


class TestReadTokenFromCredentialsFile:
    """Tests for reading OAuth token from credentials file."""

    def test_valid_credentials(self, tmp_path: Path) -> None:
        creds = {"claudeAiOauth": {"accessToken": "test-token-123"}}
        creds_file = tmp_path / ".credentials.json"
        creds_file.write_text(json.dumps(creds))

        with patch("zyclaude.fetch_claude_usage.CREDENTIALS_PATH", creds_file):
            assert read_token_from_credentials_file() == "test-token-123"

    def test_missing_file(self, tmp_path: Path) -> None:
        creds_file = tmp_path / "nonexistent.json"
        with patch("zyclaude.fetch_claude_usage.CREDENTIALS_PATH", creds_file):
            assert read_token_from_credentials_file() is None

    def test_invalid_json(self, tmp_path: Path) -> None:
        creds_file = tmp_path / ".credentials.json"
        creds_file.write_text("not json")
        with patch("zyclaude.fetch_claude_usage.CREDENTIALS_PATH", creds_file):
            assert read_token_from_credentials_file() is None

    def test_missing_access_token_key(self, tmp_path: Path) -> None:
        creds_file = tmp_path / ".credentials.json"
        creds_file.write_text(json.dumps({"claudeAiOauth": {}}))
        with patch("zyclaude.fetch_claude_usage.CREDENTIALS_PATH", creds_file):
            assert read_token_from_credentials_file() is None

    def test_empty_access_token(self, tmp_path: Path) -> None:
        creds_file = tmp_path / ".credentials.json"
        creds_file.write_text(json.dumps({"claudeAiOauth": {"accessToken": ""}}))
        with patch("zyclaude.fetch_claude_usage.CREDENTIALS_PATH", creds_file):
            assert read_token_from_credentials_file() is None


class TestReadTokenFromKeychain:
    """Tests for reading OAuth token from macOS Keychain."""

    def test_valid_keychain(self) -> None:
        keychain_json = json.dumps({"claudeAiOauth": {"accessToken": "keychain-token"}})
        mock_result = MagicMock(returncode=0, stdout=keychain_json)
        with patch("subprocess.run", return_value=mock_result):
            assert read_token_from_keychain() == "keychain-token"

    def test_keychain_not_found(self) -> None:
        mock_result = MagicMock(returncode=44, stdout="", stderr="not found")
        with patch("subprocess.run", return_value=mock_result):
            assert read_token_from_keychain() is None

    def test_keychain_timeout(self) -> None:
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 5)):
            assert read_token_from_keychain() is None

    def test_keychain_invalid_json(self) -> None:
        mock_result = MagicMock(returncode=0, stdout="not-json")
        with patch("subprocess.run", return_value=mock_result):
            assert read_token_from_keychain() is None


class TestGetToken:
    """Tests for token resolution priority."""

    def test_credentials_file_preferred(self) -> None:
        with (
            patch(
                "zyclaude.fetch_claude_usage.read_token_from_credentials_file",
                return_value="file-token",
            ),
            patch(
                "zyclaude.fetch_claude_usage.read_token_from_keychain",
                return_value="keychain-token",
            ),
        ):
            assert get_token() == "file-token"

    def test_fallback_to_keychain(self) -> None:
        with (
            patch(
                "zyclaude.fetch_claude_usage.read_token_from_credentials_file",
                return_value=None,
            ),
            patch(
                "zyclaude.fetch_claude_usage.read_token_from_keychain",
                return_value="keychain-token",
            ),
        ):
            assert get_token() == "keychain-token"

    def test_no_token_available(self) -> None:
        with (
            patch(
                "zyclaude.fetch_claude_usage.read_token_from_credentials_file",
                return_value=None,
            ),
            patch(
                "zyclaude.fetch_claude_usage.read_token_from_keychain",
                return_value=None,
            ),
        ):
            assert get_token() is None


# --- Cache tests ---


class TestCache:
    """Tests for cache read/write and TTL."""

    def test_write_and_read_cache(self, tmp_path: Path) -> None:
        cache_file = tmp_path / ".usage-cache.json"
        api_response = {
            "five_hour": {"utilization": 42.0, "resets_at": "2026-03-02T18:00:00Z"},
            "seven_day": {"utilization": 20.0, "resets_at": "2026-03-06T00:00:00Z"},
        }

        with patch("zyclaude.fetch_claude_usage.CACHE_PATH", cache_file):
            write_cache(api_response)
            result = read_cache()

        assert result is not None
        assert result.five_hour.utilization == 42.0
        assert result.five_hour.resets_at == "2026-03-02T18:00:00Z"
        assert result.seven_day is not None
        assert result.seven_day.utilization == 20.0
        assert result.seven_day.resets_at == "2026-03-06T00:00:00Z"

    def test_expired_cache_returns_none(self, tmp_path: Path) -> None:
        cache_file = tmp_path / ".usage-cache.json"
        cache_data = {
            "fetched_at": time.time() - CACHE_TTL_SECONDS - 1,
            "five_hour": {"utilization": 42.0, "resets_at": "2026-03-02T18:00:00Z"},
        }
        cache_file.write_text(json.dumps(cache_data))

        with patch("zyclaude.fetch_claude_usage.CACHE_PATH", cache_file):
            assert read_cache() is None

    def test_fresh_cache_returns_data(self, tmp_path: Path) -> None:
        cache_file = tmp_path / ".usage-cache.json"
        cache_data = {
            "fetched_at": time.time(),
            "five_hour": {"utilization": 15.0, "resets_at": None},
        }
        cache_file.write_text(json.dumps(cache_data))

        with patch("zyclaude.fetch_claude_usage.CACHE_PATH", cache_file):
            result = read_cache()
            assert result is not None
            assert result.five_hour.utilization == 15.0
            assert result.seven_day is None

    def test_corrupted_cache_returns_none(self, tmp_path: Path) -> None:
        cache_file = tmp_path / ".usage-cache.json"
        cache_file.write_text("invalid json")

        with patch("zyclaude.fetch_claude_usage.CACHE_PATH", cache_file):
            assert read_cache() is None

    def test_missing_five_hour_in_cache(self, tmp_path: Path) -> None:
        cache_file = tmp_path / ".usage-cache.json"
        cache_data = {"fetched_at": time.time(), "five_hour": None}
        cache_file.write_text(json.dumps(cache_data))

        with patch("zyclaude.fetch_claude_usage.CACHE_PATH", cache_file):
            assert read_cache() is None

    def test_cache_without_seven_day(self, tmp_path: Path) -> None:
        cache_file = tmp_path / ".usage-cache.json"
        cache_data = {
            "fetched_at": time.time(),
            "five_hour": {"utilization": 10.0, "resets_at": "2026-03-02T18:00:00Z"},
        }
        cache_file.write_text(json.dumps(cache_data))

        with patch("zyclaude.fetch_claude_usage.CACHE_PATH", cache_file):
            result = read_cache()
            assert result is not None
            assert result.seven_day is None


# --- Integration tests ---


class TestGetUsage:
    """Tests for the main get_usage function."""

    def test_returns_cached_when_fresh(self, tmp_path: Path) -> None:
        cache_file = tmp_path / ".usage-cache.json"
        cache_data = {
            "fetched_at": time.time(),
            "five_hour": {"utilization": 55.0, "resets_at": "2026-03-02T20:00:00Z"},
            "seven_day": {"utilization": 30.0, "resets_at": "2026-03-06T00:00:00Z"},
        }
        cache_file.write_text(json.dumps(cache_data))

        with patch("zyclaude.fetch_claude_usage.CACHE_PATH", cache_file):
            result = get_usage()
            assert result is not None
            assert result.five_hour.utilization == 55.0
            assert result.seven_day is not None
            assert result.seven_day.utilization == 30.0

    def test_returns_none_when_no_token(self, tmp_path: Path) -> None:
        cache_file = tmp_path / ".usage-cache.json"
        with (
            patch("zyclaude.fetch_claude_usage.CACHE_PATH", cache_file),
            patch("zyclaude.fetch_claude_usage.get_token", return_value=None),
        ):
            assert get_usage() is None

    def test_fetches_from_api_when_cache_expired(self, tmp_path: Path) -> None:
        cache_file = tmp_path / ".usage-cache.json"
        api_response = {
            "five_hour": {"utilization": 30.0, "resets_at": "2026-03-02T19:00:00Z"},
            "seven_day": {"utilization": 15.0, "resets_at": "2026-03-06T03:00:00Z"},
        }

        with (
            patch("zyclaude.fetch_claude_usage.CACHE_PATH", cache_file),
            patch("zyclaude.fetch_claude_usage.get_token", return_value="fake-token"),
            patch("zyclaude.fetch_claude_usage.fetch_usage", return_value=api_response),
        ):
            result = get_usage()
            assert result is not None
            assert result.five_hour.utilization == 30.0
            assert result.seven_day is not None
            assert result.seven_day.resets_at == "2026-03-06T03:00:00Z"

    def test_returns_none_on_api_error(self, tmp_path: Path) -> None:
        cache_file = tmp_path / ".usage-cache.json"

        with (
            patch("zyclaude.fetch_claude_usage.CACHE_PATH", cache_file),
            patch("zyclaude.fetch_claude_usage.get_token", return_value="fake-token"),
            patch(
                "zyclaude.fetch_claude_usage.fetch_usage",
                side_effect=OSError("network error"),
            ),
        ):
            assert get_usage() is None


# --- CLI output format test ---


class TestMainOutput:
    """Tests for CLI output format."""

    def test_output_format_with_7d(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        cache_file = tmp_path / ".usage-cache.json"
        cache_data = {
            "fetched_at": time.time(),
            "five_hour": {"utilization": 35.0, "resets_at": "2026-03-02T18:30:00Z"},
            "seven_day": {"utilization": 20.0, "resets_at": "2026-03-06T00:00:00Z"},
        }
        cache_file.write_text(json.dumps(cache_data))

        from zyclaude.fetch_claude_usage import main

        with patch("zyclaude.fetch_claude_usage.CACHE_PATH", cache_file):
            main()

        captured = capsys.readouterr()
        parts = captured.out.strip().split("|")
        assert len(parts) == 4
        assert parts[0] == "35"
        assert parts[1] == "2026-03-02T18:30:00Z"
        assert parts[2] == "20"
        assert parts[3] == "2026-03-06T00:00:00Z"

    def test_output_format_without_7d(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        cache_file = tmp_path / ".usage-cache.json"
        cache_data = {
            "fetched_at": time.time(),
            "five_hour": {"utilization": 10.0, "resets_at": "2026-03-02T18:30:00Z"},
        }
        cache_file.write_text(json.dumps(cache_data))

        from zyclaude.fetch_claude_usage import main

        with patch("zyclaude.fetch_claude_usage.CACHE_PATH", cache_file):
            main()

        captured = capsys.readouterr()
        parts = captured.out.strip().split("|")
        assert len(parts) == 4
        assert parts[0] == "10"
        assert parts[2] == ""  # no 7d utilization
        assert parts[3] == ""  # no 7d resets_at

    def test_output_exits_1_on_failure(self, tmp_path: Path) -> None:
        cache_file = tmp_path / ".usage-cache.json"

        from zyclaude.fetch_claude_usage import main

        with (
            patch("zyclaude.fetch_claude_usage.CACHE_PATH", cache_file),
            patch("zyclaude.fetch_claude_usage.get_token", return_value=None),
            pytest.raises(SystemExit) as exc_info,
        ):
            main()

        assert exc_info.value.code == 1
