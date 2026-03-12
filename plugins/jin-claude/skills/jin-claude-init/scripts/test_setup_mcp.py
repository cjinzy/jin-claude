"""setup_mcp_and_teams.py 단위 테스트.

MCP 서버 설치/스킵, claude mcp list 파싱을 검증한다.
"""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from setup_mcp_and_teams import MCP_SERVERS, get_installed_mcps, setup_mcp_servers


def _make_result(returncode: int = 0, stdout: str = "", stderr: str = "") -> MagicMock:
    """subprocess.CompletedProcess mock을 생성한다."""
    result = MagicMock(spec=subprocess.CompletedProcess)
    result.returncode = returncode
    result.stdout = stdout
    result.stderr = stderr
    return result


class TestGetInstalledMcps:
    """get_installed_mcps() 테스트 스위트."""

    @patch("setup_mcp_and_teams.subprocess.run")
    def test_parses_mcp_list(self, mock_run: MagicMock) -> None:
        """claude mcp list 출력에서 서버 이름을 추출한다."""
        mock_run.return_value = _make_result(
            stdout="context7  local  npx -y @anthropic-ai/context7-mcp@latest\n"
                   "filesystem  local  npx -y @anthropic-ai/filesystem-mcp /Users/user\n"
        )
        result = get_installed_mcps()
        assert "context7" in result
        assert "filesystem" in result

    @patch("setup_mcp_and_teams.subprocess.run")
    def test_empty_on_failure(self, mock_run: MagicMock) -> None:
        """claude mcp list 실패 시 빈 집합을 반환한다."""
        mock_run.return_value = _make_result(returncode=1, stderr="error")
        result = get_installed_mcps()
        assert result == set()

    @patch("setup_mcp_and_teams.subprocess.run")
    def test_empty_on_timeout(self, mock_run: MagicMock) -> None:
        """타임아웃 시 빈 집합을 반환한다."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="claude", timeout=30)
        result = get_installed_mcps()
        assert result == set()

    @patch("setup_mcp_and_teams.subprocess.run")
    def test_empty_on_file_not_found(self, mock_run: MagicMock) -> None:
        """claude 명령어가 없으면 빈 집합을 반환한다."""
        mock_run.side_effect = FileNotFoundError("claude not found")
        result = get_installed_mcps()
        assert result == set()


class TestSetupMcpServers:
    """setup_mcp_servers() 테스트 스위트."""

    @patch("setup_mcp_and_teams.subprocess.run")
    def test_installs_all_when_none_exist(self, mock_run: MagicMock) -> None:
        """MCP 서버가 없으면 모두 설치한다."""
        # 첫 번째 호출: mcp list (빈 결과)
        # 이후 3번: mcp add (각 서버)
        mock_run.side_effect = [
            _make_result(stdout=""),  # mcp list
            _make_result(0),  # context7
            _make_result(0),  # filesystem
            _make_result(0),  # context-mode
        ]
        count = setup_mcp_servers()
        assert count == 3
        assert mock_run.call_count == 4

    @patch("setup_mcp_and_teams.subprocess.run")
    def test_skips_existing(self, mock_run: MagicMock) -> None:
        """이미 설치된 서버는 스킵한다."""
        mock_run.side_effect = [
            _make_result(
                stdout="context7  local  npx\nfilesystem  local  npx\ncontext-mode  local  npx\n"
            ),
        ]
        count = setup_mcp_servers()
        assert count == 0
        assert mock_run.call_count == 1  # mcp list만 호출

    @patch("setup_mcp_and_teams.subprocess.run")
    def test_partial_install(self, mock_run: MagicMock) -> None:
        """일부만 설치된 경우 나머지만 설치한다."""
        mock_run.side_effect = [
            _make_result(stdout="context7  local  npx\n"),  # mcp list
            _make_result(0),  # filesystem
            _make_result(0),  # context-mode
        ]
        count = setup_mcp_servers()
        assert count == 2

    @patch("setup_mcp_and_teams.subprocess.run")
    def test_install_failure_continues(self, mock_run: MagicMock) -> None:
        """설치 실패해도 나머지 서버를 계속 시도한다."""
        mock_run.side_effect = [
            _make_result(stdout=""),  # mcp list
            _make_result(1, stderr="fail"),  # context7 실패
            _make_result(0),  # filesystem 성공
            _make_result(0),  # context-mode 성공
        ]
        count = setup_mcp_servers()
        assert count == 2

    @patch("setup_mcp_and_teams.subprocess.run")
    def test_timeout_continues(self, mock_run: MagicMock) -> None:
        """타임아웃이 발생해도 나머지 서버를 계속 시도한다."""
        mock_run.side_effect = [
            _make_result(stdout=""),  # mcp list
            subprocess.TimeoutExpired(cmd="claude", timeout=60),  # context7 타임아웃
            _make_result(0),  # filesystem 성공
            _make_result(0),  # context-mode 성공
        ]
        count = setup_mcp_servers()
        assert count == 2
