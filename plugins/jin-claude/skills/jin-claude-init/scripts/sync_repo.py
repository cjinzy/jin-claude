"""jin-claude git repo에서 statusline·설정·venv를 동기화하는 스크립트.

repo를 https 로 clone/pull 한 후, 개별 파일을 ~/.claude/ 하위에 복사하고
가상환경과 사용량 타이머를 설치한다. 내용이 바뀌는 기존 파일은
<stem>_backup_<YYYYMMDD><ext> 로 백업하고 변경을 report_changes 에 기록한다.
"""

import shutil
import subprocess
import sys
import traceback
from pathlib import Path

from report_changes import backup_path, text_diff, track_write

REPO_URL = "https://github.com/cjinzy/jin-claude.git"
REPO_DIR = Path.home() / ".claude" / ".jin-claude-repo"
CLAUDE_DIR = Path.home() / ".claude"
VENV_DIR = Path.home() / ".claude" / ".venv"
CACHE_BASE = Path.home() / ".claude" / "plugins" / "cache" / "jin-claudecode-mp" / "jin-claude"

# CLAUDE.md 가 @include 하는 보조 문서. 함께 복사하지 않으면 참조가 깨진다.
CLAUDE_INCLUDES = (
    "mcp-servers.md",
    "memory-routing.md",
    "backend-spec.md",
    "frontend-spec.md",
)

# (repo 상대 소스 경로, 대상 경로). agents/skills/hooks 는 plugin install 이 처리.
SYNC_FILES = [
    ("plugins/jin-claude/scripts/statusline-command.sh", CLAUDE_DIR / "statusline-command.sh"),
    (".claude/CLAUDE.md", CLAUDE_DIR / "CLAUDE.md"),
    *[(f".claude/{name}", CLAUDE_DIR / name) for name in CLAUDE_INCLUDES],
]


