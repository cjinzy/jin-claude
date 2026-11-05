#!/usr/bin/env python3
"""세션 시작 시 jin-claude 자동 업데이트 및 초기화를 수행한다.

SessionStart hook으로 사용된다.
기존 bash SessionStart hook을 Python으로 이전한 버전.
"""

import json
import subprocess
import sys
from pathlib import Path

# sync_repo.py 가 clone 하는 저장소 — 존재 = init 이력 있음
TIMER_INSTALLER = Path(".claude/.jin-claude-repo/plugins/jin-claude/scripts/install-timer.sh")
# install-timer.sh 가 만드는 OS별 타이머 파일 (HOME 기준)
TIMER_MARKERS = {
    "darwin": Path("Library/LaunchAgents/com.jin-claude.fetch-usage.plist"),
    "linux": Path(".config/systemd/user/fetch-claude-usage.timer"),
}
DEFAULT_INTERVAL_MIN = "5"


def auto_update() -> None:
    """jin-claude marketplace repo를 자동 업데이트한다."""
    base = Path.home() / ".claude" / "plugins" / "marketplaces"
    if not base.exists():
        return
    for mp_dir in base.iterdir():
        jin_dir = mp_dir / "plugins" / "jin-claude"
        if jin_dir.is_dir():
            try:
                result = subprocess.run(
                    ["git", "-C", str(mp_dir), "pull", "--ff-only"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode != 0:
                    print(
                        f"[jin-claude] warning: auto-update failed for {mp_dir.name}",
                        file=sys.stderr,
                    )
            except subprocess.TimeoutExpired:
                print(
                    f"[jin-claude] warning: auto-update timeout for {mp_dir.name}",
                    file=sys.stderr,
                )
            except OSError as e:
                print(
                    f"[jin-claude] warning: auto-update error for {mp_dir.name}: {e}",
                    file=sys.stderr,
                )


def ensure_timer() -> None:
    """사용량 수집 타이머가 사라졌으면 재등록한다.

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
            ["bash", str(installer), DEFAULT_INTERVAL_MIN],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as e:
        print(f"[jin-claude] warning: timer reinstall error: {e!r}", file=sys.stderr)


def main() -> None:
    """메인 진입점."""
    auto_update()
    ensure_timer()
    print(json.dumps({"result": "approve"}))


if __name__ == "__main__":
    main()
