"""jin-claude git repo에서 agents와 skills를 동기화하는 스크립트.

repo를 clone/pull 한 후, agents와 skills 디렉토리의 파일을
~/.claude/ 하위에 복사한다.
"""

import shutil
import subprocess
import sys
import traceback
from pathlib import Path

REPO_URL = "http://192.168.254.206:5000/jin/jin-claude.git"
REPO_DIR = Path.home() / ".claude" / ".jin-claude-repo"
CLAUDE_DIR = Path.home() / ".claude"
VENV_DIR = Path.home() / ".claude" / ".venv"

SYNC_TARGETS = [
    (".claude/agents", CLAUDE_DIR / "agents"),
    (".claude/skills", CLAUDE_DIR / "skills"),
]

SYNC_FILES = [
    (".claude/script/statusline-command.sh", CLAUDE_DIR / "statusline-command.sh"),
    (".claude/CLAUDE.md", CLAUDE_DIR / "CLAUDE.md"),
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
        result = run_git("pull", "--ff-only", cwd=REPO_DIR)
        if result.returncode != 0:
            print(f"[sync_repo] pull 실패, re-clone 시도: {result.stderr}")
            shutil.rmtree(REPO_DIR)
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


def sync_directory(src: Path, dst: Path) -> int:
    """소스 디렉토리의 파일을 대상 디렉토리로 복사한다.

    기존 파일은 덮어쓴다. 소스에 없는 대상 파일은 유지한다.

    Args:
        src: 소스 디렉토리.
        dst: 대상 디렉토리.

    Returns:
        복사된 파일 수.
    """
    if not src.exists():
        print(f"[sync_repo] 소스 디렉토리 없음, 건너뜀: {src}")
        return 0

    dst.mkdir(parents=True, exist_ok=True)
    count = 0

    for item in src.rglob("*"):
        if item.is_file():
            rel = item.relative_to(src)
            target = dst / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)
            count += 1

    return count


def sync_file(src: Path, dst: Path) -> bool:
    """단일 파일을 복사한다.

    Args:
        src: 소스 파일.
        dst: 대상 파일 경로.

    Returns:
        복사 성공 여부.
    """
    if not src.exists():
        print(f"[sync_repo] 소스 파일 없음, 건너뜀: {src}")
        return False

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


def install_superclaude() -> bool:
    """SuperClaude Framework를 pipx로 설치한다.

    pipx가 없으면 pip install --user로 fallback한다.
    설치 성공 시 superclaude install을 실행하여 초기화한다.

    Returns:
        설치 성공 여부.
    """
    # pipx 시도
    try:
        result = subprocess.run(
            ["pipx", "install", "superclaude"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            print("[sync_repo] pipx install superclaude 완료")
            init_result = subprocess.run(
                ["superclaude", "install"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if init_result.returncode == 0:
                print("[sync_repo] superclaude install 완료")
            else:
                print(f"[sync_repo] superclaude install 실패: {init_result.stderr}")
            return True
        print(f"[sync_repo] pipx install 실패: {result.stderr}")
    except FileNotFoundError:
        print("[sync_repo] pipx 미설치, pip fallback 시도")
    except subprocess.TimeoutExpired:
        print("[sync_repo] pipx install 타임아웃, pip fallback 시도")

    # pip --user fallback
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--user", "superclaude"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            print("[sync_repo] pip install --user superclaude 완료")
            init_result = subprocess.run(
                ["superclaude", "install"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if init_result.returncode == 0:
                print("[sync_repo] superclaude install 완료")
            else:
                print(f"[sync_repo] superclaude install 실패: {init_result.stderr}")
            return True
        print(f"[sync_repo] pip install --user 실패: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("[sync_repo] pip install --user 타임아웃")

    return False


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


def main() -> None:
    """메인 진입점."""
    try:
        repo_dir = clone_or_pull()

        for dir_name, target in SYNC_TARGETS:
            src = repo_dir / dir_name
            count = sync_directory(src, target)
            print(f"[sync_repo] {dir_name}/ → {target}: {count}개 파일 동기화")

        for file_name, target in SYNC_FILES:
            src = repo_dir / file_name
            ok = sync_file(src, target)
            status = "완료" if ok else "건너뜀"
            print(f"[sync_repo] {file_name} → {target}: {status}")

        ok = ensure_venv(repo_dir)
        status = "완료" if ok else "건너뜀"
        print(f"[sync_repo] venv 패키지 설치: {status}")

        ok = install_superclaude()
        status = "완료" if ok else "건너뜀"
        print(f"[sync_repo] SuperClaude 설치: {status}")

        print("[sync_repo] 동기화 완료")
    except Exception:
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
