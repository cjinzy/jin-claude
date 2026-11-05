"""hooks 모듈 단위 테스트.

keyword_detector(Python, 미등록), session_init(Python, SessionStart)의 stdin/stdout JSON 프로토콜과 keyword 매칭을 검증한다.

하이브리드 구성: 복잡한 로직(JSON 파싱, 한글 매칭)은 Python,
단순 통과(approve)는 Bash로 구현되어 있다.
"""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# hooks 디렉토리의 모듈을 import하기 위해 경로 추가
HOOKS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from keyword_detector import KEYWORDS, main as keyword_main
from session_init import LEGACY_SKILLS, auto_update, ensure_timer, main as session_main, retire_legacy_skills


class TestKeywordDetector:
    """keyword_detector.py 테스트 스위트."""

    def test_jin_init_detected(self) -> None:
        """'jin init' 키워드를 감지하면 block 결과를 반환한다."""
        event = json.dumps({"prompt": "jin init 해줘"})
        with patch("sys.stdin") as mock_stdin, patch("builtins.print") as mock_print:
            mock_stdin.read.return_value = event
            keyword_main()
            output = json.loads(mock_print.call_args[0][0])
            assert output["result"] == "block"
            assert "jin-claude-init" in output["reason"]

    def test_jin_commit_detected(self) -> None:
        """'jin commit' 키워드를 감지한다."""
        event = json.dumps({"prompt": "jin commit"})
        with patch("sys.stdin") as mock_stdin, patch("builtins.print") as mock_print:
            mock_stdin.read.return_value = event
            keyword_main()
            output = json.loads(mock_print.call_args[0][0])
            assert output["result"] == "block"
            assert "jin-commit" in output["reason"]

    def test_jin_interview_detected(self) -> None:
        """'jin interview' 키워드를 감지한다."""
        event = json.dumps({"prompt": "jin interview 시작"})
        with patch("sys.stdin") as mock_stdin, patch("builtins.print") as mock_print:
            mock_stdin.read.return_value = event
            keyword_main()
            output = json.loads(mock_print.call_args[0][0])
            assert output["result"] == "block"
            assert "jin-interview" in output["reason"]

    def test_jin_codex_detected(self) -> None:
        """'jin codex' 키워드를 감지한다 (commit 등 다른 키워드보다 우선)."""
        event = json.dumps({"prompt": "jin codex로 이 commit 검토해줘"})
        with patch("sys.stdin") as mock_stdin, patch("builtins.print") as mock_print:
            mock_stdin.read.return_value = event
            keyword_main()
            output = json.loads(mock_print.call_args[0][0])
            assert output["result"] == "block"
            assert "jin-codex-side" in output["reason"]

    def test_removed_skills_not_mapped(self) -> None:
        """제거된 스킬로 라우팅하는 키워드가 없다."""
        removed = {"jin-gcc", "jin-chub", "verify-implementation", "jin-suggest", "guidelines"}
        assert not removed & set(KEYWORDS.values())

    def test_jin_korean_keyword(self) -> None:
        """'jin 초기화' 한글 키워드를 감지한다."""
        event = json.dumps({"prompt": "jin 초기화 해줘"})
        with patch("sys.stdin") as mock_stdin, patch("builtins.print") as mock_print:
            mock_stdin.read.return_value = event
            keyword_main()
            output = json.loads(mock_print.call_args[0][0])
            assert output["result"] == "block"
            assert "jin-claude-init" in output["reason"]

    def test_no_keyword_approves(self) -> None:
        """키워드가 없으면 approve를 반환한다."""
        event = json.dumps({"prompt": "hello world"})
        with patch("sys.stdin") as mock_stdin, patch("builtins.print") as mock_print:
            mock_stdin.read.return_value = event
            keyword_main()
            output = json.loads(mock_print.call_args[0][0])
            assert output["result"] == "approve"

    def test_case_insensitive(self) -> None:
        """키워드 매칭은 대소문자를 구분하지 않는다."""
        event = json.dumps({"prompt": "JIN INIT please"})
        with patch("sys.stdin") as mock_stdin, patch("builtins.print") as mock_print:
            mock_stdin.read.return_value = event
            keyword_main()
            output = json.loads(mock_print.call_args[0][0])
            assert output["result"] == "block"

    def test_empty_prompt_approves(self) -> None:
        """빈 프롬프트이면 approve를 반환한다."""
        event = json.dumps({"prompt": ""})
        with patch("sys.stdin") as mock_stdin, patch("builtins.print") as mock_print:
            mock_stdin.read.return_value = event
            keyword_main()
            output = json.loads(mock_print.call_args[0][0])
            assert output["result"] == "approve"


class TestSessionInit:
    """session_init.py 테스트 스위트."""

    @patch("session_init.subprocess.run")
    def test_auto_update_success(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """marketplace 디렉토리가 있으면 git pull을 실행한다."""
        mp_dir = tmp_path / "mp1"
        jin_dir = mp_dir / "plugins" / "jin-claude"
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
        jin_dir = mp_dir / "plugins" / "jin-claude"
        jin_dir.mkdir(parents=True)

        with patch("session_init.Path.home", return_value=tmp_path):
            auto_update()  # 예외 없이 완료되어야 한다


class TestEnsureTimer:
    """ensure_timer(): 타이머 파일이 사라졌으면 install-timer.sh로 재등록한다."""

    INSTALLER = Path(".claude/.jin-claude-repo/plugins/jin-claude/scripts/install-timer.sh")
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


class TestHooksManifest:
    """Claude Code 가 실제로 읽는 위치(플러그인 루트 hooks/hooks.json)에 등록됐는지 검증."""

    def test_manifest_at_plugin_root(self) -> None:
        assert MANIFEST.is_file()
        assert not (PLUGIN_DIR / ".claude-plugin" / "hooks" / "hooks.json").exists()

    def test_only_session_start_registered(self) -> None:
        hooks = json.loads(MANIFEST.read_text())["hooks"]
        assert set(hooks) == {"SessionStart"}

    def test_session_start_uses_plugin_root(self) -> None:
        """${CLAUDE_PLUGIN_ROOT} 경로 → 플러그인 업데이트만으로 훅 코드가 배포된다."""
        hook = json.loads(MANIFEST.read_text())["hooks"]["SessionStart"][0]["hooks"][0]
        assert "${CLAUDE_PLUGIN_ROOT}/hooks/session_init.py" in hook["command"]
        assert (HOOKS_DIR / "session_init.py").is_file()

    @patch("session_init.subprocess.run")
    def test_git_pull_timeout_below_hook_timeout(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """git pull 이 hook timeout 보다 먼저 끝나야 hook 이 강제 종료되지 않는다."""
        hook = json.loads(MANIFEST.read_text())["hooks"]["SessionStart"][0]["hooks"][0]
        (tmp_path / ".claude" / "plugins" / "marketplaces" / "mp1" / "plugins" / "jin-claude").mkdir(parents=True)
        mock_run.return_value = MagicMock(returncode=0)
        with patch("session_init.Path.home", return_value=tmp_path):
            auto_update()
        assert mock_run.call_args.kwargs["timeout"] < hook["timeout"]