def run_git(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """git 명령어를 실행한다.

    Args:
        *args: git 하위 명령어 및 인자.
        cwd: 작업 디렉토리.

    Returns:
        CompletedProcess 결과.
    """
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return result


def clone_or_pull() -> Path:
    """repo를 clone하거나 기존 clone을 pull한다.

    Returns:
        repo 디렉토리 경로.
    """
    if (REPO_DIR / ".git").exists():
        print(f"[sync_repo] 기존 repo 업데이트: {REPO_DIR}")
        # 과거 SSH clone 도 https 로 전환 (SSH 키 없는 팀원 대응)
        run_git("remote", "set-url", "origin", REPO_URL, cwd=REPO_DIR)
        result = run_git("pull", "--ff-only", cwd=REPO_DIR)
        if result.returncode != 0:
            aside = backup_path(REPO_DIR)
            if aside.exists():
                # ponytail: 그날 백업 유지 — 현재 clone 은 오늘 재clone 된 사본이라 삭제.
                shutil.rmtree(REPO_DIR)
            else:
                REPO_DIR.rename(aside)
            print(
                f"[sync_repo] 경고: pull 실패 → 기존 clone 을 {aside} 로 보존, re-clone\n"
                f"{result.stderr}",
                file=sys.stderr,
            )
            return clone_or_pull()
        print(f"[sync_repo] pull 완료: {result.stdout.strip()}")
    else:
        print(f"[sync_repo] repo clone: {REPO_URL}")
        REPO_DIR.parent.mkdir(parents=True, exist_ok=True)
        result = run_git("clone", REPO_URL, str(REPO_DIR))
        if result.returncode != 0:
            print(f"[sync_repo] clone 실패: {result.stderr}", file=sys.stderr)
            sys.exit(1)
        print("[sync_repo] clone 완료")
    return REPO_DIR


def sync_file(src: Path, dst: Path) -> bool:
    """단일 파일을 복사한다. 내용이 바뀌는 기존 파일은 날짜 백업 후 덮어쓴다.

    Args:
        src: 소스 파일.
        dst: 대상 파일 경로.

    Returns:
        동기화 여부 (소스 없으면 False).
    """
    if not src.exists():
        print(f"[sync_repo] 소스 파일 없음, 건너뜀: {src}")
        return False

    unchanged = dst.exists() and dst.read_bytes() == src.read_bytes()
    diff = None
    if dst.exists() and not unchanged:
        old, new = (p.read_text(encoding="utf-8", errors="replace") for p in (dst, src))
        diff = text_diff(old, new)
    if track_write(dst, unchanged, diff):
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    return True


def find_uv() -> str | None:
    """시스템에서 uv 실행 파일 경로를 탐색한다.

    Returns:
        uv 경로 문자열, 없으면 None.
    """
    try:
        result = subprocess.run(
            ["which", "uv"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except subprocess.TimeoutExpired:
        print("[sync_repo] uv 탐색 타임아웃")
    except OSError:
        print("[sync_repo] uv 탐색 실패 (OSError)")
    return None


def _install_with_uv(uv_path: str, repo_dir: Path, venv_dir: Path) -> bool:
    """uv를 사용하여 venv 생성 및 패키지 설치를 수행한다.

    Args:
        uv_path: uv 실행 파일 경로.
        repo_dir: pyproject.toml이 있는 저장소 디렉토리.
        venv_dir: 생성할 가상환경 디렉토리.

    Returns:
        설치 성공 여부.
    """
    if not venv_dir.exists():
        print(f"[sync_repo] uv venv 생성: {venv_dir}")
        result = subprocess.run(
            [uv_path, "venv", str(venv_dir), "--python", "3.12"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            print(f"[sync_repo] uv venv 생성 실패: {result.stderr}")
            return False
    else:
        print(f"[sync_repo] 기존 venv 재사용: {venv_dir}")

    print("[sync_repo] uv pip install 실행")
    result = subprocess.run(
        [uv_path, "pip", "install", "-e", str(repo_dir),
         "--python", str(venv_dir / "bin" / "python")],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        print(f"[sync_repo] uv pip install 실패: {result.stderr}")
        return False

    print("[sync_repo] uv 패키지 설치 완료")
    return True


def _install_with_pip(repo_dir: Path, venv_dir: Path) -> bool:
    """python3 venv + pip를 사용하여 패키지 설치를 수행한다.

    uv가 없을 때 fallback으로 사용된다.

    Args:
        repo_dir: pyproject.toml이 있는 저장소 디렉토리.
        venv_dir: 생성할 가상환경 디렉토리.

    Returns:
        설치 성공 여부.
    """
    if not venv_dir.exists():
        print(f"[sync_repo] python3 venv 생성: {venv_dir}")
        result = subprocess.run(
            ["python3", "-m", "venv", str(venv_dir)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            print(f"[sync_repo] venv 생성 실패: {result.stderr}")
            return False
    else:
        print(f"[sync_repo] 기존 venv 재사용: {venv_dir}")

    pip_path = str(venv_dir / "bin" / "pip")
    print("[sync_repo] pip install 실행")
    result = subprocess.run(
        [pip_path, "install", "-e", str(repo_dir)],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        print(f"[sync_repo] pip install 실패: {result.stderr}")
        return False

    print("[sync_repo] pip 패키지 설치 완료")
    return True


def ensure_venv(repo_dir: Path, venv_dir: Path | None = None) -> bool:
    """가상환경을 생성하고 패키지를 설치한다.

    pyproject.toml이 존재할 때만 실행한다. uv를 우선 사용하고,
    없으면 pip로 fallback한다.

    Args:
        repo_dir: pyproject.toml이 있는 저장소 디렉토리.
        venv_dir: 가상환경 디렉토리. None이면 VENV_DIR 사용.

    Returns:
        설치 성공 여부 (pyproject.toml 미존재 시 False).
    """
    if venv_dir is None:
        venv_dir = VENV_DIR

    pyproject = repo_dir / "pyproject.toml"
    if not pyproject.exists():
        print(f"[sync_repo] pyproject.toml 없음, venv 생성 건너뜀: {pyproject}")
        return False

    uv_path = find_uv()
    if uv_path:
        print(f"[sync_repo] uv 발견: {uv_path}")
        if _install_with_uv(uv_path, repo_dir, venv_dir):
            return True
        print("[sync_repo] uv 설치 실패, pip fallback 시도")

    return _install_with_pip(repo_dir, venv_dir)


def clean_stale_cache(cache_dir: Path | None = None) -> int:
    """플러그인 캐시에서 구버전을 제거하고 최신 버전만 유지한다.

    Args:
        cache_dir: 캐시 디렉토리. None이면 CACHE_BASE 사용.

    Returns:
        제거된 구버전 수.
    """
    base = cache_dir or CACHE_BASE
    if not base.exists():
        return 0
    versions = sorted(
        [d for d in base.iterdir() if d.is_dir() and d.name[0].isdigit()],
        key=lambda d: d.name,
    )
    if len(versions) <= 1:
        return 0
    stale = versions[:-1]
    for v in stale:
        shutil.rmtree(v)
        print(f"[sync_repo] 구버전 캐시 제거: {v.name}")
    return len(stale)


def install_timer(repo_dir: Path, interval_minutes: int = 5) -> None:
    """OS별 타이머를 설치한다 (install-timer.sh가 Darwin/Linux 자동 감지).

    Args:
        repo_dir: install-timer.sh가 위치한 저장소 루트 디렉토리.
        interval_minutes: 사용량 수집 주기 (1, 3, 5, 10분). 기본값 5분.
    """
    install_script = repo_dir / "plugins" / "jin-claude" / "scripts" / "install-timer.sh"
    if not install_script.exists():
        print("[sync_repo] install-timer.sh 없음, timer 설치 건너뜀")
        return
    try:
        result = subprocess.run(
            ["bash", str(install_script), str(interval_minutes)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            print(f"[sync_repo] timer 설치 완료 (주기: {interval_minutes}분)")
        else:
            print(f"[sync_repo] timer 설치 실패: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("[sync_repo] timer 설치 타임아웃")
    except OSError as e:
        print(f"[sync_repo] timer 설치 오류: {e}")


def main() -> None:
    """메인 진입점."""
    try:
        repo_dir = clone_or_pull()

        removed = clean_stale_cache()
        if removed:
            print(f"[sync_repo] 구버전 캐시 {removed}개 제거 완료")

        for file_name, target in SYNC_FILES:
            src = repo_dir / file_name
            ok = sync_file(src, target)
            status = "완료" if ok else "건너뜀"
            print(f"[sync_repo] {file_name} → {target}: {status}")

        ok = ensure_venv(repo_dir)
        status = "완료" if ok else "건너뜀"
        print(f"[sync_repo] venv 패키지 설치: {status}")

        # CLI 인자로 timer 주기를 받음 (기본값: 5분)
        interval = 5
        if len(sys.argv) > 1:
            try:
                interval = int(sys.argv[1])
                if interval not in (1, 3, 5, 10):
                    print(f"[sync_repo] 잘못된 주기 {interval}분, 기본값 5분 사용")
                    interval = 5
            except ValueError:
                print(f"[sync_repo] 잘못된 인자 '{sys.argv[1]}', 기본값 5분 사용")
        install_timer(repo_dir, interval_minutes=interval)

        print("[sync_repo] 동기화 완료")
    except Exception:
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
