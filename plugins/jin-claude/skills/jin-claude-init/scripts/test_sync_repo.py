"""sync_repo 모듈의 단위 테스트.

sync_directory()의 파일 동기화 및 잔류 항목 제거,
install_superclaude()의 subprocess fallback 시나리오를 검증한다.
"""

import shutil
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from sync_repo import install_superclaude, sync_directory


def _make_skill(base: Path, name: str, content: str = "skill") -> None:
    """스킬 디렉토리와 SKILL.md 파일을 생성한다."""
    d = base / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text(content)


@pytest.fixture
def sync_dirs(tmp_path: Path) -> tuple[Path, Path]:
    """소스/대상 디렉토리 쌍을 생성한다."""
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    dst.mkdir()
    return src, dst


class TestSyncDirectory:
    """sync_directory() 테스트 스위트."""

    def test_copies_files_from_src_to_dst(self, sync_dirs: tuple[Path, Path]) -> None:
        """소스 파일이 대상에 복사된다."""
        src, dst = sync_dirs
        _make_skill(src, "jin-commit", "new content")

        count = sync_directory(src, dst)

        assert count == 1
        assert (dst / "jin-commit" / "SKILL.md").read_text() == "new content"

    def test_overwrites_existing_files(self, sync_dirs: tuple[Path, Path]) -> None:
        """기존 파일은 덮어쓴다."""
        src, dst = sync_dirs
        _make_skill(src, "jin-commit", "updated")
        _make_skill(dst, "jin-commit", "old")

        sync_directory(src, dst)

        assert (dst / "jin-commit" / "SKILL.md").read_text() == "updated"

    def test_removes_stale_dirs_not_in_src(self, sync_dirs: tuple[Path, Path]) -> None:
        """소스에 없는 대상 최상위 디렉토리를 제거한다."""
        src, dst = sync_dirs
        _make_skill(src, "jin-commit")
        _make_skill(dst, "zy-commit")
        _make_skill(dst, "zy-interview")

        sync_directory(src, dst)

        assert (dst / "jin-commit").exists()
        assert not (dst / "zy-commit").exists()
        assert not (dst / "zy-interview").exists()

    def test_removes_stale_files(self, sync_dirs: tuple[Path, Path]) -> None:
        """소스에 없는 대상 최상위 파일도 제거한다."""
        src, dst = sync_dirs
        _make_skill(src, "jin-commit")
        (dst / "orphan.txt").write_text("stale")

        sync_directory(src, dst)

        assert not (dst / "orphan.txt").exists()

    def test_preserves_items_in_src(self, sync_dirs: tuple[Path, Path]) -> None:
        """소스에 있는 대상 항목은 유지한다."""
        src, dst = sync_dirs
        _make_skill(src, "jin-commit")
        _make_skill(src, "py-standard")
        _make_skill(dst, "jin-commit", "old")
        _make_skill(dst, "py-standard", "old")

        sync_directory(src, dst)

        assert (dst / "jin-commit").exists()
        assert (dst / "py-standard").exists()

    def test_nonexistent_src_returns_zero(self, sync_dirs: tuple[Path, Path]) -> None:
        """소스 디렉토리가 없으면 0을 반환한다."""
        src, dst = sync_dirs
        shutil.rmtree(src)

        count = sync_directory(src, dst)

        assert count == 0

    def test_empty_src_removes_all_dst_items(self, sync_dirs: tuple[Path, Path]) -> None:
        """소스가 비어있으면 대상의 모든 항목을 제거한다."""
        src, dst = sync_dirs
        _make_skill(dst, "zy-commit")
        _make_skill(dst, "zy-interview")

        sync_directory(src, dst)

        assert list(dst.iterdir()) == []

    def test_nested_files_copied(self, sync_dirs: tuple[Path, Path]) -> None:
        """중첩된 파일 구조도 올바르게 복사된다."""
        src, dst = sync_dirs
        skill_dir = src / "jin-init" / "scripts"
        skill_dir.mkdir(parents=True)
        (skill_dir / "setup.py").write_text("setup")
        (src / "jin-init" / "SKILL.md").write_text("init skill")

        count = sync_directory(src, dst)

        assert count == 2
        assert (dst / "jin-init" / "scripts" / "setup.py").read_text() == "setup"
        assert (dst / "jin-init" / "SKILL.md").read_text() == "init skill"


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
