"""preflight.py 단위 테스트.

각 체크 함수, JSON 출력, recommendation 로직을 검증한다.
"""

import json
from pathlib import Path
from unittest.mock import patch

from preflight import (
    EXPECTED_MARKETPLACES,
    EXPECTED_PLUGINS,
    check_hooks,
    check_marketplaces,
    check_plugins,
    check_settings,
    check_statusline,
    check_venv,
    determine_recommendation,
)


class TestCheckMarketplaces:
    """check_marketplaces() 테스트 스위트."""

    def test_all_present(self) -> None:
        """모든 marketplace가 존재하면 missing이 비어야 한다."""
        settings = {"extraKnownMarketplaces": list(EXPECTED_MARKETPLACES)}
        result = check_marketplaces(settings)
        total = len(EXPECTED_MARKETPLACES)
        assert result["ok"] == total
        assert result["total"] == total
        assert result["missing"] == []

    def test_none_present(self) -> None:
        """marketplace 키가 없으면 모두 missing이어야 한다."""
        result = check_marketplaces({})
        total = len(EXPECTED_MARKETPLACES)
        assert result["ok"] == 0
        assert result["total"] == total
        assert len(result["missing"]) == total

    def test_partial(self) -> None:
        """일부만 있으면 나머지가 missing이어야 한다."""
        present = list(EXPECTED_MARKETPLACES)[:2]
        settings = {"extraKnownMarketplaces": list(present)}
        result = check_marketplaces(settings)
        assert result["ok"] == len(present)
        assert len(result["missing"]) == len(EXPECTED_MARKETPLACES) - len(present)


class TestCheckPlugins:
    """check_plugins() 테스트 스위트."""

    def test_all_present_dict(self) -> None:
        """dict 형태의 enabledPlugins에서 모든 플러그인이 존재하는 경우."""
        settings = {"enabledPlugins": {name: True for name in EXPECTED_PLUGINS}}
        result = check_plugins(settings)
        assert result["ok"] == len(EXPECTED_PLUGINS)
        assert result["missing"] == []

    def test_empty(self) -> None:
        """enabledPlugins가 없으면 모두 missing이어야 한다."""
        result = check_plugins({})
        assert result["ok"] == 0
        assert len(result["missing"]) == len(EXPECTED_PLUGINS)


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
            "model": "opus",
            "advisorModel": "fable",
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

    def test_matches_plugin_copy(self, tmp_path: Path) -> None:
        """설치본이 plugin 사본과 같으면 True."""
        ref = tmp_path / "ref.sh"
        ref.write_text("#!/bin/bash\necho new")
        (tmp_path / "statusline-command.sh").write_text("#!/bin/bash\necho new")
        with patch("preflight.CLAUDE_DIR", tmp_path), patch("preflight.PLUGIN_STATUSLINE", ref):
            assert check_statusline() is True

    def test_stale_copy(self, tmp_path: Path) -> None:
        """설치본이 plugin 사본과 다르면 False — Step 3 재실행 대상."""
        ref = tmp_path / "ref.sh"
        ref.write_text("#!/bin/bash\necho new")
        (tmp_path / "statusline-command.sh").write_text("#!/bin/bash\necho old")
        with patch("preflight.CLAUDE_DIR", tmp_path), patch("preflight.PLUGIN_STATUSLINE", ref):
            assert check_statusline() is False

    def test_plugin_copy_missing(self, tmp_path: Path) -> None:
        """기준 사본이 없으면 존재만 확인."""
        (tmp_path / "statusline-command.sh").write_text("#!/bin/bash")
        missing = tmp_path / "none.sh"
        with patch("preflight.CLAUDE_DIR", tmp_path), patch("preflight.PLUGIN_STATUSLINE", missing):
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
    """check_hooks() 테스트 스위트 — 플러그인 루트 hooks/hooks.json 기준."""

    def _write_manifest(self, root: Path, version: str, hooks: dict) -> None:
        hooks_dir = root / "plugins" / "cache" / "jin-claudecode-mp" / "jin-claude" / version / "hooks"
        hooks_dir.mkdir(parents=True)
        (hooks_dir / "hooks.json").write_text(json.dumps({"hooks": hooks}))

    def test_session_start_from_plugin_cache(self, tmp_path: Path) -> None:
        """플러그인 루트 hooks/hooks.json 에 등록된 event 를 센다."""
        self._write_manifest(tmp_path, "4.1.2", {"SessionStart": [{}], "UserPromptSubmit": [{}]})
        with patch("preflight.CLAUDE_DIR", tmp_path):
            result = check_hooks({})
        assert result == {"installed": 2, "total": 2, "missing": []}

    def test_legacy_location_not_counted(self, tmp_path: Path) -> None:
        """Claude Code 가 읽지 않는 .claude-plugin/hooks/hooks.json 은 설치로 보지 않는다."""
        legacy = tmp_path / "plugins" / "cache" / "jin-claudecode-mp" / "jin-claude" / "4.0.2" / ".claude-plugin" / "hooks"
        legacy.mkdir(parents=True)
        (legacy / "hooks.json").write_text(json.dumps({"hooks": {"SessionStart": [{}]}}))
        with patch("preflight.CLAUDE_DIR", tmp_path):
            result = check_hooks({})
        assert result["installed"] == 0

    def test_fallback_to_settings(self) -> None:
        """플러그인 캐시가 없으면 settings.json의 hooks를 fallback으로 사용한다."""
        with patch("preflight.CLAUDE_DIR", Path("/nonexistent")):
            result = check_hooks({"hooks": {"SessionStart": []}})
        assert result["installed"] == 1

    def test_no_hooks(self) -> None:
        """hooks가 어디에도 없으면 installed=0."""
        with patch("preflight.CLAUDE_DIR", Path("/nonexistent")):
            result = check_hooks({})
        assert result == {"installed": 0, "total": 2, "missing": ["SessionStart", "UserPromptSubmit"]}


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
            "context-mode": True,
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
            "context-mode": False,
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
            "context-mode": False,
            "hooks": {"installed": 1, "total": 4},
        }
        assert determine_recommendation(report) == "partial"


