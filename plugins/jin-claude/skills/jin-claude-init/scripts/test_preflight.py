"""preflight.py 단위 테스트.

각 체크 함수, JSON 출력, recommendation 로직을 검증한다.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from preflight import (
    check_hooks,
    check_marketplaces,
    check_plugins,
    check_settings,
    check_statusline,
    check_venv,
    determine_recommendation,
    run_preflight,
)


class TestCheckMarketplaces:
    """check_marketplaces() 테스트 스위트."""

    def test_all_present(self) -> None:
        """모든 marketplace가 존재하면 missing이 비어야 한다."""
        settings = {
            "extraKnownMarketplaces": [
                "obsidian-skills",
                "ui-ux-pro-max-skill",
                "superpowers-marketplace",
                "context-mode",
                "superclaude",
            ]
        }
        result = check_marketplaces(settings)
        assert result["ok"] == 5
        assert result["total"] == 5
        assert result["missing"] == []

    def test_none_present(self) -> None:
        """marketplace 키가 없으면 모두 missing이어야 한다."""
        result = check_marketplaces({})
        assert result["ok"] == 0
        assert result["total"] == 5
        assert len(result["missing"]) == 5

    def test_partial(self) -> None:
        """일부만 있으면 나머지가 missing이어야 한다."""
        settings = {"extraKnownMarketplaces": ["obsidian-skills", "superclaude"]}
        result = check_marketplaces(settings)
        assert result["ok"] == 2
        assert len(result["missing"]) == 3


class TestCheckPlugins:
    """check_plugins() 테스트 스위트."""

    def test_all_present_dict(self) -> None:
        """dict 형태의 enabledPlugins에서 모든 플러그인이 존재하는 경우."""
        settings = {
            "enabledPlugins": {
                "obsidian": True,
                "ui-ux-pro-max": True,
                "superpowers": True,
                "context-mode": True,
                "sc": True,
            }
        }
        result = check_plugins(settings)
        assert result["ok"] == 5
        assert result["missing"] == []

    def test_empty(self) -> None:
        """enabledPlugins가 없으면 모두 missing이어야 한다."""
        result = check_plugins({})
        assert result["ok"] == 0
        assert len(result["missing"]) == 5


class TestCheckSettings:
    """check_settings() 테스트 스위트."""

    def test_complete(self) -> None:
        """모든 필수 설정이 있으면 complete=True."""
        settings = {
            "env": {"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"},
            "permissions": {"defaultMode": "plan"},
            "enableAllProjectMcpServers": True,
            "statusLine": {"type": "command", "command": "bash ~/.claude/statusline-command.sh"},
            "outputStyle": "Explanatory",
            "language": "korean",
            "skipDangerousModePermissionPrompt": True,
            "effortLevel": "high",
        }
        result = check_settings(settings)
        assert result["complete"] is True
        assert result["missing"] == []

    def test_missing_keys(self) -> None:
        """일부 키가 없으면 missing에 포함되어야 한다."""
        settings = {"language": "korean"}
        result = check_settings(settings)
        assert result["complete"] is False
        assert "effortLevel" in result["missing"]


class TestCheckStatusline:
    """check_statusline() 테스트 스위트."""

    @patch("preflight.CLAUDE_DIR", new_callable=lambda: lambda: Path("/nonexistent"))
    def test_not_exists(self, mock_dir: Path) -> None:
        """statusline-command.sh가 없으면 False."""
        with patch("preflight.CLAUDE_DIR", Path("/nonexistent")):
            assert check_statusline() is False

    def test_exists(self, tmp_path: Path) -> None:
        """statusline-command.sh가 존재하면 True."""
        with patch("preflight.CLAUDE_DIR", tmp_path):
            (tmp_path / "statusline-command.sh").write_text("#!/bin/bash")
            assert check_statusline() is True


class TestCheckVenv:
    """check_venv() 테스트 스위트."""

    def test_not_exists(self) -> None:
        """venv가 없으면 False."""
        with patch("preflight.CLAUDE_DIR", Path("/nonexistent")):
            assert check_venv() is False

    def test_exists(self, tmp_path: Path) -> None:
        """venv/bin/python이 존재하면 True."""
        with patch("preflight.CLAUDE_DIR", tmp_path):
            venv_python = tmp_path / ".venv" / "bin" / "python"
            venv_python.parent.mkdir(parents=True)
            venv_python.touch()
            assert check_venv() is True


class TestCheckHooks:
    """check_hooks() 테스트 스위트."""

    def test_all_hooks_from_plugin_cache(self, tmp_path: Path) -> None:
        """플러그인 캐시의 hooks.json에서 4개 hooks를 찾으면 installed=4."""
        hooks_dir = tmp_path / "plugins" / "cache" / "jin-claudecode-mp" / "jin-claude" / "3.0.0" / ".claude-plugin" / "hooks"
        hooks_dir.mkdir(parents=True)
        hooks_json = hooks_dir / "hooks.json"
        hooks_json.write_text(json.dumps({
            "hooks": {
                "UserPromptSubmit": [{}],
                "PreToolUse": [{}],
                "PostToolUse": [{}],
                "SessionStart": [{}],
            }
        }))
        with patch("preflight.CLAUDE_DIR", tmp_path):
            result = check_hooks({})
        assert result["installed"] == 4
        assert result["total"] == 4
        assert result["missing"] == []

    def test_fallback_to_settings(self) -> None:
        """플러그인 캐시가 없으면 settings.json의 hooks를 fallback으로 사용한다."""
        settings = {
            "hooks": {
                "UserPromptSubmit": [],
                "PreToolUse": [],
                "PostToolUse": [],
                "SessionStart": [],
            }
        }
        with patch("preflight.CLAUDE_DIR", Path("/nonexistent")):
            result = check_hooks(settings)
        assert result["installed"] == 4
        assert result["missing"] == []

    def test_no_hooks(self) -> None:
        """hooks가 어디에도 없으면 installed=0."""
        with patch("preflight.CLAUDE_DIR", Path("/nonexistent")):
            result = check_hooks({})
        assert result["installed"] == 0
        assert result["total"] == 4
        assert len(result["missing"]) == 4

    def test_partial_hooks_from_cache(self, tmp_path: Path) -> None:
        """플러그인 캐시에 일부 hooks만 있으면 나머지가 missing."""
        hooks_dir = tmp_path / "plugins" / "cache" / "jin-claudecode-mp" / "jin-claude" / "1.0.0" / ".claude-plugin" / "hooks"
        hooks_dir.mkdir(parents=True)
        (hooks_dir / "hooks.json").write_text(json.dumps({
            "hooks": {"SessionStart": [{}]}
        }))
        with patch("preflight.CLAUDE_DIR", tmp_path):
            result = check_hooks({})
        assert result["installed"] == 1
        assert len(result["missing"]) == 3


class TestDetermineRecommendation:
    """determine_recommendation() 테스트 스위트."""

    def test_none_when_all_ok(self) -> None:
        """모든 항목이 OK이면 'none'."""
        report = {
            "marketplaces": {"ok": 5, "total": 5},
            "plugins": {"ok": 5, "total": 5},
            "statusline": True,
            "settings": {"complete": True},
            "venv": True,
            "timer": True,
            "context7": True,
            "filesystem": True,
            "context-mode": True,
            "serena": True,
            "hooks": {"installed": 4, "total": 4},
        }
        assert determine_recommendation(report) == "none"

    def test_full_when_nothing_installed(self) -> None:
        """아무것도 설치되지 않았으면 'full'."""
        report = {
            "marketplaces": {"ok": 0, "total": 5},
            "plugins": {"ok": 0, "total": 5},
            "statusline": False,
            "settings": {"complete": False},
            "venv": False,
            "timer": False,
            "context7": False,
            "filesystem": False,
            "context-mode": False,
            "serena": False,
            "hooks": {"installed": 0, "total": 4},
        }
        assert determine_recommendation(report) == "full"

    def test_partial(self) -> None:
        """일부만 설치되었으면 'partial'."""
        report = {
            "marketplaces": {"ok": 3, "total": 5},
            "plugins": {"ok": 5, "total": 5},
            "statusline": True,
            "settings": {"complete": True},
            "venv": True,
            "timer": False,
            "context7": True,
            "filesystem": False,
            "context-mode": False,
            "serena": False,
            "hooks": {"installed": 1, "total": 4},
        }
        assert determine_recommendation(report) == "partial"
