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


class TestMcpServersConfig:
    """MCP_SERVERS 설정값 검증 스위트."""

    def test_no_filesystem_server(self) -> None:
        """filesystem MCP 서버가 제거되었는지 검증한다."""
        names = [s["name"] for s in MCP_SERVERS]
        assert "filesystem" not in names, (
            "filesystem MCP 서버는 더 이상 사용하지 않는다"
        )

    def test_all_servers_have_name_and_args(self) -> None:
        """모든 MCP 서버에 name과 args가 있는지 검증한다."""
        for server in MCP_SERVERS:
            assert "name" in server
            assert "args" in server
            assert isinstance(server["args"], list)
            assert len(server["args"]) > 0


class TestGetInstalledMcps:
    """get_installed_mcps() 테스트 스위트."""

    @patch("setup_mcp_and_teams.subprocess.run")
    def test_parses_mcp_list(self, mock_run: MagicMock) -> None:
        """claude mcp list 출력에서 서버 이름을 추출한다."""
        mock_run.return_value = _make_result(
            stdout="foo  local  npx -y @example/foo-mcp\n"
                   "bar  local  uvx --from git+https://example.com/bar\n"
        )
        result = get_installed_mcps()
        assert "foo" in result
        assert "bar" in result

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
        server_count = len(MCP_SERVERS)
        mock_run.side_effect = [
            _make_result(stdout=""),  # mcp list
        ] + [_make_result(0) for _ in range(server_count)]  # 각 서버 설치
        count = setup_mcp_servers()
        assert count == server_count
        assert mock_run.call_count == server_count + 1  # list + 각 서버

    @patch("setup_mcp_and_teams.subprocess.run")
    def test_skips_existing(self, mock_run: MagicMock) -> None:
        """이미 설치된 서버는 스킵한다."""
        all_names = "  local  npx\n".join(s["name"] for s in MCP_SERVERS) + "  local  npx\n"
        mock_run.side_effect = [
            _make_result(stdout=all_names),
        ]
        count = setup_mcp_servers()
        assert count == 0
        assert mock_run.call_count == 1  # mcp list만 호출

    @patch("setup_mcp_and_teams.MCP_SERVERS", [
        {"name": "alpha", "args": ["echo", "alpha"]},
        {"name": "beta", "args": ["echo", "beta"]},
        {"name": "gamma", "args": ["echo", "gamma"]},
    ])
    @patch("setup_mcp_and_teams.subprocess.run")
    def test_partial_install(self, mock_run: MagicMock) -> None:
        """일부만 설치된 경우 나머지만 설치한다."""
        mock_run.side_effect = [
            _make_result(stdout="alpha  local  npx\n"),  # mcp list
            _make_result(0),  # beta
            _make_result(0),  # gamma
        ]
        count = setup_mcp_servers()
        assert count == 2

    @patch("setup_mcp_and_teams.MCP_SERVERS", [
        {"name": "alpha", "args": ["echo", "alpha"]},
        {"name": "beta", "args": ["echo", "beta"]},
        {"name": "gamma", "args": ["echo", "gamma"]},
    ])
    @patch("setup_mcp_and_teams.subprocess.run")
    def test_install_failure_continues(self, mock_run: MagicMock) -> None:
        """설치 실패해도 나머지 서버를 계속 시도한다."""
        mock_run.side_effect = [
            _make_result(stdout=""),  # mcp list
            _make_result(1, stderr="fail"),  # alpha 실패
            _make_result(0),  # beta 성공
            _make_result(0),  # gamma 성공
        ]
        count = setup_mcp_servers()
        assert count == 2

    @patch("setup_mcp_and_teams.MCP_SERVERS", [
        {"name": "alpha", "args": ["echo", "alpha"]},
        {"name": "beta", "args": ["echo", "beta"]},
        {"name": "gamma", "args": ["echo", "gamma"]},
    ])
    @patch("setup_mcp_and_teams.subprocess.run")
    def test_timeout_continues(self, mock_run: MagicMock) -> None:
        """타임아웃이 발생해도 나머지 서버를 계속 시도한다."""
        mock_run.side_effect = [
            _make_result(stdout=""),  # mcp list
            subprocess.TimeoutExpired(cmd="claude", timeout=60),  # alpha 타임아웃
            _make_result(0),  # beta 성공
            _make_result(0),  # gamma 성공
        ]
        count = setup_mcp_servers()
        assert count == 2
