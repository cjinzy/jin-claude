"""install_superclaude() 함수의 단위 테스트.

subprocess 호출을 mock하여 pipx 성공/실패, pip fallback 시나리오를 검증한다.
"""

import subprocess
from unittest.mock import MagicMock, patch

from sync_repo import install_superclaude


def _make_result(returncode: int = 0, stdout: str = "", stderr: str = "") -> MagicMock:
    """subprocess.CompletedProcess mock을 생성한다."""
    result = MagicMock(spec=subprocess.CompletedProcess)
    result.returncode = returncode
    result.stdout = stdout
    result.stderr = stderr
    return result


class TestInstallSuperclaude:
    """install_superclaude() 테스트 스위트."""

    @patch("sync_repo.subprocess.run")
    def test_pipx_success(self, mock_run: MagicMock) -> None:
        """pipx install + superclaude install 모두 성공하는 경우."""
        mock_run.side_effect = [
            _make_result(0, "installed superclaude"),  # pipx install
            _make_result(0, "initialized"),  # superclaude install
        ]

        assert install_superclaude() is True

        assert mock_run.call_count == 2
        mock_run.assert_any_call(
            ["pipx", "install", "superclaude"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        mock_run.assert_any_call(
            ["superclaude", "install"],
            capture_output=True,
            text=True,
            timeout=120,
        )

    @patch("sync_repo.subprocess.run")
    def test_pipx_success_but_init_fails(self, mock_run: MagicMock) -> None:
        """pipx install 성공, superclaude install 실패해도 True 반환."""
        mock_run.side_effect = [
            _make_result(0),  # pipx install 성공
            _make_result(1, stderr="init error"),  # superclaude install 실패
        ]

        assert install_superclaude() is True
        assert mock_run.call_count == 2

    @patch("sync_repo.subprocess.run")
    def test_pipx_not_found_pip_fallback_success(self, mock_run: MagicMock) -> None:
        """pipx 미설치(FileNotFoundError) → pip fallback 성공."""
        mock_run.side_effect = [
            FileNotFoundError("pipx not found"),  # pipx 실패
            _make_result(0),  # pip install --user 성공
            _make_result(0),  # superclaude install 성공
        ]

        assert install_superclaude() is True
        assert mock_run.call_count == 3

    @patch("sync_repo.subprocess.run")
    def test_pipx_returncode_fail_pip_fallback_success(self, mock_run: MagicMock) -> None:
        """pipx install 반환코드 실패 → pip fallback 성공."""
        mock_run.side_effect = [
            _make_result(1, stderr="pipx error"),  # pipx 반환코드 실패
            _make_result(0),  # pip install --user 성공
            _make_result(0),  # superclaude install 성공
        ]

        assert install_superclaude() is True
        assert mock_run.call_count == 3

    @patch("sync_repo.subprocess.run")
    def test_pipx_timeout_pip_fallback_success(self, mock_run: MagicMock) -> None:
        """pipx 타임아웃 → pip fallback 성공."""
        mock_run.side_effect = [
            subprocess.TimeoutExpired(cmd="pipx", timeout=120),  # pipx 타임아웃
            _make_result(0),  # pip install --user 성공
            _make_result(0),  # superclaude install 성공
        ]

        assert install_superclaude() is True
        assert mock_run.call_count == 3

    @patch("sync_repo.find_uv", return_value="/usr/local/bin/uv")
    @patch("sync_repo.subprocess.run")
    def test_pipx_and_pip_fail_uv_fallback_success(
        self, mock_run: MagicMock, mock_find_uv: MagicMock
    ) -> None:
        """pipx+pip 실패 → uv tool install 성공."""
        mock_run.side_effect = [
            FileNotFoundError("pipx not found"),  # pipx 미설치
            _make_result(1, stderr="pip error"),  # pip 실패
            _make_result(0, "installed superclaude"),  # uv tool install 성공
            _make_result(0, "initialized"),  # superclaude install 성공
        ]

        assert install_superclaude() is True
        assert mock_run.call_count == 4
        mock_run.assert_any_call(
            ["/usr/local/bin/uv", "tool", "install", "superclaude"],
            capture_output=True,
            text=True,
            timeout=120,
        )

    @patch("sync_repo.find_uv", return_value=None)
    @patch("sync_repo.subprocess.run")
    def test_all_three_fail(self, mock_run: MagicMock, mock_find_uv: MagicMock) -> None:
        """pipx+pip+uv 모두 실패하면 False 반환."""
        mock_run.side_effect = [
            FileNotFoundError("pipx not found"),  # pipx 미설치
            _make_result(1, stderr="pip error"),  # pip 실패
        ]

        assert install_superclaude() is False
        assert mock_run.call_count == 2

    @patch("sync_repo.find_uv", return_value="/usr/local/bin/uv")
    @patch("sync_repo.subprocess.run")
    def test_all_three_fail_uv_present_but_fails(
        self, mock_run: MagicMock, mock_find_uv: MagicMock
    ) -> None:
        """pipx+pip 실패, uv 존재하지만 설치 실패 → False 반환."""
        mock_run.side_effect = [
            FileNotFoundError("pipx not found"),  # pipx 미설치
            _make_result(1, stderr="pip error"),  # pip 실패
            _make_result(1, stderr="uv error"),  # uv tool install 실패
        ]

        assert install_superclaude() is False
        assert mock_run.call_count == 3

    @patch("sync_repo.find_uv", return_value=None)
    @patch("sync_repo.subprocess.run")
    def test_pip_fallback_timeout(
        self, mock_run: MagicMock, mock_find_uv: MagicMock
    ) -> None:
        """pipx 미설치, pip 타임아웃, uv 미설치 → False 반환."""
        mock_run.side_effect = [
            FileNotFoundError("pipx not found"),  # pipx 미설치
            subprocess.TimeoutExpired(cmd="pip", timeout=120),  # pip 타임아웃
        ]

        assert install_superclaude() is False
        assert mock_run.call_count == 2

    @patch("sync_repo.find_uv", return_value="/usr/local/bin/uv")
    @patch("sync_repo.subprocess.run")
    def test_uv_fallback_timeout(
        self, mock_run: MagicMock, mock_find_uv: MagicMock
    ) -> None:
        """pipx+pip 실패, uv 타임아웃 → False 반환."""
        mock_run.side_effect = [
            FileNotFoundError("pipx not found"),  # pipx 미설치
            _make_result(1, stderr="pip error"),  # pip 실패
            subprocess.TimeoutExpired(cmd="uv", timeout=120),  # uv 타임아웃
        ]

        assert install_superclaude() is False
        assert mock_run.call_count == 3
