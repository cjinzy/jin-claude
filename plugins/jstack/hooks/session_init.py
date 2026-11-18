#!/usr/bin/env python3
"""세션 시작 시 구버전 스킬 사본 정리 + 사용량 타이머 복구 + marketplace 자동 업데이트.

SessionStart hook (hooks/hooks.json). stdout 은 대화 컨텍스트에 주입되므로 쓰지 않는다.
"""

import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# sync_repo.py 가 clone 하는 저장소 — 존재 = init 이력 있음
TIMER_INSTALLER = Path(".claude/.jin-claude-repo/plugins/jstack/scripts/install-timer.sh")
# install-timer.sh 가 만드는 OS별 타이머 파일 (HOME 기준)
TIMER_MARKERS = {
    "darwin": Path("Library/LaunchAgents/com.jin-claude.fetch-usage.plist"),
    "linux": Path(".config/systemd/user/fetch-claude-usage.timer"),
}
# init 이 고른 수집 주기(분). sync_repo.py INTERVAL_FILE 과 같은 파일
# (hooks/ 와 scripts/ 는 서로 import 하지 않는다).
INTERVAL_FILE = Path(".claude/.jin-claude-usage-interval")
INTERVALS_MIN = (1, 3, 5, 10)  # install-timer.sh 허용값
DEFAULT_INTERVAL_MIN = 5
# hooks.json timeout(10s) 안에 끝나야 hook 이 강제 종료되지 않는다
GIT_PULL_TIMEOUT_SEC = 8
# 구버전(≤3.x) sync_repo 가 ~/.claude/skills 에 복사한 스킬 중 plugin 과 이름이 겹치거나(사용자 스킬이
# plugin 스킬을 가림) 제거된 것. 다른 legacy 이름(py-standard 등)은 충돌이 없어 사용자 판단에 맡긴다.
LEGACY_SKILLS = {"jin-claude-init", "jin-commit", "jin-interview", "manage-skills", "verify-implementation"}


def auto_update() -> None:
    """jstack marketplace repo를 자동 업데이트한다."""
    base = Path.home() / ".claude" / "plugins" / "marketplaces"
    if not base.exists():
        return
    for mp_dir in base.iterdir():
        jin_dir = mp_dir / "plugins" / "jstack"
        if jin_dir.is_dir():
            try:
                result = subprocess.run(
                    ["git", "-C", str(mp_dir), "pull", "--ff-only"],
                    capture_output=True,
                    text=True,
                    timeout=GIT_PULL_TIMEOUT_SEC,
                )
                if result.returncode != 0:
                    print(
                        f"[jstack] warning: auto-update failed for {mp_dir.name}",
                        file=sys.stderr,
                    )
            except subprocess.TimeoutExpired:
                print(
                    f"[jstack] warning: auto-update timeout for {mp_dir.name}",
                    file=sys.stderr,
                )
            except OSError as e:
                print(
                    f"[jstack] warning: auto-update error for {mp_dir.name}: {e}",
                    file=sys.stderr,
                )


def retire_legacy_skills() -> None:
    """LEGACY_SKILLS 사본을 ~/.claude/backups/skills_backup_<YYYYMMDD>/ 로 옮긴다 (삭제 아님)."""
    skills = Path.home() / ".claude" / "skills"
    now = datetime.now()
    for name in sorted(LEGACY_SKILLS):
        src = skills / name
        if not src.exists() and not src.is_symlink():
            continue
        dest = Path.home() / ".claude" / "backups" / f"skills_backup_{now:%Y%m%d}" / name
        if dest.exists():
            dest = dest.with_name(f"{name}_{now:%H%M%S%f}")
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), dest)
            print(f"[jstack] retired legacy skill {src} -> {dest}", file=sys.stderr)
        except OSError as e:
            print(f"[jstack] warning: retire {src} failed: {e!r}", file=sys.stderr)


def saved_interval(home: Path) -> int:
    """init 이 저장한 수집 주기. 없거나 정수 아님·허용값 밖이면 기본값."""
    try:
        minutes = int((home / INTERVAL_FILE).read_text())
    except (OSError, ValueError):
        return DEFAULT_INTERVAL_MIN
    return minutes if minutes in INTERVALS_MIN else DEFAULT_INTERVAL_MIN


def ensure_timer() -> None:
    """사용량 수집 타이머가 사라졌으면 init 때 고른 주기로 재등록한다.

    타이머는 init 때 한 번만 설치되므로, OS 업그레이드·정리 도구 등으로
    plist/timer 가 지워지면 캐시 갱신이 조용히 멈춘다. 매 세션 파일 존재만 확인.
    """
    home = Path.home()
    marker = TIMER_MARKERS.get(sys.platform)
    installer = home / TIMER_INSTALLER
    if marker is None or not installer.is_file() or (home / marker).exists():
        return
    # 분리 실행: 설치 스크립트의 초기 fetch 가 hook timeout(10s)을 넘길 수 있음.
    # ponytail: 실패해도 marker 가 없으니 다음 세션이 재시도. 동시 세션 경합은 무시.
    try:
        subprocess.Popen(
            ["bash", str(installer), str(saved_interval(home))],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as e:
        print(f"[jstack] warning: timer reinstall error: {e!r}", file=sys.stderr)


def main() -> None:
    """메인 진입점."""
    retire_legacy_skills()  # 빠름 — 사본이 plugin 스킬을 가리기 전에
    ensure_timer()  # 빠름 — 느린 git pull 보다 먼저
    auto_update()


if __name__ == "__main__":
    main()
