"""Fetch Claude API usage (5h session + 7d weekly) via undocumented OAuth endpoint.

Reads OAuth token from macOS Keychain or ~/.claude/.credentials.json,
calls the usage API, caches the result, and outputs
`5h_utilization|5h_resets_at|7d_resets_at` for statusline consumption.

Cache: ~/.claude/.usage-cache.json (5m TTL, 15s for errors)
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path

CREDENTIALS_PATH = Path.home() / ".claude" / ".credentials.json"
CACHE_PATH = Path.home() / ".claude" / ".usage-cache.json"
CACHE_TTL_SECONDS = 300        # 5분
CACHE_TTL_ERROR_SECONDS = 60   # 에러 캐시는 60초 (429 악순환 방지)

API_URL = "https://api.anthropic.com/api/oauth/usage"
BETA_HEADER = "oauth-2025-04-20"

KEYCHAIN_SERVICE = "Claude Code-credentials"

OAUTH_CLIENT_ID = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"
TOKEN_REFRESH_URL = "https://platform.claude.com/v1/oauth/token"


class PacingZone(StrEnum):
    """Smart Pacing zone 판정."""

    CHILL = "chill"
    ON_TRACK = "on_track"
    HOT = "hot"


def calculate_pacing(usage_pct: float, elapsed_pct: float) -> dict:
    """사용량 대비 경과 시간으로 pacing zone을 계산한다.

    Args:
        usage_pct: 현재 사용량 퍼센트 (0-100).
        elapsed_pct: 윈도우 경과 퍼센트 (0-100).

    Returns:
        {"zone": PacingZone, "elapsed_pct": float,
         "usage_pct": float, "burn_rate": float}
    """
    if elapsed_pct <= 0:
        burn_rate = float("inf") if usage_pct > 0 else 0.0
    else:
        burn_rate = usage_pct / elapsed_pct

    if burn_rate < 0.8:
        zone = PacingZone.CHILL
    elif burn_rate < 1.2:
        zone = PacingZone.ON_TRACK
    else:
        zone = PacingZone.HOT

    return {
        "zone": zone,
        "elapsed_pct": elapsed_pct,
        "usage_pct": usage_pct,
        "burn_rate": burn_rate,
    }


FIVE_HOUR_WINDOW = 5 * 3600
SEVEN_DAY_WINDOW = 7 * 86400


def _parse_resets_at(resets_at: str | None) -> float | None:
    """ISO 8601 resets_at 문자열을 epoch으로 변환한다."""
    if not resets_at:
        return None
    try:
        dt = datetime.fromisoformat(resets_at.replace("Z", "+00:00"))
        return dt.timestamp()
    except (ValueError, TypeError):
        return None


def compute_elapsed_pct(resets_at_epoch: float | None, window_seconds: int) -> float:
    """리셋 시간으로부터 윈도우 경과 퍼센트를 계산한다.

    Args:
        resets_at_epoch: 리셋 시각 (epoch seconds). None이면 50.0 반환.
        window_seconds: 윈도우 전체 길이 (초).

    Returns:
        경과 퍼센트 (0.0 ~ 100.0).
    """
    if resets_at_epoch is None:
        return 50.0
    remaining = resets_at_epoch - time.time()
    if remaining <= 0:
        return 100.0
    elapsed = window_seconds - remaining
    return max(0.0, min(100.0, (elapsed / window_seconds) * 100))


def _compute_pacing_for_cache(api_response: dict) -> dict | None:
    """API 응답으로부터 pacing 데이터를 계산한다."""
    pacing = {}

    five_hour = api_response.get("five_hour")
    if five_hour and five_hour.get("utilization") is not None:
        resets_epoch = _parse_resets_at(five_hour.get("resets_at"))
        elapsed = compute_elapsed_pct(resets_epoch, FIVE_HOUR_WINDOW)
        pacing["five_hour"] = calculate_pacing(five_hour["utilization"], elapsed)

    seven_day = api_response.get("seven_day")
    if seven_day and seven_day.get("utilization") is not None:
        resets_epoch = _parse_resets_at(seven_day.get("resets_at"))
        elapsed = compute_elapsed_pct(resets_epoch, SEVEN_DAY_WINDOW)
        pacing["seven_day"] = calculate_pacing(seven_day["utilization"], elapsed)

    return pacing if pacing else None


@dataclass
class UsageBucket:
    """A single usage bucket from the API response."""

    utilization: float
    resets_at: str | None = None


@dataclass
class UsageResult:
    """Combined usage result for statusline output."""

    five_hour: UsageBucket
    seven_day: UsageBucket | None = None


def _read_credentials_data() -> dict | None:
    """credentials.json의 raw dict를 반환한다."""
    try:
        return json.loads(CREDENTIALS_PATH.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def read_token_from_credentials_file() -> str | None:
    """~/.claude/.credentials.json에서 OAuth 토큰을 읽는다."""
    data = _read_credentials_data()
    if data is None:
        return None
    token = data.get("claudeAiOauth", {}).get("accessToken")
    return token if token else None


def read_token_from_keychain() -> str | None:
    """macOS Keychain에서 OAuth 토큰을 읽는다."""
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


def is_token_expired(credentials: dict) -> bool:
    """expiresAt 필드로 토큰 만료 여부를 확인한다."""
    expires_at = credentials.get("claudeAiOauth", {}).get("expiresAt")
    if expires_at is None:
        return False
    return expires_at <= time.time() * 1000  # JS timestamp (ms)


def refresh_access_token(refresh_token: str) -> dict | None:
    """OAuth refresh_token으로 새 access_token을 획득한다.

    Returns:
        성공 시 {"access_token": ..., "refresh_token": ..., "expires_in": ...} dict,
        실패 시 None.
    """
    data = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": OAUTH_CLIENT_ID,
    }).encode()
    req = urllib.request.Request(
        TOKEN_REFRESH_URL,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, OSError):
        return None


def write_back_credentials(new_token: str, new_refresh: str | None, expires_in: int | None) -> None:
    """갱신된 토큰을 credentials.json에 atomic write로 저장한다."""
    try:
        data = json.loads(CREDENTIALS_PATH.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}

    oauth = data.setdefault("claudeAiOauth", {})
    oauth["accessToken"] = new_token
    if new_refresh is not None:
        oauth["refreshToken"] = new_refresh
    if expires_in is not None:
        oauth["expiresAt"] = int(time.time() * 1000) + expires_in * 1000

    tmp_path = CREDENTIALS_PATH.with_suffix(".tmp")
    try:
        tmp_path.write_text(json.dumps(data))
        tmp_path.rename(CREDENTIALS_PATH)
    except OSError:
        pass


def get_token() -> str | None:
    """OAuth 토큰을 획득한다. 만료 시 자동으로 갱신을 시도한다."""
    creds_data = _read_credentials_data()
    if creds_data is not None:
        if is_token_expired(creds_data):
            refresh_token = creds_data.get("claudeAiOauth", {}).get("refreshToken")
            if refresh_token:
                refreshed = refresh_access_token(refresh_token)
                if refreshed:
                    write_back_credentials(
                        new_token=refreshed["access_token"],
                        new_refresh=refreshed.get("refresh_token"),
                        expires_in=refreshed.get("expires_in"),
                    )
                    return refreshed["access_token"]
            return None
        token = creds_data.get("claudeAiOauth", {}).get("accessToken")
        if token:
            return token
    return read_token_from_keychain()


def read_cache(allow_stale: bool = False) -> UsageResult | None:
    """캐시된 사용량 데이터를 읽는다.

    Args:
        allow_stale: True이면 TTL이 만료된 캐시도 반환한다.
            에러 캐시라도 보존된 정상 데이터가 있으면 stale로 반환한다.
    """
    try:
        data = json.loads(CACHE_PATH.read_text())
        fetched_at = data.get("fetched_at", 0)
        is_error = data.get("error", False)
        ttl = CACHE_TTL_ERROR_SECONDS if is_error else CACHE_TTL_SECONDS

        if not allow_stale and time.time() - fetched_at > ttl:
            return None
        if is_error and not allow_stale:
            return None  # fresh 에러 캐시는 API 재시도 방지용
        if is_error and allow_stale:
            # 에러 캐시에 보존된 정상 데이터가 있으면 stale로 반환
            if data.get("five_hour") is None:
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


def write_cache(api_response: dict | None, error: bool = False) -> None:
    """API 응답을 캐시 파일에 저장한다.

    에러 시 기존 캐시의 정상 데이터(five_hour/seven_day)를 보존하여
    stale fallback이 가능하도록 한다.

    Args:
        api_response: API 응답 dict. 에러 시 None.
        error: True이면 에러 캐시로 저장 (60초 TTL).
    """
    cache_data: dict = {
        "fetched_at": time.time(),
        "error": error,
    }
    if api_response is not None:
        cache_data["five_hour"] = api_response.get("five_hour")
        cache_data["seven_day"] = api_response.get("seven_day")
        cache_data["pacing"] = _compute_pacing_for_cache(api_response)
    elif error:
        # 에러 시 기존 캐시의 정상 데이터를 보존
        try:
            old = json.loads(CACHE_PATH.read_text())
            if not old.get("error"):
                cache_data["five_hour"] = old.get("five_hour")
                cache_data["seven_day"] = old.get("seven_day")
                cache_data["pacing"] = old.get("pacing")
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            pass
    try:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_text(json.dumps(cache_data))
    except OSError:
        pass


def fetch_usage(token: str) -> dict:
    """Anthropic OAuth API에서 사용량을 가져온다.

    Raises:
        urllib.error.URLError: 네트워크 오류 시.
        urllib.error.HTTPError: HTTP 에러 응답 시.
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
    """사용량 데이터를 가져온다. 캐시 우선, API fallback, stale cache 최종 fallback."""
    cached = read_cache()
    if cached is not None:
        return cached

    token = get_token()
    if not token:
        return read_cache(allow_stale=True)

    try:
        data = fetch_usage(token)
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, OSError):
        stale = read_cache(allow_stale=True)
        write_cache(None, error=True)
        return stale

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
