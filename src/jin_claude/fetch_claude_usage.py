"""Fetch Claude API usage (7d weekly + model-scoped weekly) via undocumented OAuth endpoint.

Reads OAuth token from macOS Keychain or ~/.claude/.credentials.json,
calls the usage API, caches the result, and outputs
`7d_util|7d_resets|model_label|model_util|model_resets` for statusline consumption.

Cache: ~/.claude/.usage-cache.json (5m TTL, 300s for errors)
Last-good cache: ~/.claude/.usage-last-good.json (마지막 성공 데이터 영구 보존)
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

from loguru import logger

CREDENTIALS_PATH = Path.home() / ".claude" / ".credentials.json"
CACHE_PATH = Path.home() / ".claude" / ".usage-cache.json"
CACHE_TTL_SECONDS = 300        # 5분
CACHE_TTL_ERROR_SECONDS = 300  # 에러 캐시 5분 — systemd 주기와 동기화
LAST_GOOD_CACHE_PATH = Path.home() / ".claude" / ".usage-last-good.json"
BACKOFF_MULTIPLIERS = [1, 2, 4, 6]  # 5min → 10min → 20min → 30min cap

logger.add(
    Path.home() / ".claude" / ".usage-fetch.log",
    rotation="1 MB",
    retention=3,
    level="DEBUG",
)

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


SEVEN_DAY_WINDOW = 7 * 86400
SCOPED_LIMIT_KIND = "weekly_scoped"
# 캐시에 저장·보존되는 usage 필드. seven_day 가 "데이터 있음" 판정 기준.
USAGE_KEYS = ("seven_day", "seven_day_model", "pacing")


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
    seven_day = api_response.get("seven_day")
    if seven_day and seven_day.get("utilization") is not None:
        resets_epoch = _parse_resets_at(seven_day.get("resets_at"))
        elapsed = compute_elapsed_pct(resets_epoch, SEVEN_DAY_WINDOW)
        pacing["seven_day"] = calculate_pacing(seven_day["utilization"], elapsed)

    return pacing if pacing else None


def _extract_model_limit(api_response: dict) -> dict | None:
    """`limits` 에서 모델별 주간 한도(예: Fable)를 꺼낸다.

    ponytail: 첫 모델 scoped 한도만 사용. 여러 모델이 동시에 오면 리스트로 확장.
    """
    for limit in api_response.get("limits") or []:
        model = ((limit.get("scope") or {}).get("model")) or {}
        if limit.get("kind") == SCOPED_LIMIT_KIND and model.get("display_name"):
            return {
                "label": model["display_name"],
                "utilization": limit.get("percent"),
                "resets_at": limit.get("resets_at"),
            }
    return None


def _usage_fields(api_response: dict) -> dict:
    """API 응답에서 캐시에 저장할 usage 필드(USAGE_KEYS)를 만든다."""
    return {
        "seven_day": api_response.get("seven_day"),
        "seven_day_model": _extract_model_limit(api_response),
        "pacing": _compute_pacing_for_cache(api_response),
    }


@dataclass
class UsageBucket:
    """A single usage bucket from the API response."""

    utilization: float
    resets_at: str | None = None
    label: str | None = None


@dataclass
class UsageResult:
    """Combined usage result for statusline output."""

    seven_day: UsageBucket
    model: UsageBucket | None = None


def _bucket(raw: dict | None) -> UsageBucket | None:
    """캐시/API dict → UsageBucket. utilization 없으면 None."""
    if not raw or raw.get("utilization") is None:
        return None
    return UsageBucket(
        utilization=raw["utilization"],
        resets_at=raw.get("resets_at"),
        label=raw.get("label"),
    )


def _result_from(data: dict) -> UsageResult | None:
    """usage 필드 dict → UsageResult. seven_day 없으면 None."""
    seven_day = _bucket(data.get("seven_day"))
    if seven_day is None:
        return None
    return UsageResult(seven_day=seven_day, model=_bucket(data.get("seven_day_model")))


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
                    logger.info("Token refreshed successfully")
                    return refreshed["access_token"]
                logger.error("Token refresh failed")
            # stale .credentials.json 이 살아있는 keychain 토큰을 가리지 않도록 폴백
            return read_token_from_keychain()
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
        # 에러 캐시라도 보존된 정상 데이터가 있으면 stale로 반환
        return _result_from(data)
    except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError):
        return None


def _write_last_good(api_response: dict) -> None:
    """성공한 API 응답을 last-known-good 캐시에 저장한다."""
    try:
        data = {"fetched_at": time.time(), **_usage_fields(api_response)}
        LAST_GOOD_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        LAST_GOOD_CACHE_PATH.write_text(json.dumps(data))
    except OSError:
        pass


def _read_last_good() -> dict | None:
    """last-known-good 캐시에서 데이터를 읽는다."""
    try:
        return json.loads(LAST_GOOD_CACHE_PATH.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _should_skip_due_to_backoff() -> bool:
    """exponential backoff 기반으로 API 호출을 건너뛸지 판단한다.

    연속 에러 횟수에 따라 backoff window를 계산하고,
    현재 시간이 window 내에 있으면 True를 반환하여 API 호출을 건너뛰게 한다.
    """
    try:
        data = json.loads(CACHE_PATH.read_text())
        if not data.get("error"):
            return False
        consecutive = data.get("consecutive_errors", 0)
        if consecutive <= 0:
            return False
        idx = min(consecutive - 1, len(BACKOFF_MULTIPLIERS) - 1)
        multiplier = BACKOFF_MULTIPLIERS[idx]
        effective_ttl = CACHE_TTL_ERROR_SECONDS * multiplier
        age = time.time() - data.get("fetched_at", 0)
        return age < effective_ttl
    except (FileNotFoundError, json.JSONDecodeError):
        return False


def _read_last_good_as_result() -> UsageResult | None:
    """last-known-good 캐시에서 UsageResult를 생성한다."""
    data = _read_last_good()
    if data is None:
        return None
    try:
        return _result_from(data)
    except (KeyError, TypeError, AttributeError):
        return None


def write_cache(
    api_response: dict | None,
    error: bool = False,
    error_reason: str | None = None,
) -> None:
    """API 응답을 캐시 파일에 저장한다.

    에러 시 기존 캐시의 정상 데이터(USAGE_KEYS)를 보존하여
    stale fallback이 가능하도록 한다. 기존 캐시에도 데이터가 없으면
    last-known-good 캐시에서 복원을 시도한다.

    Args:
        api_response: API 응답 dict. 에러 시 None.
        error: True이면 에러 캐시로 저장 (300초 TTL).
        error_reason: 에러 원인 식별자.
            가능한 값: "rate_limited", "token_expired", "refresh_failed",
            "network_error", "api_error", "token_needs_relogin".
    """
    cache_data: dict = {
        "fetched_at": time.time(),
        "error": error,
        "error_reason": error_reason,
    }
    if api_response is not None:
        cache_data.update(_usage_fields(api_response))
        cache_data["consecutive_errors"] = 0
        _write_last_good(api_response)
    elif error:
        # 에러 시 기존 캐시의 usage 데이터를 보존 (연속 에러에도 유지)
        try:
            old = json.loads(CACHE_PATH.read_text())
            old_consecutive = old.get("consecutive_errors", 0)
            cache_data["consecutive_errors"] = old_consecutive + 1
            # first_error_at: 연속 에러의 시작 시점 보존
            if old_consecutive > 0 and old.get("first_error_at"):
                cache_data["first_error_at"] = old["first_error_at"]
            else:
                cache_data["first_error_at"] = time.time()
            # 기존 캐시에 데이터 없으면 last-good에서 복원
            source = old if old.get("seven_day") is not None else _read_last_good()
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            cache_data["consecutive_errors"] = 1
            cache_data["first_error_at"] = time.time()
            source = _read_last_good()
        if source is not None:
            cache_data.update({k: source.get(k) for k in USAGE_KEYS})
    try:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_text(json.dumps(cache_data))
    except OSError:
        pass


def fetch_usage(token: str) -> dict:
    """Anthropic OAuth API에서 사용량을 가져온다.

    Raises:
        urllib.error.URLError: 네트워크 오류 시.
        urllib.error.HTTPError: HTTP 에러 응답 시. e.code로 상태 코드 확인 가능.
            429 시 e.headers.get("Retry-After") 로 재시도 대기 시간 확인.
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
    """사용량 데이터를 가져온다.

    캐시 우선 → backoff 체크 → API fallback → stale cache → last-good 최종 fallback.
    """
    cached = read_cache()
    if cached is not None:
        return cached

    # Exponential backoff: 연속 에러 시 API 호출 건너뜀
    if _should_skip_due_to_backoff():
        logger.debug("Skipping API call: within exponential backoff window")
        stale = read_cache(allow_stale=True)
        if stale is not None:
            return stale
        return _read_last_good_as_result()

    token = get_token()
    if not token:
        logger.warning("Usage fetch failed: token_needs_relogin - no valid token found")
        write_cache(None, error=True, error_reason="token_needs_relogin")
        return read_cache(allow_stale=True) or _read_last_good_as_result()

    try:
        data = fetch_usage(token)
    except urllib.error.HTTPError as e:
        stale = read_cache(allow_stale=True)
        if e.code == 429:
            retry_after = e.headers.get("Retry-After", "unknown")
            error_reason = "rate_limited"
            logger.warning(
                f"Usage fetch failed: {error_reason} - HTTP 429 (Retry-After: {retry_after})"
            )
        elif e.code in (401, 403):
            error_reason = "token_expired"
            logger.warning(
                f"Usage fetch failed: {error_reason} - HTTP {e.code}"
            )
        else:
            error_reason = "api_error"
            logger.warning(
                f"Usage fetch failed: {error_reason} - HTTP {e.code}"
            )
        write_cache(None, error=True, error_reason=error_reason)
        return stale or _read_last_good_as_result()
    except urllib.error.URLError as e:
        stale = read_cache(allow_stale=True)
        logger.warning(f"Usage fetch failed: network_error - {e.reason}")
        write_cache(None, error=True, error_reason="network_error")
        return stale or _read_last_good_as_result()
    except (json.JSONDecodeError, OSError) as e:
        stale = read_cache(allow_stale=True)
        logger.warning(f"Usage fetch failed: api_error - {e}")
        write_cache(None, error=True, error_reason="api_error")
        return stale or _read_last_good_as_result()

    write_cache(data)

    result = _result_from(_usage_fields(data))
    if result is None:
        logger.warning("Usage fetch: seven_day missing in API response")
        return None
    logger.info(
        f"Usage fetched: 7d={result.seven_day.utilization}%"
        + (f", {result.model.label}={result.model.utilization}%" if result.model else "")
    )
    return result


def main() -> None:
    """CLI entry point. Outputs `7d_util|7d_resets|model_label|model_util|model_resets`."""
    result = get_usage()
    if result is None:
        sys.exit(1)
    seven_day, model = result.seven_day, result.model
    fields = [f"{seven_day.utilization:.0f}", seven_day.resets_at or ""]
    fields += (
        [model.label or "", f"{model.utilization:.0f}", model.resets_at or ""]
        if model
        else ["", "", ""]
    )
    print("|".join(fields))


if __name__ == "__main__":
    main()
