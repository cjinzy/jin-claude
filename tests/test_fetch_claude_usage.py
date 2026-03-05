"""Tests for fetch_claude_usage module."""

from __future__ import annotations

import json
import subprocess
import time
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jin_claude.fetch_claude_usage import (
    CACHE_TTL_ERROR_SECONDS,
    CACHE_TTL_SECONDS,
    get_token,
    get_usage,
    is_token_expired,
    read_cache,
    read_token_from_credentials_file,
    read_token_from_keychain,
    refresh_access_token,
    write_back_credentials,
    write_cache,
)

# --- Token reading tests ---


class TestReadTokenFromCredentialsFile:
    """Tests for reading OAuth token from credentials file."""

    def test_valid_credentials(self, tmp_path: Path) -> None:
        creds = {"claudeAiOauth": {"accessToken": "test-token-123"}}
        creds_file = tmp_path / ".credentials.json"
        creds_file.write_text(json.dumps(creds))

        with patch("jin_claude.fetch_claude_usage.CREDENTIALS_PATH", creds_file):
            assert read_token_from_credentials_file() == "test-token-123"

    def test_missing_file(self, tmp_path: Path) -> None:
        creds_file = tmp_path / "nonexistent.json"
        with patch("jin_claude.fetch_claude_usage.CREDENTIALS_PATH", creds_file):
            assert read_token_from_credentials_file() is None

    def test_invalid_json(self, tmp_path: Path) -> None:
        creds_file = tmp_path / ".credentials.json"
        creds_file.write_text("not json")
        with patch("jin_claude.fetch_claude_usage.CREDENTIALS_PATH", creds_file):
            assert read_token_from_credentials_file() is None

    def test_missing_access_token_key(self, tmp_path: Path) -> None:
        creds_file = tmp_path / ".credentials.json"
        creds_file.write_text(json.dumps({"claudeAiOauth": {}}))
        with patch("jin_claude.fetch_claude_usage.CREDENTIALS_PATH", creds_file):
            assert read_token_from_credentials_file() is None

    def test_empty_access_token(self, tmp_path: Path) -> None:
        creds_file = tmp_path / ".credentials.json"
        creds_file.write_text(json.dumps({"claudeAiOauth": {"accessToken": ""}}))
        with patch("jin_claude.fetch_claude_usage.CREDENTIALS_PATH", creds_file):
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
        creds = {"claudeAiOauth": {"accessToken": "file-token"}}
        with (
            patch(
                "jin_claude.fetch_claude_usage._read_credentials_data",
                return_value=creds,
            ),
            patch(
                "jin_claude.fetch_claude_usage.read_token_from_keychain",
                return_value="keychain-token",
            ),
        ):
            assert get_token() == "file-token"

    def test_fallback_to_keychain(self) -> None:
        with (
            patch(
                "jin_claude.fetch_claude_usage._read_credentials_data",
                return_value=None,
            ),
            patch(
                "jin_claude.fetch_claude_usage.read_token_from_keychain",
                return_value="keychain-token",
            ),
        ):
            assert get_token() == "keychain-token"

    def test_no_token_available(self) -> None:
        with (
            patch(
                "jin_claude.fetch_claude_usage._read_credentials_data",
                return_value=None,
            ),
            patch(
                "jin_claude.fetch_claude_usage.read_token_from_keychain",
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

        with patch("jin_claude.fetch_claude_usage.CACHE_PATH", cache_file):
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

        with patch("jin_claude.fetch_claude_usage.CACHE_PATH", cache_file):
            assert read_cache() is None

    def test_fresh_cache_returns_data(self, tmp_path: Path) -> None:
        cache_file = tmp_path / ".usage-cache.json"
        cache_data = {
            "fetched_at": time.time(),
            "five_hour": {"utilization": 15.0, "resets_at": None},
        }
        cache_file.write_text(json.dumps(cache_data))

        with patch("jin_claude.fetch_claude_usage.CACHE_PATH", cache_file):
            result = read_cache()
            assert result is not None
            assert result.five_hour.utilization == 15.0
            assert result.seven_day is None

    def test_corrupted_cache_returns_none(self, tmp_path: Path) -> None:
        cache_file = tmp_path / ".usage-cache.json"
        cache_file.write_text("invalid json")

        with patch("jin_claude.fetch_claude_usage.CACHE_PATH", cache_file):
            assert read_cache() is None

    def test_missing_five_hour_in_cache(self, tmp_path: Path) -> None:
        cache_file = tmp_path / ".usage-cache.json"
        cache_data = {"fetched_at": time.time(), "five_hour": None}
        cache_file.write_text(json.dumps(cache_data))

        with patch("jin_claude.fetch_claude_usage.CACHE_PATH", cache_file):
            assert read_cache() is None

    def test_cache_without_seven_day(self, tmp_path: Path) -> None:
        cache_file = tmp_path / ".usage-cache.json"
        cache_data = {
            "fetched_at": time.time(),
            "five_hour": {"utilization": 10.0, "resets_at": "2026-03-02T18:00:00Z"},
        }
        cache_file.write_text(json.dumps(cache_data))

        with patch("jin_claude.fetch_claude_usage.CACHE_PATH", cache_file):
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

        with patch("jin_claude.fetch_claude_usage.CACHE_PATH", cache_file):
            result = get_usage()
            assert result is not None
            assert result.five_hour.utilization == 55.0
            assert result.seven_day is not None
            assert result.seven_day.utilization == 30.0

    def test_returns_none_when_no_token(self, tmp_path: Path) -> None:
        cache_file = tmp_path / ".usage-cache.json"
        with (
            patch("jin_claude.fetch_claude_usage.CACHE_PATH", cache_file),
            patch("jin_claude.fetch_claude_usage.get_token", return_value=None),
        ):
            assert get_usage() is None

    def test_fetches_from_api_when_cache_expired(self, tmp_path: Path) -> None:
        cache_file = tmp_path / ".usage-cache.json"
        api_response = {
            "five_hour": {"utilization": 30.0, "resets_at": "2026-03-02T19:00:00Z"},
            "seven_day": {"utilization": 15.0, "resets_at": "2026-03-06T03:00:00Z"},
        }

        with (
            patch("jin_claude.fetch_claude_usage.CACHE_PATH", cache_file),
            patch("jin_claude.fetch_claude_usage.get_token", return_value="fake-token"),
            patch("jin_claude.fetch_claude_usage.fetch_usage", return_value=api_response),
        ):
            result = get_usage()
            assert result is not None
            assert result.five_hour.utilization == 30.0
            assert result.seven_day is not None
            assert result.seven_day.resets_at == "2026-03-06T03:00:00Z"

    def test_returns_none_on_api_error(self, tmp_path: Path) -> None:
        cache_file = tmp_path / ".usage-cache.json"

        with (
            patch("jin_claude.fetch_claude_usage.CACHE_PATH", cache_file),
            patch("jin_claude.fetch_claude_usage.get_token", return_value="fake-token"),
            patch(
                "jin_claude.fetch_claude_usage.fetch_usage",
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

        from jin_claude.fetch_claude_usage import main

        with patch("jin_claude.fetch_claude_usage.CACHE_PATH", cache_file):
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

        from jin_claude.fetch_claude_usage import main

        with patch("jin_claude.fetch_claude_usage.CACHE_PATH", cache_file):
            main()

        captured = capsys.readouterr()
        parts = captured.out.strip().split("|")
        assert len(parts) == 4
        assert parts[0] == "10"
        assert parts[2] == ""  # no 7d utilization
        assert parts[3] == ""  # no 7d resets_at

    def test_output_exits_1_on_failure(self, tmp_path: Path) -> None:
        cache_file = tmp_path / ".usage-cache.json"

        from jin_claude.fetch_claude_usage import main

        with (
            patch("jin_claude.fetch_claude_usage.CACHE_PATH", cache_file),
            patch("jin_claude.fetch_claude_usage.get_token", return_value=None),
            pytest.raises(SystemExit) as exc_info,
        ):
            main()

        assert exc_info.value.code == 1


class TestTokenRefresh:
    """OAuth 토큰 갱신 테스트."""

    def test_is_token_expired_true(self) -> None:
        creds = {"claudeAiOauth": {"expiresAt": 1000}}  # far past
        assert is_token_expired(creds) is True

    def test_is_token_expired_false(self) -> None:
        future_ms = int(time.time() * 1000) + 3600_000  # 1h in future
        creds = {"claudeAiOauth": {"expiresAt": future_ms}}
        assert is_token_expired(creds) is False

    def test_is_token_expired_no_field(self) -> None:
        creds = {"claudeAiOauth": {}}
        assert is_token_expired(creds) is False

    def test_refresh_access_token_success(self) -> None:
        response_data = {
            "access_token": "new-token",
            "refresh_token": "new-refresh",
            "expires_in": 3600,
        }
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(response_data).encode()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = refresh_access_token("old-refresh")
            assert result is not None
            assert result["access_token"] == "new-token"

    def test_refresh_access_token_failure(self) -> None:
        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("fail"),
        ):
            assert refresh_access_token("bad-refresh") is None

    def test_write_back_credentials(self, tmp_path: Path) -> None:
        creds_file = tmp_path / ".credentials.json"
        creds_file.write_text(json.dumps({"claudeAiOauth": {"accessToken": "old"}}))

        with patch("jin_claude.fetch_claude_usage.CREDENTIALS_PATH", creds_file):
            write_back_credentials("new-token", "new-refresh", 3600)

        data = json.loads(creds_file.read_text())
        assert data["claudeAiOauth"]["accessToken"] == "new-token"
        assert data["claudeAiOauth"]["refreshToken"] == "new-refresh"
        assert "expiresAt" in data["claudeAiOauth"]

    def test_get_token_refreshes_expired(self, tmp_path: Path) -> None:
        creds_file = tmp_path / ".credentials.json"
        creds = {
            "claudeAiOauth": {
                "accessToken": "expired-token",
                "refreshToken": "my-refresh",
                "expiresAt": 1000,  # far past
            }
        }
        creds_file.write_text(json.dumps(creds))

        refreshed = {
            "access_token": "fresh-token",
            "refresh_token": "fresh-refresh",
            "expires_in": 3600,
        }

        with (
            patch("jin_claude.fetch_claude_usage.CREDENTIALS_PATH", creds_file),
            patch(
                "jin_claude.fetch_claude_usage.refresh_access_token",
                return_value=refreshed,
            ),
        ):
            assert get_token() == "fresh-token"


class TestStaleCacheFallback:
    """Stale cache fallback 및 에러 캐싱 테스트."""

    def test_returns_stale_cache_on_api_error(self, tmp_path: Path) -> None:
        cache_file = tmp_path / ".usage-cache.json"
        # 만료된 캐시 (정상 데이터)
        cache_data = {
            "fetched_at": time.time() - CACHE_TTL_SECONDS - 100,
            "five_hour": {"utilization": 42.0, "resets_at": "2026-03-02T18:00:00Z"},
            "seven_day": {"utilization": 20.0, "resets_at": "2026-03-06T00:00:00Z"},
        }
        cache_file.write_text(json.dumps(cache_data))

        with (
            patch("jin_claude.fetch_claude_usage.CACHE_PATH", cache_file),
            patch("jin_claude.fetch_claude_usage.get_token", return_value="fake-token"),
            patch(
                "jin_claude.fetch_claude_usage.fetch_usage",
                side_effect=OSError("network error"),
            ),
        ):
            result = get_usage()
            assert result is not None
            assert result.five_hour.utilization == 42.0

    def test_returns_stale_cache_when_no_token(self, tmp_path: Path) -> None:
        cache_file = tmp_path / ".usage-cache.json"
        cache_data = {
            "fetched_at": time.time() - CACHE_TTL_SECONDS - 100,
            "five_hour": {"utilization": 30.0, "resets_at": None},
        }
        cache_file.write_text(json.dumps(cache_data))

        with (
            patch("jin_claude.fetch_claude_usage.CACHE_PATH", cache_file),
            patch("jin_claude.fetch_claude_usage.get_token", return_value=None),
        ):
            result = get_usage()
            assert result is not None
            assert result.five_hour.utilization == 30.0

    def test_consecutive_errors_preserve_data(self, tmp_path: Path) -> None:
        """연속 API 에러 시에도 최초 정상 데이터가 보존되어 반환된다."""
        cache_file = tmp_path / ".usage-cache.json"
        # 만료된 정상 캐시
        cache_data = {
            "fetched_at": time.time() - CACHE_TTL_SECONDS - 100,
            "five_hour": {"utilization": 42.0, "resets_at": "2026-03-02T18:00:00Z"},
            "seven_day": {"utilization": 20.0, "resets_at": "2026-03-06T00:00:00Z"},
        }
        cache_file.write_text(json.dumps(cache_data))

        with (
            patch("jin_claude.fetch_claude_usage.CACHE_PATH", cache_file),
            patch("jin_claude.fetch_claude_usage.get_token", return_value="fake-token"),
            patch(
                "jin_claude.fetch_claude_usage.fetch_usage",
                side_effect=OSError("429"),
            ),
        ):
            # 첫 번째 에러: stale 정상 캐시에서 데이터 반환
            result1 = get_usage()
            assert result1 is not None
            assert result1.five_hour.utilization == 42.0

        # 에러 캐시 TTL을 만료시킴
        data = json.loads(cache_file.read_text())
        data["fetched_at"] = time.time() - CACHE_TTL_ERROR_SECONDS - 1
        cache_file.write_text(json.dumps(data))

        with (
            patch("jin_claude.fetch_claude_usage.CACHE_PATH", cache_file),
            patch("jin_claude.fetch_claude_usage.get_token", return_value="fake-token"),
            patch(
                "jin_claude.fetch_claude_usage.fetch_usage",
                side_effect=OSError("429 again"),
            ),
        ):
            # 두 번째 에러: 에러 캐시에 보존된 데이터에서 반환
            result2 = get_usage()
            assert result2 is not None
            assert result2.five_hour.utilization == 42.0

    def test_returns_none_when_no_cache_and_api_fails(self, tmp_path: Path) -> None:
        cache_file = tmp_path / "nonexistent-cache.json"

        with (
            patch("jin_claude.fetch_claude_usage.CACHE_PATH", cache_file),
            patch("jin_claude.fetch_claude_usage.get_token", return_value="fake-token"),
            patch(
                "jin_claude.fetch_claude_usage.fetch_usage",
                side_effect=OSError("fail"),
            ),
        ):
            result = get_usage()
            assert result is None


class TestErrorCache:
    """에러 캐시 TTL 테스트."""

    def test_error_cache_short_ttl_fresh(self, tmp_path: Path) -> None:
        """에러 캐시가 fresh(15초 이내)이면 None 반환 (API 재시도 방지)."""
        cache_file = tmp_path / ".usage-cache.json"
        cache_data = {
            "fetched_at": time.time(),
            "error": True,
        }
        cache_file.write_text(json.dumps(cache_data))

        with patch("jin_claude.fetch_claude_usage.CACHE_PATH", cache_file):
            assert read_cache() is None  # 에러 캐시는 항상 None

    def test_error_cache_expired_allows_retry(self, tmp_path: Path) -> None:
        """에러 캐시가 만료(15초 경과)되면 None 반환하여 API 재시도 허용."""
        cache_file = tmp_path / ".usage-cache.json"
        cache_data = {
            "fetched_at": time.time() - CACHE_TTL_ERROR_SECONDS - 1,
            "error": True,
        }
        cache_file.write_text(json.dumps(cache_data))

        with patch("jin_claude.fetch_claude_usage.CACHE_PATH", cache_file):
            assert read_cache() is None  # 만료 → None → API 재시도

    def test_write_error_cache_without_prior_data(self, tmp_path: Path) -> None:
        """이전 캐시가 없을 때 에러 캐시는 데이터 없이 저장된다."""
        cache_file = tmp_path / ".usage-cache.json"

        with patch("jin_claude.fetch_claude_usage.CACHE_PATH", cache_file):
            write_cache(None, error=True)

        data = json.loads(cache_file.read_text())
        assert data["error"] is True
        assert "five_hour" not in data

    def test_write_error_cache_preserves_prior_data(self, tmp_path: Path) -> None:
        """에러 시 기존 캐시의 정상 데이터(five_hour/seven_day)를 보존한다."""
        cache_file = tmp_path / ".usage-cache.json"
        # 기존 정상 캐시
        old_cache = {
            "fetched_at": time.time() - 100,
            "five_hour": {"utilization": 42.0, "resets_at": "2026-03-02T18:00:00Z"},
            "seven_day": {"utilization": 20.0, "resets_at": "2026-03-06T00:00:00Z"},
        }
        cache_file.write_text(json.dumps(old_cache))

        with patch("jin_claude.fetch_claude_usage.CACHE_PATH", cache_file):
            write_cache(None, error=True)

        data = json.loads(cache_file.read_text())
        assert data["error"] is True
        assert data["five_hour"]["utilization"] == 42.0
        assert data["seven_day"]["utilization"] == 20.0

    def test_write_error_cache_does_not_preserve_prior_error(self, tmp_path: Path) -> None:
        """이전 캐시도 에러였으면 데이터를 보존하지 않는다."""
        cache_file = tmp_path / ".usage-cache.json"
        old_cache = {
            "fetched_at": time.time() - 100,
            "error": True,
        }
        cache_file.write_text(json.dumps(old_cache))

        with patch("jin_claude.fetch_claude_usage.CACHE_PATH", cache_file):
            write_cache(None, error=True)

        data = json.loads(cache_file.read_text())
        assert data["error"] is True
        assert "five_hour" not in data

    def test_read_error_cache_with_preserved_data_stale(self, tmp_path: Path) -> None:
        """에러 캐시에 보존된 정상 데이터가 있으면 allow_stale=True 시 반환한다."""
        cache_file = tmp_path / ".usage-cache.json"
        cache_data = {
            "fetched_at": time.time(),
            "error": True,
            "five_hour": {"utilization": 42.0, "resets_at": "2026-03-02T18:00:00Z"},
            "seven_day": {"utilization": 20.0, "resets_at": "2026-03-06T00:00:00Z"},
        }
        cache_file.write_text(json.dumps(cache_data))

        with patch("jin_claude.fetch_claude_usage.CACHE_PATH", cache_file):
            # allow_stale=False → None (fresh 에러 캐시는 재시도 방지)
            assert read_cache(allow_stale=False) is None
            # allow_stale=True → 보존된 데이터 반환
            result = read_cache(allow_stale=True)
            assert result is not None
            assert result.five_hour.utilization == 42.0
            assert result.seven_day is not None
            assert result.seven_day.utilization == 20.0

    def test_read_error_cache_without_data_stale(self, tmp_path: Path) -> None:
        """에러 캐시에 데이터가 없으면 allow_stale=True여도 None을 반환한다."""
        cache_file = tmp_path / ".usage-cache.json"
        cache_data = {
            "fetched_at": time.time(),
            "error": True,
        }
        cache_file.write_text(json.dumps(cache_data))

        with patch("jin_claude.fetch_claude_usage.CACHE_PATH", cache_file):
            assert read_cache(allow_stale=True) is None
