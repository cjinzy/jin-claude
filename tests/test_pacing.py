"""Smart Pacing 계산 로직 테스트."""

from __future__ import annotations

import json
import time
from unittest.mock import patch

import pytest

from jin_claude.fetch_claude_usage import (
    PacingZone,
    calculate_pacing,
    compute_elapsed_pct,
    write_cache,
)


class TestCalculatePacing:
    """calculate_pacing 함수 테스트."""

    def test_chill_zone(self):
        """burn_rate < 0.8이면 chill."""
        result = calculate_pacing(usage_pct=20.0, elapsed_pct=50.0)
        assert result["zone"] == PacingZone.CHILL
        assert result["burn_rate"] == pytest.approx(0.4, abs=0.01)

    def test_on_track_zone(self):
        """0.8 <= burn_rate < 1.2이면 on_track."""
        result = calculate_pacing(usage_pct=50.0, elapsed_pct=50.0)
        assert result["zone"] == PacingZone.ON_TRACK
        assert result["burn_rate"] == pytest.approx(1.0, abs=0.01)

    def test_hot_zone(self):
        """burn_rate >= 1.2이면 hot."""
        result = calculate_pacing(usage_pct=45.0, elapsed_pct=20.0)
        assert result["zone"] == PacingZone.HOT
        assert result["burn_rate"] == pytest.approx(2.25, abs=0.01)

    def test_zero_elapsed(self):
        """경과 시간 0이면 사용량에 따라 판정."""
        result = calculate_pacing(usage_pct=10.0, elapsed_pct=0.0)
        assert result["zone"] == PacingZone.HOT
        assert result["burn_rate"] == float("inf")

    def test_zero_usage_zero_elapsed(self):
        """사용량과 경과 시간 모두 0이면 chill."""
        result = calculate_pacing(usage_pct=0.0, elapsed_pct=0.0)
        assert result["zone"] == PacingZone.CHILL
        assert result["burn_rate"] == 0.0

    def test_boundary_chill_on_track(self):
        """burn_rate 정확히 0.8이면 on_track."""
        result = calculate_pacing(usage_pct=40.0, elapsed_pct=50.0)
        assert result["zone"] == PacingZone.ON_TRACK

    def test_boundary_on_track_hot(self):
        """burn_rate 정확히 1.2이면 hot."""
        result = calculate_pacing(usage_pct=60.0, elapsed_pct=50.0)
        assert result["zone"] == PacingZone.HOT


class TestComputeElapsedPct:
    """compute_elapsed_pct 함수 테스트."""

    def test_five_hour_half_elapsed(self):
        """5h 윈도우에서 2.5시간 경과."""
        resets_at_epoch = time.time() + 2.5 * 3600
        result = compute_elapsed_pct(resets_at_epoch, window_seconds=5 * 3600)
        assert 49.0 < result < 51.0

    def test_seven_day_start(self):
        """7d 윈도우 시작 직후."""
        resets_at_epoch = time.time() + 6.9 * 86400
        result = compute_elapsed_pct(resets_at_epoch, window_seconds=7 * 86400)
        assert 0.0 < result < 5.0

    def test_past_reset(self):
        """리셋 시간이 이미 지남 -> 100%."""
        resets_at_epoch = time.time() - 100
        result = compute_elapsed_pct(resets_at_epoch, window_seconds=5 * 3600)
        assert result == 100.0

    def test_no_reset_time(self):
        """리셋 시간 없으면 50% 기본값."""
        result = compute_elapsed_pct(None, window_seconds=5 * 3600)
        assert result == 50.0


class TestWriteCachePacing:
    """write_cache의 pacing 데이터 포함 테스트."""

    def test_pacing_included_on_success(self, tmp_path):
        """성공 응답 시 캐시에 pacing 포함."""
        cache_path = tmp_path / ".usage-cache.json"
        api_response = {
            "five_hour": {"utilization": 40.0, "resets_at": "2026-03-05T20:00:00Z"},
            "seven_day": {"utilization": 15.0, "resets_at": "2026-03-10T00:00:00Z"},
        }
        with patch("jin_claude.fetch_claude_usage.CACHE_PATH", cache_path):
            write_cache(api_response)
        data = json.loads(cache_path.read_text())
        assert "pacing" in data
        assert "five_hour" in data["pacing"]
        assert data["pacing"]["five_hour"]["zone"] in ("chill", "on_track", "hot")

    def test_pacing_preserved_on_error(self, tmp_path):
        """에러 시 기존 pacing 보존."""
        cache_path = tmp_path / ".usage-cache.json"
        old_cache = {
            "fetched_at": time.time() - 10,
            "error": False,
            "five_hour": {"utilization": 30.0, "resets_at": None},
            "pacing": {"five_hour": {"zone": "chill", "burn_rate": 0.5,
                                     "elapsed_pct": 60.0, "usage_pct": 30.0}},
        }
        cache_path.write_text(json.dumps(old_cache))
        with patch("jin_claude.fetch_claude_usage.CACHE_PATH", cache_path):
            write_cache(None, error=True)
        data = json.loads(cache_path.read_text())
        assert data["pacing"]["five_hour"]["zone"] == "chill"
