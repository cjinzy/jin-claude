"""sync_repo 모듈의 단위 테스트."""

import subprocess
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import report_changes
import sync_repo
from sync_repo import clean_stale_cache, clone_or_pull, install_timer, sync_file


def _make_result(returncode: int = 0, stdout: str = "", stderr: str = "") -> MagicMock:
    """subprocess.CompletedProcess mock을 생성한다."""
    result = MagicMock(spec=subprocess.CompletedProcess)
    result.returncode = returncode
    result.stdout = stdout
    result.stderr = stderr
    return result


TODAY = date.today().strftime(report_changes.DATE_FORMAT)


class TestCloneOrPull:
    """clone_or_pull() — https origin 강제, pull 실패 시 기존 clone 보존."""

    @pytest.fixture
    def repo(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
        repo = tmp_path / ".jin-claude-repo"
        (repo / ".git").mkdir(parents=True)
        (repo / "local.txt").write_text("local edit")
        monkeypatch.setattr(sync_repo, "REPO_DIR", repo)
        return repo

    def test_repo_url_is_https(self) -> None:
        assert sync_repo.REPO_URL == "https://github.com/cjinzy/jin-claude.git"

    def test_switches_origin_to_https_before_pull(self, repo: Path) -> None:
        with patch("sync_repo.run_git", return_value=_make_result(0)) as git:
            clone_or_pull()
        calls = [c.args for c in git.call_args_list]
        assert calls[0] == ("remote", "set-url", "origin", sync_repo.REPO_URL)
        assert calls[1] == ("pull", "--ff-only")

    def test_pull_failure_moves_clone_aside(self, repo: Path) -> None:
        def fake_git(*args: str, cwd: Path | None = None) -> MagicMock:
            if args[0] == "pull":
                return _make_result(1, stderr="diverged")
            if args[0] == "clone":
                Path(args[2]).mkdir()
            return _make_result(0)

        with patch("sync_repo.run_git", side_effect=fake_git):
            clone_or_pull()
        aside = repo.parent / f".jin-claude-repo_backup_{TODAY}"
        assert (aside / "local.txt").read_text() == "local edit"
        assert repo.exists()


class TestSyncFile:
    """sync_file() — 변경 시에만 날짜 백업 후 덮어쓰기."""

    def test_changed_file_backed_up(self, tmp_path: Path) -> None:
        src, dst = tmp_path / "src.md", tmp_path / "CLAUDE.md"
        src.write_text("new")
        dst.write_text("old")
        assert sync_file(src, dst) is True
        assert dst.read_text() == "new"
        assert (tmp_path / f"CLAUDE_backup_{TODAY}.md").read_text() == "old"
        assert not (tmp_path / "CLAUDE.md.bak").exists()

    def test_changed_file_records_line_diff(self, tmp_path: Path) -> None:
        src, dst = tmp_path / "src.md", tmp_path / "CLAUDE.md"
        src.write_text("keep\nnew\n")
        dst.write_text("keep\nold\n")
        sync_file(src, dst)
        diff = report_changes.load_report()[str(dst)]["diff"]
        assert diff == {"plus": 1, "minus": 1, "lines": ["-old", "+new"]}

    def test_unchanged_file_no_backup(self, tmp_path: Path) -> None:
        src, dst = tmp_path / "src.md", tmp_path / "CLAUDE.md"
        src.write_text("same")
        dst.write_text("same")
        assert sync_file(src, dst) is True
        assert not (tmp_path / f"CLAUDE_backup_{TODAY}.md").exists()
        assert report_changes.load_report()[str(dst)]["status"] == report_changes.UNCHANGED

    def test_new_file_recorded(self, tmp_path: Path) -> None:
        src, dst = tmp_path / "src.sh", tmp_path / "sub" / "statusline-command.sh"
        src.write_text("echo")
        assert sync_file(src, dst) is True
        assert dst.read_text() == "echo"
        assert report_changes.load_report()[str(dst)]["status"] == report_changes.NEW

    def test_missing_source_skipped(self, tmp_path: Path) -> None:
        assert sync_file(tmp_path / "nope", tmp_path / "dst") is False


class TestCleanStaleCache:
    """clean_stale_cache() 테스트 스위트."""

    def test_no_cache_dir(self, tmp_path: Path) -> None:
        """캐시 디렉토리가 없으면 0을 반환한다."""
        nonexistent = tmp_path / "nonexistent"
        assert clean_stale_cache(nonexistent) == 0

    def test_single_version_kept(self, tmp_path: Path) -> None:
        """버전이 1개뿐이면 제거하지 않는다."""
        (tmp_path / "1.0.0").mkdir()
        assert clean_stale_cache(tmp_path) == 0
        assert (tmp_path / "1.0.0").exists()

    def test_removes_old_versions(self, tmp_path: Path) -> None:
        """구버전을 제거하고 최신 버전만 유지한다."""
        (tmp_path / "1.0.0").mkdir()
        (tmp_path / "2.0.0").mkdir()
        (tmp_path / "2.1.0").mkdir()

        removed = clean_stale_cache(tmp_path)

        assert removed == 2
        assert not (tmp_path / "1.0.0").exists()
        assert not (tmp_path / "2.0.0").exists()
        assert (tmp_path / "2.1.0").exists()

    def test_ignores_non_version_dirs(self, tmp_path: Path) -> None:
        """숫자로 시작하지 않는 디렉토리는 무시한다."""
        (tmp_path / "1.0.0").mkdir()
        (tmp_path / "2.0.0").mkdir()
        (tmp_path / ".tmp").mkdir()

        removed = clean_stale_cache(tmp_path)

        assert removed == 1
        assert (tmp_path / ".tmp").exists()
        assert (tmp_path / "2.0.0").exists()

    def test_empty_cache_dir(self, tmp_path: Path) -> None:
        """빈 캐시 디렉토리이면 0을 반환한다."""
        assert clean_stale_cache(tmp_path) == 0


class TestInstallTimer:
    """install_timer() 테스트 스위트."""

    @patch("sync_repo.subprocess.run")
    def test_script_not_found(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """install-timer.sh가 없으면 건너뛴다."""
        install_timer(tmp_path)
        mock_run.assert_not_called()

    @patch("sync_repo.subprocess.run")
    def test_success(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """install-timer.sh 실행 성공."""
        script = tmp_path / "plugins" / "jin-claude" / "scripts" / "install-timer.sh"
        script.parent.mkdir(parents=True)
        script.write_text("#!/bin/bash\necho ok")

        mock_run.return_value = _make_result(0)
        install_timer(tmp_path, interval_minutes=5)
        mock_run.assert_called_once()

    @patch("sync_repo.subprocess.run")
    def test_failure(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """install-timer.sh 실행 실패 시 오류 메시지 출력."""
        script = tmp_path / "plugins" / "jin-claude" / "scripts" / "install-timer.sh"
        script.parent.mkdir(parents=True)
        script.write_text("#!/bin/bash\nexit 1")

        mock_run.return_value = _make_result(1, stderr="error")
        install_timer(tmp_path)
        mock_run.assert_called_once()

    @patch("sync_repo.subprocess.run")
    def test_timeout(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """타임아웃 시 오류 메시지 출력."""
        script = tmp_path / "plugins" / "jin-claude" / "scripts" / "install-timer.sh"
        script.parent.mkdir(parents=True)
        script.write_text("#!/bin/bash\nsleep 100")

        mock_run.side_effect = subprocess.TimeoutExpired(cmd="bash", timeout=60)
        install_timer(tmp_path)

    @patch("sync_repo.subprocess.run")
    def test_os_error(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """OSError 발생 시 오류 메시지 출력."""
        script = tmp_path / "plugins" / "jin-claude" / "scripts" / "install-timer.sh"
        script.parent.mkdir(parents=True)
        script.write_text("#!/bin/bash")

        mock_run.side_effect = OSError("permission denied")
        install_timer(tmp_path)


REPO_CLAUDE_DIR = Path(__file__).resolve().parents[5] / ".claude"


class TestClaudeIncludes:
    """배포 CLAUDE.md 가 @include 하는 문서 집합 == sync 대상 (깨진 참조·고아 파일 방지)."""

    def _referenced(self) -> set[str]:
        import re

        seen, todo = set(), ["CLAUDE.md"]
        while todo:
            text = (REPO_CLAUDE_DIR / todo.pop()).read_text()
            for name in re.findall(r"@([\w.-]+\.md)", text):
                if name not in seen:
                    seen.add(name)
                    todo.append(name)
        return seen

    def test_includes_match_references(self) -> None:
        assert set(sync_repo.CLAUDE_INCLUDES) == self._referenced()

    def test_includes_exist(self) -> None:
        missing = [n for n in sync_repo.CLAUDE_INCLUDES if not (REPO_CLAUDE_DIR / n).is_file()]
        assert not missing
