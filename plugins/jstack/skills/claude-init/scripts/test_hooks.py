"""hooks 단위 테스트.

session_init(SessionStart), ambition_plan(UserPromptSubmit), hooks.json 등록.
"""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import sync_repo

# hooks 디렉토리의 모듈을 import하기 위해 경로 추가
HOOKS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from ambition_plan import ASK, LOAD, context_for, main as ambition_main
import session_init
from session_init import LEGACY_SKILLS, auto_update, ensure_timer, main as session_main, retire_legacy_skills


class TestSessionInit:
    """session_init.py 테스트 스위트."""

    @patch("session_init.subprocess.run")
    def test_auto_update_success(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """marketplace 디렉토리가 있으면 git pull을 실행한다."""
        mp_dir = tmp_path / "mp1"
        jin_dir = mp_dir / "plugins" / "jstack"
        jin_dir.mkdir(parents=True)
        mock_run.return_value = MagicMock(returncode=0)

        with patch("session_init.Path.home", return_value=tmp_path):
            # marketplaces 디렉토리 생성
            marketplaces = tmp_path / ".claude" / "plugins" / "marketplaces"
            marketplaces.mkdir(parents=True)
            mp_link = marketplaces / "mp1"
            mp_link.symlink_to(mp_dir)

            auto_update()

        mock_run.assert_called_once()

    @patch("session_init.subprocess.run")
    def test_auto_update_no_marketplaces(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """marketplaces 디렉토리가 없으면 아무것도 하지 않는다."""
        with patch("session_init.Path.home", return_value=tmp_path):
            auto_update()
        mock_run.assert_not_called()

    @patch("session_init.retire_legacy_skills")
    @patch("session_init.ensure_timer")
    @patch("session_init.auto_update")
    def test_main_outputs_approve(self, mock_update: MagicMock, mock_timer: MagicMock, mock_retire: MagicMock) -> None:
        """main()은 retire_legacy_skills + ensure_timer + auto_update 를 실행하고 stdout 에 쓰지 않는다.

        SessionStart stdout 은 대화 컨텍스트에 주입되므로 비워 둔다.
        """
        with patch("builtins.print") as mock_print:
            session_main()
        mock_print.assert_not_called()
        mock_update.assert_called_once()
        mock_timer.assert_called_once()
        mock_retire.assert_called_once()

    @patch("session_init.subprocess.run")
    def test_auto_update_timeout_handled(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """git pull 타임아웃이 발생해도 예외 없이 처리된다."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="git", timeout=30)

        marketplaces = tmp_path / ".claude" / "plugins" / "marketplaces"
        mp_dir = marketplaces / "mp1"
        jin_dir = mp_dir / "plugins" / "jstack"
        jin_dir.mkdir(parents=True)

        with patch("session_init.Path.home", return_value=tmp_path):
            auto_update()  # 예외 없이 완료되어야 한다


class TestEnsureTimer:
    """ensure_timer(): 타이머 파일이 사라졌으면 install-timer.sh로 재등록한다."""

    INSTALLER = Path(".claude/.jin-claude-repo/plugins/jstack/scripts/install-timer.sh")
    PLIST = Path("Library/LaunchAgents/com.jin-claude.fetch-usage.plist")

    def _installer(self, home: Path) -> Path:
        path = home / self.INSTALLER
        path.parent.mkdir(parents=True)
        path.touch()
        return path

    @patch("session_init.subprocess.Popen")
    def test_reinstalls_when_plist_missing(self, mock_run: MagicMock, tmp_path: Path) -> None:
        installer = self._installer(tmp_path)
        with patch("session_init.Path.home", return_value=tmp_path), \
             patch("session_init.sys.platform", "darwin"):
            ensure_timer()
        mock_run.assert_called_once()
        assert mock_run.call_args[0][0] == ["bash", str(installer), "5"]

    @pytest.mark.parametrize(
        ("saved", "arg"), [("10", "10"), ("3\n", "3"), ("abc", "5"), ("7", "5")]
    )
    @patch("session_init.subprocess.Popen")
    def test_reinstalls_with_saved_interval(
        self, mock_run: MagicMock, saved: str, arg: str, tmp_path: Path
    ) -> None:
        """init 이 고른 주기로 재등록. 정수 아님·허용값(1/3/5/10) 밖이면 5."""
        installer = self._installer(tmp_path)
        (tmp_path / ".claude" / ".jin-claude-usage-interval").write_text(saved)
        with patch("session_init.Path.home", return_value=tmp_path), \
             patch("session_init.sys.platform", "darwin"):
            ensure_timer()
        assert mock_run.call_args[0][0] == ["bash", str(installer), arg]

    def test_interval_file_matches_sync_repo(self) -> None:
        """hooks/·scripts/ 는 서로 import 하지 않아 경로 복제 — 어긋나면 주기를 못 읽는다."""
        assert sync_repo.CLAUDE_DIR.parent / session_init.INTERVAL_FILE == sync_repo.INTERVAL_FILE

    @patch("session_init.subprocess.Popen")
    def test_skips_when_plist_exists(self, mock_run: MagicMock, tmp_path: Path) -> None:
        self._installer(tmp_path)
        (tmp_path / self.PLIST).parent.mkdir(parents=True)
        (tmp_path / self.PLIST).touch()
        with patch("session_init.Path.home", return_value=tmp_path), \
             patch("session_init.sys.platform", "darwin"):
            ensure_timer()
        mock_run.assert_not_called()

    @patch("session_init.subprocess.Popen")
    def test_skips_without_init(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """init(sync_repo) 이력이 없으면 설치하지 않는다."""
        with patch("session_init.Path.home", return_value=tmp_path), \
             patch("session_init.sys.platform", "darwin"):
            ensure_timer()
        mock_run.assert_not_called()

    @patch("session_init.subprocess.Popen")
    def test_skips_unsupported_platform(self, mock_run: MagicMock, tmp_path: Path) -> None:
        self._installer(tmp_path)
        with patch("session_init.Path.home", return_value=tmp_path), \
             patch("session_init.sys.platform", "win32"):
            ensure_timer()
        mock_run.assert_not_called()

    @patch("session_init.subprocess.Popen")
    def test_install_failure_handled(self, mock_run: MagicMock, tmp_path: Path) -> None:
        self._installer(tmp_path)
        mock_run.side_effect = OSError("bash not found")
        with patch("session_init.Path.home", return_value=tmp_path), \
             patch("session_init.sys.platform", "linux"):
            ensure_timer()  # 예외 없이 완료되어야 한다


PLUGIN_DIR = HOOKS_DIR.parent
MANIFEST = PLUGIN_DIR / "hooks" / "hooks.json"


class TestRetireLegacySkills:
    """retire_legacy_skills(): 구버전 sync 가 남긴 ~/.claude/skills 사본은 plugin 스킬을 가리므로 백업 폴더로 옮긴다."""

    def _skill(self, home: Path, name: str) -> Path:
        path = home / ".claude" / "skills" / name
        path.mkdir(parents=True)
        (path / "SKILL.md").write_text(name)
        return path

    def test_moves_legacy_keeps_others(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        legacy = self._skill(tmp_path, "jin-commit")
        mine = self._skill(tmp_path, "my-skill")
        with patch("session_init.Path.home", return_value=tmp_path):
            retire_legacy_skills()
        assert not legacy.exists()
        assert mine.exists()
        moved = list((tmp_path / ".claude" / "backups").glob("skills_backup_*/jin-commit/SKILL.md"))
        assert len(moved) == 1
        assert capsys.readouterr().out == ""  # SessionStart stdout = 컨텍스트 주입

    def test_collision_keeps_both(self, tmp_path: Path) -> None:
        """같은 날 두 번째 이동이 첫 백업을 덮지 않는다."""
        with patch("session_init.Path.home", return_value=tmp_path):
            self._skill(tmp_path, "jin-commit")
            retire_legacy_skills()
            self._skill(tmp_path, "jin-commit")
            retire_legacy_skills()
        assert len(list((tmp_path / ".claude" / "backups").glob("skills_backup_*/jin-commit*"))) == 2

    def test_noop_without_skills_dir(self, tmp_path: Path) -> None:
        with patch("session_init.Path.home", return_value=tmp_path):
            retire_legacy_skills()
        assert not (tmp_path / ".claude" / "backups").exists()

    def test_covers_plugin_skill_names(self) -> None:
        """plugin 에 같은 이름이 있거나 제거된 스킬만 대상."""
        assert LEGACY_SKILLS == {"jin-claude-init", "jin-commit", "jin-interview", "manage-skills", "verify-implementation"}


class TestAmbitionPlan:
    """UserPromptSubmit: plan 모드면 ambition 여부를 묻게 하고, 프롬프트에 ambition 이 있으면 묻지 않고 3개 스킬 로드."""

    @pytest.mark.parametrize("mode", ["plan", "default", "auto"])
    def test_keyword_loads_without_asking(self, mode: str) -> None:
        assert context_for("이번 계획은 Ambition 으로", mode) == LOAD
        assert context_for("앰비션 모드로 계획", mode) == LOAD

    def test_plan_mode_asks(self) -> None:
        assert context_for("로그인 기능 계획 세워줘", "plan") == ASK

    def test_other_modes_silent(self) -> None:
        assert context_for("로그인 기능 만들어줘", "default") is None

    def test_load_names_single_skill(self) -> None:
        """세 축은 ambition 한 스킬 (목록 1칸, compaction 때 본문째 재부착)."""
        for name in ("jstack:ambition", "## Ambition"):
            assert name in LOAD and name in ASK
        for old in ("jin-altitude", "jin-depth", "jin-range"):
            assert old not in LOAD and old not in ASK

    def test_ambition_skill_has_all_axes(self) -> None:
        skills = Path(__file__).resolve().parents[2]
        text = (skills / "ambition" / "SKILL.md").read_text(encoding="utf-8")
        assert "name: ambition" in text
        for axis in ("## Altitude", "## Depth", "## Range", "$ARGUMENTS"):
            assert axis in text
        assert "적용한 축마다 한 항목" in text and "적용한 축마다 한 항목" in LOAD  # 인자로 축 하나만 적용 가능
        for old in ("jin-altitude", "jin-depth", "jin-range"):
            assert not (skills / old).exists()

    def test_main_emits_additional_context(self, capsys: pytest.CaptureFixture) -> None:
        payload = json.dumps({"prompt": "계획", "permission_mode": "plan", "hook_event_name": "UserPromptSubmit"})
        with patch("sys.stdin.read", return_value=payload):
            ambition_main()
        out = json.loads(capsys.readouterr().out)
        assert out["hookSpecificOutput"] == {"hookEventName": "UserPromptSubmit", "additionalContext": ASK}

    @pytest.mark.parametrize("raw", ["", "not json", json.dumps({"prompt": "x", "permission_mode": "default"})])
    def test_main_silent_never_blocks(self, raw: str, capsys: pytest.CaptureFixture) -> None:
        """잘못된 입력·대상 아님 → 출력 없음, 예외 없음 (프롬프트를 막지 않는다)."""
        with patch("sys.stdin.read", return_value=raw):
            ambition_main()
        assert capsys.readouterr().out == ""


class TestHooksManifest:
    """Claude Code 가 실제로 읽는 위치(플러그인 루트 hooks/hooks.json)에 등록됐는지 검증."""

    def test_manifest_at_plugin_root(self) -> None:
        assert MANIFEST.is_file()
        assert not (PLUGIN_DIR / ".claude-plugin" / "hooks" / "hooks.json").exists()

    def test_registered_events(self) -> None:
        hooks = json.loads(MANIFEST.read_text())["hooks"]
        assert set(hooks) == {"SessionStart", "UserPromptSubmit"}
        cmd = hooks["UserPromptSubmit"][0]["hooks"][0]["command"]
        assert "${CLAUDE_PLUGIN_ROOT}/hooks/ambition_plan.py" in cmd
        assert (HOOKS_DIR / "ambition_plan.py").is_file()

    def test_session_start_uses_plugin_root(self) -> None:
        """${CLAUDE_PLUGIN_ROOT} 경로 → 플러그인 업데이트만으로 훅 코드가 배포된다."""
        hook = json.loads(MANIFEST.read_text())["hooks"]["SessionStart"][0]["hooks"][0]
        assert "${CLAUDE_PLUGIN_ROOT}/hooks/session_init.py" in hook["command"]
        assert (HOOKS_DIR / "session_init.py").is_file()

    @patch("session_init.subprocess.run")
    def test_git_pull_timeout_below_hook_timeout(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """git pull 이 hook timeout 보다 먼저 끝나야 hook 이 강제 종료되지 않는다."""
        hook = json.loads(MANIFEST.read_text())["hooks"]["SessionStart"][0]["hooks"][0]
        (tmp_path / ".claude" / "plugins" / "marketplaces" / "mp1" / "plugins" / "jstack").mkdir(parents=True)
        mock_run.return_value = MagicMock(returncode=0)
        with patch("session_init.Path.home", return_value=tmp_path):
            auto_update()
        assert mock_run.call_args.kwargs["timeout"] < hook["timeout"]
