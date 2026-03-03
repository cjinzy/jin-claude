"""Fetch Claude API usage (5h session + 7d weekly) via undocumented OAuth endpoint.

Reads OAuth token from macOS Keychain or ~/.claude/.credentials.json,
calls the usage API, caches the result, and outputs
`5h_utilization|5h_resets_at|7d_resets_at` for statusline consumption.

Cache: ~/.claude/.usage-cache.json (30s TTL)
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

CREDENTIALS_PATH = Path.home() / ".claude" / ".credentials.json"
CACHE_PATH = Path.home() / ".claude" / ".usage-cache.json"
CACHE_TTL_SECONDS = 30

API_URL = "https://api.anthropic.com/api/oauth/usage"
BETA_HEADER = "oauth-2025-04-20"

KEYCHAIN_SERVICE = "Claude Code-credentials"


@dataclass
class UsageBucket:
    """A single usage bucket from the API response."""

    utilization: float
    resets_at: str | None = None


def read_token_from_credentials_file() -> str | None:
    """Read OAuth token from ~/.claude/.credentials.json."""
    try:
        data = json.loads(CREDENTIALS_PATH.read_text())
        token = data.get("claudeAiOauth", {}).get("accessToken")
        return token if token else None
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return None


def read_token_from_keychain() -> str | None:
    """Read OAuth token from macOS Keychain via security CLI."""
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return None
        raw = result.stdout.strip()
        data = json.loads(raw)
        token = data.get("claudeAiOauth", {}).get("accessToken")
        return token if token else None
    except (subprocess.TimeoutExpired, json.JSONDecodeError, KeyError, OSError):
        return None


def get_token() -> str | None:
    """Get OAuth token, trying credentials file first, then Keychain."""
    return read_token_from_credentials_file() or read_token_from_keychain()


@dataclass
class UsageResult:
    """Combined usage result for statusline output."""

    five_hour: UsageBucket
    seven_day: UsageBucket | None = None


def read_cache() -> UsageResult | None:
    """Read cached usage if still fresh (within TTL)."""
    try:
        data = json.loads(CACHE_PATH.read_text())
        fetched_at = data.get("fetched_at", 0)
        if time.time() - fetched_at > CACHE_TTL_SECONDS:
            return None
        five_hour = data.get("five_hour")
        if five_hour is None:
            return None
        seven_day = data.get("seven_day")
        return UsageResult(
            five_hour=UsageBucket(
                utilization=five_hour["utilization"],
                resets_at=five_hour.get("resets_at"),
            ),
            seven_day=UsageBucket(
                utilization=seven_day["utilization"],
                resets_at=seven_day.get("resets_at"),
            )
            if seven_day
            else None,
        )
    except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError):
        return None


def write_cache(api_response: dict) -> None:
    """Write API response to cache file."""
    cache_data = {
        "fetched_at": time.time(),
        "five_hour": api_response.get("five_hour"),
        "seven_day": api_response.get("seven_day"),
    }
    try:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_text(json.dumps(cache_data))
    except OSError:
        pass


def fetch_usage(token: str) -> dict:
    """Fetch usage from Anthropic OAuth API.

    Raises:
        urllib.error.URLError: On network errors.
        urllib.error.HTTPError: On HTTP error responses.
    """
    req = urllib.request.Request(
        API_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "anthropic-beta": BETA_HEADER,
        },
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def get_usage() -> UsageResult | None:
    """Get usage data, using cache when available."""
    cached = read_cache()
    if cached is not None:
        return cached

    token = get_token()
    if not token:
        return None

    try:
        data = fetch_usage(token)
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, OSError):
        return None

    write_cache(data)

    five_hour = data.get("five_hour")
    if five_hour is None:
        return None

    seven_day = data.get("seven_day")
    return UsageResult(
        five_hour=UsageBucket(
            utilization=five_hour["utilization"],
            resets_at=five_hour.get("resets_at"),
        ),
        seven_day=UsageBucket(
            utilization=seven_day["utilization"],
            resets_at=seven_day.get("resets_at"),
        )
        if seven_day
        else None,
    )


def main() -> None:
    """CLI entry point. Outputs `5h_util|5h_resets|7d_util|7d_resets` to stdout."""
    result = get_usage()
    if result is None:
        sys.exit(1)
    five_hour_resets = result.five_hour.resets_at or ""
    seven_day_util = f"{result.seven_day.utilization:.0f}" if result.seven_day else ""
    seven_day_resets = result.seven_day.resets_at or "" if result.seven_day else ""
    print(
        f"{result.five_hour.utilization:.0f}|{five_hour_resets}|{seven_day_util}|{seven_day_resets}"
    )


if __name__ == "__main__":
    main()
