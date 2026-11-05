"""hooks 모듈 단위 테스트.

keyword_detector(Python), pre_tool_enforcer(Bash), post_tool_verifier(Bash),
session_init(Python)의 stdin/stdout JSON 프로토콜과 keyword 매칭을 검증한다.

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
from session_init import auto_update, ensure_timer, main as session_main


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

    def test_jin_gcc_detected(self) -> None:
        """'jin gcc' 키워드를 감지한다."""
        event = json.dumps({"prompt": "jin gcc로 검토해줘"})
        with patch("sys.stdin") as mock_stdin, patch("builtins.print") as mock_print:
            mock_stdin.read.return_value = event
            keyword_main()
            output = json.loads(mock_print.call_args[0][0])
            assert output["result"] == "block"
            assert "jin-gcc" in output["reason"]

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


class TestPreToolEnforcerBash:
    """pre_tool_enforcer.sh (Bash) 테스트 스위트."""

    def test_approves_any_tool(self) -> None:
        """모든 도구에 대해 approve를 반환한다."""
        script = HOOKS_DIR / "pre_tool_enforcer.sh"
        result = subprocess.run(
            ["bash", str(script)],
            input='{"tool_name": "Edit"}',
            capture_output=True,
            text=True,
            timeout=5,
        )
        output = json.loads(result.stdout.strip())
        assert output["result"] == "approve"

    def test_handles_empty_stdin(self) -> None:
        """빈 stdin에도 approve를 반환한다."""
        script = HOOKS_DIR / "pre_tool_enforcer.sh"
        result = subprocess.run(
            ["bash", str(script)],
            input="",
            capture_output=True,
            text=True,
            timeout=5,
        )
        output = json.loads(result.stdout.strip())
        assert output["result"] == "approve"


class TestPostToolVerifierBash:
    """post_tool_verifier.sh (Bash) 테스트 스위트."""

    def test_approves(self) -> None:
        """기본 구현은 항상 approve를 반환한다."""
        script = HOOKS_DIR / "post_tool_verifier.sh"
        result = subprocess.run(
            ["bash", str(script)],
            input='{"tool_name": "Read", "output": "file content"}',
            capture_output=True,
            text=True,
            timeout=5,
        )
        output = json.loads(result.stdout.strip())
        assert output["result"] == "approve"

    def test_handles_large_input(self) -> None:
        """대량 stdin에도 정상 동작한다."""
        script = HOOKS_DIR / "post_tool_verifier.sh"
        large_input = json.dumps({"output": "x" * 10000})
        result = subprocess.run(
            ["bash", str(script)],
            input=large_input,
            capture_output=True,
            text=True,
            timeout=5,
        )
        output = json.loads(result.stdout.strip())
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

    @patch("session_init.ensure_timer")
    @patch("session_init.auto_update")
    def test_main_outputs_approve(self, mock_update: MagicMock, mock_timer: MagicMock) -> None:
        """main()은 auto_update + ensure_timer 후 approve JSON을 출력한다."""
        with patch("builtins.print") as mock_print:
            session_main()
            output = json.loads(mock_print.call_args[0][0])
            assert output["result"] == "approve"
        mock_update.assert_called_once()
        mock_timer.assert_called_once()

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