class TestCheckMcpHealth:
    """check_mcp_health(): jin 플러그인 MCP 미연결 = missing, 그 외 실패 = 정보."""

    LIST = (
        "Checking MCP server health…\n\n"
        "claude.ai Linear: https://x - ✔ Connected\n"
        "plugin:serena:serena: uvx --from x serena - ✘ Failed to connect — spawn uvx ENOENT\n"
        "plugin:context-mode:context-mode: node x - ✔ Connected\n"
        "plugin:other:thing: node y - ✘ Failed to connect — boom\n"
        "gbrain: gbrain serve --token=SECRET - ✘ Failed to connect — CONNECTION_CLOSED\n"
    )
    JIN = ["serena@claude-plugins-official", "context-mode@context-mode"]

    def test_jin_plugin_failure_is_missing_with_hint(self) -> None:
        from preflight import MCP_HINTS, check_mcp_health

        r = check_mcp_health(self.LIST, self.JIN)
        assert r["missing"] == [{"server": "plugin:serena:serena", "plugin": self.JIN[0], "hint": MCP_HINTS[self.JIN[0]]}]
        assert r["ok"] == ["plugin:context-mode:context-mode"]

    def test_other_failures_are_info_names_only(self) -> None:
        from preflight import check_mcp_health

        r = check_mcp_health(self.LIST, self.JIN)
        assert r["other_failed"] == ["plugin:other:thing", "gbrain"]
        assert "SECRET" not in json.dumps(r) and "ENOENT" not in json.dumps(r)

    def test_list_unavailable_reports_error(self) -> None:
        from preflight import check_mcp_health

        assert check_mcp_health(None, self.JIN) == {"ok": [], "missing": [], "other_failed": [], "error": "claude mcp list 실행 실패"}

    def test_mcp_list_timeout_covers_slow_servers(self) -> None:
        """개인 MCP 하나가 30초 타임아웃이면 목록 전체가 30초+ 걸린다 (실측 35초)."""
        from preflight import MCP_LIST_TIMEOUT_SEC

        assert MCP_LIST_TIMEOUT_SEC > 60

    def test_cli_flag_prints_only_mcp(self, capsys) -> None:
        import preflight

        with patch.object(preflight, "_mcp_list", return_value=self.LIST), patch.object(preflight, "selected_plugins", return_value=self.JIN), patch("sys.argv", ["preflight.py", "--mcp"]):
            preflight.main()
        out = json.loads(capsys.readouterr().out)
        assert set(out) == {"mcp"} and out["mcp"]["missing"][0]["server"] == "plugin:serena:serena"
