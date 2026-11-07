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
    check_venv,
    determine_recommendation,
    stale_synced_files,
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


class TestStaleSyncedFiles:
    """stale_synced_files(): Step 3 대상 중 없거나 marketplace 사본과 다른 파일."""

    @staticmethod
    def _setup(tmp_path: Path, installed: dict[str, str], ref: dict[str, str]) -> list:
        """installed·ref 를 tmp_path 에 쓰고 SYNC_FILES 형태 목록을 돌려준다."""
        home, repo = tmp_path / "home", tmp_path / "repo"
        for root, files in ((home, installed), (repo, ref)):
            root.mkdir(exist_ok=True)
            for name, text in files.items():
                (root / name).write_text(text)
        return [(name, home / name) for name in ("CLAUDE.md", "statusline-command.sh")]

    def _run(self, tmp_path: Path, installed: dict[str, str], ref: dict[str, str]) -> list[str]:
        sync_files = self._setup(tmp_path, installed, ref)
        repo = tmp_path / "repo"
        with patch("preflight.SYNC_FILES", sync_files), patch("preflight.MARKETPLACE_DIR", repo):
            return stale_synced_files()

    def test_all_current(self, tmp_path: Path) -> None:
        """모두 사본과 같으면 빈 목록."""
        files = {"CLAUDE.md": "a", "statusline-command.sh": "b"}
        assert self._run(tmp_path, files, files) == []

    def test_missing(self, tmp_path: Path) -> None:
        """설치본이 없으면 stale."""
        ref = {"CLAUDE.md": "a", "statusline-command.sh": "b"}
        assert self._run(tmp_path, {"statusline-command.sh": "b"}, ref) == ["CLAUDE.md"]

    def test_outdated(self, tmp_path: Path) -> None:
        """내용이 다르면 stale — 존재만 보면 Step 3 이 계속 스킵된다."""
        ref = {"CLAUDE.md": "new", "statusline-command.sh": "new"}
        installed = {"CLAUDE.md": "old", "statusline-command.sh": "new"}
        assert self._run(tmp_path, installed, ref) == ["CLAUDE.md"]

    def test_no_reference(self, tmp_path: Path) -> None:
        """기준 사본이 없으면 존재 여부만 본다."""
        assert self._run(tmp_path, {"CLAUDE.md": "x", "statusline-command.sh": "y"}, {}) == []


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
            "claude_md": {"missing": []},
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
            "claude_md": {"missing": ["CLAUDE.md"]},
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
            "claude_md": {"missing": []},
            "settings": {"complete": True},
            "venv": True,
            "timer": False,
            "context-mode": False,
            "hooks": {"installed": 1, "total": 4},
        }
        assert determine_recommendation(report) == "partial"

    def test_partial_when_claude_md_stale(self) -> None:
        """CLAUDE.md 만 낡아도 'partial' (Step 3 재실행)."""
        report = {
            "marketplaces": {"ok": 5, "total": 5},
            "plugins": {"ok": 5, "total": 5},
            "statusline": True,
            "claude_md": {"missing": ["CLAUDE.md"]},
            "settings": {"complete": True},
            "venv": True,
            "timer": True,
            "hooks": {"installed": 4, "total": 4},
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
